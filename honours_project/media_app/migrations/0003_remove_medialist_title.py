# Generated by Django 4.1.7 on 2023-03-22 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("media_app", "0002_medialist"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="medialist",
            name="title",
        ),
    ]