from functools import cached_property

from django import forms
from django.core.exceptions import BadRequest, ValidationError
from django.db.models import QuerySet

from jobby.models import Stellenangebot, SucheModel

null_boolean_select = forms.Select(choices=[(None, "---------"), (True, "Ja"), (False, "Nein")])


class SucheForm(forms.ModelForm):
    class Meta:
        model = SucheModel
        # FIXME: queries that include these parameters never return results, so
        #  ignore them for now:
        exclude = ["behinderung", "corona"]
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

        The fields ``was``, ``wo``, and ``umkreis`` should always be shown.
        Fields that have a non-emtpy value should also be shown.
        """
        always_shown = ("was", "wo", "umkreis")
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
            "externe_url": forms.HiddenInput(),
            "beschreibung": forms.HiddenInput(),
            "api": forms.HiddenInput(),
            "expired": forms.HiddenInput(),
        }

    def get_initial_for_field(self, field, field_name):
        initial = super().get_initial_for_field(field, field_name)
        # Turn initial data for date/datetime fields into date/datetime objects
        # so that the template can render them as localized.
        if isinstance(field, (forms.DateField, forms.DateTimeField)) and isinstance(initial, str):
            try:
                return field.to_python(initial)
            except ValidationError:
                # Invalid date - can't localize anyway.
                pass
        return initial

    def clean_beschreibung(self):
        # Fetch a job description from the job details page on arbeitsagentur.de
        # if no description is given:
        beschreibung = self.cleaned_data.get("beschreibung", "")
        if not beschreibung:
            from jobby.views import _get_beschreibung  # avoid circular imports

            try:
                beschreibung = _get_beschreibung(self.cleaned_data["refnr"])
            except BadRequest:
                pass
        return beschreibung


class WatchlistSearchForm(forms.Form):
    # TODO: add watchlist select once multiple watchlists are supported
    q = forms.CharField(required=False, label="Textsuche")
    bewerbungsstatus = forms.ChoiceField(choices=Stellenangebot.BewerbungChoices, required=False)

    def get_filter_params(self, cleaned_data):
        """Return the search form's data as queryset filter parameters."""
        params = {}
        for field_name, value in cleaned_data.items():
            formfield = self.fields[field_name]
            if (
                isinstance(formfield, forms.BooleanField)
                and not isinstance(formfield, forms.NullBooleanField)
                and not value
            ):  # pragma: no cover
                # NOTE: Currently, there the search form does not use any
                #  BooleanFields, so this branch is never entered.
                # value is False on a simple BooleanField; don't include it.
                continue
            elif value in formfield.empty_values or isinstance(value, QuerySet) and not value.exists():
                # Don't want empty values as filter parameters!
                continue
            params[field_name] = value
        return params
