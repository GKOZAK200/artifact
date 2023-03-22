from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests

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

def search_media(request):
    if request.method == 'POST':
        # Get search query from the search bar
        query = request.POST.get('search')

        # Make request to APIs to search for media
        #response = requests.get('https://api.example.com/media', params={'q': query})

        # Parse the response and get the media information
        #media = response.json().get('results')

        # Render the results
        media = ""
        return render(request, 'search_results.html', {'media': media})

    # If the request method is GET, render the template
    return render(request, 'search.html')