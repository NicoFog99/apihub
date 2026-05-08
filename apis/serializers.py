from rest_framework import serializers
from django.db.models import Avg
from .models import Api, Categoria

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Categoria
        fields = '__all__'

class ApiSerializer(serializers.ModelSerializer):
    categoria_nombre   = serializers.CharField(source='categoria.nombre', read_only=True)
    categoria_icono    = serializers.CharField(source='categoria.icono',  read_only=True)
    valoracion_media   = serializers.SerializerMethodField()
    total_valoraciones = serializers.SerializerMethodField()

    def get_valoracion_media(self, obj):
        resultado = obj.valoraciones.aggregate(media=Avg('puntuacion'))['media']
        return round(resultado, 1) if resultado else None

    def get_total_valoraciones(self, obj):
        return obj.valoraciones.count()

    class Meta:
        model  = Api
        fields = [
            'id', 'nombre', 'descripcion', 'url_base',
            'auth_tipo', 'categoria', 'categoria_nombre', 'categoria_icono',
            'documentacion_url', 'ejemplo_endpoint', 'parametros_ejemplo',
            'render_tipo', 'activa', 'valoracion_media', 'total_valoraciones',
            'total_visitas', 'implementada',
        ]