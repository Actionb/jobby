from datetime import datetime
from unittest.mock import Mock, create_autospec, patch

# noinspection PyPackageRequirements
import pytest
from django.core.files import File
from django.db import models
from django.urls import path
from django.utils.timezone import make_aware
from jobby.forms import StellenangebotForm
from jobby.models import Stellenangebot, StellenangebotKontakt, _as_dict, _update_stellenangebot

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def other(refnr):
    return StellenangebotFactory.build(
        titel="Software Entwickler",
        refnr=refnr,
        beruf="",
        arbeitgeber="IHK Dortmund",
        arbeitsort="Dortmund",
        eintrittsdatum="2024-07-01",
        veroeffentlicht="2024-05-30",
        modified=make_aware(datetime.fromisoformat("2024-05-22T09:00:15.099")),
    )


class TestUpdateStellenangebot:

    def test_update_stellenangebot(self, stellenangebot, other):
        """
        Assert that ``_update_stellenangebot`` updates the given Stellenangebot
        instance with the data from the other.
        """
        assert _update_stellenangebot(stellenangebot, other)
        stellenangebot.refresh_from_db()
        assert stellenangebot.titel == other.titel
        assert stellenangebot.beruf == other.beruf

    def test_update_stellenangebot_identical(self, stellenangebot, django_assert_num_queries):
        """
        Assert that ``_update_stellenangebot`` does not perform any queries if the
        two Stellenangebot arguments are identical.
        """
        with django_assert_num_queries(0):
            assert not _update_stellenangebot(stellenangebot, stellenangebot)

    def test_update_stellenangebot_different_refnr(self, stellenangebot, other, django_assert_num_queries):
        """
        Assert that ``_update_stellenangebot`` does not perform any queries if the
        two Stellenangebot do not have the same refnr.
        """
        other.refnr = "1"
        with django_assert_num_queries(0):
            assert not _update_stellenangebot(stellenangebot, other)

    def test_update_stellenangebot_not_stellenangebot_instances(self, stellenangebot, other):
        """
        Assert that ``_update_stellenangebot`` raises a TypeError if either of
        the arguments is not a Stellenangebot instance.
        """
        with pytest.raises(TypeError):
            _update_stellenangebot(stellenangebot, "foo")
        with pytest.raises(TypeError):
            _update_stellenangebot("bar", other)


class AsDictTestModel(models.Model):
    name = models.CharField(max_length=10)
    empty = models.CharField(max_length=10, blank=True, null=True)
    default = models.CharField(max_length=10, default="default")


class TestAsDict:
    def test_as_dict(self):
        """Assert that ``as_dict`` returns the expected result."""
        instance = AsDictTestModel(name="test")
        expected = {"id": None, "name": "test", "empty": None, "default": "default"}
        assert _as_dict(instance, empty=True, default=True) == expected

    def test_as_dict_ignores_empty_values(self):
        """
        Assert that ``as_dict`` filters out empty values if empty argument is
        False.
        """
        instance = AsDictTestModel(name="test", default="not default")
        expected = {"name": "test", "default": "not default"}
        assert _as_dict(instance, empty=False) == expected

    def test_as_dict_ignores_default_values(self):
        """Assert that ``as_dict`` filters out values that are a field's default."""
        instance = AsDictTestModel(name="test", empty="not empty")
        expected = {"name": "test", "empty": "not empty"}
        assert _as_dict(instance, default=False) == expected


urlpatterns = [
    path("foo/<int:id>", lambda r: None, name="stellenangebot_edit"),
    path("foo/", lambda r: None, name="stellenangebot_add"),
]


@pytest.mark.urls(__name__)
class TestStellenangebot:

    def test_str(self, stellenangebot):
        assert stellenangebot.__str__() == stellenangebot.titel

    def test_search_result_form(self, stellenangebot):
        form = stellenangebot.as_search_result_form()
        assert isinstance(form, StellenangebotForm)
        assert form.instance == stellenangebot

    def test_as_url_saved_instance(self, stellenangebot):
        """
        Assert that ``as_url`` returns the URL to the instance's edit page if
        the instance is saved.
        """
        assert stellenangebot.as_url() == f"/foo/{stellenangebot.pk}"

    def test_as_url_unsaved_instance(self):
        """
        Assert that ``as_url`` returns the URL to the add page if the instance
        is not saved.
        """
        stellenangebot = StellenangebotFactory.build()
        with patch("jobby.models._as_dict", new=Mock(return_value={"titel": "foo", "refnr": 1234})):
            assert stellenangebot.as_url() == "/foo/?titel=foo&refnr=1234"

    def test_has_user_data(self, stellenangebot):
        """
        Assert that ``has_user_data`` returns False if the user has not added
        any data to the user controlled fields or relations.
        """
        assert not stellenangebot.has_user_data()

    def test_has_user_data_has_notizen(self, stellenangebot):
        """
        Assert that ``has_user_data`` returns True if the instance has values
        in the 'notizen' field.
        """
        stellenangebot.notizen = "Foo"
        assert stellenangebot.has_user_data()

    def test_has_user_data_has_url(self, stellenangebot):
        """
        Assert that ``has_user_data`` returns True if the instance has any
        user-defined urls associated with it.
        """
        stellenangebot.urls.create(url="www.foobar.com")
        assert stellenangebot.has_user_data()

    def test_has_user_data_has_kontakte(self, stellenangebot):
        """
        Assert that ``has_user_data`` returns True if the instance has any
        user-defined contact data associated with it.
        """
        stellenangebot.kontakte.create(kontakt_typ=StellenangebotKontakt.TypChoices.TELEFON, kontakt_daten="1234")
        assert stellenangebot.has_user_data()

    def test_has_user_data_has_files(self, stellenangebot):
        """
        Assert that ``has_user_data`` returns True if the instance has any
        user-defined files associated with it.
        """
        file = create_autospec(File)
        file.name = "test_file"
        stellenangebot.files.create(file=file)
        assert stellenangebot.has_user_data()


class TestStellenangebotQuerySet:

    @pytest.fixture
    def titel_obj(self):
        """An object that should be found via its 'titel' field."""
        return StellenangebotFactory(titel="Software Developer")

    @pytest.fixture
    def beschreibung_obj(self):
        """An object that should be found via its 'beschreibung' field."""
        return StellenangebotFactory(titel="Fensterputzer", beschreibung="Kein Software Tester")

    @pytest.fixture
    def arbeitgeber_obj(self):
        """An object that should be found via its 'arbeitgeber' field."""
        return StellenangebotFactory(titel="Verkäufer", arbeitgeber="Software Incorporated")

    @pytest.fixture
    def arbeitsort_obj(self):
        """An object that should be found via its 'arbeitsort' field."""
        return StellenangebotFactory(titel="Feuerwehrmann", arbeitsort="Software City")

    @pytest.fixture
    def not_found_obj(self):
        """An object that should not appear in the search results."""
        return StellenangebotFactory(titel="Pilot", beschreibung="Fliegt.")

    @pytest.fixture
    def search_string(self):
        return "sftwr"

    @pytest.fixture
    def search_queryset(self, search_string):
        return Stellenangebot.objects.search(search_string)

    def test_search(self, titel_obj, beschreibung_obj, arbeitgeber_obj, not_found_obj, arbeitsort_obj, search_queryset):
        assert titel_obj in search_queryset
        assert beschreibung_obj in search_queryset
        assert arbeitgeber_obj in search_queryset
        assert arbeitsort_obj in search_queryset
        assert not_found_obj not in search_queryset


class TestWatchlist:

    def test_on_watchlist(self, watchlist, watchlist_item, stellenangebot):
        assert watchlist.on_watchlist(stellenangebot)

    def test_on_watchlist_not_on_watchlist(self, watchlist, stellenangebot):
        assert not watchlist.on_watchlist(stellenangebot)

    def test_add_watchlist_item(self, watchlist, stellenangebot):
        """
        Assert that ``add_watchlist_item`` adds the given Stellenangebot
        instance to the watchlist.
        """
        added = watchlist.add_watchlist_item(stellenangebot)
        assert added
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_add_watchlist_item_already_on_watchlist(self, watchlist, watchlist_item, stellenangebot):
        """
        Assert that ``add_watchlist_item`` does not add the given Stellenangebot
        instance to the watchlist if it is already on the watchlist.
        """
        added = watchlist.add_watchlist_item(stellenangebot)
        assert not added
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_remove_watchlist_item(self, watchlist, watchlist_item, stellenangebot):
        """
        Assert that ``remove_watchlist_item`` removes the given Stellenangebot
        instance from the watchlist.
        """
        stellenangebot_pk = stellenangebot.pk
        watchlist.remove_watchlist_item(stellenangebot)
        assert not watchlist.items.filter(stellenangebot_id=stellenangebot_pk).exists()

    def test_remove_watchlist_item_deletes_stellenangebote(self, watchlist, watchlist_item, stellenangebot):
        """
        Assert that ``remove_watchlist_item`` deletes the Stellenangebot
        instance if the user has not added extra data to it.
        """
        stellenangebot_pk = stellenangebot.pk
        with patch.object(stellenangebot, "has_user_data", new=Mock(return_value=False)):
            watchlist.remove_watchlist_item(stellenangebot)
            assert not Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()

    def test_remove_watchlist_item_stellenangebot_has_user_data(self, watchlist, watchlist_item, stellenangebot):
        """
        Assert that ``remove_watchlist_item`` does not delete the Stellenangebot
        instance if the user has added extra data to it.
        """
        stellenangebot_pk = stellenangebot.pk
        with patch.object(stellenangebot, "has_user_data", new=Mock(return_value=True)):
            watchlist.remove_watchlist_item(stellenangebot)
            assert Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()

    def test_get_stellenangebote(self, watchlist, watchlist_item, stellenangebot, django_assert_num_queries):
        """
        Assert that ``get_stellenangebote`` returns the Stellenangebot
        instances that are on the watchlist.
        """
        not_on_watchlist = StellenangebotFactory()
        with django_assert_num_queries(1):
            watchlist_stellenangebot = watchlist.get_stellenangebote()
            assert stellenangebot in watchlist_stellenangebot
            assert not_on_watchlist not in watchlist_stellenangebot
