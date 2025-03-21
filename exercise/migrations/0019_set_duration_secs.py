# Generated by Django 5.1 on 2025-02-23 02:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0018_alter_set_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="set",
            name="duration_secs",
            field=models.PositiveIntegerField(
                blank=True, help_text="Time taken to complete the set in seconds", null=True
            ),
        ),
    ]
