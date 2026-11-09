#views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Favorito, PerfilUsuario, Valoracion
from .serializers import RegisterSerializer, FavoritoSerializer
from apis.models import Api

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.is_active = False  # no puede login hasta verificar
        user.save()

        perfil = PerfilUsuario.objects.create(usuario=user)
        enviar_email_verificacion(request, perfil)

        return Response({
            'mensaje': f'Cuenta creada. Revisa tu email para verificarla (el enlace caduca en {settings.VERIFICACION_HORAS} horas).'
        }, status=201)
    return Response(serializer.errors, status=400)


def enviar_email_verificacion(request, perfil):
    # Construye el enlace con el dominio actual y lo envía por email (en desarrollo sale por la terminal)
    enlace = f"{request.scheme}://{request.get_host()}/verificar/{perfil.token_verificacion}/"
    send_mail(
        subject='Verifica tu cuenta en API Hub',
        message=(f'Hola {perfil.usuario.username}! Verifica tu cuenta aquí: {enlace}\n'
                 f'El enlace caduca en {settings.VERIFICACION_HORAS} horas.'),
        from_email='apihub@demo.com',
        recipient_list=[perfil.usuario.email or 'sin-email@demo.com'],
        fail_silently=False,
    )

from django.shortcuts import render, redirect

@api_view(['GET'])
@permission_classes([AllowAny])
# Vista para manejar la verificación de email a través del token enviado por correo (pasado por consola para demo).
# El enlace caduca a las VERIFICACION_HORAS y solo se puede usar una vez.
def verificar_email(request, token):
    perfil = PerfilUsuario.objects.filter(token_verificacion=token).select_related('usuario').first() if token else None

    if perfil is None:
        mensaje = 'El enlace no es válido o ya se ha utilizado.'
        exito   = False
    elif perfil.token_caducado():
        # En vez de dejar al usuario bloqueado, se le envía un enlace nuevo
        perfil.nuevo_token()
        perfil.save()
        enviar_email_verificacion(request, perfil)
        mensaje = 'El enlace había caducado. Te hemos enviado uno nuevo a tu email.'
        exito   = False
    else:
        perfil.verificado         = True
        perfil.token_verificacion = ''  # un solo uso
        perfil.save()
        perfil.usuario.is_active = True
        perfil.usuario.save()
        mensaje = '✅ Cuenta verificada correctamente. Ya puedes iniciar sesión.'
        exito   = True

    return render(request, 'verificacion.html', {'mensaje': mensaje, 'exito': exito})

@api_view(['POST'])
@permission_classes([AllowAny])
# Vista para manejar el inicio de sesión, verificando que el usuario esté activo (es decir, que haya verificado su email).
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user:
        if not user.is_active:
            return Response({'error': 'Debes verificar tu email antes de iniciar sesión.'}, status=400)
        login(request, user)
        return Response({'mensaje': f'Bienvenido, {user.username}!'})
    return Response({'error': 'Credenciales incorrectas.'}, status=400)

@api_view(['POST'])
# Vista para manejar el cierre de sesión del usuario.
def user_logout(request):
    logout(request)
    return Response({'mensaje': 'Sesión cerrada.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
# Vista para obtener los datos del usuario autenticado, como su nombre de usuario y email.
def me(request):
    return Response({'username': request.user.username, 'email': request.user.email})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
# Vista para obtener la lista de APIs favoritas del usuario autenticado, utilizando el serializador FavoritoSerializer para formatear la respuesta.
def favoritos_list(request):
    favs = Favorito.objects.filter(usuario=request.user).select_related('api')
    return Response(FavoritoSerializer(favs, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorito_toggle(request, api_id):
    api = get_object_or_404(Api, pk=api_id, activa=True)
    fav, created = Favorito.objects.get_or_create(usuario=request.user, api=api)
    if not created:
        fav.delete()
        return Response({'favorito': False})
    return Response({'favorito': True}, status=201)

# Valoración de APIs

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# Vista para manejar la valoración de una API por parte del usuario autenticado, permitiendo crear o actualizar la puntuación.
def valorar_api(request, api_id):
    try:
        puntuacion = int(request.data.get('puntuacion'))
    except (TypeError, ValueError):
        puntuacion = 0
    if not (1 <= puntuacion <= 5):
        return Response({'error': 'Puntuación debe ser entre 1 y 5.'}, status=400)
    api = get_object_or_404(Api, pk=api_id, activa=True)
    valoracion, created = Valoracion.objects.update_or_create(
        usuario=request.user,
        api=api,
        defaults={'puntuacion': int(puntuacion)}
    )
    return Response({'mensaje': 'Valoración guardada.', 'puntuacion': valoracion.puntuacion})
# Obtener la valoración del usuario para una API específica
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# Vista para obtener la valoración que el usuario autenticado ha dado a una API específica, 
# devolviendo la puntuación o null si no ha valorado.
def mi_valoracion(request, api_id):
    try:
        v = Valoracion.objects.get(usuario=request.user, api_id=api_id)
        return Response({'puntuacion': v.puntuacion})
    except Valoracion.DoesNotExist:
        return Response({'puntuacion': None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
# Vista para manejar el cambio de contraseña del usuario autenticado, 
# verificando la contraseña actual y validando la nueva contraseña antes de actualizarla.
def cambiar_password(request):
    password_actual = request.data.get('password_actual')
    password_nuevo  = request.data.get('password_nuevo')
    if not request.user.check_password(password_actual):
        return Response({'error': 'La contraseña actual no es correcta.'}, status=400)
    if not password_nuevo or len(password_nuevo) < 6:
        return Response({'error': 'La nueva contraseña debe tener al menos 6 caracteres.'}, status=400)
    request.user.set_password(password_nuevo)
    request.user.save()
    # Mantener la sesión activa tras el cambio
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    return Response({'mensaje': 'Contraseña actualizada correctamente.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# Vista para manejar el cambio de email del usuario autenticado, 
# validando el nuevo email y asegurándose de que no esté en uso por otro usuario antes de actualizarlo.
def cambiar_email(request):
    email = (request.data.get('email') or '').strip()
    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'Email no válido.'}, status=400)
    if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
        return Response({'error': 'Este email ya está en uso.'}, status=400)
    request.user.email = email
    request.user.save()
    return Response({'mensaje': 'Email actualizado correctamente.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# Vista para manejar el cambio de nombre de usuario del usuario autenticado,
def cambiar_username(request):
    username = (request.data.get('username') or '').strip()
    if not username:
        return Response({'error': 'El nombre de usuario no puede estar vacío.'}, status=400)
    # Mismas reglas que en el registro: letras, números y @ . + - _ (máx. 150 caracteres)
    try:
        UnicodeUsernameValidator()(username)
    except ValidationError:
        return Response({'error': 'El nombre de usuario solo puede tener letras, números y @ . + - _'}, status=400)
    if len(username) > 150:
        return Response({'error': 'El nombre de usuario es demasiado largo.'}, status=400)
    if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
        return Response({'error': 'Este nombre de usuario ya está en uso.'}, status=400)
    request.user.username = username
    request.user.save()
    return Response({'mensaje': 'Nombre de usuario actualizado correctamente.'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
# Vista para manejar la eliminación de la cuenta del usuario autenticado, 
# verificando la contraseña antes de proceder con la eliminación.
def eliminar_cuenta(request):
    password = request.data.get('password')
    if not request.user.check_password(password):
        return Response({'error': 'Contraseña incorrecta.'}, status=400)
    request.user.delete()
    return Response({'mensaje': 'Cuenta eliminada correctamente.'})