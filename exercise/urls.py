from django.urls import path
from django.urls import include

from exercise.views import index, next_workout, superset

urlpatterns = [
    path("", index, name="index"),
    path("next", next_workout, name="next_workout"),
    path("superset/", superset, name="superset"),
]
