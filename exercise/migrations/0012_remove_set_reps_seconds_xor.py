# Generated by Django 5.1 on 2024-09-21 23:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0011_remove_set_pounds_resistance_constraint"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="set",
            name="reps_seconds_xor",
        ),
    ]
