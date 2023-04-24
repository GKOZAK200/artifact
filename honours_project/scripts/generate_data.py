import random
import string
from django.contrib.auth.models import User
from media_app.models import Media, Ratings

# Define the number of users and the number of ratings per user
N = 300  # Number of users
K = 8   # Number of ratings per user

# Generate N users
for i in range(N):
    # Generate a random username and password for each user
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))

    # Create a new user with the generated username and password
    user = User.objects.create_user(username=username, password=password)

    # Generate a list of K random media objects
    media_list = Media.objects.order_by('?')[:K]

    # For each media object, generate a random rating between 1 and 10 and associate it with the user
    for media in media_list:
        score = random.randint(1, 10)
        Ratings.objects.create(user=user, media=media, score=score)
