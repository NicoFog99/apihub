#models.py

import secrets
from django.db import models
from django.contrib.auth.models import User
from apis.models import Api


class PerfilUsuario(models.Model):
    # Perfil extendido para el usuario, con campos adicionales como verificación y token de verificación.
    usuario            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    verificado         = models.BooleanField(default=False)
    token_verificacion = models.CharField(max_length=64, default='', editable=False)

    def save(self, *args, **kwargs):
        # Genera un token de verificación único si no existe, utilizando el módulo secrets para mayor seguridad.
        if not self.token_verificacion:
            self.token_verificacion = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        # Representación legible del perfil, mostrando el nombre de usuario y un emoji que indica si está verificado o no.
        return f"{self.usuario.username} — {'✅' if self.verificado else '⏳'}"

class Favorito(models.Model):
    # Modelo para representar las APIs favoritas de cada usuario, con una relación ManyToMany a través de este modelo intermedio.
    usuario  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    api      = models.ForeignKey(Api,  on_delete=models.CASCADE, related_name='favoritos')
    guardado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # La combinación de usuario y API debe ser única para evitar duplicados, y se ordena por fecha de guardado descendente.
        unique_together = ('usuario', 'api')
        ordering = ['-guardado']

    def __str__(self):
        return f"{self.usuario.username} → {self.api.nombre}"

class Valoracion(models.Model):
    # Modelo para representar las valoraciones de los usuarios a las APIs, con una relación ManyToMany a través de este modelo intermedio.
    usuario    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='valoraciones')
    api        = models.ForeignKey(Api,  on_delete=models.CASCADE, related_name='valoraciones')
    puntuacion = models.PositiveSmallIntegerField()  # 1-5

    class Meta:
        unique_together = ('usuario', 'api')

    def __str__(self):
        return f"{self.usuario.username} → {self.api.nombre}: {self.puntuacion}★"