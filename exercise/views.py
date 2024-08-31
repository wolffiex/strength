from django.shortcuts import render
from django.db.models import Max, Case, When, DateField
from exercise.models import Exercise


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
