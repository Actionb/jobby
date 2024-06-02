from django import forms

from jobby.models import SucheModel


class SucheForm(forms.ModelForm):
    class Meta:
        model = SucheModel
        fields = forms.ALL_FIELDS
        widgets = {
            "page": forms.HiddenInput,
            "size": forms.HiddenInput,
        }
