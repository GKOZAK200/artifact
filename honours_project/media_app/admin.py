from django.contrib import admin
from .models import Media, MediaList, Ratings

# Register your models here.

class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'media_type', 'poster_url')
    list_filter = ('title', 'media_type')
    search_fields = ('title', 'media_type')

admin.site.register(Media, MediaAdmin)

class MediaListAdmin(admin.ModelAdmin):
    list_display = ('user',)

admin.site.register(MediaList, MediaListAdmin)

class RatingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'media', 'score')
    list_filter = ('user', 'media')
    search_fields = ('user__username', 'media__title')
    autocomplete_fields = ['user', 'media']

admin.site.register(Ratings, RatingsAdmin)