# conftest.py
# Configuración común a todos los tests. pytest carga este archivo automáticamente.
import pytest


@pytest.fixture(autouse=True)
def sin_modo_demo(settings):
    # Los tests empiezan siempre con el modo demo desactivado, tenga lo que tenga el .env.
    # Los tests de test_demo.py lo activan con su propio fixture.
    settings.MODO_DEMO = False

@pytest.fixture(autouse=True)
def estaticos_sin_manifest(settings):
    # En producción WhiteNoise usa un "manifest" que crea collectstatic. En los tests no se ejecuta
    # collectstatic, así que se usa el almacenamiento normal para que las plantillas no fallen.
    settings.STORAGES = {
        **settings.STORAGES,
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
