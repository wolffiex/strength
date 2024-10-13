from django.urls import path

from exercise.views import (
    index,
    choose_next_category,
    next_category,
    begin_category,
    workout_step,
    workout_set,
    prev_category,
    workout_summary,
    finish_workout,
)

urlpatterns = [
    path("", index, name="index"),
    path("choose-next/<str:category>", choose_next_category, name="choose_next_category"),
    path("next/<str:category>", next_category, name="next_category"),
    path("begin/<str:category>/", begin_category, name="begin_category"),
    path("prev/<str:category>/", prev_category, name="prev_category"),
    path("workout-step/<int:workout>/<int:step>/", workout_step, name="workout_step"),
    path(
        "workout-set/<int:set_num>/wo/<int:exercise>/", workout_set, name="workout_set"
    ),
    path("workouts/<int:workout>/", workout_summary, name="workout_summary"),
    path("finish-workout/<int:workout>/", finish_workout, name="finish_workout"),
]
