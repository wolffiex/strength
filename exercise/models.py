from django.db import models
from django.db.models import Q


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

    def __str__(self):
        return self.name


class Workout(models.Model):
    date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.date.strftime("%m/%d/%Y") if self.date else "next"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["completed"],
                condition=models.Q(completed=False),
                name="unique_uncompleted_workout",
            ),
            models.CheckConstraint(
                check=Q(completed=False) | Q(date__isnull=False),
                name="completed_workout_date_not_null",
            ),
        ]


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
    )
    order = models.PositiveIntegerField(blank=True, null=True)

    @property
    def name(self):
        return self.exercise.name

    def __str__(self):
        description = f"{self.exercise.name} on {self.workout}"
        if self.order is not None:
            description += f" #{self.order}"
        return description


class Set(models.Model):
    exercise = models.ForeignKey(
        WorkoutExercise, on_delete=models.CASCADE, related_name="sets"
    )

    set_num = models.PositiveIntegerField()
    reps = models.PositiveIntegerField(null=True, blank=True)
    seconds = models.PositiveIntegerField(null=True, blank=True)
    pounds = models.PositiveIntegerField(null=True, blank=True)
    resistance = models.CharField(blank=True, max_length=255)

    def render(self):
        rendering = f"{self.reps} reps"
        if self.pounds:
            rendering += f" x {self.pounds } lbs"
        return rendering

    def __str__(self):
        rep_str = ""
        if self.reps:
            rep_str = f"{self.reps} reps"
        if self.seconds:
            rep_str += f"{self.seconds} seconds"

        weight_str = ""
        if self.pounds:
            weight_str = f" at {self.pounds} lbs"
        if self.resistance:
            weight_str += f" {self.resistance}"

        return f"{rep_str}{weight_str} {self.exercise}"
