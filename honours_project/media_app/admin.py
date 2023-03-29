from django.contrib import admin
from .models import Media, MediaList

# Register your models here.

class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'media_type', 'poster_url')
    list_filter = ('title', 'media_type')
    search_fields = ('title', 'media_type')

admin.site.register(Media, MediaAdmin)

class MediaListAdmin(admin.ModelAdmin):
    list_display = ('user',)

admin.site.register(MediaList, MediaListAdmin)