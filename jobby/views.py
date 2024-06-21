import requests
from bs4 import BeautifulSoup
from django.contrib import messages
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from jobby.apis.registry import registry
from jobby.forms import StellenangebotForm, SucheForm, WatchlistSearchForm
from jobby.models import Stellenangebot, Watchlist, WatchlistItem

PAGE_VAR = "page"
PAGE_SIZE = 100


class BaseMixin(ContextMixin):
    site_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["site_title"] = self.site_title
        ctx["orphan_count"] = Stellenangebot.objects.exclude(
            Exists(WatchlistItem.objects.filter(stellenangebot_id=OuterRef("id")))
        ).count()
        return ctx


class SucheView(BaseMixin, FormView):
    site_title = "Suche"
    form_class = SucheForm
    template_name = "jobby/suche.html"

    def get(self, request, *args, **kwargs):
        if "suche" in request.GET:
            form = self.form_class(data=request.GET)
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        ctx = self.get_context_data(form=form)
        try:
            search_response = registry.search(**form.cleaned_data)
        except Exception as e:
            self._send_error_message(e)
        else:
            ctx.update(self.get_results_context(search_response))
            if search_response.has_results and search_response.result_count:
                ctx.update(self.get_pagination_context(search_response.result_count))
            ctx["watchlist_toggle_url"] = reverse("watchlist_toggle")
        return self.render_to_response(ctx)

    def _send_error_message(self, exception):  # pragma: no cover
        messages.add_message(self.request, level=messages.ERROR, message=f"Fehler bei der Suche: {exception}")

    def _get_watchlisted_ids(self, results):
        if results:
            queryset = WatchlistItem.objects.filter(stellenangebot__in=[r for r in results if r.pk])
            return set(queryset.values_list("stellenangebot_id", flat=True))
        else:
            return set()

    def get_results_context(self, search_response):
        results = search_response.results
        watchlist_item_ids = self._get_watchlisted_ids(results)
        return {
            "results": [(result, result.pk in watchlist_item_ids) for result in results],
            "result_count": search_response.result_count,
        }

    def get_pagination_context(self, result_count, per_page=PAGE_SIZE):
        paginator = Paginator(range(1, result_count + 1), per_page=per_page)
        page = self.kwargs.get(PAGE_VAR) or self.request.GET.get(PAGE_VAR) or 1
        try:
            page_number = int(page)
        except ValueError:
            page_number = 1
        return {
            "current_page": page_number,
            "page_range": list(paginator.get_elided_page_range(page_number)),
            "pagination_required": result_count > per_page,
        }


class StellenangebotView(BaseMixin, UpdateView):
    model = Stellenangebot
    form_class = StellenangebotForm
    template_name = "jobby/angebot.html"
    pk_url_kwarg = "id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add = self.extra_context["add"]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Check if this is an add view for a refnr for which a Stellenangebot
        # instance already exists. If that is the case, redirect to the
        # instance's edit page.
        # (this can happen when bookmarking a Stellenangebot on the results page
        # and then clicking on the link to the add view next to it)
        refnr = request.GET.get("refnr", None)
        if self.object is None and self.add and refnr:
            try:
                obj = Stellenangebot.objects.get(refnr=refnr)
                return redirect(reverse("stellenangebot_edit", kwargs={"id": obj.pk}))
            except Stellenangebot.DoesNotExist:  # noqa
                pass
        return response

    def get_object(self, queryset=None):
        if not self.add:
            return super().get_object(queryset)

    def get_initial(self):
        initial = super().get_initial()
        if self.add:
            initial.update(self.request.GET.dict())
        return initial

    def get_success_url(self):  # pragma: no cover
        # TODO: return to previous page (either suche or merkliste)
        return reverse("stellenangebot_edit", kwargs={"id": self.object.pk})

    @property
    def site_title(self):
        if self.add:
            return self.request.GET.get("titel", "Stellenangebot")
        else:
            return self.object.titel or "Stellenangebot"

    def get_arge_link(self):
        if self.add:
            refnr = self.request.GET.get("refnr", None)
        else:
            refnr = self.object.refnr
        if refnr:
            return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

    def get_context_data(self, **kwargs):  # pragma: no cover
        ctx = super().get_context_data(**kwargs)
        ctx["arge_link"] = self.get_arge_link()
        return ctx

    def get_watchlist(self, request):
        watchlist, _created = Watchlist.objects.get_or_create(name=request.POST.get("watchlist_name", "default"))
        return watchlist

    def form_valid(self, form):
        response = super().form_valid(form)
        self.get_watchlist(self.request).add_watchlist_item(self.object)
        return response


################################################################################
# Watchlist
################################################################################


class WatchlistView(BaseMixin, ListView):
    site_title = "Merkliste"
    template_name = "jobby/watchlist.html"

    def current_watchlist_name(self, request):
        return request.GET.get("watchlist_name", "default")

    def get_watchlist(self, request):
        watchlist, _created = Watchlist.objects.get_or_create(name=self.current_watchlist_name(request))
        return watchlist

    def get_queryset(self):
        # TODO: implement text search
        queryset = self.get_watchlist(self.request).get_stellenangebote()
        search_form = WatchlistSearchForm(data=self.request.GET.dict())
        if search_form.is_valid():
            filters = search_form.get_filter_params(search_form.cleaned_data)
            queryset = queryset.filter(**filters)
        return queryset

    def get_watchlist_names(self):
        return Watchlist.objects.values_list("name", flat=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_form"] = WatchlistSearchForm(data=self.request.GET.dict())
        return ctx


@csrf_protect
def watchlist_toggle(request):
    """
    Add an item to the watchlist, or remove an item if it already exists on the
    watchlist.
    """
    try:
        refnr = request.POST["refnr"]
    except KeyError:
        return HttpResponseBadRequest()

    watchlist_name = request.POST.get("watchlist_name", "default")
    watchlist, _created = Watchlist.objects.get_or_create(name=watchlist_name)
    try:
        obj = Stellenangebot.objects.get(refnr=refnr)
    except Stellenangebot.DoesNotExist:  # noqa
        # Create a new Stellenangebot instance from the POST data:
        form = StellenangebotForm(data=request.POST)
        if form.is_valid():
            obj = form.save()
        else:
            return HttpResponseBadRequest()

    if watchlist.on_watchlist(obj):
        watchlist.remove_watchlist_item(obj)
        on_watchlist = False
    else:
        watchlist.add_watchlist_item(obj)
        on_watchlist = True
    return JsonResponse({"on_watchlist": on_watchlist, "link_url": obj.as_url()})


@csrf_protect
def watchlist_remove(request):
    """Remove an item from the watchlist."""
    try:
        refnr = request.POST["refnr"]
    except KeyError:
        return HttpResponseBadRequest()
    try:
        watchlist = Watchlist.objects.get(name=request.POST.get("watchlist_name", "default"))
        obj = Stellenangebot.objects.get(refnr=refnr)
    except ObjectDoesNotExist:
        # The Stellenangebot is not on the watchlist either because the
        # Stellenangebot does not exist or because the watchlist itself does
        # not exist. Job done!
        pass
    else:
        watchlist.remove_watchlist_item(obj)
    return JsonResponse({})


@csrf_protect
def watchlist_remove_all(request):
    """Remove all items from the watchlist."""
    try:
        watchlist = Watchlist.objects.get(name=request.POST.get("watchlist_name", "default"))
    except Watchlist.DoesNotExist:  # noqa
        # This watchlist already has all its items removed, because it does not
        # exist.
        pass
    else:
        for item in watchlist.items.all():
            watchlist.remove_watchlist_item(item.stellenangebot)
    return JsonResponse({})


# The id of the element on the job details page that contains the description:
DETAILS_BESCHREIBUNG_ID = "detail-beschreibung-beschreibung"
# The id of the link on the job details page that links to the external page
# that contains the job description:
EXTERNAL_BESCHREIBUNG_LINK = "detail-beschreibung-externe-url-btn"


def _get_beschreibung(refnr):
    """
    Fetch the job details page of the job with the given refnr, and return the
    'beschreibung' part of the page.
    """
    response = requests.get(f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}")
    if not response.status_code == 200:
        raise BadRequest

    soup = BeautifulSoup(response.content, "html.parser")
    if beschreibung := soup.find(id=DETAILS_BESCHREIBUNG_ID):
        return "".join(str(elem) for elem in beschreibung.children)
    elif extern_link := soup.find(id=EXTERNAL_BESCHREIBUNG_LINK):
        return f"""Beschreibung auf externer Seite: <a href="{extern_link["href"]}">{extern_link.string}</a>"""
    else:
        return "Keine Beschreibung gegeben!"


def get_beschreibung(request, refnr=""):
    """Get the job description HTML from the details page on arbeitsagentur.de."""
    try:
        beschreibung = _get_beschreibung(refnr)
    except BadRequest:
        return HttpResponseBadRequest()
    return HttpResponse(beschreibung)


class PapierkorbView(BaseMixin, ListView):
    site_title = "Papierkorb"
    template_name = "jobby/papierkorb.html"

    def get_queryset(self):
        return Stellenangebot.objects.exclude(Exists(WatchlistItem.objects.filter(stellenangebot_id=OuterRef("id"))))


def delete_stellenangebot(request):
    try:
        pk = request.POST["pk"]
    except KeyError:
        return HttpResponseBadRequest()

    Stellenangebot.objects.filter(pk=pk).delete()
    return HttpResponse()
