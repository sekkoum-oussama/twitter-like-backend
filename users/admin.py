from django.contrib import admin
from .models import Profile
from tweets.models import Tweet


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["email", "is_staff", "is_superuser"]