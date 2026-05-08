from django.urls import path
from django.views.generic import TemplateView
from users import views as user_views
from django.views.defaults import page_not_found
from frontend import views


urlpatterns = [
    path('',               TemplateView.as_view(template_name='index.html'),   name='home'),
    path('api/<int:pk>/',  TemplateView.as_view(template_name='detalle.html'),  name='api-detalle'),
    path('perfil/',        TemplateView.as_view(template_name='perfil.html'),   name='perfil'),
    path('verificar/<str:token>/', user_views.verificar_email, name='verificar-web'),
    path('stats/', views.stats, name='stats'),
]