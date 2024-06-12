import json
from unittest.mock import Mock, patch

# noinspection PyPackageRequirements
import pytest
import requests
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from jobby.models import Stellenangebot, Watchlist
from jobby.views import (
    DETAILS_BESCHREIBUNG_ID,
    PAGE_VAR,
    StellenangebotView,
    SucheView,
    WatchlistView,
    get_beschreibung,
    watchlist_remove,
    watchlist_remove_all,
    watchlist_toggle,
)

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def search_results():
    """Return a list of integers to act as search results."""
    return list(range(1, 11))


@pytest.fixture
def search_response_mock(search_results):
    """Return a mock object to act as the response of a search request."""
    return Mock(
        results=search_results,
        result_count=len(search_results),
    )


@pytest.fixture
def search_mock(search_response_mock):
    """Mock the ``search`` function to return a mocked response."""
    with patch("jobby.views.search") as m:
        m.return_value = search_response_mock
        yield m


@pytest.fixture
def cleaned_data():
    """The cleaned data of the mocked search form."""
    return {}


@pytest.fixture
def form_mock(cleaned_data):
    """Return a mock with cleaned_data."""
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
        """Return the context data for the get_context_data mock."""
        return {}

    @pytest.fixture(autouse=True)
    def get_context_data_mock(self, view, context_data):
        """Mock out the view's ``get_context_data`` method."""
        with patch.object(view, "get_context_data") as m:
            m.return_value = context_data
            yield m

    @pytest.fixture(autouse=True)
    def render_mock(self, view):
        """Mock out the view's ``render_to_response`` method."""
        with patch.object(view, "render_to_response") as m:
            yield m

    @pytest.fixture
    def form_is_valid(self):
        """Return whether the mocked form class is valid."""
        return True

    @pytest.fixture(autouse=True)
    def form_class_mock(self, view, form_is_valid):
        """Replace the view's ``form_class`` with a Mock."""
        with patch.object(view, "form_class") as m:
            m.return_value.is_valid.return_value = form_is_valid
            yield m

    @pytest.mark.parametrize("request_data", [{"suche": ""}])
    @pytest.mark.parametrize("form_is_valid", [True])
    def test_get_form_valid(self, view, get_request, request_data, form_is_valid):
        """Assert that get() calls ``form_valid`` if the form is valid."""
        with patch.object(view, "form_valid") as form_valid_mock:
            view.get(get_request)

        form_valid_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{"suche": ""}])
    @pytest.mark.parametrize("form_is_valid", [False])
    def test_get_form_invalid(self, view, get_request, request_data, form_is_valid):
        """Assert that get() calls ``form_invalid`` if the form is invalid."""
        with patch.object(view, "form_invalid") as form_invalid_mock:
            view.get(get_request)

        form_invalid_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{}])
    def test_get_calls_super_if_suche_not_in_request_data(self, view, get_request, request_data):
        """
        Assert that get() calls the super method if the request data does not
        contain a ``suche`` key.
        """
        with patch("jobby.views.super") as super_mock:
            view.get(get_request)

        super_mock.assert_called()

    def test_form_valid(self, view, search_mock, form_mock, render_mock, search_results, search_response_mock):
        """Assert that form_valid() calls ``render_to_response``."""
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
        """
        Assert ``get_pagination_context`` is not called if the search did not
        return results.
        """
        with patch.object(view, "get_pagination_context") as pagination_context_mock:
            pagination_context_mock.return_value = {}
            view.form_valid(form_mock)

        pagination_context_mock.assert_not_called()

    def test_user_message_on_exception(self, view, search_mock, form_mock):
        """
        Assert that form_valid calls ``_send_error_message`` if the search
        raised an exception.
        """
        search_mock.side_effect = Exception("A test exception has occurred.")
        with patch.object(view, "_send_error_message") as send_message_mock:
            view.form_valid(form_mock)
            send_message_mock.assert_called()

    def test_get_watchlisted_ids(self, view, watchlist_item, stellenangebot):
        """
        Assert that ``_get_watchlisted_ids`` returns the ids of the
        Stellenangebot instances that have been watchlisted.
        """
        assert view._get_watchlisted_ids(results=[stellenangebot]) == {stellenangebot.pk}

    def test_get_watchlisted_ids_filter(self, view, stellenangebot):
        """
        Assert that ``_get_watchlisted_ids`` filters only with saved model
        instances.
        """
        with patch("jobby.views.WatchlistItem") as watchlist_item_mock:
            filter_mock = Mock()
            filter_mock.return_value.values_list.return_value = [stellenangebot.pk]
            watchlist_item_mock.objects.filter = filter_mock
            view._get_watchlisted_ids(results=[stellenangebot, StellenangebotFactory.build()])
            filter_mock.assert_called_with(stellenangebot__in=[stellenangebot])

    def test_get_watchlisted_ids_no_results(self, view):
        """
        Assert that ``_get_watchlisted_ids`` returns an empty set if there are
        no results.
        """
        assert view._get_watchlisted_ids(results=[]) == set()

    def test_get_results_context(self, view, search_response_mock, stellenangebot):
        """Assert that ``get_results_context`` returns the expected data."""
        new = StellenangebotFactory.build()
        search_response_mock.results = [stellenangebot, new]
        search_response_mock.result_count = 2
        with patch.object(view, "_get_watchlisted_ids", new=Mock(return_value={stellenangebot.pk})):
            ctx = view.get_results_context(search_response_mock)
        assert ctx["results"] == [(stellenangebot, True), (new, False)]
        assert ctx["result_count"] == 2

    @pytest.mark.parametrize("request_data", [{PAGE_VAR: "2"}])
    def test_get_pagination_context(self, view, request_data):
        """Assert that ``get_pagination_context`` returns the expected data."""
        ctx = view.get_pagination_context(result_count=11, per_page=1)
        assert ctx["current_page"] == 2
        assert ctx["page_range"] == [1, 2, 3, 4, 5, Paginator.ELLIPSIS, 10, 11]
        assert ctx["pagination_required"]

    @pytest.mark.parametrize("request_data", [{PAGE_VAR: "foo"}])
    def test_get_pagination_context_invalid_page(self, view, request_data):
        """
        Assert that ``get_pagination_context`` sets the current page to 1 if
        the PAGE_VAR of the request is not a valid integer.
        """
        ctx = view.get_pagination_context(result_count=1)
        assert ctx["current_page"] == 1


class TestWatchlistView:

    @pytest.fixture
    def view_class(self):
        return WatchlistView

    @pytest.fixture
    def request_data(self, watchlist_name):
        """Return the data for the request."""
        return {"watchlist_name": watchlist_name}

    @pytest.fixture
    def current_mock(self, view):
        """Mock out the view's ``current_watchlist_name`` method."""
        with patch.object(view, "current_watchlist_name") as m:
            yield m

    @pytest.fixture
    def watchlist_names_mock(self, view):
        """Mock out the view's ``get_watchlist_names`` method."""
        with patch.object(view, "get_watchlist_names") as m:
            yield m

    @pytest.mark.parametrize("request_data", [{"watchlist_name": "foo"}])
    def test_current_watchlist_name(self, view, get_request, request_data):
        """Assert that ``current_watchlist_name`` returns the expected data."""
        assert view.current_watchlist_name(get_request) == "foo"

    def test_get_watchlist(self, view, get_request, watchlist):
        """Assert that ``get_watchlist`` returns the expected Watchlist instance."""
        assert view.get_watchlist(get_request) == watchlist

    def test_get_queryset(self, view, watchlist, watchlist_item, stellenangebot):
        """Assert that ``get_queryset`` returns the expected queryset."""
        queryset = view.get_queryset()
        assert isinstance(queryset, QuerySet)
        assert stellenangebot in queryset

    def test_get_watchlist_names(self, view, watchlist, watchlist_name):
        """Assert that ``get_watchlist_names`` returns the expected list of names."""
        assert list(view.get_watchlist_names()) == [watchlist_name]

    def test_creates_watchlist_if_does_not_exist(self, view, client):
        """
        Assert that a watchlist with the requested name will be created if no
        such watchlist exists.
        """
        assert Watchlist.objects.count() == 0
        response = client.get(reverse("watchlist"), data={"watchlist_name": "foo"})
        assert response.status_code == 200
        assert Watchlist.objects.count() == 1
        assert Watchlist.objects.filter(name="foo").exists()


@pytest.mark.usefixtures("watchlist", "ignore_csrf_protection")
class TestWatchlistToggle:

    @pytest.fixture
    def request_data(self, stellenangebot, watchlist_name):
        """Return the data for the request."""
        return {"titel": stellenangebot.titel, "refnr": stellenangebot.refnr, "watchlist_name": watchlist_name}

    def test_watchlist_toggle_not_on_watchlist(self, post_request, watchlist, stellenangebot):
        """
        Assert that ``watchlist_toggle`` adds a Stellenangebot instance to the
        watchlist if it is not already on it.
        """
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_watchlist_toggle_already_on_watchlist(self, post_request, watchlist, watchlist_item, stellenangebot):
        """
        Assert that ``watchlist_toggle`` removes a Stellenangebot instance from
        the watchlist if it is already on it.
        """
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert not json.loads(response.content)["on_watchlist"]
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    def test_watchlist_toggle_new_angebot(self, post_request, watchlist, stellenangebot):
        """
        Assert that ``watchlist_toggle`` creates a Stellenangebot instance if
        no Stellenangebot with the requested refnr exists.
        """
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        assert json.loads(response.content)["on_watchlist"]
        assert Stellenangebot.objects.filter(refnr=stellenangebot.refnr).exists()
        saved_angebot = Stellenangebot.objects.get(refnr=stellenangebot.refnr)
        assert watchlist.items.filter(stellenangebot=saved_angebot).exists()

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_toggle_no_refnr(self, post_request, request_data):
        """
        Assert that ``watchlist_toggle`` returns a response with status code
        400 if the no refnr was included in the request data.
        """
        response = watchlist_toggle(post_request)
        assert response.status_code == 400

    @pytest.fixture
    def search_result_form_mock(self):
        """Mock the StellenangebotForm."""
        with patch("jobby.views.StellenangebotForm") as m:
            yield m

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    def test_watchlist_toggle_new_angebot_form_invalid(self, post_request, search_result_form_mock, stellenangebot):
        """
        Assert that ``watchlist_toggle`` returns a response with status code
        400 if form validation fails.
        """
        search_result_form_mock.return_value.is_valid.return_value = False
        response = watchlist_toggle(post_request)
        assert response.status_code == 400


class TestStellenangebotView:

    @pytest.fixture
    def view_class(self):
        return StellenangebotView

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_object_add(self, view, view_extra_context):
        """Assert that ``get_object`` returns None if this is an 'add' view."""
        assert view.get_object() is None

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_object_edit(self, view, view_extra_context, super_mock):
        """
        Assert that ``get_object`` calls the super method if this is an 'edit'
        view.
        """
        get_object_mock = Mock()
        super_mock.return_value.get_object = get_object_mock
        view.get_object()
        get_object_mock.assert_called()

    @pytest.mark.parametrize("request_data", [{"titel": "foo"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_initial_add(self, view, view_extra_context, super_mock, request_data):
        """
        Assert that ``get_initial`` includes the request's GET data if the view
        is an 'add' view.
        """
        super_mock.return_value.get_initial.return_value = {"foo": "bar"}
        assert view.get_initial() == {"foo": "bar", **request_data}

    @pytest.mark.parametrize("request_data", [{"titel": "foo"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_initial_edit(self, view, view_extra_context, super_mock, request_data):
        """
        Assert that ``get_initial`` does *not* include the request's GET data if
        the view is an 'edit' view.
        """
        super_mock.return_value.get_initial.return_value = {"foo": "bar"}
        assert view.get_initial() == {"foo": "bar"}

    @pytest.fixture
    def super_get_mock(self, view, super_mock):
        """Mock out super().get() to return a mocked response."""

        def get(*_args, **_kwargs):
            view.object = None
            return response_mock

        response_mock = Mock()
        super_mock.return_value.get = Mock(side_effect=get)
        return response_mock

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_refnr_exists(self, view, get_request, stellenangebot, super_get_mock, view_extra_context):
        """
        Assert that ``get`` returns a redirect to an edit page if a
        Stellenangebot with the given refnr exists.
        """
        get_request.GET = {"refnr": stellenangebot.refnr}
        response = view.get(get_request)
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse("stellenangebot_edit", kwargs={"id": stellenangebot.pk})

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_refnr_does_not_exist(self, view, get_request, super_get_mock, view_extra_context):
        """
        Assert that ``get`` returns the response from super().get() if no
        Stellenangebot instance with the given refnr exists.
        """
        get_request.GET = {"refnr": "1234"}
        response = view.get(get_request)
        assert response == super_get_mock

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_add_no_refnr(self, view, get_request, super_get_mock, view_extra_context):
        """
        Assert that ``get`` returns the response from super().get() if the
        request data does not contain a refnr.
        """
        get_request.GET = {}
        response = view.get(get_request)
        assert response == super_get_mock

    @pytest.mark.parametrize("request_data", [{"refnr": "1234"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_arge_link_request_has_refnr(self, view, view_extra_context, request_data):
        """
        Assert that ``get_arge_link`` returns a URL to the details page of the
        refnr given in the 'add' view's request data.
        """
        assert view.get_arge_link() == f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{request_data['refnr']}"

    @pytest.mark.parametrize("request_data", [{}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_arge_link_request_does_not_have_refnr(self, view, view_extra_context, request_data):
        """
        Assert that ``get_arge_link`` returns None if the request data for an
        'add' view does not contain a refnr.
        """
        assert not view.get_arge_link()

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_arge_link_edit(self, view, view_extra_context, stellenangebot, refnr):
        """
        Assert that ``get_arge_link`` returns the URL to the details page of the
        edit view's Stellenangebot instance.
        """
        view.object = stellenangebot
        assert view.get_arge_link() == f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

    @pytest.mark.parametrize("refnr", [""])
    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_arge_link_edit_no_refnr(self, view, view_extra_context, stellenangebot, refnr):
        """
        Assert that ``get_arge_link`` returns None if the edit view's instance
        does not have a refnr set.
        """
        view.object = stellenangebot
        assert not view.get_arge_link()


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestWatchlistRemove:

    @pytest.fixture
    def request_data(self, refnr, watchlist_name):
        return {"refnr": refnr, "watchlist_name": watchlist_name}

    def test_watchlist_remove(self, post_request, stellenangebot, watchlist_item, watchlist):
        """Assert that ``watchlist_remove`` removes the item from the watchlist."""
        response = watchlist_remove(post_request)
        assert response.status_code == 200
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

    @pytest.mark.parametrize("request_data", [{}])
    def test_watchlist_remove_missing_parameter(self, post_request, request_data):
        """
        Assert that ``watchlist_remove`` returns a 400 response if the
        request does not contain a refnr.
        """
        response = watchlist_remove(post_request)
        assert response.status_code == 400

    @pytest.mark.parametrize("refnr", ["foo"])
    def test_watchlist_remove_object_does_not_exist(self, post_request, refnr):
        """
        Assert that ``watchlist_remove`` returns an OK response if no
        Stellenangebot with the requested refnr exists.
        """
        response = watchlist_remove(post_request)
        assert response.status_code == 200

    @pytest.mark.parametrize("watchlist", [None])
    def test_watchlist_does_not_exist(self, post_request, watchlist):
        """
        Assert that ``watchlist_remove`` returns an OK response if the
        requested watchlist does not exist.
        """
        response = watchlist_remove(post_request)
        assert response.status_code == 200


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestWatchlistRemoveAll:

    @pytest.fixture
    def request_data(self, refnr, watchlist_name):
        return {"refnr": refnr, "watchlist_name": watchlist_name}

    def test_watchlist_remove_all(self, post_request, watchlist_item, watchlist):
        """
        Assert that ``watchlist_remove_all`` removes all items from the
        watchlist.
        """
        response = watchlist_remove_all(post_request)
        assert response.status_code == 200
        assert not watchlist.items.exists()

    @pytest.mark.parametrize("watchlist", [None])
    def test_watchlist_does_not_exist(self, post_request, watchlist):
        """
        Assert that ``watchlist_remove_all`` returns an OK response if the
        requested watchlist does not exist.
        """
        response = watchlist_remove_all(post_request)
        assert response.status_code == 200


class TestGetBeschreibung:

    @pytest.fixture
    def details_url(self, refnr):
        return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

    @pytest.fixture
    def beschreibung_html(self):
        return """<p>A paragraph</p><ul><li>Some list item</li><li>Another list item</li></ul>"""

    @pytest.fixture
    def beschreibung_id(self):
        return DETAILS_BESCHREIBUNG_ID

    @pytest.fixture
    def details_html(self, beschreibung_html, beschreibung_id):
        return f"""<div>This is not the beschreibung</div><p id="{beschreibung_id}">{beschreibung_html}</p>"""

    @pytest.fixture
    def status_code(self):
        """Return the status code of the job details response."""
        return requests.codes["ok"]

    @pytest.fixture
    def get_request(self, get_request, requests_mock, details_url, details_html, status_code):
        """Create a mocked response for the job details request call."""
        requests_mock.get(details_url, text=details_html, status_code=status_code)
        return get_request

    @pytest.fixture
    def get_beschreibung_response(self, get_request, refnr):
        """Call ``get_beschreibung`` and return the response."""
        return get_beschreibung(get_request, refnr=refnr)

    def test_get_beschreibung(self, get_beschreibung_response, beschreibung_html):
        """Assert that ``get_beschreibung`` returns the expected HTML."""
        assert get_beschreibung_response.content.decode("utf-8") == beschreibung_html

    def test_get_beschreibung_url(self, get_beschreibung_response, details_url, requests_mock):
        """Assert that ``get_beschreibung`` made a request against the expected URL."""
        assert requests_mock.request_history[0].url == details_url

    @pytest.mark.parametrize("status_code", [123])
    def test_get_beschreibung_bad_response(self, get_beschreibung_response, status_code):
        """
        Assert that ``get_beschreibung`` returns a response with status code
        400 if the fetch request was not ok.
        """
        assert get_beschreibung_response.status_code == 400

    @pytest.mark.parametrize("beschreibung_id", ["foo"])
    def test_get_beschreibung_no_beschreibung(self, get_beschreibung_response, beschreibung_id):
        """
        Assert that ``get_beschreibung`` returns a response with a short message
        if the job details page does not contain an element with the
        'beschreibung id'.
        """
        assert get_beschreibung_response.content.decode("utf-8") == "Keine Beschreibung gegeben!"
