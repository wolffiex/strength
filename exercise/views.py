import json
import pytz
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.db.models import Max, Case, When, DateField, F, Prefetch
from django.http import StreamingHttpResponse
from exercise.models import Exercise, Workout, Set, WorkoutExercise


def fetch_set_and_date(exercise):
    latest_workout_exercise = (
        exercise.workoutexercise_set.filter(workout__completed=True)
        .order_by("-workout__date")
        .select_related("workout")
        .first()
    )
    if not latest_workout_exercise:
        return [], None

    set_str = ""
    if set_instance := latest_workout_exercise.sets.order_by("-set_num").first():
        set_str = set_instance.render()

    return set_str, latest_workout_exercise.workout.date


def index(_):
    workout = (
        Workout.objects.prefetch_related(
            Prefetch(
                "exercises",
                queryset=WorkoutExercise.objects.select_related(
                    "exercise"
                ).prefetch_related("sets"),
            )
        )
        .filter(completed=False)
        .first()
    )

    category = Exercise.CATEGORIES[0][0]
    if workout:
        existing_categories = (
            workout.exercises
            .filter(sets__isnull=False)
            .values_list('exercise__category', flat=True)
            .distinct())
        for cat in Exercise.CATEGORIES:
            if cat[0] not in existing_categories:
                category = cat[0]
                break
    return redirect("choose_next_category", category)


def choose_next_category(request, category: str):
    exercise_qset = Exercise.objects.filter(category=category)

    exercises = []
    for exercise in exercise_qset:
        set_str, latest_date = fetch_set_and_date(exercise)
        exercises.append(
            {"exercise": exercise, "set": set_str, "latest_date": latest_date}
        )

    # Sort exercises by latest_date
    exercises.sort(key=lambda x: (x["latest_date"] is None, x["latest_date"]))

    context = {
        "category": category,
        "category_name": Exercise.get_category_name(category),
        "exercises": exercises,
    }

    return render(request, "choose_next_category.html", context)


SUPERSETS = {  # Category: sets
    "COND": 2,
    "MAIN": 4,
    "ACCE": 3,
    "CORE": 2,
}


def save_category(category, selected_exercises):
    # Get or create the incomplete workout
    workout, _ = Workout.objects.get_or_create(completed=False)
    # Assert that the workout has no associated sets
    assert not Set.objects.filter(
        exercise__exercise__category=category, exercise__workout=workout
    ).exists(), "Workout already has associated sets"

    # Add new WorkoutExercises based on the selected exercises
    with transaction.atomic():
        # Remove existing WorkoutExercises for the workout
        workout.exercises.filter(exercise__category=category).delete()

        for order, exercise_pk in enumerate(selected_exercises, start=1):
            exercise = Exercise.objects.get(pk=exercise_pk)
            WorkoutExercise.objects.create(
                workout=workout, exercise=exercise, order=order
            )


def next_category(request, category):
    workout = Workout.objects.filter(completed=False).first()
    if request.method == "POST":
        save_category(category, json.loads(request.POST["selected_exercises"]))
        return redirect("preview_category", category)

    selection = request.GET.get("selected_exercises", None)
    exercises = None
    needs_save = bool(selection)
    if selection:
        selection_list = json.loads(selection)
        objects = Exercise.objects.in_bulk(selection_list)
        exercises = [objects[int(pk)] for pk in selection_list]
    else:
        exercises = (
            []
            if not workout
            else (
                workout.exercises.filter(exercise__category=category)
                .order_by("order")
                .select_related("exercise")
            )
        )

    selected_exercises = []
    filtered_exercises = []
    set_count = SUPERSETS[category]
    for exercise in exercises:
        filtered_exercises.append((len(selected_exercises), exercise))
        selected_exercises.append(exercise.pk)
    superset = {
        "name": Exercise.get_category_name(category),
        "count": set_count,
        "exercises": filtered_exercises,
    }
    return render(
        request,
        "new_category.html",
        {
            "workout": workout,
            "category": category,
            "superset": superset,
            "selected_exercises": json.dumps(selected_exercises),
            "needs_save": needs_save,
        },
    )


def gen_workout_steps(workout):
    exercises = list(Workout.objects.get(pk=workout).exercises.order_by("order"))
    for category, set_count in SUPERSETS.items():
        yield ("choose_next_category", (category,))
        yield ("preview_category", (category,))
        for set_num in range(0, set_count):
            for exercise in filter(
                lambda wo: wo.exercise.category == category, exercises
            ):
                yield (
                    "workout_set",
                    (set_num + 1, exercise.pk),
                )
        yield ("summarize_category", (category,))
    yield (
        "finish_workout",
        (workout,),
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
        reps_or_secs = request.POST["reps_or_secs"]
        pounds = request.POST["pounds"]
        note = request.POST["note"]
        duration_secs = request.POST["duration_secs"]
        reps_or_secs = int(reps_or_secs) if reps_or_secs else None
        pounds = int(pounds) if pounds else None
        duration_secs = int(duration_secs) if duration_secs else None
        next_url = request.POST.get("next_url", None)
        pk = request.POST.get("existing_set", None)
        new_set = Set(
            exercise=wo,
            set_num=set_num,
            reps_or_secs=reps_or_secs,
            pounds=pounds,
            pk=pk,
            note=note,
            duration_secs=duration_secs,
        )
        new_set.save()
        return redirect(next_url)

    today_sets = map(
        lambda s: s.render(),
        Set.objects.filter(exercise=wo).order_by("set_num"))
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


def summarize_category(request, category):
    workout = Workout.objects.get(completed=False)
    exercises = workout.exercises.filter(exercise__category=category).order_by("order")

    exercise_data = []
    for exercise in exercises:
        current_sets = list(map(lambda s: s.render(), exercise.sets.all().order_by('set_num')))

        last_workout = None
        last_sets = []
        try:
            last_workout = Workout.objects.filter(
                completed=True, exercises__exercise=exercise.exercise
            ).latest("date")
            last_exercise = WorkoutExercise.objects.get(
                workout=last_workout, exercise=exercise.exercise
            )
            last_sets = list(map(
                lambda s: s.render(), Set.objects.filter(exercise=last_exercise).order_by('set_num')
            ))
        except Workout.DoesNotExist:
            pass

        exercise_data.append(
            {
                "last_workout": last_workout,
                "exercise": exercise,
                "current_sets": current_sets,
                "last_sets": last_sets,
            }
        )

    category_name = dict(Exercise.CATEGORIES)[category]
    return render(
        request,
        "category_summary.html",
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
            ).prefetch_related(
                Prefetch("sets", queryset=Set.objects.order_by("set_num"))
            ).order_by("order"),
        )
    ).get(pk=workout)

    if workout.date is not None:
        # Fetch the next and previous workouts by date
        next_workout = (
            Workout.objects.filter(date__gt=workout.date).order_by("date").first()
        )
        if not next_workout:
            next_workout = Workout.objects.filter(date__isnull=True).first()

        prev_workout = (
            Workout.objects.filter(date__lt=workout.date).order_by("-date").first()
        )
    else:
        # If workout.date is empty, there's no next workout
        next_workout = None
        # Fetch the previous workout by date
        prev_workout = Workout.objects.exclude(date=None).order_by("-date").first()

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


def finish_workout(request, workout):
    workout = Workout.objects.get(pk=workout)
    # Create a timezone object for Pacific time
    pacific_tz = pytz.timezone("US/Pacific")

    # Localize the current date to Pacific time
    localized_date = timezone.now().astimezone(pacific_tz).date()

    # Set the date field of the model instance to the localized date
    workout.date = localized_date
    workout.completed = True
    workout.save()

    return redirect(reverse("workout_summary", args=(workout.pk,)))

def workouts_index(request):
    workout = Workout.objects.filter(completed=True).order_by('-date').first()
    return redirect(reverse("workout_summary", args=(workout.pk,)))


def get_exercise_summary(exercise_id):
    """Generate a workout summary showing exercise history and current progress"""
    # Get the current exercise and its category
    wo = WorkoutExercise.objects.select_related('exercise', 'workout').get(pk=exercise_id)
    category = wo.exercise.category
    
    # Get all exercises in this category for today's workout
    category_exercises = WorkoutExercise.objects.filter(
        workout=wo.workout,
        exercise__category=category
    ).select_related('exercise').order_by('order')
    
    narrative = []
    narrative.append(f"== {Exercise.get_category_name(category)} ==")
    narrative.append(f"Currently on: {wo.exercise.name}")
    narrative.append("")  # Blank line
    
    # Show history and today's progress for each exercise
    for exercise in category_exercises:
        narrative.append(f"* {exercise.exercise.name} *")

        # Get previous workouts for this exercise
        previous_sets = Set.objects.filter(
            exercise__exercise=exercise.exercise,
            exercise__workout__completed=True
        ).order_by('-exercise__workout__date')
        
        # Group by workout date
        prev_dates = {}
        for set in previous_sets:
            date = set.exercise.workout.date
            if date not in prev_dates:
                prev_dates[date] = []
            prev_dates[date].append(set)
        prev_dates = dict(sorted(list(prev_dates.items())[:2], reverse=True))  # Last 2 dates

        # Show previous attempts
        if prev_dates:
            for date, sets in prev_dates.items():
                days_ago = (timezone.now().date() - date).days
                sets_str = "; ".join(f"Set {s.set_num}: {s.render()}" for s in sorted(sets, key=lambda x: x.set_num))
                narrative.append(f"{days_ago} days ago: {sets_str}")
        else:
            narrative.append("No previous attempts")
        
        # Show today's progress
        today_sets = Set.objects.filter(exercise=exercise).order_by('set_num')
        narrative.append("Today: " + (
            "; ".join(f"Set {s.set_num}: {s.render()}" for s in today_sets)
            if today_sets else "Not started yet"
        ))
        narrative.append("")  # Blank line between exercises
    
    return narrative


def generate_coach_stream(exercise_id):
    """Generate SSE events for coach response"""
    from .coach import get_coach_response
    summary_lines = get_exercise_summary(exercise_id)
    for text in get_coach_response(summary_lines):
        yield f"data: {text}\n\n"


def coach_stream(request, exercise):
    response = StreamingHttpResponse(
        streaming_content=generate_coach_stream(exercise),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

