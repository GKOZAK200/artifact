from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Media(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=50)
    poster_url = models.URLField(blank=True)

    def __str__(self):
        return self.title

class MediaList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media = models.ManyToManyField('Media')

class ReviewList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media = models.ManyToManyField('Media')
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
