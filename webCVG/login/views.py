from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import UsuarioSesion
from django.contrib.sessions.models import Session
from django.utils import timezone

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
    if request.user.is_authenticated:
        UsuarioSesion.objects.filter(user=request.user).delete()

    logout(request)
    return redirect('home')


def signin(request):

    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })

    # POST
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

    # Verificar si ya existe una sesión registrada
    try:
        registro = UsuarioSesion.objects.get(user=user)

        # Validar si la sesión aún existe y no está expirada
        sesion_activa = Session.objects.filter(
            session_key=registro.session_key,
            expire_date__gt=timezone.now()
        ).first()

        if sesion_activa:
            sesion_activa.delete()

        registro.delete()

    except UsuarioSesion.DoesNotExist:
        pass

    # Iniciar nueva sesión
    login(request, user)

    # Guardar nueva sesión
    UsuarioSesion.objects.update_or_create(
        user=user,
        defaults={'session_key': request.session.session_key}
    )

    return redirect('menu')


@login_required
def menu(request):
    return render(request, 'menu.html')
