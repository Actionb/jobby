# Generated by Django 5.0.6 on 2024-06-06 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobby", "0005_alter_watchlist_options_alter_watchlistitem_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stellenangebot",
            name="notizen",
            field=models.TextField(blank=True, null=True, verbose_name="Notizen"),
        ),
    ]
