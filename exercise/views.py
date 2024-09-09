from django.shortcuts import render
from django.db import transaction
from django.db.models import Max, Case, When, DateField
from exercise.models import Exercise, Workout, Set, WorkoutExercise
from datetime import date


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
        exercises_by_category[category_name] = exercises

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
    if request.method == "POST":
        order = 0
        with transaction.atomic():
            WorkoutExercise.objects.filter(workout=workout).delete()
            for category in SUPERSETS.keys():
                for input in inputs[category]:
                    order += 1
                    exercise_pk = request.POST.get(input, None)
                    if exercise_pk:
                        WorkoutExercise.objects.create(
                            workout=workout,
                            exercise_id=exercise_pk,
                            order=order,
                        )

    return render_form(request, inputs)


def render_form(request, inputs):
    supersets = [
        {
            "name": category_name,
            "exercises": Exercise.objects.filter(category=category),
            "inputs": inputs[category],
        }
        for category, category_name in Exercise.CATEGORIES
    ]
    # print("Exercise.CATEGORIES:", Exercise.CATEGORIES)
    # print("context:")
    # for category, superset in context.items():
    #     print(f"Category: {category}")
    #     print(f"  Name: {superset['name']}")
    #     print(f"  Exercises: {superset['exercises']}")
    #     print(f"  Num Exercises: {superset['num_exercises']}")
    #     print(f"  Num Sets: {superset['num_sets']}")
    return render(request, "new_workout.html", {"supersets": supersets})
