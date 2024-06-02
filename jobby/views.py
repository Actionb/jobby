from django import forms
from django.contrib import messages
from django.views.generic import FormView

from jobby.models import SucheModel
from jobby.search import search


class SucheView(FormView):
    form_class = forms.modelform_factory(SucheModel, fields=forms.ALL_FIELDS)
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
            ctx["results"] = search(**form.cleaned_data)
        except Exception as e:
            self._send_error_message(e)
        return self.render_to_response(ctx)

    def _send_error_message(self, exception):
        messages.add_message(self.request, level=messages.ERROR, message=f"Fehler bei der Suche: {exception}")
