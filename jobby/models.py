from django.db import models
from django.forms import model_to_dict
from django.urls import reverse
from django.utils.http import urlencode

CHARFIELD_MAX = 256


def _update_stellenangebot(existing, other):
    """Update the existing Stellenangebot object with data from the other."""
    if not isinstance(existing, Stellenangebot) or not isinstance(other, Stellenangebot):
        raise TypeError("Arguments must be Stellenangebot instances.")

    if existing.refnr != other.refnr:
        # Not the same Stellenangebot.
        return False

    update_dict = {}
    for field in existing._meta.get_fields():
        if not field.concrete or field.primary_key:
            # This either a relation field or the field is a primary key
            # (which should not be updated).
            continue
        existing_value = field.value_from_object(existing)
        other_field = other._meta.get_field(field.name)
        other_value = other_field.value_from_object(other)
        if existing_value != other_value:
            update_dict[field.name] = other_value
    if update_dict:
        Stellenangebot.objects.filter(refnr=existing.refnr).update(**update_dict)
        return True
    return False


def _as_dict(instance, empty=False, default=False):
    """
    Return the model instance as a dictionary.

    :param instance: the model instance
    :param empty: whether to include values that are considered empty
    :param default: whether to include default values
    :return: dictionary of model field name to field data
    """
    r = {}
    for field_name, value in model_to_dict(instance).items():
        model_field = instance._meta.get_field(field_name)
        if not empty and value in model_field.empty_values:
            continue
        if not default and value == model_field.default:
            continue
        r[field_name] = value
    return r


class SucheModel(models.Model):
    class AngebotsChoices(models.IntegerChoices):
        ARBEIT = 1, "Arbeit"
        SELBSTÄNDIGKEIT = 2, "Selbständigkeit"
        AUSBILDUNG = 4, "Ausbildung/Duales Studium"
        PRAKTIKUM = 34, "Praktikum/Trainee"

    class BefristungChoices(models.IntegerChoices):
        BEFRISTET = 1, "befristet"
        UNBEFRISTET = 2, "unbefristet"

    class ArbeitszeitChoices(models.TextChoices):
        VOLLZEIT = "vz", "Vollzeit"
        TEILZEIT = "tz", "Teilzeit"
        SCHICHT = "snw", "Schicht/Nachtarbeit/Wochenende"
        HOME_OFFICE = "ho", "Heim-/Telearbeit"
        MINIJOB = "mj", "Minijob"

    was = models.CharField(max_length=CHARFIELD_MAX)
    wo = models.CharField(max_length=CHARFIELD_MAX)  # TODO: required?
    berufsfeld = models.CharField(max_length=CHARFIELD_MAX, blank=True)
    arbeitgeber = models.CharField(max_length=CHARFIELD_MAX, blank=True)
    veroeffentlichtseit = models.PositiveSmallIntegerField(verbose_name="Veröffentlicht seit", blank=True, null=True)
    zeitarbeit = models.BooleanField(blank=True, null=True)
    angebotsart = models.IntegerField(choices=AngebotsChoices, blank=True, null=True)
    befristung = models.IntegerField(choices=BefristungChoices, blank=True, null=True)
    arbeitszeit = models.CharField(max_length=3, choices=ArbeitszeitChoices, blank=True)
    behinderung = models.BooleanField(blank=True, null=True)
    corona = models.BooleanField(blank=True, null=True)
    umkreis = models.PositiveSmallIntegerField(blank=True, null=True, default=25)

    # Query specific options
    page = models.PositiveSmallIntegerField(blank=True, null=True, default=1)
    size = models.PositiveSmallIntegerField(blank=True, null=True, default=50)

    class Meta:
        verbose_name = "Such-Parameter"
        verbose_name_plural = "Such-Parameter"


class Stellenangebot(models.Model):
    # TODO: set editable = False on all fields?
    class BewerbungChoices(models.TextChoices):
        NICHT_BEWORBEN = "nicht beworben"
        GEPLANT = "geplant"
        BEWORBEN = "beworben"
        ABGELEHNT = "abgelehnt"
        ANGENOMMEN = "angenommen"
        NICHT_GEPLANT = "nicht geplant"
        __empty__ = "---"

    titel = models.CharField(max_length=CHARFIELD_MAX, verbose_name="Titel")
    refnr = models.CharField(
        max_length=CHARFIELD_MAX,
        verbose_name="Referenz-Nummer",
        unique=True,
        error_messages={"unique": "Stellenangebot mit dieser Referenz-Nummer existiert bereits"},
    )
    beruf = models.CharField(max_length=CHARFIELD_MAX, blank=True, verbose_name="Beruf")
    # TODO: arbeitgeber could be a relation?
    arbeitgeber = models.CharField(max_length=CHARFIELD_MAX, blank=True, verbose_name="Arbeitgeber")
    arbeitsort = models.CharField(max_length=CHARFIELD_MAX, blank=True)
    eintrittsdatum = models.DateField(blank=True, null=True, verbose_name="Eintrittsdatum")
    veroeffentlicht = models.DateField(blank=True, null=True, verbose_name="Veröffentlicht am")
    modified = models.DateTimeField(blank=True, null=True, verbose_name="Zuletzt verändert am")
    externe_url = models.URLField(blank=True, null=True, verbose_name="Externe URL")
    beschreibung = models.TextField(blank=True, verbose_name="Beschreibung")

    bewerbungsstatus = models.CharField(
        max_length=CHARFIELD_MAX,
        choices=BewerbungChoices,
        default=BewerbungChoices.NICHT_GEPLANT,
        verbose_name="Bewerbungsstatus",
        blank=True,
        null=True,
    )
    notizen = models.TextField(verbose_name="Notizen", blank=True)

    class Meta:
        verbose_name = "Stellenangebot"
        verbose_name_plural = "Stellenangebote"

    def __str__(self):
        return self.titel

    def as_search_result_form(self):
        from jobby.forms import StellenangebotForm

        return StellenangebotForm(instance=self)

    def as_url(self):
        if self.pk:
            return reverse("stellenangebot_edit", kwargs={"id": self.pk})
        else:
            # noinspection PyTypeChecker
            return f"{reverse('stellenangebot_add')}?{urlencode(_as_dict(self))}"

    def has_user_data(self):
        """Return whether a user has added additional data to this instance."""
        local_user_data_fields = ["notizen"]
        for local_field_name in local_user_data_fields:
            field = self._meta.get_field(local_field_name)
            value = field.value_from_object(self)
            if value not in field.empty_values and value != field.default:
                return True

        related_names = ["urls", "kontakte"]
        for related_name in related_names:
            if getattr(self, related_name).exists():
                return True

        return False


class StellenangebotURLs(models.Model):
    url = models.URLField()
    angebot = models.ForeignKey("jobby.Stellenangebot", on_delete=models.CASCADE, related_name="urls")

    class Meta:
        verbose_name = "URL"
        verbose_name_plural = "URLs"


class StellenangebotKontakt(models.Model):
    class TypChoices(models.TextChoices):
        EMAIL = "E-Mail"
        TELEFON = "Telefon"
        ANSCHRIFT = "Anschrift"

    kontakt_typ = models.CharField(max_length=CHARFIELD_MAX, choices=TypChoices, verbose_name="Art")
    kontakt_daten = models.CharField(max_length=CHARFIELD_MAX, verbose_name="Daten")
    angebot = models.ForeignKey("jobby.Stellenangebot", on_delete=models.CASCADE, related_name="kontakte")


class StellenangebotFiles(models.Model):

    description = models.CharField(max_length=CHARFIELD_MAX, verbose_name="Beschreibung", blank=True)
    file = models.FileField(verbose_name="Datei", upload_to="uploads/")
    angebot = models.ForeignKey("jobby.Stellenangebot", on_delete=models.CASCADE, related_name="files")

    class Meta:
        verbose_name = "Bewerbungsunterlagen"
        verbose_name_plural = "Bewerbungsunterlagen"


class Watchlist(models.Model):
    name = models.CharField(max_length=CHARFIELD_MAX, default="default")  # TODO: make unique?

    def on_watchlist(self, stellenangebot):
        return self.items.filter(stellenangebot=stellenangebot).exists()

    def add_watchlist_item(self, stellenangebot):
        if self.on_watchlist(stellenangebot):
            return False
        self.items.create(stellenangebot=stellenangebot)
        return True

    def remove_watchlist_item(self, stellenangebot):
        """
        Remove the given Stellenangebot instance from the watchlist.

        If the Stellenangebot does not have extra data added by the user,
        delete the Stellenangebot instance.
        """
        WatchlistItem.objects.filter(watchlist=self, stellenangebot=stellenangebot).delete()
        if not stellenangebot.has_user_data():
            stellenangebot.delete()

    def get_stellenangebote(self):
        return Stellenangebot.objects.filter(id__in=self.items.values_list("stellenangebot_id", flat=True))

    class Meta:
        verbose_name = "Merkliste"
        verbose_name_plural = "Merklisten"

    def __str__(self):  # pragma: no cover
        return self.name


class WatchlistItem(models.Model):
    watchlist = models.ForeignKey("jobby.Watchlist", on_delete=models.CASCADE, related_name="items")
    stellenangebot = models.ForeignKey("jobby.Stellenangebot", on_delete=models.CASCADE, related_name="watchlist_items")

    class Meta:
        verbose_name = "Gemerktes Stellenangebot"
        verbose_name_plural = "Gemerkte Stellenangebote"

    def __str__(self):  # pragma: no cover
        return f"{self.stellenangebot} ({self.watchlist.name})"
