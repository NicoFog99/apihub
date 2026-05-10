from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Favorito
from apis.serializers import ApiSerializer
 
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
 
    class Meta:
        model  = User
        fields = ('username', 'email', 'password')
 
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
 
class FavoritoSerializer(serializers.ModelSerializer):
    api_detalle = ApiSerializer(source='api', read_only=True)
 
    class Meta:
        model  = Favorito
        fields = ('id', 'api', 'api_detalle', 'guardado')