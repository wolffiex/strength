from django.urls import path

from exercise.views import index, next_workout, exercise_set

urlpatterns = [
    path("", index, name="index"),
    path("next/", next_workout, name="next_workout"),
    path("exercise/<int:exercise_num>/set/<int:set_num>/", exercise_set, name="set"),
]
