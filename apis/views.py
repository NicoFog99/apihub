# views.py

from urllib.parse import urljoin, urlparse

import requests
from django.db.models import F
from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg
from .models import Api, Categoria
from .serializers import ApiSerializer, CategoriaSerializer

# ViewSet para listar categorías, con opción de búsqueda por nombre
class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Categoria.objects.all()
    serializer_class = CategoriaSerializer

# ViewSet para listar APIs, con filtros por categoría, tipo de autenticación, ordenamiento y si están implementadas en el frontend
class ApiViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Api.objects.filter(activa=True)
    serializer_class = ApiSerializer
    filter_backends  = [filters.SearchFilter]
    search_fields    = ['nombre', 'descripcion', 'categoria__nombre']

    def get_queryset(self):
        qs = Api.objects.filter(activa=True).select_related('categoria').annotate(
            rating_medio=Avg('valoraciones__puntuacion')
        ).order_by('nombre')

        categoria = self.request.query_params.get('categoria')
        auth      = self.request.query_params.get('auth')
        orden     = self.request.query_params.get('orden')

        if categoria:
            qs = qs.filter(categoria__id=categoria)
        if auth:
            qs = qs.filter(auth_tipo=auth)

        orden_map = {
            'nombre':     'nombre',
            '-nombre':    '-nombre',
            'creada_en':  'creada_en',
            '-creada_en': '-creada_en',
            '-rating':    '-rating_medio',
            '-visitas':   '-total_visitas',
        }
        if orden in orden_map:
            qs = qs.order_by(orden_map[orden])
        implementada = self.request.query_params.get('implementada')
        if implementada is not None and implementada != '':
            qs = qs.filter(implementada=implementada == 'true')

        return qs

def api_del_catalogo(url):
    """
    Devuelve la API activa del catálogo a la que pertenece esta URL, o None si no pertenece a ninguna.

    Se compara por partes (protocolo, dominio y ruta) en lugar de con startswith, porque con
    startswith una URL como "https://test.com.evil.com" o "https://test.com@evil.com"
    pasaría el filtro de "https://test.com".
    """
    if not isinstance(url, str):
        return None
    destino = urlparse(url)
    if destino.scheme not in ('http', 'https') or not destino.hostname or destino.username or '..' in destino.path:
        return None

    for api in Api.objects.filter(activa=True).only('id', 'url_base'):
        base = urlparse(api.url_base)
        if destino.scheme != base.scheme or destino.netloc.lower() != base.netloc.lower():
            continue
        ruta_base = base.path.rstrip('/')
        if not ruta_base or destino.path == ruta_base or destino.path.startswith(ruta_base + '/'):
            return api
    return None


MAX_REDIRECCIONES = 3


# Endpoint para hacer peticiones proxy a APIs externas, usado por el frontend para evitar problemas de CORS y para incrementar el contador de visitas de cada API.
# Solo acepta URLs que pertenezcan a una API del catálogo: así nadie puede usar el servidor para hacer peticiones a sitios arbitrarios (SSRF).
@api_view(['POST'])
@permission_classes([AllowAny])
def proxy_request(request):
    url    = request.data.get('url')
    params = request.data.get('params') or {}
    if not isinstance(params, dict):
        return Response({'error': 'Los parámetros deben ser un objeto JSON.'}, status=400)

    api = api_del_catalogo(url)
    if api is None:
        return Response({'error': 'Solo se pueden probar APIs del catálogo.'}, status=400)

    # Suma la visita directamente en la base de datos (F evita perder visitas si llegan dos peticiones a la vez)
    Api.objects.filter(pk=api.pk).update(total_visitas=F('total_visitas') + 1)

    try:
        # Las redirecciones se siguen a mano para comprobar que el destino también es del catálogo
        for _ in range(MAX_REDIRECCIONES + 1):
            resp = requests.get(url, params=params, headers={'Accept': 'application/json'},
                                timeout=10, allow_redirects=False)
            if not resp.is_redirect:
                break
            url, params = urljoin(url, resp.headers.get('Location', '')), None
            if api_del_catalogo(url) is None:
                return Response({'error': 'La API redirige a un sitio que no está en el catálogo.'}, status=502)
        else:
            return Response({'error': 'La API ha hecho demasiadas redirecciones.'}, status=502)
    except requests.Timeout:
        return Response({'error': 'La API externa ha tardado demasiado en responder.'}, status=504)
    except requests.RequestException:
        return Response({'error': 'No se ha podido conectar con la API externa.'}, status=502)

    try:
        datos = resp.json()
    except ValueError:
        return Response({'error': 'La API externa no ha devuelto JSON.', 'status': resp.status_code}, status=502)

    return Response({'status': resp.status_code, 'data': datos})
    
# Endpoint para obtener estadísticas generales de la plataforma, como APIs más valoradas, más visitadas, categorías con más APIs, etc.    
@api_view(['GET'])
@permission_classes([AllowAny])
def estadisticas(request):
    from django.db.models import Avg, Count, Max
    from django.contrib.auth.models import User

    apis       = Api.objects.filter(activa=True).annotate(
        media=Avg('valoraciones__puntuacion'),
        visitas=Count('total_visitas')
    )
    categorias = Categoria.objects.annotate(total=Count('apis'))

    mas_valorada = Api.objects.filter(activa=True).annotate(
        media=Avg('valoraciones__puntuacion')
    ).order_by('-media').first()

    mas_visitada = Api.objects.filter(activa=True).order_by('-total_visitas').first()

    cat_mas_apis = categorias.order_by('-total').first()

    return Response({
        'total_apis':       Api.objects.filter(activa=True).count(),
        'total_categorias': Categoria.objects.count(),
        'total_usuarios':   User.objects.filter(is_active=True).count(),
        'mas_valorada': {
            'nombre': mas_valorada.nombre if mas_valorada else None,
            'id':     mas_valorada.id     if mas_valorada else None,
            'media':  round(Avg('valoraciones__puntuacion') and mas_valorada.valoraciones.aggregate(m=Avg('puntuacion'))['m'] or 0, 1) if mas_valorada else 0,
        },
        'mas_visitada': {
            'nombre':        mas_visitada.nombre        if mas_visitada else None,
            'id':            mas_visitada.id            if mas_visitada else None,
            'total_visitas': mas_visitada.total_visitas if mas_visitada else 0,
        },
        'cat_mas_apis': {
            'nombre': cat_mas_apis.nombre if cat_mas_apis else None,
            'icono':  cat_mas_apis.icono  if cat_mas_apis else None,
            'total':  cat_mas_apis.total  if cat_mas_apis else 0,
        },
        'categorias': [
            {'nombre': c.nombre, 'icono': c.icono, 'total': c.total}
            for c in categorias.order_by('-total')
        ],
        'top_valoradas': [
            {
                'id':     a.id,
                'nombre': a.nombre,
                'media':  round(a.valoraciones.aggregate(m=Avg('puntuacion'))['m'] or 0, 1),
                'visitas': a.total_visitas,
            }
            for a in Api.objects.filter(activa=True).annotate(
                media=Avg('valoraciones__puntuacion')
            ).order_by('-media')[:5]
        ],
        'top_visitadas': [
            {'id': a.id, 'nombre': a.nombre, 'visitas': a.total_visitas}
            for a in Api.objects.filter(activa=True).order_by('-total_visitas')[:5]
        ],
    })