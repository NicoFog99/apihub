# test_demo.py
# Pruebas del modo demo: con MODO_DEMO=True se bloquean el registro y los cambios
# en la cuenta compartida, pero el resto de usuarios y funciones siguen igual.
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from users.models import PerfilUsuario


@pytest.fixture(autouse=True)
def limpiar_throttling():
    # El throttling guarda los contadores en la caché; se vacía para que unos tests no limiten a otros
    from django.core.cache import cache
    cache.clear()

@pytest.fixture
def modo_demo(settings):
    settings.MODO_DEMO = True
    settings.DEMO_USUARIO = 'demo'
    settings.DEMO_PASSWORD = 'Demo-12345'
    return settings

@pytest.fixture
def cliente_demo(client, modo_demo, db):
    call_command('crear_demo')
    client.login(username='demo', password='Demo-12345')
    return client


def test_registro_bloqueado_en_modo_demo(client, modo_demo, db):
    res = client.post('/api/users/register/',
                      {'username': 'nuevo', 'email': 'nuevo@test.com', 'password': 'pass12345'},
                      content_type='application/json')
    assert res.status_code == 403
    assert not User.objects.filter(username='nuevo').exists()

@pytest.mark.parametrize('metodo, url, datos', [
    ('post',   '/api/users/cambiar-username/', {'username': 'otro'}),
    ('post',   '/api/users/cambiar-email/',    {'email': 'otro@test.com'}),
    ('post',   '/api/users/cambiar-password/', {'password_actual': 'Demo-12345', 'password_nuevo': 'nueva123'}),
    ('delete', '/api/users/eliminar-cuenta/',  {'password': 'Demo-12345'}),
])
def test_cuenta_demo_no_se_puede_modificar(cliente_demo, metodo, url, datos):
    res = getattr(cliente_demo, metodo)(url, datos, content_type='application/json')
    assert res.status_code == 403
    assert 'cuenta demo' in res.json()['error']
    # La cuenta sigue igual: mismo nombre y misma contraseña
    demo = User.objects.get(username='demo')
    assert demo.check_password('Demo-12345')

def test_otro_usuario_si_puede_cambiar_su_cuenta(client, modo_demo, db):
    User.objects.create_user(username='otro', password='pass12345', is_active=True)
    client.login(username='otro', password='pass12345')
    res = client.post('/api/users/cambiar-username/', {'username': 'otro2'}, content_type='application/json')
    assert res.status_code == 200

def test_cuenta_demo_si_puede_usar_favoritos_y_login(cliente_demo):
    assert cliente_demo.get('/api/users/me/').json()['username'] == 'demo'

def test_crear_demo_es_repetible(modo_demo, db):
    call_command('crear_demo')
    call_command('crear_demo')  # la segunda vez actualiza, no duplica
    assert User.objects.filter(username='demo').count() == 1
    assert PerfilUsuario.objects.get(usuario__username='demo').verificado

def test_pagina_incluye_config_demo(client, modo_demo, db):
    html = client.get('/').content.decode()
    assert 'id="demo-config"' in html and '"activo": true' in html

def test_sin_modo_demo_no_se_publica_la_password(client, db, settings):
    settings.MODO_DEMO = False
    settings.DEMO_PASSWORD = 'secreta'
    html = client.get('/').content.decode()
    assert 'secreta' not in html