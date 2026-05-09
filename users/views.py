from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
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

        # Enlace de verificación
# Enlace de verificación
        # Enlace de verificación
        token = str(perfil.token_verificacion)
        #Arreglo para railway, variable anterior: enlace = f"http://localhost:8000/verificar/{token}/"
        enlace = f"{request.scheme}://{request.get_host()}/verificar/{token}/"

        # Enviar email (sale por terminal en desarrollo), futura solucion con SendGrid o similar
        send_mail(
            subject='Verifica tu cuenta en API Hub',
            message=f'Hola {user.username}! Verifica tu cuenta aqui: {enlace}',
            from_email='apihub@demo.com',
            recipient_list=[user.email or 'sin-email@demo.com'],
            fail_silently=False,
        )

        return Response({
            'mensaje': 'Cuenta creada. Revisa tu email para verificarla.'
        }, status=201)
    return Response(serializer.errors, status=400)

from django.shortcuts import render, redirect

@api_view(['GET'])
@permission_classes([AllowAny])
def verificar_email(request, token):
    try:
        perfil = PerfilUsuario.objects.get(token_verificacion=token)
        if perfil.verificado:
            mensaje = 'Esta cuenta ya estaba verificada.'
            exito   = True
        else:
            perfil.verificado = True
            perfil.save()
            perfil.usuario.is_active = True
            perfil.usuario.save()
            mensaje = '✅ Cuenta verificada correctamente. Ya puedes iniciar sesión.'
            exito   = True
    except PerfilUsuario.DoesNotExist:
        mensaje = 'Token inválido o expirado.'
        exito   = False

    return render(request, 'verificacion.html', {'mensaje': mensaje, 'exito': exito})

@api_view(['POST'])
@permission_classes([AllowAny])
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
def user_logout(request):
    logout(request)
    return Response({'mensaje': 'Sesión cerrada.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({'username': request.user.username, 'email': request.user.email})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favoritos_list(request):
    favs = Favorito.objects.filter(usuario=request.user).select_related('api')
    return Response(FavoritoSerializer(favs, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorito_toggle(request, api_id):
    fav, created = Favorito.objects.get_or_create(usuario=request.user, api_id=api_id)
    if not created:
        fav.delete()
        return Response({'favorito': False})
    return Response({'favorito': True}, status=201)

# Valoración de APIs

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def valorar_api(request, api_id):
    puntuacion = request.data.get('puntuacion')
    if not puntuacion or not (1 <= int(puntuacion) <= 5):
        return Response({'error': 'Puntuación debe ser entre 1 y 5.'}, status=400)
    api = Api.objects.get(pk=api_id)
    valoracion, created = Valoracion.objects.update_or_create(
        usuario=request.user,
        api=api,
        defaults={'puntuacion': int(puntuacion)}
    )
    return Response({'mensaje': 'Valoración guardada.', 'puntuacion': valoracion.puntuacion})
# Obtener la valoración del usuario para una API específica
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_valoracion(request, api_id):
    try:
        v = Valoracion.objects.get(usuario=request.user, api_id=api_id)
        return Response({'puntuacion': v.puntuacion})
    except Valoracion.DoesNotExist:
        return Response({'puntuacion': None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    password_actual = request.data.get('password_actual')
    password_nuevo  = request.data.get('password_nuevo')
    if not request.user.check_password(password_actual):
        return Response({'error': 'La contraseña actual no es correcta.'}, status=400)
    if len(password_nuevo) < 8:
        return Response({'error': 'La nueva contraseña debe tener al menos 8 caracteres.'}, status=400)
    request.user.set_password(password_nuevo)
    request.user.save()
    # Mantener la sesión activa tras el cambio
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    return Response({'mensaje': 'Contraseña actualizada correctamente.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_email(request):
    email = request.data.get('email', '').strip()
    if not email or '@' not in email:
        return Response({'error': 'Email no válido.'}, status=400)
    if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
        return Response({'error': 'Este email ya está en uso.'}, status=400)
    request.user.email = email
    request.user.save()
    return Response({'mensaje': 'Email actualizado correctamente.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_username(request):
    username = request.data.get('username', '').strip()
    if not username:
        return Response({'error': 'El nombre de usuario no puede estar vacío.'}, status=400)
    if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
        return Response({'error': 'Este nombre de usuario ya está en uso.'}, status=400)
    request.user.username = username
    request.user.save()
    return Response({'mensaje': 'Nombre de usuario actualizado correctamente.'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_cuenta(request):
    password = request.data.get('password')
    if not request.user.check_password(password):
        return Response({'error': 'Contraseña incorrecta.'}, status=400)
    request.user.delete()
    return Response({'mensaje': 'Cuenta eliminada correctamente.'})