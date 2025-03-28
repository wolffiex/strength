# Generated by Django 5.1 on 2024-09-09 03:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0008_workoutexercise_alter_set_exercise"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="set",
            name="pounds_resistance_xor",
        ),
        migrations.AddConstraint(
            model_name="set",
            constraint=models.CheckConstraint(
                condition=models.Q(("pounds__isnull", False), ("resistance__gt", ""), _connector="OR"),
                name="pounds_resistance_or",
            ),
        ),
    ]
