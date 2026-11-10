# core/urls.py

from django.contrib import admin
from django.urls import path, include
from decouple import config
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Rutas principales del proyecto, incluyendo el panel de administración, las APIs de las aplicaciones y la documentación de la API
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    path('api/users/', include('users.urls')),
    path('', include('frontend.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        # La ruta del panel se lee del .env para no dejarla en /admin/, que es lo primero que prueban los bots
    path(config('ADMIN_URL', default='admin/'), admin.site.urls),
]

from django.conf.urls import handler404
from frontend.views import custom_404

# Personalización de páginas de error 404 y 500 para mejorar la experiencia del usuario en caso de errores
handler404 = 'frontend.views.custom_404'
handler500 = 'frontend.views.custom_500'