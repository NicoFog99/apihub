import requests
from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg
from .models import Api, Categoria
from .serializers import ApiSerializer, CategoriaSerializer


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Categoria.objects.all()
    serializer_class = CategoriaSerializer


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


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def proxy_request(request):
    url     = request.data.get('url') or request.query_params.get('url')
    params  = request.data.get('params', {})
    headers = {'Accept': 'application/json'}

    # Incrementar visitas buscando la API cuya url_base coincide con la petición
    try:
        for a in Api.objects.filter(activa=True):
            if url and url.startswith(a.url_base):
                a.total_visitas += 1
                a.save()
                break
    except Exception:
        pass

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        return Response({'status': resp.status_code, 'data': resp.json()})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
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