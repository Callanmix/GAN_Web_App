from django.contrib import admin


# Register your models here.
from .models import MLAlgorithm, Profile

admin.site.register([MLAlgorithm, Profile])