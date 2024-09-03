from django.urls import path
from django.urls import include

from exercise.views import index, new_workout

urlpatterns = [
    path("", index, name="index"),
    path("new", new_workout, name="new_workout"),
]
