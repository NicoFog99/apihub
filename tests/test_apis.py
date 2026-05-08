import pytest
from django.contrib.auth.models import User
from apis.models import Api, Categoria
from users.models import Favorito, Valoracion

# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nombre='Test', icono='🧪')

@pytest.fixture
def api(db, categoria):
    return Api.objects.create(
        nombre='API Test',
        descripcion='Descripción de prueba',
        url_base='https://test.com',
        auth_tipo='none',
        categoria=categoria,
        activa=True,
    )

@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        is_active=True,
    )

@pytest.fixture
def cliente_auth(client, usuario):
    client.login(username='testuser', password='testpass123')
    return client

# ── Tests: Catálogo ───────────────────────────────────────────

@pytest.mark.django_db
def test_listar_apis(client, api):
    res = client.get('/api/apis/')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
def test_detalle_api(client, api):
    res = client.get(f'/api/apis/{api.id}/')
    assert res.status_code == 200
    assert res.json()['nombre'] == 'API Test'

@pytest.mark.django_db
def test_filtro_categoria(client, api):
    res = client.get(f'/api/apis/?categoria={api.categoria.id}')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
def test_filtro_auth(client, api):
    res = client.get('/api/apis/?auth=none')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
def test_busqueda(client, api):
    res = client.get('/api/apis/?search=API Test')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
def test_api_inactiva_no_aparece(client, categoria):
    Api.objects.create(
        nombre='API Inactiva',
        descripcion='...',
        url_base='https://test.com',
        auth_tipo='none',
        categoria=categoria,
        activa=False,
    )
    res = client.get('/api/apis/')
    assert res.json()['count'] == 0

# ── Tests: Autenticación ──────────────────────────────────────

@pytest.mark.django_db
def test_register(client):
    res = client.post('/api/users/register/', {
        'username': 'nuevo',
        'password': 'pass1234',
        'email': 'nuevo@test.com',
    }, content_type='application/json')
    assert res.status_code == 201
    assert User.objects.filter(username='nuevo').exists()

@pytest.mark.django_db
def test_login_correcto(client, usuario):
    res = client.post('/api/users/login/', {
        'username': 'testuser',
        'password': 'testpass123',
    }, content_type='application/json')
    assert res.status_code == 200

@pytest.mark.django_db
def test_login_incorrecto(client):
    res = client.post('/api/users/login/', {
        'username': 'noexiste',
        'password': 'wrongpass',
    }, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
def test_logout(cliente_auth):
    res = cliente_auth.post('/api/users/logout/')
    assert res.status_code == 200

@pytest.mark.django_db
def test_me_autenticado(cliente_auth):
    res = cliente_auth.get('/api/users/me/')
    assert res.status_code == 200
    assert res.json()['username'] == 'testuser'

@pytest.mark.django_db
def test_me_no_autenticado(client):
    res = client.get('/api/users/me/')
    assert res.status_code == 403

# ── Tests: Favoritos ──────────────────────────────────────────

@pytest.mark.django_db
def test_toggle_favorito_añadir(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.status_code == 201
    assert res.json()['favorito'] is True

@pytest.mark.django_db
def test_toggle_favorito_quitar(cliente_auth, api, usuario):
    Favorito.objects.create(usuario=usuario, api=api)
    res = cliente_auth.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.json()['favorito'] is False

@pytest.mark.django_db
def test_favoritos_requiere_auth(client, api):
    res = client.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.status_code == 403

@pytest.mark.django_db
def test_listar_favoritos(cliente_auth, api, usuario):
    Favorito.objects.create(usuario=usuario, api=api)
    res = cliente_auth.get('/api/users/favoritos/')
    assert res.status_code == 200
    assert len(res.json()) == 1

# ── Tests: Valoraciones ───────────────────────────────────────

@pytest.mark.django_db
def test_valorar_api(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 5
    }, content_type='application/json')
    assert res.status_code == 200
    assert res.json()['puntuacion'] == 5

@pytest.mark.django_db
def test_valoracion_actualiza_media(cliente_auth, api):
    cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 4
    }, content_type='application/json')
    res = cliente_auth.get(f'/api/apis/{api.id}/')
    assert res.json()['valoracion_media'] == 4.0

@pytest.mark.django_db
def test_valoracion_invalida(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 9
    }, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
def test_valoracion_requiere_auth(client, api):
    res = client.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 5
    }, content_type='application/json')
    assert res.status_code == 403