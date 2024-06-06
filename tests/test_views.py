import json
from unittest.mock import Mock, patch

# noinspection PyPackageRequirements
import pytest
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from jobby.models import Stellenangebot
from jobby.views import PAGE_VAR, StellenangebotView, SucheView, WatchlistView, watchlist_toggle

from tests.factories import StellenangebotFactory

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

    def test_form_valid(self, view, search_mock, form_mock, render_mock, search_results, search_response_mock):
        with patch.object(view, "get_pagination_context") as pagination_context_mock:
            with patch.object(view, "get_results_context") as results_context_mock:
                results_context_mock.return_value = {}
                pagination_context_mock.return_value = {}
                view.form_valid(form_mock)

        render_mock.assert_called()
        results_context_mock.assert_called_with(search_response_mock)
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

    def test_get_watchlisted_ids(self, view, watchlist_item, stellenangebot):
        assert view._get_watchlisted_ids(results=[stellenangebot]) == {stellenangebot.pk}

    def test_get_watchlisted_ids_filter(self, view, stellenangebot):
        """
        Assert that _get_watchlisted_ids filters only with saved model
        instances.
        """
        with patch("jobby.views.WatchlistItem") as watchlist_item_mock:
            filter_mock = Mock()
            filter_mock.return_value.values_list.return_value = [stellenangebot.pk]
            watchlist_item_mock.objects.filter = filter_mock
            view._get_watchlisted_ids(results=[stellenangebot, StellenangebotFactory.build()])
            filter_mock.assert_called_with(stellenangebot__in=[stellenangebot])

    def test_get_watchlisted_ids_no_results(self, view):
        with patch("jobby.views.WatchlistItem") as watchlist_item_mock:
            none_mock = Mock()
            none_mock.return_value.values_list.return_value = []
            watchlist_item_mock.objects.none = none_mock
            view._get_watchlisted_ids(results=[])
            none_mock.assert_called()

    def test_get_results_context(self, view, search_response_mock, stellenangebot):
        new = StellenangebotFactory.build()
        search_response_mock.results = [stellenangebot, new]
        search_response_mock.result_count = 2
        with patch.object(view, "_get_watchlisted_ids", new=Mock(return_value={stellenangebot.pk})):
            ctx = view.get_results_context(search_response_mock)
        assert ctx["results"] == [(stellenangebot, True), (new, False)]
        assert ctx["result_count"] == 2

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


@pytest.mark.usefixtures("watchlist")
class TestWatchlistToggle:

    @pytest.fixture
    def request_data(self, stellenangebot, watchlist_name):
        return {"titel": stellenangebot.titel, "refnr": stellenangebot.refnr, "watchlist_name": watchlist_name}

    def test_watchlist_toggle_not_on_watchlist(self, post_request, watchlist, stellenangebot):
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_watchlist_toggle_already_on_watchlist(self, post_request, watchlist, watchlist_item, stellenangebot):
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    def test_watchlist_toggle_new_angebot(self, post_request, watchlist, stellenangebot):
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]
        assert Stellenangebot.objects.filter(refnr=stellenangebot.refnr).exists()
        saved_angebot = Stellenangebot.objects.get(refnr=stellenangebot.refnr)
        assert watchlist.items.filter(stellenangebot=saved_angebot).exists()

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_toggle_no_refnr(self, post_request, request_data):
        response = watchlist_toggle(post_request)
        assert response.status_code == 400

    @pytest.fixture
    def search_result_form_mock(self):
        with patch("jobby.views.SearchResultForm") as m:
            yield m

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    def test_watchlist_toggle_new_angebot_form_invalid(self, post_request, search_result_form_mock, stellenangebot):
        search_result_form_mock.return_value.is_valid.return_value = False
        response = watchlist_toggle(post_request)
        assert response.status_code == 400


class TestStellenangebotView:

    @pytest.fixture
    def view_class(self):
        return StellenangebotView

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_object_add(self, view, view_extra_context):
        assert view.get_object() is None

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_object_edit(self, view, view_extra_context, super_mock):
        get_object_mock = Mock()
        super_mock.return_value.get_object = get_object_mock
        view.get_object()
        get_object_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{"titel": "foo"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_initial_add(self, view, view_extra_context, super_mock, request_data):
        """
        Assert that get_initial includes the request's data if the view is an
        'add' view.
        """
        super_mock.return_value.get_initial.return_value = {"foo": "bar"}
        assert view.get_initial() == {"foo": "bar", **request_data}

    @pytest.mark.parametrize("request_data", [{"titel": "foo"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_initial_edit(self, view, view_extra_context, super_mock, request_data):
        super_mock.return_value.get_initial.return_value = {"foo": "bar"}
        assert view.get_initial() == {"foo": "bar"}

    @pytest.fixture
    def super_get_mock(self, view, super_mock):
        def get(*_args, **_kwargs):
            view.object = None
            return response_mock

        response_mock = Mock()
        super_mock.return_value.get = Mock(side_effect=get)
        return response_mock

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_refnr_exists(self, view, http_request, stellenangebot, super_get_mock, view_extra_context):
        """
        Assert that get returns a redirect to an edit page if a Stellenangebot
        with the given refnr exists.
        """
        http_request.GET = {"refnr": stellenangebot.refnr}
        response = view.get(http_request)
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse("stellenangebot_edit", kwargs={"id": stellenangebot.pk})

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_refnr_does_not_exist(self, view, http_request, super_get_mock, view_extra_context):
        """
        Assert that get returns the response from super().get() if no
        Stellenangebot instance with the given refnr exists.
        """
        http_request.GET = {"refnr": "1234"}
        response = view.get(http_request)
        assert response == super_get_mock

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_no_refnr(self, view, http_request, super_get_mock, view_extra_context):
        """
        Assert that get returns the response from super().get() if the request
        data does not contain a refnr.
        """
        http_request.GET = {}
        response = view.get(http_request)
        assert response == super_get_mock
