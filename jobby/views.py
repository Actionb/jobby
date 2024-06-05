from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.generic import FormView, ListView
from django.views.generic.base import ContextMixin

from jobby.forms import SucheForm
from jobby.models import Stellenangebot, Watchlist, WatchlistItem
from jobby.search import search

PAGE_VAR = "page"
PAGE_SIZE = 100


class BaseMixin(ContextMixin):
    site_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["site_title"] = self.site_title
        return ctx


class SucheView(BaseMixin, FormView):
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
            search_response = search(**form.cleaned_data)
        except Exception as e:
            self._send_error_message(e)
        else:
            ctx.update(self.get_results_context(search_response))
            if search_response.result_count:
                ctx.update(self.get_pagination_context(search_response.result_count))
        return self.render_to_response(ctx)

    def _send_error_message(self, exception):  # pragma: no cover
        messages.add_message(self.request, level=messages.ERROR, message=f"Fehler bei der Suche: {exception}")

    def _get_watchlist_item_ids(self, results):
        if results:
            saved_results = [r for r in results if r.pk]
            queryset = WatchlistItem.objects.filter(stellenangebot__in=saved_results)
        else:
            queryset = WatchlistItem.objects.none()
        return set(queryset.values_list("pk", flat=True))

    def get_results_context(self, search_response):
        results = search_response.results
        watchlist_item_ids = self._get_watchlist_item_ids(results)
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


class WatchlistView(BaseMixin, ListView):
    site_title = "Merkliste"
    template_name = "jobby/watchlist.html"

    def current_watchlist_name(self, request):
        return request.GET["watchlist_name"]

    def get_watchlist(self, request):
        return Watchlist.objects.get(name=self.current_watchlist_name(request))

    def get_queryset(self):
        # TODO: implement text search
        return self.get_watchlist(self.request).get_stellenangebote()

    def get_watchlist_names(self):
        return Watchlist.objects.values_list("name", flat=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current_watchlist_name = self.current_watchlist_name(self.request)
        ctx["current_watchlist"] = current_watchlist_name
        ctx["watchlist_names"] = self.get_watchlist_names().exclude(name=current_watchlist_name)
        return ctx


def watchlist_toggle(request):
    """
    Add an object to the watchlist, or remove an object if it already exists on
    the watchlist.
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
        obj = Stellenangebot.objects.create(titel="Woops, add a titel!", refnr=refnr)

    if watchlist.on_watchlist(obj):
        watchlist.remove_watchlist_item(obj)
        on_watchlist = False
    else:
        watchlist.add_watchlist_item(obj)
        on_watchlist = True
    return JsonResponse({"on_watchlist": on_watchlist})
