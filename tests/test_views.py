from unittest.mock import Mock, patch

# noinspection PyPackageRequirements
import pytest
from django.core.paginator import Paginator
from django.db.models import QuerySet
from jobby.views import PAGE_VAR, SucheView, WatchlistView

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def search_results():
    return list(range(1, 11))


@pytest.fixture
def search_response_mock(search_results):
    return Mock(
        results=search_results,
        result_count=len(search_results),
    )


@pytest.fixture
def search_mock(search_response_mock):
    with patch("jobby.views.search") as m:
        m.return_value = search_response_mock
        yield m


@pytest.fixture
def cleaned_data():
    return {}


@pytest.fixture
def form_mock(cleaned_data):
    return Mock(cleaned_data=cleaned_data)


@pytest.fixture
def super_mock():
    with patch("jobby.views.super") as m:
        yield m


class TestSucheView:

    @pytest.fixture
    def view_class(self):
        return SucheView

    @pytest.fixture
    def context_data(self):
        return {}

    @pytest.fixture(autouse=True)
    def get_context_data_mock(self, view, context_data):
        with patch.object(view, "get_context_data") as m:
            m.return_value = context_data
            yield m

    @pytest.fixture(autouse=True)
    def render_mock(self, view):
        with patch.object(view, "render_to_response") as m:
            yield m

    @pytest.fixture
    def form_is_valid(self):
        return True

    @pytest.fixture(autouse=True)
    def form_class_mock(self, view, form_is_valid):
        with patch.object(view, "form_class") as m:
            m.return_value.is_valid.return_value = form_is_valid
            yield m

    @pytest.mark.parametrize("request_data", [{"suche": ""}])
    @pytest.mark.parametrize("form_is_valid", [True])
    def test_get_form_valid(self, view, http_request, request_data, form_is_valid):
        with patch.object(view, "form_valid") as form_valid_mock:
            view.get(http_request)

        form_valid_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{"suche": ""}])
    @pytest.mark.parametrize("form_is_valid", [False])
    def test_get_form_invalid(self, view, http_request, request_data, form_is_valid):
        with patch.object(view, "form_invalid") as form_invalid_mock:
            view.get(http_request)

        form_invalid_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{}])
    def test_get_calls_super_if_suche_not_in_request_data(self, view, http_request, request_data):
        with patch("jobby.views.super") as super_mock:
            view.get(http_request)

        super_mock.assert_called()

    def test_form_valid(self, view, search_mock, form_mock, render_mock, search_results):
        with patch.object(view, "get_pagination_context") as pagination_context_mock:
            pagination_context_mock.return_value = {}
            view.form_valid(form_mock)

        render_mock.assert_called()
        args, _kwargs = render_mock.call_args
        ctx = args[0]
        assert ctx["results"] == search_results
        assert ctx["result_count"] == len(search_results)
        pagination_context_mock.assert_called_with(len(search_results))

    @pytest.mark.parametrize("search_results", [[]])
    def test_form_valid_no_results(self, view, search_mock, form_mock, search_results):
        with patch.object(view, "get_pagination_context") as pagination_context_mock:
            pagination_context_mock.return_value = {}
            view.form_valid(form_mock)

        pagination_context_mock.assert_not_called()

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


class TestWatchlistView:

    @pytest.fixture
    def view_class(self):
        return WatchlistView

    @pytest.fixture
    def request_data(self, watchlist_name):
        return {"watchlist_name": watchlist_name}

    @pytest.fixture
    def current_mock(self, view):
        with patch.object(view, "current_watchlist_name") as m:
            yield m

    @pytest.fixture
    def watchlist_names_mock(self, view):
        with patch.object(view, "get_watchlist_names") as m:
            yield m

    @pytest.mark.parametrize("request_data", [{"watchlist_name": "foo"}])
    def test_current_watchlist_name(self, view, http_request, request_data):
        assert view.current_watchlist_name(http_request) == "foo"

    def test_get_watchlist(self, view, http_request, watchlist):
        assert view.get_watchlist(http_request) == watchlist

    def test_get_queryset(self, view, watchlist, watchlist_item, stellenangebot):
        queryset = view.get_queryset()
        assert isinstance(queryset, QuerySet)
        assert stellenangebot in queryset

    def test_get_watchlist_names(self, view, watchlist, watchlist_name):
        assert list(view.get_watchlist_names()) == [watchlist_name]

    def test_get_context_data_contains_current_watchlist(self, view, super_mock, current_mock, watchlist_names_mock):
        super_mock.return_value.get_context_data.return_value = {}
        ctx = view.get_context_data()
        assert "current_watchlist" in ctx

    def test_get_context_data_contains_watchlist_names(self, view, super_mock, current_mock, watchlist_names_mock):
        super_mock.return_value.get_context_data.return_value = {}
        ctx = view.get_context_data()
        assert "watchlist_names" in ctx
