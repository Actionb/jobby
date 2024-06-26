import json
from unittest.mock import Mock, patch

# noinspection PyPackageRequirements
import pytest
import requests
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from jobby.models import Stellenangebot, Watchlist
from jobby.views import (
    DETAILS_BESCHREIBUNG_ID,
    PAGE_VAR,
    BaseMixin,
    PapierkorbView,
    StellenangebotView,
    SucheView,
    WatchlistView,
    get_beschreibung,
    papierkorb_delete,
    stellenangebot_remove,
    watchlist_remove,
    watchlist_remove_all,
    watchlist_toggle,
)

from tests.factories import StellenangebotFactory, WatchlistItemFactory

urlpatterns = [
    path("", lambda r: HttpResponse(), name="index"),
    path("suche/", SucheView.as_view(), name="suche"),
    path("merkliste/", WatchlistView.as_view(), name="watchlist"),
    path("merkliste/toggle/", watchlist_toggle, name="watchlist_toggle"),
    path("merkliste/remove/", watchlist_remove, name="watchlist_remove"),
    path("merkliste/remove_all/", watchlist_remove_all, name="watchlist_remove_all"),
    path("angebot/", StellenangebotView.as_view(extra_context={"add": True}), name="stellenangebot_add"),
    path("angebot/<int:id>/", StellenangebotView.as_view(extra_context={"add": False}), name="stellenangebot_edit"),
    path("fetch_description/<str:refnr>/", get_beschreibung, name="get_angebot_beschreibung"),
    path("papierkorb/", PapierkorbView.as_view(), name="papierkorb"),
    path("papierkorb/delete/", papierkorb_delete, name="papierkorb_delete"),
    path("angebote/<int:id>/remove/", stellenangebot_remove, name="stellenangebot_remove"),
    path("not_suche/", lambda r: HttpResponse(), name="not_suche"),
]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]


@pytest.fixture
def search_results(stellenangebot):
    """Return a list of integers to act as search results."""
    return [stellenangebot, StellenangebotFactory()]


@pytest.fixture
def search_response_mock(search_results):
    """Return a mock object to act as the response of a search request."""
    return Mock(
        results=search_results,
        result_count=len(search_results),
    )


@pytest.fixture
def registry_mock():
    with patch("jobby.views.registry") as m:
        yield m


@pytest.fixture
def search_mock(registry_mock, search_response_mock):
    """Mock the registry's ``search`` function to return a mocked response."""
    search_mock = Mock(return_value=search_response_mock)
    registry_mock.search = search_mock
    yield search_mock


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

    def test(self, client):
        response = client.get(reverse("suche"))
        assert response.status_code == 200

    def test_search(self, client, search_mock, stellenangebot, search_results, watchlist_item):
        response = client.get(reverse("suche"), data={"was": "Software", "wo": "Dortmund", "suche": ""})
        assert response.status_code == 200
        assert response.context["results"] == [(stellenangebot, True), (search_results[-1], False)]

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

    def test(self, client):
        response = client.get(reverse("watchlist"))
        assert response.status_code == 200

    @pytest.mark.parametrize("request_data", [{"watchlist_name": "foo"}])
    def test_current_watchlist_name(self, view, get_request, request_data):
        """Assert that ``current_watchlist_name`` returns the expected data."""
        assert view.current_watchlist_name(get_request) == "foo"

    def test_get_watchlist(self, view, get_request, watchlist):
        """Assert that ``get_watchlist`` returns the expected Watchlist instance."""
        assert view.get_watchlist(get_request) == watchlist

    def test_get_queryset(self, view, watchlist_item, stellenangebot):
        """Assert that ``get_queryset`` returns the expected queryset."""
        queryset = view.get_queryset()
        assert isinstance(queryset, QuerySet)
        assert stellenangebot in queryset

    @pytest.mark.parametrize("request_data", [{"q": "Foo"}])
    def test_get_queryset_search(self, view, watchlist_item, request_data):
        """
        Assert that ``get_queryset`` calls the search method of the queryset if
        the request contains a search term.
        """
        search_mock = Mock()
        search_mock.name = "my search mock"
        queryset_mock = Mock(search=search_mock)
        queryset_mock.filter.return_value = queryset_mock
        with patch.object(view, "get_watchlist") as m:
            m.return_value.get_stellenangebote.return_value = queryset_mock
            view.get_queryset()
            search_mock.assert_called_with("Foo")

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
    def beschreibung(self):
        return "foo"

    @pytest.fixture
    def includes_beschreibung(self):
        """Return whether the POST data contains a 'beschreibung'."""
        return True

    @pytest.fixture
    def request_data(self, stellenangebot, watchlist_name, includes_beschreibung, beschreibung):
        """Return the data for the request."""
        data = {"titel": stellenangebot.titel, "refnr": stellenangebot.refnr, "watchlist_name": watchlist_name}
        if includes_beschreibung:
            data["beschreibung"] = beschreibung
        return data

    @pytest.fixture
    def get_beschreibung_mock(self, beschreibung):
        with patch("jobby.views._get_beschreibung") as m:
            m.return_value = beschreibung
            yield m

    def test_not_on_watchlist(self, client, watchlist, stellenangebot):
        response = client.post(reverse("watchlist_toggle"), data={"refnr": stellenangebot.refnr})
        assert response.status_code == 200
        assert watchlist.items.filter(stellenangebot=stellenangebot).exists()

    def test_already_on_watchlist(self, client, watchlist, watchlist_item, stellenangebot):
        response = client.post(reverse("watchlist_toggle"), data={"refnr": stellenangebot.refnr})
        assert response.status_code == 200
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

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

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    @pytest.mark.parametrize("includes_beschreibung", [False])
    def test_watchlist_toggle_new_angebot_beschreibung(
        self,
        post_request,
        stellenangebot,
        includes_beschreibung,
        beschreibung,
        get_beschreibung_mock,
    ):
        """
        Assert that a 'beschreibung' is added to new Stellenangebot objects
        when they are being added to the watchlist via the toggle.
        """
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        get_beschreibung_mock.assert_called_with(stellenangebot.refnr)
        saved_angebot = Stellenangebot.objects.get(refnr=stellenangebot.refnr)
        assert saved_angebot.beschreibung == beschreibung

    @pytest.mark.parametrize("stellenangebot", [StellenangebotFactory.build()])
    @pytest.mark.parametrize("includes_beschreibung", [False])
    def test_watchlist_toggle_new_angebot_beschreibung_bad_request(
        self,
        post_request,
        stellenangebot,
        includes_beschreibung,
        get_beschreibung_mock,
    ):
        """
        Assert that no 'beschreibung' is added to new Stellenangebot objects if
        ``_get_beschreibung`` raises a BadRequest during the toggle process.
        """
        get_beschreibung_mock.side_effect = BadRequest
        response = watchlist_toggle(post_request)
        assert response.status_code == 200
        saved_angebot = Stellenangebot.objects.get(refnr=stellenangebot.refnr)
        assert not saved_angebot.beschreibung

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

    @pytest.fixture
    def request_data(self, request_data, watchlist_name):
        request_data["watchlist_name"] = watchlist_name
        return request_data

    @pytest.fixture
    def super_get_mock(self, view, view_extra_context, stellenangebot, super_mock):
        """Mock out super().get() to return a mocked response."""

        def get(*_args, **_kwargs):
            if "add" in view_extra_context and not view_extra_context["add"]:
                view.object = stellenangebot
            else:
                view.object = None
            return response_mock

        response_mock = Mock()
        super_mock.return_value.get = Mock(side_effect=get)
        return response_mock

    @pytest.fixture
    def is_expired_mock(self):
        """Mock out the view's is_expired method."""
        with patch("jobby.views.StellenangebotView.is_expired") as m:
            m.return_value = False
            yield m

    @pytest.fixture
    def messages_mock(self):
        """Mock out the django messages package."""
        with patch("jobby.views.messages") as m:
            yield m

    @pytest.fixture
    def formset_mock(self):
        """
        Mock out the formsets of the StellenangebotView, so we don't have to
        supply their management data in the request data.
        """
        with patch("jobby.views.StellenangebotView.formset_classes", new=[]) as m:
            yield m

    def test_add(self, client):
        response = client.get(reverse("stellenangebot_add"))
        assert response.status_code == 200

    def test_add_save(self, client, formset_mock):
        request_data = {"notizen": "foo", "titel": "Software Tester", "refnr": "1234", "beschreibung": "Text"}
        response = client.post(reverse("stellenangebot_add"), request_data, follow=True)
        assert response.status_code == 200
        assert Stellenangebot.objects.filter(**request_data).exists()

    def test_edit(self, client, stellenangebot):
        response = client.get(reverse("stellenangebot_edit", kwargs={"id": stellenangebot.pk}))
        assert response.status_code == 200

    def test_edit_save(self, client, stellenangebot, formset_mock, is_expired_mock):
        stellenangebot.notizen = "foo"
        stellenangebot.save()
        request_data = {
            "notizen": "bar",
            "titel": stellenangebot.titel,
            "refnr": stellenangebot.refnr,
            "beschreibung": "Text",
        }
        response = client.post(
            reverse("stellenangebot_edit", kwargs={"id": stellenangebot.pk}),
            data=request_data,
            follow=True,
        )
        assert response.status_code == 200
        stellenangebot.refresh_from_db()
        assert stellenangebot.notizen == "bar"

    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_object_add(self, view, view_extra_context):
        """Assert that ``get_object`` returns None if this is an 'add' view."""
        assert view.get_object() is None

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_object_edit(self, view, view_extra_context, super_mock, is_expired_mock):
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

    @pytest.mark.parametrize("request_data", [{"refnr": "1234", "api": "api_mock"}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_details_url_request_has_refnr(self, registry_mock, view, view_extra_context, request_data):
        """
        Assert that ``get_details_url`` calls the registry's get_details_url
        method if both refnr and api name are in the GET request data.
        """
        view.get_details_url()
        registry_mock.get_details_url.assert_called_with(request_data["api"], request_data["refnr"])

    @pytest.mark.parametrize("request_data", [{}])
    @pytest.mark.parametrize("view_extra_context", [{"add": True}])
    def test_get_details_url_request_does_not_have_refnr(self, view, view_extra_context, request_data):
        """
        Assert that ``get_details_url`` returns None if the request data for an
        'add' view does not contain a refnr.
        """
        assert not view.get_details_url()

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_details_url_edit(self, registry_mock, view, view_extra_context, stellenangebot, refnr):
        """
        Assert that ``get_details_url`` calls the registry's get_details_url
        method with the refnr and api name of the view object.
        """
        view.object = stellenangebot
        view.get_details_url()
        registry_mock.get_details_url.assert_called_with(stellenangebot.api, stellenangebot.refnr)

    @pytest.mark.parametrize("refnr", [""])
    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_get_details_url_edit_no_refnr(self, view, view_extra_context, stellenangebot, refnr):
        """
        Assert that ``get_details_url`` returns None if the edit view's instance
        does not have a refnr set.
        """
        view.object = stellenangebot
        assert not view.get_details_url()

    @pytest.mark.parametrize("view_extra_context", [{"add": True}, {"add": False}])
    def test_get_watchlist(self, view, view_extra_context, post_request, watchlist):
        """Assert that ``get_watchlist`` returns the expected watchlist."""
        assert view.get_watchlist(post_request) == watchlist

    @pytest.mark.parametrize("view_extra_context", [{"add": True}, {"add": False}])
    def test_form_valid_adds_to_watchlist(self, view, view_extra_context, super_mock, stellenangebot, watchlist):
        """Asser that ``form_valid`` adds the view object to the watchlist."""
        view.object = stellenangebot
        with patch.object(view, "get_watchlist", new=Mock(return_value=watchlist)):
            with patch.object(watchlist, "add_watchlist_item") as add_mock:
                view.form_valid(None)
                add_mock.assert_called_with(stellenangebot)

    @pytest.mark.parametrize("view_extra_context", [{"add": True}, {"add": False}])
    @pytest.mark.parametrize("request_data", [{"submit_suche": ""}])
    def test_get_success_url_suche(self, view_post_request, view_extra_context, request_data):
        """
        Assert that ``get_success_url`` returns the URL for the 'suche' page if
        'submit_suche' is in request.POST.
        """
        assert view_post_request.get_success_url() == reverse("suche")

    @pytest.mark.parametrize("view_extra_context", [{"add": True}, {"add": False}])
    @pytest.mark.parametrize("request_data", [{"submit_watchlist": ""}])
    def test_get_success_url_watchlist(self, view_post_request, view_extra_context, request_data):
        """
        Assert that ``get_success_url`` returns the URL for the 'watchlist' page
        if 'submit_watchlist' is in request.POST.
        """
        assert view_post_request.get_success_url() == reverse("watchlist")

    @pytest.mark.parametrize("view_extra_context", [{"add": True}, {"add": False}])
    @pytest.mark.parametrize("request_data", [{}])
    def test_get_success_url_edit(self, view_post_request, view_extra_context, request_data, stellenangebot):
        """
        Assert that ``get_success_url`` returns the URL for the edit page if
        request.POST does not contain 'submit_suche' or 'submit_watchlist'.
        """
        view_post_request.object = stellenangebot
        assert view_post_request.get_success_url() == reverse("stellenangebot_edit", kwargs={"id": stellenangebot.pk})

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_check_if_expired(
        self,
        view,
        view_extra_context,
        get_request,
        stellenangebot,
        is_expired_mock,
        messages_mock,
    ):
        """
        Assert that ``check_if_expired`` calls the is_expired method and
        updates the view's Stellenangebot if it has expired.
        """
        view.object = stellenangebot
        view.add = False
        is_expired_mock.return_value = True
        view.check_if_expired(get_request)
        is_expired_mock.assert_called()
        stellenangebot.refresh_from_db()
        assert stellenangebot.expired

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_is_expired(self, view, view_extra_context, requests_mock):
        """
        Assert that ``is_expired`` returns whether the response for the
        external job details page was ok.
        """
        details_url = "http://foo.bar"
        with patch.object(view, "get_details_url") as get_details_url_mock:
            get_details_url_mock.return_value = details_url
            requests_mock.get(details_url, status_code=404)
            assert view.is_expired()

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    def test_is_expired_exception(self, view, view_extra_context):
        """
        Assert that ``is_expired`` catches exceptions raised by requests and
        returns False instead.
        """
        with patch.object(view, "get_details_url"):
            with patch("jobby.views.requests") as requests_mock:
                requests_mock.get = Mock(side_effect=Exception)
                assert not view.is_expired()

    @pytest.mark.parametrize("view_extra_context", [{"add": False}])
    @pytest.mark.parametrize("stellenangebot_extra_data", [{"expired": True}, {"expired": False}])
    def test_check_if_expired_sends_user_message_if_expired(
        self,
        view,
        get_request,
        view_extra_context,
        stellenangebot,
        stellenangebot_extra_data,
        messages_mock,
        is_expired_mock,
    ):
        """Assert that ``check_if_expired`` emits a user message if the view
        object has expired.
        """
        view.object = stellenangebot
        view.add = False
        add_message_mock = Mock()
        messages_mock.add_message = add_message_mock
        messages_mock.ERROR = messages.ERROR

        view.check_if_expired(get_request)
        if stellenangebot_extra_data["expired"]:
            add_message_mock.assert_called_with(
                get_request, level=messages.ERROR, message="Dieses Stellenangebot ist nicht mehr verfügbar."
            )
        else:
            add_message_mock.assert_not_called()

    @pytest.mark.parametrize("view_extra_context", [{"add": False}, {"add": True}])
    def test_get_calls_check_if_expired(self, view, view_extra_context, super_get_mock, get_request):
        """
        Assert that get calls the ``check_if_expired`` method if it is an edit
        view.
        """
        with patch.object(view, "check_if_expired") as check_mock:
            view.get(get_request)
            if view_extra_context["add"]:
                check_mock.assert_not_called()
            else:
                check_mock.assert_called()


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestWatchlistRemove:

    @pytest.fixture
    def request_data(self, refnr, watchlist_name):
        return {"refnr": refnr, "watchlist_name": watchlist_name}

    def test(self, client, watchlist, watchlist_item, stellenangebot):
        response = client.post(reverse("watchlist_remove"), data={"refnr": stellenangebot.refnr})
        assert response.status_code == 200
        assert not watchlist.items.filter(stellenangebot=stellenangebot).exists()

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

    def test_deletes_stellenangebot_without_user_data(self, post_request, watchlist_item, watchlist, stellenangebot):
        """
        Assert that a Stellenangebot without extra user data is deleted if
        removed from the watchlist via ``watchlist_remove``.
        """
        stellenangebot_pk = stellenangebot.pk
        watchlist_remove(post_request)
        assert not Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()

    def test_deletes_stellenangebot_with_user_data(self, post_request, watchlist_item, watchlist, stellenangebot):
        """
        Assert that a Stellenangebot without extra user data is deleted if
        removed from the watchlist via ``watchlist_remove``.
        """
        stellenangebot.notizen = "Foo"
        stellenangebot.save()
        stellenangebot_pk = stellenangebot.pk
        watchlist_remove(post_request)
        assert Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestWatchlistRemoveAll:

    @pytest.fixture
    def request_data(self, refnr, watchlist_name):
        return {"refnr": refnr, "watchlist_name": watchlist_name}

    def test(self, client, watchlist, watchlist_item):
        response = client.post(reverse("watchlist_remove_all"))
        assert response.status_code == 200
        assert not watchlist.items.exists()

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

    def test_deletes_stellenangebot_without_user_data(self, post_request, watchlist_item, watchlist, stellenangebot):
        """
        Assert that a Stellenangebot without extra user data is deleted if
        removed from the watchlist via ``watchlist_remove_all``.
        """
        stellenangebot_pk = stellenangebot.pk
        watchlist_remove_all(post_request)
        assert not Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()

    def test_deletes_stellenangebot_with_user_data(self, post_request, watchlist_item, watchlist, stellenangebot):
        """
        Assert that a Stellenangebot without extra user data is deleted if
        removed from the watchlist via ``watchlist_remove_all``.
        """
        stellenangebot.notizen = "Foo"
        stellenangebot.save()
        stellenangebot_pk = stellenangebot.pk
        watchlist_remove_all(post_request)
        assert Stellenangebot.objects.filter(pk=stellenangebot_pk).exists()


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
    def jobdetails_request_mock(self, requests_mock, details_url, details_html, status_code):
        requests_mock.get(details_url, text=details_html, status_code=status_code)

    @pytest.fixture
    def get_request(self, jobdetails_request_mock, get_request):
        """Create a mocked response for the job details request call."""
        return get_request

    @pytest.fixture
    def get_beschreibung_response(self, get_request, refnr):
        """Call ``get_beschreibung`` and return the response."""
        return get_beschreibung(get_request, refnr=refnr)

    def test(self, jobdetails_request_mock, client, refnr, beschreibung_html):
        response = client.post(reverse("get_angebot_beschreibung", kwargs={"refnr": refnr}))
        assert response.status_code == 200
        assert response.content.decode("utf-8") == beschreibung_html

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

    @pytest.mark.parametrize(
        "details_html,beschreibung_html",
        [
            (
                """<div id="detail-beschreibung-extern">
                        <a id="detail-beschreibung-externe-url-btn" href="www.foobar.com">www.foobar.com</a>
                        </div>""",
                """Beschreibung auf externer Seite: <a href="www.foobar.com">www.foobar.com</a>""",
            )
        ],
    )
    def test_get_beschreibung_externe_url(self, get_beschreibung_response, details_html, beschreibung_html):
        """
        Assert that ``get_beschreibung`` also checks links to external
        descriptions.
        """
        assert get_beschreibung_response.content.decode("utf-8") == beschreibung_html


class TestPapierkorbView:

    @pytest.fixture
    def view_class(self):
        return PapierkorbView

    @pytest.fixture
    def other_watchlist_item(self, watchlist):
        # Add a 'control' item that should not appear in the view's queryset.
        return WatchlistItemFactory(watchlist=watchlist, stellenangebot=StellenangebotFactory())

    def test(self, client):
        response = client.get(reverse("papierkorb"))
        assert response.status_code == 200

    def test_get_queryset(self, view, watchlist, stellenangebot, other_watchlist_item):
        """
        Assert that PapierkorbView.get_queryset returns all Stellenangebot
        instances that are not on any watchlist.
        """
        queryset = view.get_queryset()
        assert stellenangebot in queryset
        assert other_watchlist_item.stellenangebot not in queryset


class TestBaseMixin:

    @pytest.fixture
    def client_request(self, client, request_path, request_data):
        response = client.get(request_path, data=request_data)
        return response.wsgi_request

    @pytest.mark.parametrize("request_path", ["404/"])
    def test_get_search_filters_no_match(self, client_request, request_path):
        assert BaseMixin().get_search_filters(client_request) == ""

    @pytest.mark.parametrize("request_path", ["/suche/"])
    @pytest.mark.parametrize("request_data", [{"foo": "bar"}])
    def test_get_search_filters_suche(self, client_request, request_path, request_data):
        assert BaseMixin().get_search_filters(client_request) == "_search_filters=foo%3Dbar"

    @pytest.mark.parametrize("request_path", ["/not_suche/"])
    @pytest.mark.parametrize("request_data", [{"_search_filters": "foo=bar"}])
    def test_get_search_filters_not_suche(self, client_request, request_path, request_data):
        assert BaseMixin().get_search_filters(client_request) == "_search_filters=foo%3Dbar"


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestStellenangebotRemove:

    def test(self, client, stellenangebot, watchlist_item, watchlist):
        response = client.post(reverse("stellenangebot_remove", kwargs={"id": stellenangebot.pk}), follow=True)
        assert response.status_code == 200
        assert not watchlist.on_watchlist(stellenangebot)

    @pytest.fixture
    def request_data(self, watchlist_name):
        return {"watchlist_name": watchlist_name}

    def test_stellenangebot_remove(self, post_request, stellenangebot, watchlist_item, watchlist):
        """
        Assert that ``stellenangebot_remove`` removes the Stellenangebot from
        the watchlist.
        """
        stellenangebot_remove(post_request, stellenangebot.pk)
        assert not watchlist.on_watchlist(stellenangebot)

    @pytest.mark.parametrize("request_kwargs", [{"follow": True}])
    def test_stellenangebot_remove_redirects(self, post_request, stellenangebot, request_kwargs):
        """Assert that ``stellenangebot_remove`` redirects to the watchlist."""
        response = stellenangebot_remove(post_request, stellenangebot.pk)
        assert response.url == reverse("watchlist")

    def test_stellenangebot_remove_object_does_not_exist(self, post_request):
        """
        Assert that ``stellenangebot_remove`` returns an OK response if no
        Stellenangebot with the requested refnr exists.
        """
        response = stellenangebot_remove(post_request, 0)
        assert response.status_code == 302


@pytest.mark.usefixtures("ignore_csrf_protection")
class TestPapierkorbDelete:

    @pytest.fixture
    def request_data(self, stellenangebot):
        return {"pk": stellenangebot.pk}

    def test(self, client, request_data, stellenangebot):
        pk = stellenangebot.pk
        response = client.post(reverse("papierkorb_delete"), data=request_data)
        assert response.status_code == 200
        assert not Stellenangebot.objects.filter(pk=pk).exists()

    @pytest.mark.parametrize("request_data", [{}])
    def test_no_pk(self, post_request, request_data):
        assert papierkorb_delete(post_request).status_code == 400
