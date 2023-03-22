from django.db import models

# Create your models here.

class Media(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=50)
    release_year = models.IntegerField(blank=True)
    poster_url = models.URLField(blank=True)
