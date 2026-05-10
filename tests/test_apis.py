# test_apis.py
# Este archivo contiene pruebas unitarias para los endpoints de la API relacionados con el catálogo de APIs, autenticación, favoritos y valoraciones.
import pytest
from django.contrib.auth.models import User
from apis.models import Api, Categoria
from users.models import Favorito, Valoracion


# ── Fixtures ──────────────────────────────────────────────────
# Las fixtures proporcionan datos de prueba para las pruebas unitarias. Incluyen una categoría, una API, un usuario y un cliente autenticado.
@pytest.fixture
# Crea una categoría de prueba para asociar con las APIs en las pruebas.
def categoria(db):
    return Categoria.objects.create(nombre='Test', icono='🧪')

@pytest.fixture
# Crea una API de prueba utilizando la categoría creada anteriormente.
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
# Crea un usuario de prueba para las pruebas de autenticación, favoritos y valoraciones.
def usuario(db):
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        is_active=True,
    )

@pytest.fixture
# Proporciona un cliente autenticado para las pruebas que requieren autenticación. Inicia sesión con el usuario de prueba.
def cliente_auth(client, usuario):
    client.login(username='testuser', password='testpass123')
    return client

# ── Tests: Catálogo ───────────────────────────────────────────

@pytest.mark.django_db
# Prueba para listar APIs, verificando que se devuelve la API creada en la fixture.
def test_listar_apis(client, api):
    res = client.get('/api/apis/')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
# Prueba para obtener el detalle de una API específica, verificando que se devuelve la información correcta.
def test_detalle_api(client, api):
    res = client.get(f'/api/apis/{api.id}/')
    assert res.status_code == 200
    assert res.json()['nombre'] == 'API Test'

@pytest.mark.django_db
# Prueba para filtrar APIs por categoría, verificando que se devuelve la API asociada a la categoría creada en la fixture.
def test_filtro_categoria(client, api):
    res = client.get(f'/api/apis/?categoria={api.categoria.id}')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
# Prueba para filtrar APIs por tipo de autenticación, verificando que se devuelve la API con auth_tipo 'none'.
def test_filtro_auth(client, api):
    res = client.get('/api/apis/?auth=none')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
# Prueba para buscar APIs por nombre, verificando que se devuelve la API que coincide con el término de búsqueda.
def test_busqueda(client, api):
    res = client.get('/api/apis/?search=API Test')
    assert res.status_code == 200
    assert res.json()['count'] == 1

@pytest.mark.django_db
# Prueba para verificar que las APIs inactivas no aparecen en el listado, creando una API con activa=False y verificando que no se devuelve en la respuesta.
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
# Prueba para registrar un nuevo usuario, verificando que se crea el usuario en la base de datos.
def test_register(client):
    res = client.post('/api/users/register/', {
        'username': 'nuevo',
        'password': 'pass1234',
        'email': 'nuevo@test.com',
    }, content_type='application/json')
    assert res.status_code == 201
    assert User.objects.filter(username='nuevo').exists()

@pytest.mark.django_db
# Prueba para iniciar sesión con credenciales correctas, verificando que se devuelve un token de autenticación.
def test_login_correcto(client, usuario):
    res = client.post('/api/users/login/', {
        'username': 'testuser',
        'password': 'testpass123',
    }, content_type='application/json')
    assert res.status_code == 200

@pytest.mark.django_db
# Prueba para iniciar sesión con credenciales incorrectas, verificando que se devuelve un error 400.
def test_login_incorrecto(client):
    res = client.post('/api/users/login/', {
        'username': 'noexiste',
        'password': 'wrongpass',
    }, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
# Prueba para cerrar sesión, verificando que se devuelve un status 200.
def test_logout(cliente_auth):
    res = cliente_auth.post('/api/users/logout/')
    assert res.status_code == 200

@pytest.mark.django_db
# Prueba para obtener los datos del usuario autenticado, verificando que se devuelve la información correcta del usuario.
def test_me_autenticado(cliente_auth):
    res = cliente_auth.get('/api/users/me/')
    assert res.status_code == 200
    assert res.json()['username'] == 'testuser'

@pytest.mark.django_db
# Prueba para obtener los datos del usuario sin autenticación, verificando que se devuelve un error 403.
def test_me_no_autenticado(client):
    res = client.get('/api/users/me/')
    assert res.status_code == 403

# ── Tests: Favoritos ──────────────────────────────────────────

@pytest.mark.django_db
# Prueba para agregar una API a favoritos, verificando que se crea un registro de favorito en la base de datos.
def test_toggle_favorito_añadir(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.status_code == 201
    assert res.json()['favorito'] is True

@pytest.mark.django_db
# Prueba para quitar una API de favoritos, verificando que se elimina el registro de favorito en la base de datos.
def test_toggle_favorito_quitar(cliente_auth, api, usuario):
    Favorito.objects.create(usuario=usuario, api=api)
    res = cliente_auth.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.json()['favorito'] is False

@pytest.mark.django_db
# Prueba para verificar que el endpoint de favoritos requiere autenticación, verificando que se devuelve un error 403 al intentar acceder sin autenticación.
def test_favoritos_requiere_auth(client, api):
    res = client.post(f'/api/users/favoritos/{api.id}/toggle/')
    assert res.status_code == 403

@pytest.mark.django_db
# Prueba para listar las APIs favoritas del usuario, verificando que se devuelve la API que el usuario ha marcado como favorita.
def test_listar_favoritos(cliente_auth, api, usuario):
    Favorito.objects.create(usuario=usuario, api=api)
    res = cliente_auth.get('/api/users/favoritos/')
    assert res.status_code == 200
    assert len(res.json()) == 1

# ── Tests: Valoraciones ───────────────────────────────────────

@pytest.mark.django_db
#  Prueba para valorar una API, verificando que se crea un registro de valoración en la base de datos y que se devuelve la puntuación correcta.
def test_valorar_api(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 5
    }, content_type='application/json')
    assert res.status_code == 200
    assert res.json()['puntuacion'] == 5

@pytest.mark.django_db
# Prueba para actualizar la valoración de una API, verificando que se actualiza el registro de valoración en la base de datos y que se devuelve la nueva puntuación.
def test_valoracion_actualiza_media(cliente_auth, api):
    cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 4
    }, content_type='application/json')
    res = cliente_auth.get(f'/api/apis/{api.id}/')
    assert res.json()['valoracion_media'] == 4.0

@pytest.mark.django_db
# Prueba para valorar una API con una puntuación inválida, verificando que se devuelve un error 400.
def test_valoracion_invalida(cliente_auth, api):
    res = cliente_auth.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 9
    }, content_type='application/json')
    assert res.status_code == 400

@pytest.mark.django_db
# Prueba para verificar que el endpoint de valoración requiere autenticación, verificando que se devuelve un error 403 al intentar acceder sin autenticación.
def test_valoracion_requiere_auth(client, api):
    res = client.post(f'/api/users/valorar/{api.id}/', {
        'puntuacion': 5
    }, content_type='application/json')
    assert res.status_code == 403