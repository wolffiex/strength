import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import transaction
from django.db.models import Max, Case, When, DateField, F, Prefetch
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
        save_workout(json.loads(request.POST["selected_exercises"]))
        return redirect(reverse("next_workout"))

    selection = request.GET.get("selected_exercises", None)
    needs_save = bool(selection)
    exercises = None
    if selection:
        selection_list = json.loads(selection)
        objects = Exercise.objects.in_bulk(selection_list)
        exercises = [objects[int(pk)] for pk in selection_list]
    else:
        workout_exercises = workout.exercises.order_by("order").select_related(
            "exercise"
        )
        exercises = [exer.exercise for exer in workout_exercises]

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
            "workout": workout,
            "supersets": supersets,
            "selected_exercises": json.dumps(selected_exercises),
            "needs_save": needs_save,
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


def get_step_urls(request_path, workout_pk):
    step = None
    count = 0
    for view_name, args in gen_workout_steps(workout_pk):
        path = reverse(view_name, args=args)
        if path == request_path:
            step = count
        count += 1

    if step is None:
        raise ValueError(f"Step not found for {request_path}")

    def get_url(dir):
        new_step = step + dir
        if new_step >= 0 and new_step < count:
            return reverse("workout_step", args=(workout_pk, step + dir))

        return None

    return {"prev_url": get_url(-1), "next_url": get_url(1)}


def get_set(exercise, set_num):
    try:
        return Set.objects.get(exercise=exercise, set_num=set_num)
    except Set.DoesNotExist:
        return None


def workout_set(request, set_num, exercise):
    wo = WorkoutExercise.objects.get(pk=exercise)
    if request.method == "POST":
        reps = request.POST["reps"]
        pounds = request.POST["pounds"]
        reps = int(reps) if reps else None
        pounds = int(pounds) if pounds else None
        next_url = request.POST.get("next_url", None)
        pk = request.POST.get("existing_set", None)
        new_set = Set(exercise=wo, set_num=set_num, reps=reps, pounds=pounds, pk=pk)
        new_set.save()
        return redirect(next_url)

    today_sets = map(lambda s: s.render(), Set.objects.filter(exercise=wo))
    last_workout = None
    try:
        last_workout = Workout.objects.filter(
            completed=True, exercises__exercise=wo.exercise
        ).latest("date")
        last_exercise = WorkoutExercise.objects.get(
            workout=last_workout, exercise=wo.exercise
        )
        last_sets = map(
            lambda s: s.render(), Set.objects.filter(exercise=last_exercise)
        )
    except Workout.DoesNotExist:
        last_sets = []

    return render(
        request,
        "set.html",
        {
            "exercise": wo,
            "current_set": get_set(wo.pk, set_num),
            "set_num": set_num,
            "today_sets": today_sets,
            "last_sets": last_sets,
            "last_workout": last_workout,
            **get_step_urls(request.path, wo.workout_id),
        },
    )


def workout(request, workout, category):
    workout = Workout.objects.get(pk=workout)
    exercises = workout.exercises.filter(exercise__category=category).order_by("order")

    exercise_data = []
    for exercise in exercises:
        last_workout = None
        try:
            last_workout = Workout.objects.filter(
                completed=True, exercises__exercise=exercise.exercise
            ).latest("date")
            last_exercise = WorkoutExercise.objects.get(
                workout=last_workout, exercise=exercise.exercise
            )
            last_sets = map(
                lambda s: s.render(), Set.objects.filter(exercise=last_exercise)
            )
        except Workout.DoesNotExist:
            last_sets = []

        exercise_data.append(
            {
                "last_workout": last_workout,
                "exercise": exercise,
                "last_sets": list(last_sets),
            }
        )

    category_name = dict(Exercise.CATEGORIES)[category]
    return render(
        request,
        "workout.html",
        {
            "workout": workout,
            "exercises": exercise_data,
            "category": category_name,
            **get_step_urls(request.path, workout.pk),
        },
    )


def workout_summary(request, workout):
    workout = Workout.objects.prefetch_related(
        Prefetch(
            "exercises",
            queryset=WorkoutExercise.objects.select_related(
                "exercise"
            ).prefetch_related("sets"),
        )
    ).get(pk=workout)
    # Fetch the next and previous workouts by date
    next_workout = (
        Workout.objects.filter(date__gt=workout.date).order_by("date").first()
    )
    prev_workout = (
        Workout.objects.filter(date__lt=workout.date).order_by("-date").first()
    )
    supersets = []
    for category, category_name in Exercise.CATEGORIES:
        exercises = workout.exercises.filter(exercise__category=category)
        exercise_data = []
        for exercise in exercises:
            exercise_data.append(
                {
                    "name": exercise.name,
                    "sets": map(lambda s: s.render(), exercise.sets.all()),
                }
            )
        superset = {
            "name": category_name,
            "exercises": exercise_data,
        }
        supersets.append(superset)
    context = {
        "workout": workout,
        "supersets": supersets,
        "next_workout": next_workout,
        "prev_workout": prev_workout,
    }

    return render(request, "workout_summary.html", context)
