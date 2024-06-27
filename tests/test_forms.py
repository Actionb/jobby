import datetime
from unittest.mock import PropertyMock, patch

import pytest
from django.core.exceptions import BadRequest
from jobby.forms import StellenangebotForm, SucheForm, WatchlistSearchForm
from jobby.models import Stellenangebot

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def form_data():
    return {}


@pytest.fixture
def initial_data():
    return {}


@pytest.fixture
def form(form_class, form_data, initial_data):
    return form_class(data=form_data, initial=initial_data)


class TestSucheForm:

    @pytest.fixture
    def form_class(self):
        return SucheForm

    @pytest.mark.parametrize("form_data", [{"was": "foo", "wo": "Dortmund", "arbeitgeber": "bar"}])
    def test_shown_fields(self, form, form_data):
        """
        Assert that ``shown_fields`` includes the 'always_shown' fields as well
        as any field with data.
        """
        assert len(form.shown_fields) == 4
        assert form["was"] in form.shown_fields
        assert form["wo"] in form.shown_fields
        assert form["umkreis"] in form.shown_fields
        assert form["arbeitgeber"] in form.shown_fields

    def test_collapsed_fields(self, form):
        """
        Assert that ``collapsed_fields`` excludes fields returned by
        ``shown_fields``.
        """
        with patch("jobby.forms.SucheForm.shown_fields", new=PropertyMock(return_value=[form["arbeitgeber"]])):
            assert form["arbeitgeber"] not in form.collapsed_fields


class TestStellenangebotForm:

    @pytest.fixture
    def form_class(self):
        return StellenangebotForm

    @pytest.fixture
    def cleaned_data(self, refnr):
        return {"refnr": refnr}

    @pytest.fixture
    def beschreibung(self):
        return "foo"

    @pytest.fixture
    def get_beschreibung_mock(self, beschreibung):
        with patch("jobby.views._get_beschreibung") as m:
            m.return_value = beschreibung
            yield m

    def test_existing_instance(self, form_class, get_beschreibung_mock, stellenangebot):
        """Assert that the form can be instantiated with a Stellenangebot."""
        form = form_class(instance=stellenangebot)
        assert form.initial["titel"] == stellenangebot.titel

    @pytest.mark.parametrize("form_data", [{"titel": "Software Tester", "refnr": "1234"}])
    def test_new_instance(self, form, get_beschreibung_mock, form_data):
        """Assert that the form can be saved to create a new Stellenangebot."""
        assert form.is_valid()
        saved = form.save()
        assert saved.titel == form_data["titel"]
        assert saved.refnr == form_data["refnr"]

    @pytest.mark.parametrize(
        "initial_data",
        [
            {"eintrittsdatum": "2024-06-14"},
            {"eintrittsdatum": datetime.date.fromisoformat("2024-06-14")},
        ],
    )
    def test_get_initial_for_field_date_field(self, form, initial_data):
        """Assert that initial data for date fields are cast into date objects."""
        assert isinstance(form.get_initial_for_field(form.fields["eintrittsdatum"], "eintrittsdatum"), datetime.date)

    @pytest.mark.parametrize(
        "initial_data",
        [
            {"modified": "2024-06-12 08:03:16.208000+00:00"},
            {"modified": datetime.datetime.fromisoformat("2024-06-12 08:03:16.208000+00:00")},
        ],
    )
    def test_get_initial_for_field_datetime_field(self, form, initial_data):
        """
        Assert that initial data for datetime fields are cast into datetime
        objects.
        """
        assert isinstance(form.get_initial_for_field(form.fields["modified"], "modified"), datetime.datetime)

    @pytest.mark.parametrize("initial_data", [{"titel": "Foo"}])
    def test_get_initial_for_field_not_date_or_datetime(self, form, initial_data):
        """
        Assert that ``get_initial_for_field`` only casts the initial data for
        date/datetime fields.
        """
        assert isinstance(form.get_initial_for_field(form.fields["titel"], "titel"), str)

    @pytest.mark.parametrize("initial_data", [{"eintrittsdatum": "2024-13-14"}])
    def test_get_initial_for_field_invalid_date(self, form, initial_data):
        """Assert that an invalid date is handled."""
        assert isinstance(form.get_initial_for_field(form.fields["eintrittsdatum"], "eintrittsdatum"), str)

    @pytest.mark.parametrize("initial_data", [{"modified": "2024-13-12 08:03:16.208000+00:00"}])
    def test_get_initial_for_field_invalid_datetime(self, form, initial_data):
        """Assert that an invalid datetime is handled."""
        assert isinstance(form.get_initial_for_field(form.fields["modified"], "modified"), str)

    def test_clean_beschreibung_no_beschreibung(self, form, cleaned_data, get_beschreibung_mock, beschreibung, refnr):
        """
        Assert that ``clean_beschreibung`` calls ``_get_beschreibung`` if the
        form's cleaned data does not contain a beschreibung.
        """
        form.cleaned_data = cleaned_data
        assert form.clean_beschreibung() == beschreibung
        get_beschreibung_mock.assert_called_with(refnr)

    def test_clean_beschreibung_bad_request(self, form, cleaned_data, get_beschreibung_mock, beschreibung):
        """
        Assert that ``clean_beschreibung`` returns an empty string if
        ``_get_beschreibung`` raises a BadRequest.
        """
        form.cleaned_data = cleaned_data
        get_beschreibung_mock.side_effect = BadRequest
        assert form.clean_beschreibung() == ""

    @pytest.mark.parametrize("cleaned_data", [{"beschreibung": "foo"}])
    def test_clean_beschreibung_cleaned_data_contains_beschreibung(self, form, cleaned_data, get_beschreibung_mock):
        """
        Assert that ``clean_beschreibung`` does not call ``_get_beschreibung``
        if the form's cleaned data contains a beschreibung.
        """
        form.cleaned_data = cleaned_data
        form.clean_beschreibung()
        get_beschreibung_mock.assert_not_called()


class TestWatchlistSearchForm:

    @pytest.fixture
    def form_class(self):
        return WatchlistSearchForm

    def test_get_filter_params(self, form):
        cleaned_data = {"q": "Foo", "bewerbungsstatus": Stellenangebot.BewerbungChoices.BEWORBEN}
        assert form.get_filter_params(cleaned_data) == cleaned_data

    def test_get_filter_params_empty_value(self, form):
        """Assert that ``get_filter_params`` excludes fields with empty values."""
        cleaned_data = {"q": "", "bewerbungsstatus": ""}
        assert not form.get_filter_params(cleaned_data)
