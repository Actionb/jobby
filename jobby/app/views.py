from django import forms
from django.views.generic import FormView

from jobby.app.models import SucheModel


class SucheView(FormView):
    form_class = forms.modelform_factory(SucheModel, fields=forms.ALL_FIELDS)
