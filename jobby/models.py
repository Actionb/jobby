from django.db import models
from django.forms import model_to_dict
from django.urls import reverse
from django.utils.http import urlencode

CHARFIELD_MAX = 256


def _update_stellenangebot(existing, other):
    """Update the existing Stellenangebot object with data from the other."""
    if existing.refnr != other.refnr:
        # Not the same Stellenangebot.
        return False

    update_dict = {}
    for field in existing._meta.get_fields():
        if not field.concrete or not hasattr(other, field.name) or field.primary_key:  # pragma: no cover
            continue
        # TODO: do not overwrite values on existing with default values on other
        #  (ignore default values on other?)
        # TODO: how to handle empty values on other?
        if getattr(existing, field.name) != getattr(other, field.name):
            update_dict[field.name] = getattr(other, field.name)
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
    berufsfeld = models.CharField(max_length=CHARFIELD_MAX, blank=True, null=True)
    arbeitgeber = models.CharField(max_length=CHARFIELD_MAX, blank=True, null=True)
    veroeffentlichtseit = models.PositiveSmallIntegerField(verbose_name="Veröffentlicht seit", blank=True, null=True)
    zeitarbeit = models.BooleanField(blank=True, null=True)
    # TODO: null=True on IntegerField a problem?
    angebotsart = models.IntegerField(choices=AngebotsChoices, blank=True, null=True)
    befristung = models.IntegerField(choices=BefristungChoices, blank=True, null=True)
    arbeitszeit = models.CharField(max_length=3, choices=ArbeitszeitChoices, blank=True, null=True)
    behinderung = models.BooleanField(default=False)
    corona = models.BooleanField(default=False)  # TODO: might be out-dated
    umfeld = models.PositiveSmallIntegerField(blank=True, null=True)

    # Query specific options
    page = models.PositiveSmallIntegerField(blank=True, null=True)
    size = models.PositiveSmallIntegerField(blank=True, null=True)

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
        NICHT_GEPLANT = "---"

    titel = models.CharField(max_length=CHARFIELD_MAX, verbose_name="Titel")
    refnr = models.CharField(max_length=CHARFIELD_MAX, verbose_name="Referenz-Nummer")
    beruf = models.CharField(max_length=CHARFIELD_MAX, blank=True, null=True, verbose_name="Beruf")
    # TODO: arbeitgeber could be a relation?
    arbeitgeber = models.CharField(max_length=CHARFIELD_MAX, blank=True, null=True, verbose_name="Arbeitgeber")
    arbeitsort = models.CharField(max_length=CHARFIELD_MAX, blank=True, null=True)
    eintrittsdatum = models.DateField(blank=True, null=True, verbose_name="Eintrittsdatum")
    veroeffentlicht = models.DateField(blank=True, null=True, verbose_name="Veröffentlicht am")
    modified = models.DateTimeField(blank=True, null=True)
    # TODO: add externe_url field (in addition to StellenangebotURLs)?
    # TODO: add full text from the corresponding arbeitsagentur page

    bewerbungsstatus = models.CharField(
        max_length=CHARFIELD_MAX,
        choices=BewerbungChoices,
        default=BewerbungChoices.NICHT_GEPLANT,
        verbose_name="Bewerbungsstatus",
    )
    notizen = models.TextField(verbose_name="Notizen")

    class Meta:
        verbose_name = "Stellenangebot"
        verbose_name_plural = "Stellenangebote"

    def __str__(self):
        return self.titel

    def as_search_result_form(self):
        from jobby.forms import SearchResultForm

        return SearchResultForm(instance=self)

    def as_url(self):
        if self.pk:
            return reverse("stellenangebot_edit", kwargs={"id": self.pk})
        else:
            # noinspection PyTypeChecker
            return f"{reverse('stellenangebot_add')}?{urlencode(_as_dict(self))}"


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
        WatchlistItem.objects.filter(watchlist=self, stellenangebot=stellenangebot).delete()

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
