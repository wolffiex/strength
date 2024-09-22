import json
from django.shortcuts import render, redirect
from django.db.models import Max, Case, When, DateField, F
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
    if request.method == 'POST':
        selected_exercises = json.loads(request.POST.get('selected_exercises', '[]'))
        return next_workout(request, selected_exercises)

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
            .order_by(F("latest_date").asc(nulls_first=True))
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
    "COND": 2,
    "MAIN": 4,
    "ACCE": 3,
    "CORE": 2,
}


def next_workout(request, exercise_pks):
    qset = Exercise.objects.in_bulk(exercise_pks)
    exercises = [qset[int(pk)] for pk in exercise_pks]
    supersets = []
    for category, category_name in Exercise.CATEGORIES:
        set_count = SUPERSETS[category]
        filtered_exercises = [exercise for exercise in exercises if exercise.category == category]
        superset = {
            "name": category_name,
            "count": set_count,
            "exercises": filtered_exercises
        }
        supersets.append(superset)
    return render(request, "new_workout.html", {"supersets": supersets})

def superset(request):
    return render(request, "superset.html", {"supersets": {}})
