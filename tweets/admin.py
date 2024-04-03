from django.contrib import admin

from .models import Tweet, Media


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ("author", "type","date")
    list_filter = ("type","date")
    search_fields = ("author__username",)
    ordering = ("type", "-author")

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    pass

