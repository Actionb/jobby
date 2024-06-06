from django import forms

from jobby.models import Stellenangebot, SucheModel

null_boolean_select = forms.Select(choices=[(None, "---------"), (True, "Ja"), (False, "Nein")])


class SucheForm(forms.ModelForm):
    class Meta:
        model = SucheModel
        fields = forms.ALL_FIELDS
        exclude = ["corona"]
        widgets = {
            "page": forms.HiddenInput,
            "size": forms.HiddenInput,
            "zeitarbeit": null_boolean_select,
            "behinderung": null_boolean_select,
        }


class SearchResultForm(forms.ModelForm):
    class Meta:
        model = Stellenangebot
        exclude = ["bewerbungsstatus", "notizen"]


class StellenangebotForm(forms.ModelForm):
    class Meta:
        model = Stellenangebot
        fields = forms.ALL_FIELDS
