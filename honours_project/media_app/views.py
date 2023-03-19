from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.

def home(request):
    template = loader.get_template('homepage.html')
    return HttpResponse(template.render())

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