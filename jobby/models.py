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
