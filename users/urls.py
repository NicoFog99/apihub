from django.urls import path
from . import views

urlpatterns = [
    path('register/',                        views.register,        name='register'),
    path('login/',                           views.user_login,      name='login'),
    path('logout/',                          views.user_logout,     name='logout'),
    path('me/',                              views.me,              name='me'),
    path('favoritos/',                       views.favoritos_list,  name='favoritos'),
    path('favoritos/<int:api_id>/toggle/',   views.favorito_toggle, name='favorito-toggle'),
    path('verificar/<str:token>/',           views.verificar_email, name='verificar-email'),
    path('valorar/<int:api_id>/',            views.valorar_api,     name='valorar-api'),
    path('mi-valoracion/<int:api_id>/',      views.mi_valoracion,   name='mi-valoracion'),
    path('cambiar-password/',  views.cambiar_password,  name='cambiar-password'),
    path('cambiar-email/',     views.cambiar_email,      name='cambiar-email'),
    path('cambiar-username/',  views.cambiar_username,   name='cambiar-username'),
    path('eliminar-cuenta/',   views.eliminar_cuenta,    name='eliminar-cuenta'),
]