# Generated by Django 5.1 on 2024-09-21 23:23

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0010_remove_set_pounds_resistance_or_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="set",
            name="pounds_resistance_constraint",
        ),
    ]
