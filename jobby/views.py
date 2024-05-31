from django import forms
from django.views.generic import FormView

from jobby.models import SucheModel
from jobby.query import get_angebote


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
        ctx["results"] = get_angebote(**form.cleaned_data)
        return self.render_to_response(ctx)
