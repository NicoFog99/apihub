#admin.py
# Register your models here.

from django.contrib import admin
from .models import Api, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono')

@admin.register(Api)
class ApiAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'categoria', 'auth_tipo', 'activa')
    list_filter   = ('categoria', 'auth_tipo', 'activa')
    search_fields = ('nombre', 'descripcion')
