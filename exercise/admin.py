from django.contrib import admin
from django.apps import apps

# Register your models here.
from .models import *

app_models = apps.get_app_config("exercise").get_models()
for model in app_models:
    admin.site.register(model)
