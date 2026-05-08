import secrets
from django.db import models
from django.contrib.auth.models import User
from apis.models import Api

class PerfilUsuario(models.Model):
    usuario            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    verificado         = models.BooleanField(default=False)
    token_verificacion = models.CharField(max_length=64, default='', editable=False)

    def save(self, *args, **kwargs):
        if not self.token_verificacion:
            self.token_verificacion = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.username} — {'✅' if self.verificado else '⏳'}"

class Favorito(models.Model):
    usuario  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    api      = models.ForeignKey(Api,  on_delete=models.CASCADE, related_name='favoritos')
    guardado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'api')
        ordering = ['-guardado']

    def __str__(self):
        return f"{self.usuario.username} → {self.api.nombre}"

class Valoracion(models.Model):
    usuario    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='valoraciones')
    api        = models.ForeignKey(Api,  on_delete=models.CASCADE, related_name='valoraciones')
    puntuacion = models.PositiveSmallIntegerField()  # 1-5

    class Meta:
        unique_together = ('usuario', 'api')

    def __str__(self):
        return f"{self.usuario.username} → {self.api.nombre}: {self.puntuacion}★"