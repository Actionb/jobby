from datetime import datetime
from unittest.mock import Mock, patch

# noinspection PyPackageRequirements
import pytest
from django.db import models
from django.urls import path
from django.utils.timezone import make_aware
from jobby.models import _as_dict, _update_stellenangebot

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


def test_update_stellenangebot(stellenangebot, other):
    assert _update_stellenangebot(stellenangebot, other)
    stellenangebot.refresh_from_db()
    assert stellenangebot.titel == other.titel
    assert stellenangebot.beruf == other.beruf


def test_update_stellenangebot_identical(stellenangebot, django_assert_num_queries):
    with django_assert_num_queries(0):
        assert not _update_stellenangebot(stellenangebot, stellenangebot)


def test_update_stellenangebot_different_refnr(stellenangebot, other, django_assert_num_queries):
    other.refnr = "1"
    with django_assert_num_queries(0):
        assert not _update_stellenangebot(stellenangebot, other)


class AsDictTestModel(models.Model):
    name = models.CharField(max_length=10)
    empty = models.CharField(max_length=10, blank=True, null=True)
    default = models.CharField(max_length=10, default="default")


def test_as_dict():
    instance = AsDictTestModel(name="test")
    expected = {"id": None, "name": "test", "empty": None, "default": "default"}
    assert _as_dict(instance, empty=True, default=True) == expected


def test_as_dict_ignores_empty_values():
    instance = AsDictTestModel(name="test", default="not default")
    expected = {"name": "test", "default": "not default"}
    assert _as_dict(instance, empty=False) == expected


def test_as_dict_ignores_default_values():
    instance = AsDictTestModel(name="test", empty="not empty")
    expected = {"name": "test", "empty": "not empty"}
    assert _as_dict(instance, default=False) == expected


urlpatterns = [
    path("foo/<int:id>", lambda r: None, name="stellenangebot_edit"),
    path("foo/", lambda r: None, name="stellenangebot_add"),
]


@pytest.mark.urls(__name__)
class TestStellenangebot:

    def test_as_url_saved_instance(self, stellenangebot):
        assert stellenangebot.as_url() == f"/foo/{stellenangebot.pk}"

    def test_as_url_unsaved_instance(self):
        stellenangebot = StellenangebotFactory.build()
        with patch("jobby.models._as_dict", new=Mock(return_value={"titel": "foo", "refnr": 1234})):
            assert stellenangebot.as_url() == "/foo/?titel=foo&refnr=1234"


class TestWatchlist:

    def test_add_watchlist_item(self, watchlist, stellenangebot):
        added = watchlist.add_watchlist_item(stellenangebot)
        assert added
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_add_watchlist_item_already_on_watchlist(self, watchlist, watchlist_item, stellenangebot):
        added = watchlist.add_watchlist_item(stellenangebot)
        assert not added
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_remove_watchlist_item(self, watchlist, watchlist_item, stellenangebot):
        watchlist.remove_watchlist_item(stellenangebot)
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_get_stellenangebote(self, watchlist, watchlist_item, stellenangebot, django_assert_num_queries):
        with django_assert_num_queries(1):
            assert stellenangebot in watchlist.get_stellenangebote()
