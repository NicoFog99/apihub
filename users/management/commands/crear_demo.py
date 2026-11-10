# crear_demo.py
# Crea (o actualiza) la cuenta demo compartida del portfolio con los datos del .env.
# Uso: python manage.py crear_demo
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from users.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Crea o actualiza la cuenta demo (DEMO_USUARIO / DEMO_PASSWORD)'

    def handle(self, *args, **options):
        if not settings.DEMO_PASSWORD:
            raise CommandError('Falta DEMO_PASSWORD en el .env o en las variables de entorno.')

        usuario, creado = User.objects.get_or_create(username=settings.DEMO_USUARIO)
        usuario.set_password(settings.DEMO_PASSWORD)
        usuario.is_active = True  # sin verificación por email
        usuario.save()

        # La cuenta demo se marca como verificada, igual que si hubiera pulsado el enlace del correo
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
        perfil.verificado = True
        perfil.token_verificacion = ''
        perfil.save()

        accion = 'creada' if creado else 'actualizada'
        self.stdout.write(self.style.SUCCESS(f'Cuenta demo "{usuario.username}" {accion}.'))