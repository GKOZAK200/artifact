from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    return render(request, 'homepage.html', {'user': request.user})

@login_required
def login_view(request):
    return redirect('home')

def login_view(request):
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('')
            else:
                form.add_error(None, 'Invalid username or password')
        else:
            form = AuthenticationForm()

    return render(request, 'login.html', {'form': form })

def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful")
            return redirect('home')
        messages.error(request, "Unsuccessful registration, invalid information")
    form = NewUserForm()
    return render (request=request, template_name='register.html', context={"register_form": form })
