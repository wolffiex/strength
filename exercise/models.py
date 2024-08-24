from django.db import models
from django.core.exceptions import ValidationError


class Exercise(models.Model):
    CATEGORIES = (
        ("COND", "Conditioning"),
        ("MAIN", "Main Lift"),
        ("ACCE", "Accessory Lift"),
        ("CORE", "Core"),
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=4, choices=CATEGORIES)
    note = models.TextField()


class Set(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    reps = models.PositiveIntegerField()
    pounds = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=100)


class Workout(models.Model):
    date = models.DateField()


class WorkoutSet(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name="workout_sets"
    )
    completed = models.BooleanField(null=False, blank=False)
    planned = models.ForeignKey(
        Set, on_delete=models.CASCADE, related_name="planned_sets"
    )
    actual = models.ForeignKey(
        Set, on_delete=models.CASCADE, null=True, blank=True, related_name="actual_sets"
    )

    def clean(self):
        if self.actual is not None and self.planned.exercise != self.actual.exercise:
            raise ValidationError(
                "Planned exercise and actual exercise must match if actual exercise is provided."
            )
