from django.contrib import admin


# Register your models here.
from .models import MLAlgorithm, Profile, Uploaded_Images

admin.site.register([MLAlgorithm, Profile, Uploaded_Images])