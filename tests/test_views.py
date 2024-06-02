from unittest.mock import Mock, patch

import pytest
from django.core.paginator import Paginator
from jobby.views import PAGE_VAR, SucheView


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
    def view(self, http_request):
        view = self.view_class()
        view.setup(http_request)
        return view

    def test_user_message_on_exception(self, view, search_mock, form_mock):
        search_mock.side_effect = Exception("A test exception has occurred.")
        with patch.object(view, "_send_error_message") as send_message_mock:
            view.form_valid(form_mock)
            send_message_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{PAGE_VAR: "2"}])
    def test_get_pagination_context(self, view, request_data):
        ctx = view.get_pagination_context(result_count=11, per_page=1)
        assert ctx["current_page"] == 2
        assert ctx["page_range"] == [1, 2, 3, 4, 5, Paginator.ELLIPSIS, 10, 11]
        assert ctx["pagination_required"]

    @pytest.mark.parametrize("request_data", [{PAGE_VAR: "foo"}])
    def test_get_pagination_context_invalid_page(self, view, request_data):
        ctx = view.get_pagination_context(result_count=1)
        assert ctx["current_page"] == 1
