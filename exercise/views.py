from django.shortcuts import render, redirect
from django.db import transaction
from django.db.models import Max, Case, When, DateField
from exercise.models import Exercise, Workout, WorkoutExercise, WorkoutSet, Set
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


def next_workout(request):
    counts = {
        "COND": (4, 1),
        "MAIN": (2, 4),
        "ACCE": (3, 3),
        "CORE": (4, 1),
    }
    inputs = {}
    for category in counts.keys():
        exercise_count, set_count = counts[category]
        category_key = category.lower()
        inputs[category] = [
            {
                "exercise": f"{category_key}_{i}",
                "sets": [
                    {
                        "reps": f"{category_key}_{i}_reps_{j}",
                        "lbs": f"{category_key}_{i}_lbs_{j}",
                    }
                    for j in range(set_count)
                ],
            }
            for i in range(exercise_count)
        ]

    workout, _ = Workout.objects.get_or_create(completed=False)
    if request.method == "POST":
        order = 0
        with transaction.atomic():
            for category in counts.keys():
                for input in inputs[category]:
                    order += 1
                    exercise_pk = request.POST.get(input["exercise"], None)
                    if exercise_pk:
                        exercise = WorkoutExercise.objects.create(
                            workout=workout,
                            exercise_id=exercise_pk,
                            order=order,
                        )
                        for set in input["sets"]:
                            reps = request.POST.get(set["reps"], None)
                            if reps:
                                lbs = request.POST.get(set["lbs"], None)
                                planned_set = Set.objects.create(
                                    reps=reps,
                                    pounds=lbs,
                                )
                                WorkoutSet.objects.create(
                                    exercise=exercise,
                                    planned=planned_set,
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
