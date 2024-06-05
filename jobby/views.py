from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import FormView, ListView
from django.views.generic.base import ContextMixin

from jobby.forms import SucheForm
from jobby.models import Watchlist
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
            results = search_response.results
            ctx["results"] = results
            ctx["result_count"] = search_response.result_count
            if search_response.result_count:
                ctx.update(**self.get_pagination_context(search_response.result_count))
        return self.render_to_response(ctx)

    def _send_error_message(self, exception):  # pragma: no cover
        messages.add_message(self.request, level=messages.ERROR, message=f"Fehler bei der Suche: {exception}")

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


class WatchlistView(ListView):

    template_name = "jobby/watchlist.html"

    def get_watchlist(self, request):
        return Watchlist.objects.get(name=request.GET["watchlist_name"])

    def get_queryset(self):
        return self.get_watchlist(self.request).get_stellenangebote()
