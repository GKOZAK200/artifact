from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
from decouple import config
import json
from urllib.parse import urljoin
from media_app.models import Media, MediaList, Ratings, User
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from surprise import KNNBasic
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import train_test_split
from collections import defaultdict
import heapq
from operator import itemgetter
import pandas as pd

PLACEHOLDER_IMG_URL = 'https://via.placeholder.com/300x444.png?text=No+Image+Available'

# Create your views here.

def home(request):
    return render(request, 'homepage.html', {'user': request.user})

@login_required
def login_view(request):
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        messages.error(request, "Unsuccessful registration, invalid information")
    form = NewUserForm()
    return render (request=request, template_name='register.html', context={"register_form": form })

def logout_view(request):
    logout(request)
    return redirect('home')

import requests
from decouple import config

def search_media(request):
    if request.method == 'POST':
        # Get search query from the search bar
        query = request.POST.get('search')

        # Make request to OMDb API to search for movies
        movie_response = requests.get('http://www.omdbapi.com/', params={'s': query, 'type': 'movie', 'apikey': config("OMDB_KEY")})
        movie_data = movie_response.json()
        movies = movie_data.get('Search', [])
        print (movies)
        for movie in movies:
            # Make a request for each individual movie to get the plot
            movie_id = movie['imdbID']
            movie_detail_response = requests.get('http://www.omdbapi.com/', params={'i': movie_id, 'apikey': config("OMDB_KEY")})
            movie_detail_data = movie_detail_response.json()
            movie['Plot'] = movie_detail_data.get('Plot', '')
            # Replace the cover URL with the placeholder image URL if not available
            if movie['Poster'] == 'N/A':
                movie['Poster'] = PLACEHOLDER_IMG_URL

        # Make request to OMDb API to search for TV shows
        tv_response = requests.get('http://www.omdbapi.com/', params={'s': query, 'type': 'series', 'apikey': config("OMDB_KEY")})
        tv_data = tv_response.json()
        tv_shows = tv_data.get('Search', [])
        for tv_show in tv_shows:
            # Make a request for each individual TV show to get the plot
            tv_show_id = tv_show['imdbID']
            tv_show_detail_response = requests.get('http://www.omdbapi.com/', params={'i': tv_show_id, 'apikey': config("OMDB_KEY")})
            tv_show_detail_data = tv_show_detail_response.json()
            tv_show['Plot'] = tv_show_detail_data.get('Plot', '')
            if 'N/A' in tv_show['Poster']:
                tv_show['Poster'] = PLACEHOLDER_IMG_URL

        # Make request to IGDB API to search for games
        igdb_response = requests.post('https://api.igdb.com/v4/games', headers={
            'Client-ID': config("IGDB_CLIENT_ID"),
            'Authorization': f'Bearer {config("IGDB_ACCESS_TOKEN")}'
        }, data=f'search "{query}"; fields name, cover.url, summary; limit 5;')
        print(igdb_response.json())
        igdb_data = igdb_response.json()
        games = igdb_data

    # Replace the cover URL with the placeholder image URL if not available
        for game in games:
            if 'cover' in game and game['cover']:
                if 'url' in game['cover'] and game['cover']['url']:
                    game['cover_url'] = game['cover']['url']
                else:
                    game['cover_url'] = PLACEHOLDER_IMG_URL
            else:
                game['cover_url'] = PLACEHOLDER_IMG_URL

        # Make a request to Google Books for books
        google_books_api_key = config("GOOGLE_BOOKS_KEY")
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?key={google_books_api_key}&q={query}&maxResults=5"
        google_books_response = requests.get(google_books_url)
        google_books_data = google_books_response.json()
        print (google_books_data)

        # Make a request to MusicBrainz API to search for albums
        musicbrainz_response = requests.get('https://musicbrainz.org/ws/2/release-group/', params={'query': query, 'type': 'album', 'limit': 5}, headers={'Accept': 'application/json'})
        print(musicbrainz_response)
        musicbrainz_data = musicbrainz_response.json()
        print(musicbrainz_data)
        
        # Parse the responses and get the media information
        movies = movie_data.get('Search', [])[:5] if movie_response.ok and movie_data.get('Response') == 'True' else []
        tv_shows = tv_data.get('Search', [])[:5] if tv_response.ok and tv_data.get('Response') == 'True' else []
        games = igdb_response.json() if igdb_response.ok else []
        books = google_books_data.get('items', []) if google_books_response.ok and google_books_data.get('totalItems', 0) > 0 else []
        albums = []
        if musicbrainz_response.ok and musicbrainz_data.get('release-groups'):
            for release_group in musicbrainz_data['release-groups'][:5]:
                album = {}
                album['title'] = release_group['title']
                album['artist'] = release_group['artist-credit'][0]['artist']['name']
                album['cover_url'] = urljoin('https://coverartarchive.org/release-group/', release_group['id']) + '/front-500'
                albums.append(album)


        media = {'movies': movies, 'tv_shows': tv_shows, 'games': games, 'books': books, 'albums': albums}

        # Render the results
        return render(request, 'search_results.html', {'media': media})
        
    # If the request method is GET, render the template
    return render(request, 'search.html')


def add_to_list(request):
    if request.method == 'POST':
        title = request.POST['title']
        poster_url = request.POST['poster_url']
        description = request.POST.get('description')
        media_type = request.POST.get('media_type')

        # Check if media with same title and type already exists
        existing_media = Media.objects.filter(title=title, media_type=media_type).first()

        if existing_media:
            # If media already exists, add it to the user's media list
            media_list, created = MediaList.objects.get_or_create(user=request.user)
            media_list.media.add(existing_media)
        else:
            # If media does not exist, create it and add it to the user's media list
            new_media = Media(title=title, poster_url=poster_url, description=description, media_type=media_type)
            new_media.save()
            media_list, created = MediaList.objects.get_or_create(user=request.user)
            media_list.media.add(new_media)

        return redirect('home')

def remove_from_list(request, medialist_id, media_id):
    medialist = get_object_or_404(MediaList, id=medialist_id, user=request.user)
    media = get_object_or_404(Media, id=media_id)
    medialist.media.remove(media)
    return redirect('home')

def add_rating(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    
    user_id = request.POST.get('user_id')
    media_id = request.POST.get('media_id')
    score = request.POST.get('score')
    
    user = get_object_or_404(User, id=user_id)
    media = get_object_or_404(Media, id=media_id)
    
    # Try to get an existing rating for this user and media
    rating = Ratings.objects.filter(user=user, media=media).first()
    if rating:
        # Update the existing rating
        rating.score = score
        rating.save()
        return redirect('home')
    
    # Create a new rating
    rating = Ratings.objects.create(user=user, media=media, score=score)
    return redirect('home')

@login_required
def recommend_media(request):
    # Get the current user
    currentUser = request.user.id
    print(f"Current user ID: {currentUser}")
    
    # Get the ratings data
    ratings = Ratings.objects.filter(user=currentUser)
    print(f"Ratings QuerySet: {ratings}")
    
    # Load the data into a Surprise dataset
    reader = Reader(rating_scale=(0, 10))
    print("Reader created")
    
    # Convert QuerySet to DataFrame
    ratings_df = pd.DataFrame.from_records(ratings.values_list('user', 'media', 'score'), columns=['user', 'item', 'rating'])
    print(f"Ratings DataFrame: {ratings_df}")
    print(ratings_df.dtypes)
    
    # Load data to Dataset object
    data = Dataset.load_from_df(ratings_df, reader)
    print("Data loaded into Dataset object")
    print(data)
    
    # Put data into training and test sets
    trainSet = data.build_full_trainset()
    for ui, ii, r in trainSet.all_ratings():
        print(ui, ii, r)

    
    # Set parameters for k nearest neighbor (KNN) algorithm
    sim_options = {'name': 'cosine', 'user_based': True}
    
    # Create model
    model = KNNBasic(sim_options=sim_options)
    print("KNN model created")
    
    # Fit model to training data
    model.fit(trainSet)
    print("Model fitted to training data")
    
    # Create similarity matrix between users
    similarityMatrix = model.compute_similarities()
    print("Similarity matrix created")
    
    # Get top N similar users to current user
    testUserInnerID = trainSet.to_inner_uid(str(currentUser))
    print(f"Current user inner ID: {testUserInnerID}")
    similarityRow = similarityMatrix[testUserInnerID]
    print(f"Similarity row for current user: {similarityRow}")
    similarUsers = []
    for innerID, score in enumerate(similarityRow):
        if (innerID != testUserInnerID):
            similarUsers.append((innerID, score))
    kNeighbours = heapq.nlargest(1, similarUsers, key=lambda t: t[1])
    print(f"Top 10 similar users: {kNeighbours}")
    
    # Get the media that the user has already seen
    watched = set(ratings.values_list('media', flat=True))
    print(f"Media watched by current user: {watched}")
    
    # Get the ratings of the similar users for each media that the current user has not seen
    candidates = defaultdict(float)
    for similarUser in kNeighbours:
        innerID = similarUser[0]
        userSimilarityScore = similarUser[1]
        theirRatings = trainSet.ur[innerID]
        for rating in theirRatings:
            if rating[0] not in watched:
                candidates[rating[0]] += (rating[1] / 5.0) * userSimilarityScore
    
    # Get the top 5 rated media
    top5Media = []
    for mediaID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True)[:1]:
        media = Media.objects.get(id=mediaID)
        media.avg_rating = Ratings.objects.filter(media=media).aggregate(Avg('score'))['score__avg']
        top5Media.append(media)
    
    # Render the template with the recommended media
    return render(request, 'recommendations.html', {'media': top5Media})
