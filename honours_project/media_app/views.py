from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
from decouple import config
import json

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

        # Make request to IGDB API to search for games
        igdb_response = requests.post('https://api.igdb.com/v4/games', headers={
            'Client-ID': config("IGDB_CLIENT_ID"),
            'Authorization': f'Bearer {config("IGDB_ACCESS_TOKEN")}'
        }, data=f'search "{query}"; fields name, cover.url, summary; limit 5;')
        print(igdb_response.json())
        igdb_data = igdb_response.json()
        games = igdb_data

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
        albums = musicbrainz_data.get('release-groups', [])[:5] if musicbrainz_response.ok and musicbrainz_data.get('release-groups') else []

        media = {'movies': movies, 'tv_shows': tv_shows, 'games': games, 'books': books, 'albums': albums}

        # Render the results
        return render(request, 'search_results.html', {'media': media})
        
    # If the request method is GET, render the template
    return render(request, 'search.html')


def add_to_list(request):
    if request.method == 'POST':
        title = request.POST['title']
        # Add movie to list
        return redirect('my_list')