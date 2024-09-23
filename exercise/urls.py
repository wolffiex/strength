from django.urls import path

from exercise.views import index, next_workout, workout_step, workout_set, workout

urlpatterns = [
    path("", index, name="index"),
    path("next/", next_workout, name="next_workout"),
    path("workout/<int:workout>/<str:category>/", workout, name="workout"),
    path("workout-step/<int:workout>/<int:step>/", workout_step, name="workout_step"),
    path(
        "workout-set/<int:set_num>/wo/<int:exercise>/", workout_set, name="workout_set"
    ),
]
