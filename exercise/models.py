from django.db import models


class Exercise(models.Model):
    CATEGORIES = (
        ("COND", "Conditioning"),
        ("MAIN", "Main Lift"),
        ("ACCE", "Accessory Lift"),
        ("CORE", "Core"),
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=4, choices=CATEGORIES)
    note = models.TextField


class Set(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    reps = models.PositiveIntegerField()
    pounds = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=100)


class Workout(models.Model):
    date = models.DateField()


class ActualSet(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name="actual_sets"
    )
    completed = models.BooleanField(null=False, blank=False)
    planned = models.ForeignKey(
        Set, on_delete=models.CASCADE, related_name="planned_sets"
    )
    actual = models.ForeignKey(
        Set, on_delete=models.CASCADE, null=True, blank=True, related_name="actual_sets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["planned", "actual"],
                condition=models.Q(planned__exercise=models.F("actual__exercise")),
                name="matching_exercise_constraint",
            )
        ]
