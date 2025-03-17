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
    is_sides = models.BooleanField(default=False)
    is_seconds = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_category_name(cls, key):
        for category in cls.CATEGORIES:
            if category[0] == key:
                return category[1]
        raise KeyError(f"Invalid category key: {key}")


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
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="exercises")
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
    )
    order = models.PositiveIntegerField(blank=True, null=True)

    @property
    def name(self):
        return self.exercise.name

    @property
    def category(self):
        return self.exercise.category

    @property
    def is_seconds(self):
        return self.exercise.is_seconds

    @property
    def is_sides(self):
        return self.exercise.is_sides

    def __str__(self):
        description = f"{self.exercise.name} on {self.workout}"
        if self.order is not None:
            description += f" #{self.order}"
        return description


class Set(models.Model):
    exercise = models.ForeignKey(WorkoutExercise, on_delete=models.CASCADE, related_name="sets")

    set_num = models.PositiveIntegerField()
    reps_or_secs = models.PositiveIntegerField(null=True, blank=True)
    pounds = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    duration_secs = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time taken to complete the set in seconds"
    )

    class Meta:
        unique_together = ["exercise", "set_num"]

    def render(self):
        label = "secs" if self.exercise.is_seconds else "reps"
        rendering = f"{self.reps_or_secs} {label}"
        if self.exercise.is_sides:
            rendering += " ea side"
        if self.pounds:
            rendering += f" x {self.pounds} lbs"
        if self.duration_secs:
            mins = self.duration_secs // 60
            secs = self.duration_secs % 60
            rendering += f" ({mins:02d}:{secs:02d})"
        return rendering

    def __str__(self):
        label = "secs" if self.exercise.is_seconds else "reps"
        rep_str = f"{self.reps_or_secs} {label}"
        if self.exercise.is_sides:
            rep_str += " ea side"

        weight_str = ""
        if self.pounds:
            weight_str = f" at {self.pounds} lbs"
        if self.note:
            weight_str += f" {self.note}"

        return f"{rep_str}{weight_str} {self.exercise}"
