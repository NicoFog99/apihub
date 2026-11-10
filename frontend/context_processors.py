# context_processors.py
# Pasa a todas las plantillas la configuración del modo demo, para que el frontend sepa
# si tiene que ocultar el registro y mostrar los datos de la cuenta demo.
from django.conf import settings


def modo_demo(request):
    if not settings.MODO_DEMO:
        return {'demo_config': {'activo': False}}
    return {'demo_config': {
        'activo': True,
        'usuario': settings.DEMO_USUARIO,
        'password': settings.DEMO_PASSWORD,
    }}