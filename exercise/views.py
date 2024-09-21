from django.shortcuts import render
from django.db import transaction
from django.db.models import Max, Case, When, DateField, Prefetch
from exercise.models import Exercise, Workout, Set, WorkoutExercise
from datetime import date


def fetch_sets(exercise):
    latest_workout_exercise = (
        exercise.workoutexercise_set.filter(workout__completed=True)
        .order_by("-workout__date")
        .first()
    )
    if not latest_workout_exercise:
        return []

    sets = []
    for set_instance in latest_workout_exercise.sets.all():
        rep_str = (
            f"{set_instance.reps} reps"
            if set_instance.reps
            else f"{set_instance.seconds} seconds"
        )

        weight_str = (
            f" at {set_instance.pounds} lbs"
            if set_instance.pounds
            else f" {set_instance.resistance}"
            if set_instance.resistance
            else ""
        )

    sets.append(f"{rep_str}{weight_str}")

    return sets


def index(request):
    exercises_by_category = {}

    for category, category_name in Exercise.CATEGORIES:
        exercises = (
            Exercise.objects.filter(category=category)
            .annotate(
                latest_date=Case(
                    When(
                        workoutexercise__workout__completed=True,
                        then=Max("workoutexercise__workout__date"),
                    ),
                    default=None,
                    output_field=DateField(),
                )
            )
            .order_by("-latest_date")
        )

        exercises_by_category[category_name] = [
            {"exercise": exercise, "sets": fetch_sets(exercise)}
            for exercise in exercises
        ]

    context = {
        "exercises_by_category": exercises_by_category,
    }
    return render(request, "index.html", context, status=201)


SUPERSETS = {  # Category: (exercises, sets)
    "COND": (4, 2),
    "MAIN": (2, 4),
    "ACCE": (3, 3),
    "CORE": (4, 2),
}


def next_workout(request):
    inputs = {
        category: [f"{category.lower()}_{i}" for i in range(exercise_count)]
        for category, (exercise_count, _) in SUPERSETS.items()
    }

    workout, _ = Workout.objects.get_or_create(completed=False)
    print(workout)
    print(workout.id)
    if request.method == "POST":
        order = 0
        with transaction.atomic():
            WorkoutExercise.objects.filter(workout=workout).delete()
            for category in SUPERSETS.keys():
                for input in inputs[category]:
                    order += 1
                    exercise_id = request.POST.get(input, None)
                    if exercise_id:
                        WorkoutExercise.objects.create(
                            workout=workout,
                            exercise_id=exercise_id,
                            order=order,
                        )

    supersets = []
    for category, category_name in Exercise.CATEGORIES:
        exercise_count, _ = SUPERSETS[category]
        exercises = Exercise.objects.filter(category=category)
        workout_exercises = list(
            WorkoutExercise.objects.filter(workout=workout, exercise__category=category)
            .values_list("exercise_id", flat=True)
            .order_by("order")
        )
        workout_exercises += [""] * exercise_count
        superset = {
            "name": category_name,
            "exercises": exercises,
            "workout_exercises": [
                {"name": name, "value": value}
                for name, value in zip(inputs[category], workout_exercises)
            ],
        }
        supersets.append(superset)
    return render(request, "new_workout.html", {"supersets": supersets})
