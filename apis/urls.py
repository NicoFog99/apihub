#urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categorias', views.CategoriaViewSet)
router.register('apis', views.ApiViewSet)

# Rutas adicionales para funcionalidades específicas de la API
urlpatterns = [
    path('', include(router.urls)),
    path('proxy/', views.proxy_request, name='proxy'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]
