# Generated by Django 5.1 on 2024-09-27 18:55

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0015_alter_set_note"),
    ]

    operations = [
        migrations.RenameField(
            model_name="set",
            old_name="reps",
            new_name="reps_or_secs",
        ),
    ]
