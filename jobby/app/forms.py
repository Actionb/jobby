from django import forms

from jobby.app import models as _models


class SucheForm(forms.ModelForm):
    class Meta:
        model = _models.SucheModel
        fields = ["was", "wo", ""]
