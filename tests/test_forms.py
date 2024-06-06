from unittest.mock import PropertyMock, patch

import pytest
from jobby.forms import SucheForm


@pytest.fixture
def form_data():
    return {}


@pytest.fixture
def form(form_class, form_data):
    return form_class(data=form_data)


class TestSucheForm:

    @pytest.fixture
    def form_class(self):
        return SucheForm

    @pytest.mark.parametrize("form_data", [{"was": "foo", "wo": "Dortmund", "arbeitgeber": "bar"}])
    def test_shown_fields(self, form, form_data):
        assert len(form.shown_fields) == 4
        assert form["was"] in form.shown_fields
        assert form["wo"] in form.shown_fields
        assert form["umfeld"] in form.shown_fields
        assert form["arbeitgeber"] in form.shown_fields

    def test_collapsed_fields(self, form):
        with patch("jobby.forms.SucheForm.shown_fields", new=PropertyMock(return_value=[form["arbeitgeber"]])):
            assert form["arbeitgeber"] not in form.collapsed_fields
