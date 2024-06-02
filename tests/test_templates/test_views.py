from unittest.mock import Mock, patch

import pytest
from django.test import RequestFactory
from jobby.views import SucheView


@pytest.fixture
def search_mock():
    with patch("jobby.views.search") as m:
        yield m


@pytest.fixture
def cleaned_data():
    return {}


@pytest.fixture
def form_mock(cleaned_data):
    return Mock(cleaned_data=cleaned_data)


class TestSucheView:
    view_class = SucheView

    @pytest.fixture
    def http_request(self):
        return RequestFactory().get("")

    @pytest.fixture
    def view(self, http_request):
        view = self.view_class()
        view.request = http_request
        return view

    def test_user_message_on_exception(self, view, search_mock, form_mock):
        search_mock.side_effect = Exception("A test exception has occurred.")
        with patch.object(view, "_send_error_message") as send_message_mock:
            view.form_valid(form_mock)
            send_message_mock.assert_called()
