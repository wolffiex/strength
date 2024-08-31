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
    note = models.TextField(blank=True)


class Set(models.Model):
    reps = models.PositiveIntegerField(null=True, blank=True)
    seconds = models.PositiveIntegerField(null=True, blank=True)
    pounds = models.PositiveIntegerField(null=True, blank=True)
    resistance = models.CharField(blank=True, max_length=255)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(reps__isnull=False, seconds__isnull=True)
                    | models.Q(reps__isnull=True, seconds__isnull=False)
                ),
                name="reps_seconds_xor",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(pounds__isnull=False, resistance__exact="")
                    | models.Q(pounds__isnull=True, resistance__gt="")
                ),
                name="pounds_resistance_xor",
            ),
        ]


class Workout(models.Model):
    date = models.DateField()
    completed = models.BooleanField(default=False)


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workout", "exercise"], name="unique_workout_exercise"
            ),
            models.UniqueConstraint(
                fields=["workout", "order"],
                name="unique_workout_order",
                condition=models.Q(order__isnull=False),
            ),
        ]


class WorkoutSet(models.Model):
    exercise = models.ForeignKey(
        WorkoutExercise, on_delete=models.CASCADE, related_name="sets"
    )
    planned = models.ForeignKey(
        Set,
        on_delete=models.CASCADE,
        related_name="planned",
    )
    actual = models.ForeignKey(
        Set,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="actual",
    )
    note = models.TextField(blank=True)
