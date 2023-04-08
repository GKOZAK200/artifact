# Script that generates 100 users with 10 random ratings

import random
from django.contrib.auth.models import User
from media_app.models import Media, Ratings

# Generate 100 users
for i in range(100):
    # Create a user
    username = f"user{i+1}"
    password = "password123"  # You may want to generate a random password for each user
    user = User.objects.create_user(username=username, password=password)

    # Generate a list of 10 random media objects
    media_list = Media.objects.order_by('?')[:10]

    # For each media object, generate a random rating between 1 and 10 and associate it with the user
    for media in media_list:
        score = random.randint(1, 10)
        Ratings.objects.create(user=user, media=media, score=score)
