import json
from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Max, Case, When, DateField, F
from exercise.models import Exercise, Workout, Set, WorkoutExercise


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


def save_workout(selected_exercises):
    # Get or create the incomplete workout
    workout, _ = Workout.objects.get_or_create(completed=False)
    # Assert that the workout has no associated sets
    assert not Set.objects.filter(
        exercise__workout=workout
    ).exists(), "Workout already has associated sets"

    # Add new WorkoutExercises based on the selected exercises
    with transaction.atomic():
        # Remove existing WorkoutExercises for the workout
        workout.exercises.all().delete()

        for order, exercise_pk in enumerate(selected_exercises, start=1):
            exercise = Exercise.objects.get(pk=exercise_pk)
            WorkoutExercise.objects.create(
                workout=workout, exercise=exercise, order=order
            )


def load_next_selected():
    workout = Workout.objects.filter(completed=False).get()
    return list(
        workout.exercises.order_by("order").values_list("exercise__id", flat=True)
    )


def next_workout(request):
    if request.method == "POST":
        save_workout(json.loads(request.POST["selected_exercises"]))
        return redirect("next_workout")

    selection = request.GET.get("selected_exercises", None)
    exercise_pks = json.loads(selection) if selection else load_next_selected()

    assert exercise_pks
    qset = Exercise.objects.in_bulk(exercise_pks)

    supersets = []
    selected_exercises = []
    for category, category_name in Exercise.CATEGORIES:
        set_count = SUPERSETS[category]
        filtered_exercises = []
        for pk in exercise_pks:
            exercise = qset[int(pk)]
            if exercise.category == category:
                filtered_exercises.append((len(selected_exercises), exercise))
                selected_exercises.append(exercise.pk)
        superset = {
            "name": category_name,
            "count": set_count,
            "exercises": filtered_exercises,
        }
        supersets.append(superset)
    return render(
        request,
        "new_workout.html",
        {
            "supersets": supersets,
            "selected_exercises": json.dumps(selected_exercises),
        },
    )


def exercise_set(request, set_num, exercise_num):
    exercises = load_next_selected()
    exercise = Exercise.objects.get(pk=exercises[exercise_num])
    incomplete_workout = Workout.objects.get(completed=False)
    workout_exercise = WorkoutExercise.objects.get(
        workout=incomplete_workout, exercise=exercise
    )
    today_sets = map(lambda s: s.render(), Set.objects.filter(exercise=workout_exercise))

    try:
        last_workout = Workout.objects.filter(
            completed=True,
            exercises__exercise=exercise
        ).latest('date')
        workout_exercise = WorkoutExercise.objects.get(workout=last_workout, exercise=exercise)
        last_sets = map(lambda s: s.render(), Set.objects.filter(exercise=workout_exercise))
    except Workout.DoesNotExist:
        last_sets = []

    return render(
        request,
        "set.html",
        {"exercise": exercise, "set_num": set_num, "today_sets": today_sets, "last_sets": last_sets},
    )
