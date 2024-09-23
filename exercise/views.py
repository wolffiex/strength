import json
from django.shortcuts import render, redirect
from django.urls import reverse
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


SUPERSETS = {  # Category: sets
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


def next_workout(request):
    workout = Workout.objects.filter(completed=False).get()
    if request.method == "POST":
        print(request.POST["selected_exercises"])
        save_workout(json.loads(request.POST["selected_exercises"]))
        return redirect(reverse("next_workout"))

    selection = request.GET.get("selected_exercises", None)
    exercises = None
    if selection:
        selection_list = json.loads(selection)
        objects = Exercise.objects.in_bulk(selection_list)
        exercises = [objects[pk] for pk in selection_list]
    else:
        workout_exercises = workout.exercises.order_by("order").select_related("exercise")
        exercises = [exer.exercise for exer in workout_exercises]


    print(selection)
    print(exercises)

    supersets = []
    selected_exercises = []
    for category, category_name in Exercise.CATEGORIES:
        set_count = SUPERSETS[category]
        filtered_exercises = []
        for exercise in exercises:
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


def gen_workout_steps(workout):
    exercises = list(Workout.objects.get(pk=workout).exercises.order_by("order"))
    for category, set_count in SUPERSETS.items():
        yield ("workout", (workout, category))
        for set_num in range(0, set_count):
            for exercise in filter(
                lambda wo: wo.exercise.category == category, exercises
            ):
                yield (
                    "workout_set",
                    (set_num + 1, exercise.pk),
                )


def workout_step(_, workout, step):
    view_name, args = list(gen_workout_steps(workout))[step]
    return redirect(view_name, *args, permanent=False)


def lookup_step(request_path, workout):
    n = 0
    for view_name, args in gen_workout_steps(workout):
        print(args)
        path = reverse(view_name, args=args)
        if path == request_path:
            return n
        n += 1
    raise ValueError(f"Step not found for {request_path}")


def workout_set(request, set_num, exercise):
    if request.method == "POST":
        new_set = Set(exercise=exercise, set_num=set_num)
        new_set.save()

    today_sets = map(lambda s: s.render(), Set.objects.filter(exercise=exercise))
    wo = WorkoutExercise.objects.get(pk=exercise)
    step = lookup_step(request.path, wo.workout_id)

    try:
        last_workout = Workout.objects.filter(
            completed=True, exercises__exercise=exercise
        ).latest("date")
        last_exercise = WorkoutExercise.objects.get(
            workout=last_workout, exercise=exercise.exercise
        )
        last_sets = map(
            lambda s: s.render(), Set.objects.filter(exercise=last_exercise)
        )
    except Workout.DoesNotExist:
        last_sets = []

    prev_url = (
        None if step == 0 else reverse("workout_step", args=(wo.workout_id, step - 1))
    )
    next_url = (
        None if step == 0 else reverse("workout_step", args=(wo.workout_id, step + 1))
    )
    return render(
        request,
        "set.html",
        {
            "exercise": wo,
            "set_num": set_num,
            "today_sets": today_sets,
            "last_sets": last_sets,
            "prev_url": prev_url,
            "next_url": next_url,
        },
    )


def workout(request, cateworkout, category):
    pass
