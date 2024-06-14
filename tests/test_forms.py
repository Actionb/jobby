import datetime
from unittest.mock import PropertyMock, patch

import pytest
from jobby.forms import StellenangebotForm, SucheForm


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
