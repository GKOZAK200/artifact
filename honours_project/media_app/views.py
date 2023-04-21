from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from .forms import NewUserForm
from media_app.models import Media, MediaList, Ratings, User
from surprise import KNNBasic, Dataset, Reader, SVD
from surprise.model_selection import cross_validate, LeaveOneOut
from collections import defaultdict
import heapq
from operator import itemgetter
import pandas as pd
import requests
from decouple import config
from urllib.parse import urljoin

# Image that shows up when no cover is provided
PLACEHOLDER_IMG_URL = 'https://via.placeholder.com/300x444.png?text=No+Image+Available'

# Create your views here.

# Home view
def home(request):
    if request.user.is_authenticated:
        media_in_medialist = Media.objects.filter(medialist__user=request.user)
        unrated_media = Media.objects.filter(
            id__in=Subquery(media_in_medialist.values('id')),).exclude(ratings__user=request.user)
        context = {
            'user': request.user,
            'unrated_media': unrated_media,
        }
        return render(request, 'homepage.html', context)
    else:
        return render(request, 'homepage.html', {'user': request.user})

# Ratings view
def ratings(request):
    return render(request, 'ratings.html', {'user': request.user})

# Login view that redirects to home if user is already logged in
@login_required
def login_view(request):
    return redirect('home')

# Login view
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

# Register view
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

# Log out view
def logout_view(request):
    logout(request)
    return redirect('home')

# Searches for media across the 4 APIs and renders the results
def search_media(request):
    if request.method == 'POST':
        # Get search query from the search bar
        query = request.POST.get('search')

        # Make request to OMDb API to search for movies
        movie_response = requests.get('http://www.omdbapi.com/', params={'s': query, 'type': 'movie', 'apikey': config("OMDB_KEY")})
        movie_data = movie_response.json()
        movies = movie_data.get('Search', [])
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

        # Make a request to MusicBrainz API to search for albums
        musicbrainz_response = requests.get('https://musicbrainz.org/ws/2/release-group/', params={'query': query, 'type': 'album', 'limit': 5}, headers={'Accept': 'application/json'})
        musicbrainz_data = musicbrainz_response.json()
        
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

# Add item to user's media list
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

# Removes item from user's media list and rating from ratings database
def remove_from_list(request, medialist_id, media_id):
    medialist = get_object_or_404(MediaList, id=medialist_id, user=request.user)
    media = get_object_or_404(Media, id=media_id)
    rating = Ratings.objects.filter(user=request.user, media=media).first()  # Get rating
    if rating:
        rating.delete()  # Delete rating if it exists
    medialist.media.remove(media)
    return redirect('home')

# Adds rating to Ratings database
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

# User based collaborative filtering algorithm that recommends N media items
def recommend_media(request):
    # Set current user (user the algorithm is running recommendations for)
    currentUser = request.user.id

    # Check if user has rated anything
    user_ratings = Ratings.objects.filter(user_id=currentUser)
    if not user_ratings:
        return HttpResponse("Seems that you haven't rated anything yet. Please rate some media items first and try again later.")

    # Set k (How many other users are compared to current user)
    k = 10

    # Set N (How many items will be recommended to the user)
    N = 5

    # Create Surprise Dataset object
    reader = Reader(rating_scale=(0, 10))
    ratings = Ratings.objects.all().values('user_id', 'media_id', 'score')
    df = pd.DataFrame.from_records(ratings)
    surprise_data = Dataset.load_from_df(df, reader)
    trainset = surprise_data.build_full_trainset()


    # Set parameters for k nearest neighbor (KNN) algorithm
    # Cosine similarity method is used (computes the cosine similarity between all pairs of users)
    # User based is set to true because this is a user based algorithm instead of an item based one
    sim_options = {'name': 'cosine', 'user_based': True}

    # Create model
    model = KNNBasic(k=k, sim_options=sim_options)

    # Fit model to training data
    model.fit(trainset)

    # Create similarity matrix between users
    similarityMatrix = model.compute_similarities()

    # Convert user raw ID to inner ID
    testUserInnerID = trainset.to_inner_uid(currentUser)

    # Creates list of similarity value per user compared to current user
    similarityRow = similarityMatrix[testUserInnerID]

    # Create list of similar users
    similarUsers = []
    for innerID, score in enumerate(similarityRow):
        if (innerID != testUserInnerID):
            similarUsers.append((innerID, score))

    # Create list of K most similar users
    kNeighbours = heapq.nlargest(k, similarUsers, key=lambda t: t[1])

    # Get the media they rated, and add up ratings for each item, weighted by user similarity
    candidates = defaultdict(float)
    for similarUser in kNeighbours:
        innerID = similarUser[0]
        userSimilarityScore = similarUser[1]
        theirRatings = trainset.ur[innerID]
        for rating in theirRatings:
            candidates[rating[0]] += (rating[1] / 5.0) * userSimilarityScore

    # Build a dictionary of media the user has already consumed
    consumed = {}
    for itemID, rating in trainset.ur[testUserInnerID]:
        consumed[itemID] = 1

    # Get top N rated items from similar users:
    pos = 0
    recommendations = []
    for itemID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
        if not itemID in consumed:
            mediaID = trainset.to_raw_iid(itemID)
            media = Media.objects.get(id=int(mediaID))
            media_name = media.title
            media_poster = media.poster_url
            media_description = media.description
            recommendations.append({'media_id': mediaID, 'media_name': media_name, 'score': ratingSum, 'media_poster': media_poster, 'media_description': media_description})
            pos += 1
            if (pos > N-1):
                break

    # Run leave-one-out cross validation and print results
    loo = LeaveOneOut()
    cv_results = cross_validate(model, surprise_data, measures=['RMSE', 'MAE'], cv=loo, verbose=True)
    print(cv_results)

    return render(request, 'recommendations.html', {'media': recommendations})