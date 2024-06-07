from functools import cached_property

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

    @cached_property
    def shown_fields(self):
        """
        Return the fields that should be shown (i.e. not rendered as collapsed).

        The fields ``was``, ``wo``, and ``umfeld`` should always be shown.
        Fields that have a non-emtpy value should also be shown.
        """
        always_shown = ("was", "wo", "umfeld")
        fields = []
        for bound_field in self:
            if bound_field.name in always_shown or bound_field.value() not in bound_field.field.empty_values:
                fields.append(bound_field)
        return fields

    @cached_property
    def collapsed_fields(self):
        """Return the fields that should be rendered as collapsed."""
        return [bound_field for bound_field in self if bound_field not in self.shown_fields]


class StellenangebotForm(forms.ModelForm):
    class Meta:
        model = Stellenangebot
        fields = forms.ALL_FIELDS
        widgets = {
            # The user should not need to edit the values for these fields:
            "titel": forms.HiddenInput(),
            "refnr": forms.HiddenInput(),
            "beruf": forms.HiddenInput(),
            "arbeitgeber": forms.HiddenInput(),
            "arbeitsort": forms.HiddenInput(),
            "eintrittsdatum": forms.HiddenInput(),
            "veroeffentlicht": forms.HiddenInput(),
            "modified": forms.HiddenInput(),
        }
