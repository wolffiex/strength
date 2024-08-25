from django.urls import path
from django.urls import include

from exercise.views import index

urlpatterns = [
    path('', index, name="index")
]
