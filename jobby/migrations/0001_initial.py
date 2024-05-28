# Generated by Django 5.0.6 on 2024-05-27 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SucheModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("was", models.CharField(max_length=100)),
                ("wo", models.CharField(max_length=100)),
                ("berufsfeld", models.CharField(blank=True, max_length=100, null=True)),
                ("arbeitgeber", models.CharField(blank=True, max_length=100, null=True)),
                ("published_since", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("zeitarbeit", models.BooleanField(blank=True, null=True)),
                (
                    "angebot_art",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Arbeit"),
                            (2, "Selbständigkeit"),
                            (4, "Ausbildung/Duales Studium"),
                            (34, "Praktikum/Trainee"),
                        ],
                        null=True,
                    ),
                ),
                (
                    "befristung",
                    models.IntegerField(blank=True, choices=[(1, "befristet"), (2, "unbefristet")], null=True),
                ),
                (
                    "arbeitszeit",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("vz", "Vollzeit"),
                            ("tz", "Teilzeit"),
                            ("snw", "Schicht/Nachtarbeit/Wochenende"),
                            ("ho", "Heim-/Telearbeit"),
                            ("mj", "Minijob"),
                        ],
                        max_length=3,
                        null=True,
                    ),
                ),
                ("behinderung", models.BooleanField(default=False)),
                ("corona", models.BooleanField(default=False)),
                ("umfeld", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("page", models.PositiveSmallIntegerField()),
                ("size", models.PositiveSmallIntegerField()),
            ],
        ),
    ]