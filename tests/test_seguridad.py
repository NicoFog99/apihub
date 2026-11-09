# test_seguridad.py
# Pruebas de las mejoras de seguridad: proxy limitado al catálogo, verificación de email
# con caducidad y un solo uso, y validación de datos en las vistas de usuario.
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone

from apis.models import Api
from users.models import PerfilUsuario


# ── Fixtures ──────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def limpiar_throttling():
    # El throttling guarda los contadores en la caché; se vacía para que unos tests no limiten a otros
    from django.core.cache import cache
    cache.clear()

@pytest.fixture
def api(db):
    return Api.objects.create(
        nombre='PokeAPI', descripcion='Pokémon', url_base='https://pokeapi.co/api/v2',
        auth_tipo='none', activa=True,
    )

@pytest.fixture
def usuario(db):
    return User.objects.create_user(username='testuser', password='testpass123', is_active=True)

@pytest.fixture
def cliente_auth(client, usuario):
    client.login(username='testuser', password='testpass123')
    return client

def respuesta_falsa(status=200, json_data=None, redirect_a=None):
    # Simula la respuesta de requests.get sin salir a internet
    r = MagicMock()
    r.status_code = status
    r.is_redirect = redirect_a is not None
    r.headers = {'Location': redirect_a} if redirect_a else {}
    r.json.return_value = json_data if json_data is not None else {}
    return r

def proxy(client, url, params=None):
    return client.post('/api/proxy/', {'url': url, 'params': params or {}}, content_type='application/json')


# ── Tests: Proxy ──────────────────────────────────────────────
@pytest.mark.django_db
@patch('apis.views.requests.get')
def test_proxy_acepta_url_del_catalogo_y_suma_visita(mock_get, client, api):
    mock_get.return_value = respuesta_falsa(json_data={'name': 'ditto'})
    res = proxy(client, 'https://pokeapi.co/api/v2/pokemon/ditto')
    assert res.status_code == 200
    assert res.json()['data'] == {'name': 'ditto'}
    api.refresh_from_db()
    assert api.total_visitas == 1

@pytest.mark.django_db
@pytest.mark.parametrize('url', [
    'https://evil.com/robar',                      # otro dominio
    'https://pokeapi.co.evil.com/api/v2/pokemon',  # dominio que empieza igual
    'https://pokeapi.co@evil.com/api/v2/pokemon',  # truco con usuario@dominio
    'https://pokeapi.co/otra-ruta',                # mismo dominio pero fuera de la ruta base
    'https://pokeapi.co/api/v2/../../admin',       # salir de la ruta con ..
    'http://pokeapi.co/api/v2/pokemon',            # otro protocolo
    'file:///etc/passwd',
    '',
])
@patch('apis.views.requests.get')
def test_proxy_rechaza_urls_fuera_del_catalogo(mock_get, client, api, url):
    res = proxy(client, url)
    assert res.status_code == 400
    mock_get.assert_not_called()

@pytest.mark.django_db
def test_proxy_no_acepta_get(client, api):
    res = client.get('/api/proxy/', {'url': 'https://pokeapi.co/api/v2/pokemon/ditto'})
    assert res.status_code == 405

@pytest.mark.django_db
@patch('apis.views.requests.get')
def test_proxy_no_sigue_redirecciones_fuera_del_catalogo(mock_get, client, api):
    mock_get.return_value = respuesta_falsa(status=302, redirect_a='http://169.254.169.254/latest/meta-data')
    res = proxy(client, 'https://pokeapi.co/api/v2/pokemon/ditto')
    assert res.status_code == 502
    assert mock_get.call_count == 1

@pytest.mark.django_db
@patch('apis.views.requests.get')
def test_proxy_sigue_redirecciones_dentro_del_catalogo(mock_get, client, api):
    mock_get.side_effect = [
        respuesta_falsa(status=301, redirect_a='/api/v2/pokemon/ditto/'),
        respuesta_falsa(json_data={'name': 'ditto'}),
    ]
    res = proxy(client, 'https://pokeapi.co/api/v2/pokemon/ditto')
    assert res.status_code == 200
    assert mock_get.call_args_list[1].args[0] == 'https://pokeapi.co/api/v2/pokemon/ditto/'

@pytest.mark.django_db
@patch('apis.views.requests.get')
def test_proxy_respuesta_que_no_es_json(mock_get, client, api):
    r = respuesta_falsa()
    r.json.side_effect = ValueError('no es JSON')
    mock_get.return_value = r
    res = proxy(client, 'https://pokeapi.co/api/v2/pokemon/ditto')
    assert res.status_code == 502


# ── Tests: Verificación de email ──────────────────────────────
@pytest.fixture
def perfil_pendiente(db):
    user = User.objects.create_user(username='nuevo', password='x123456', email='n@test.com', is_active=False)
    return PerfilUsuario.objects.create(usuario=user)

@pytest.mark.django_db
def test_verificacion_activa_la_cuenta_y_el_enlace_es_de_un_solo_uso(client, perfil_pendiente):
    token = perfil_pendiente.token_verificacion
    client.get(f'/verificar/{token}/')
    perfil_pendiente.refresh_from_db()
    assert perfil_pendiente.verificado
    assert perfil_pendiente.usuario.is_active
    assert perfil_pendiente.token_verificacion == ''
    # Segundo uso del mismo enlace: ya no es válido
    res = client.get(f'/verificar/{token}/')
    assert 'no es válido' in res.content.decode()

@pytest.mark.django_db
def test_enlace_caducado_no_verifica_y_envia_uno_nuevo(client, perfil_pendiente):
    token_viejo = perfil_pendiente.token_verificacion
    PerfilUsuario.objects.filter(pk=perfil_pendiente.pk).update(token_creado=timezone.now() - timedelta(days=2))
    res = client.get(f'/verificar/{token_viejo}/')
    perfil_pendiente.refresh_from_db()
    assert 'caducado' in res.content.decode()
    assert not perfil_pendiente.verificado
    assert perfil_pendiente.token_verificacion != token_viejo
    assert len(mail.outbox) == 1
    assert perfil_pendiente.token_verificacion in mail.outbox[0].body


# ── Tests: Validación en vistas de usuario ────────────────────
@pytest.mark.django_db
@pytest.mark.parametrize('valor', ['abc', None, 0, 6])
def test_valorar_con_puntuacion_invalida(cliente_auth, api, valor):
    res = cliente_auth.post(f'/api/users/valorar/{api.id}/', {'puntuacion': valor}, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
def test_valorar_api_inexistente(cliente_auth):
    res = cliente_auth.post('/api/users/valorar/9999/', {'puntuacion': 4}, content_type='application/json')
    assert res.status_code == 404

@pytest.mark.django_db
def test_favorito_de_api_inexistente(cliente_auth):
    res = cliente_auth.post('/api/users/favoritos/9999/toggle/')
    assert res.status_code == 404

@pytest.mark.django_db
def test_cambiar_email_invalido(cliente_auth):
    res = cliente_auth.post('/api/users/cambiar-email/', {'email': '<script>@x'}, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
def test_cambiar_username_con_caracteres_no_permitidos(cliente_auth):
    res = cliente_auth.post('/api/users/cambiar-username/', {'username': '<img src=x>'}, content_type='application/json')
    assert res.status_code == 400
