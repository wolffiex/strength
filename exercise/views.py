from django.shortcuts import render, redirect
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


def new_workout(request):
    print("EW;lkjf")
    if request.method == "POST":
        workout = Workout.objects.create(date=date.today())
        for i in range(1, 5):
            exercise_id = request.POST.get(f"cond_exercise_{i}")
            exercise = Exercise.objects.get(id=exercise_id)
            workout_exercise = WorkoutExercise.objects.create(
                workout=workout, exercise=exercise, order=i
            )
            for j in range(1, 3):
                reps = request.POST.get(f"cond_set_{i}_{j}_reps")
                pounds = request.POST.get(f"cond_set_{i}_{j}_pounds")
                planned_set = Set.objects.create(reps=reps, pounds=pounds)
                WorkoutSet.objects.create(
                    exercise=workout_exercise, planned=planned_set
                )
        return redirect("workout_detail", pk=workout.pk)
    else:
        counts = {
            "COND": (4, 2),
            "MAIN": (2, 4),
            "ACCE": (3, 3),
            "CORE": (4, 2),
        }
        supersets = [
            {
                "category": category,
                "name": category_name,
                "exercises": Exercise.objects.filter(category=category),
                "num_exercises": counts[category][0],
                "num_sets": counts[category][1],
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
