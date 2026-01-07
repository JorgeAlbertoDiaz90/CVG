from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import Http404

User = get_user_model()   # ← IMPORTANTE

def home(request):
    return render(request, 'home.html')

def signup(request):

    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1']
                )
                user.save()
                login(request, user)
                return redirect('menu')
            except IntegrityError:
                return render(request, 'signin.html', {
                    'form': UserCreationForm,
                    'error': 'El usuario ya existe.'
                })
        return render(request, 'signin.html', {
            'form': UserCreationForm,
            'error': 'Lo siento, las contraseñas no coinciden.'
        })


def signout(request):
    logout(request)
    return redirect('home')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm,
                'error': 'El usuario o la contraseña son incorrectas.'
            })
        else:
            login(request, user)
            return redirect('menu')


@login_required
def menu(request):
    return render(request, 'menu.html')
