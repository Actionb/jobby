# Generated by Django 5.0.6 on 2024-06-14 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobby", "0013_stellenangebot_externe_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stellenangebot",
            name="modified",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Zuletzt verändert am"),
        ),
    ]
