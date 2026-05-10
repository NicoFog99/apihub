# models.py
from django.db import models

# 
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    icono  = models.CharField(max_length=50, blank=True, help_text="Emoji o clase de icono")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Categorías"


class Api(models.Model):
    # Opciones de autenticación para el campo auth_tipo
    AUTH_OPCIONES = [
        ('none',   'Sin autenticación'),
        ('apikey', 'API Key'),
        ('oauth',  'OAuth'),
        
    ]

    # Opciones de renderizado para el frontend, que pueden ser usadas para mostrar la respuesta de la API de diferentes formas
    RENDER_OPCIONES = [
        ('json',    'JSON'),
        ('pokemon', 'Pokémon'),
        ('iss',     'Mapa ISS'),
        ('crypto',  'Gráfica Crypto'),
        ('apod',    'NASA APOD'),
        ('meal',        'TheMealDB'),
        ('country',     'RestCountries'),
        ('weather', 'Clima Open-Meteo'),
        ('joke', 'JokeAPI'),  
    ]

    # Campos principales de la API
    nombre      = models.CharField(max_length=200)
    descripcion = models.TextField()
    url_base    = models.URLField()
    auth_tipo   = models.CharField(max_length=20, choices=AUTH_OPCIONES, default='none')
    categoria   = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='apis')
    documentacion_url  = models.URLField(blank=True)
    ejemplo_endpoint   = models.CharField(max_length=300, blank=True)
    parametros_ejemplo = models.JSONField(default=dict, blank=True)
    render_tipo        = models.CharField(max_length=20, choices=RENDER_OPCIONES, default='json')
    activa      = models.BooleanField(default=True)
    creada_en   = models.DateTimeField(auto_now_add=True)

    #puntuacion estrellas
    puntuacion_promedio = models.FloatField(default=0.0)
    total_puntuaciones = models.PositiveIntegerField(default=0)
    # contador de visitas para mostrar popularidad
    total_visitas = models.PositiveIntegerField(default=0)
    # campo para marcar si la API ha sido implementada en el frontend (para mostrar un badge "En desarrollo" si no lo está)
    implementada = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "APIs"
        ordering = ['nombre']

#Clase para guardar puntuaciones de usuarios a APIs
class PuntuacionApi(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='puntuaciones')
    api = models.ForeignKey(Api, on_delete=models.CASCADE, related_name='puntuaciones')
    valor = models.IntegerField()

    class Meta:
        unique_together = ['usuario', 'api']  # Un usuario solo puede votar una vez por API
