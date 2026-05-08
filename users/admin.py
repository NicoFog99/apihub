from django.contrib import admin
from .models import Favorito, PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'verificado', 'token_verificacion')

@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'api', 'guardado')