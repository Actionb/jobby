# Generated by Django 5.0.6 on 2024-06-25 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobby", "0022_stellenangebot_api"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="stellenangeboturls",
            options={"verbose_name": "Internet-Adresse", "verbose_name_plural": "Internet-Adressen"},
        ),
        migrations.AlterField(
            model_name="stellenangebot",
            name="arbeitsort",
            field=models.CharField(blank=True, max_length=256, verbose_name="Arbeitsort"),
        ),
        migrations.AlterField(
            model_name="stellenangebotkontakt",
            name="kontakt_daten",
            field=models.CharField(max_length=256, verbose_name="Kontaktdaten"),
        ),
        migrations.AlterField(
            model_name="stellenangebotkontakt",
            name="kontakt_typ",
            field=models.CharField(
                choices=[("E-Mail", "Email"), ("Telefon", "Telefon"), ("Anschrift", "Anschrift")],
                max_length=256,
                verbose_name="Kontakt Art",
            ),
        ),
        migrations.AlterField(
            model_name="stellenangeboturls",
            name="url",
            field=models.URLField(verbose_name="URL"),
        ),
    ]
