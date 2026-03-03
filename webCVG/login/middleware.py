import time
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
from .models import UsuarioSesion

class SessionIdleTimeout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity', current_time)

            # Tiempo máximo de inactividad (segundos)
            max_idle = getattr(settings, 'SESSION_IDLE_TIMEOUT', 600)

            if current_time - last_activity > max_idle:
                logout(request)

            request.session['last_activity'] = current_time

        response = self.get_response(request)
        return response
    
class UnaSesionPorUsuarioMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            session_key = request.session.session_key

            try:
                registro = UsuarioSesion.objects.get(user=request.user)

                # Si la sesión es diferente -> cerrar y avisar
                if registro.session_key != session_key:
                    logout(request)
                    messages.warning(
                        request,
                        "Tu sesión fue iniciada en otro navegador o dispositivo."
                    )

            except UsuarioSesion.DoesNotExist:
                UsuarioSesion.objects.create(
                    user=request.user,
                    session_key=session_key
                )

        response = self.get_response(request)
        return response