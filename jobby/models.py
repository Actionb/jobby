from django.db import models

CHARFIELD_MAX = 256


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
    eintrittsdatum = models.DateField(blank=True, null=True, verbose_name="Eintrittsdatum")
    veroeffentlicht = models.DateField(blank=True, null=True, verbose_name="Veröffentlicht am")

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
