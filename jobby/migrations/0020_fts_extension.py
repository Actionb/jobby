# Generated by Django 5.0.6 on 2024-06-24 14:00
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobby", "0019_alter_suchemodel_size"),
    ]

    operations = [TrigramExtension()]
