from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count

from .models import Resena, Favorito
from .serializer_resenas_favoritos import ResenaSerializer, FavoritoSerializer


# PERMISOS
class EsSoloTurista(permissions.BasePermission):
    """Turistas y admins pueden escribir. Lectura pública."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        rol = getattr(request.user, 'rol', None)
        if not rol:
            return False
        return rol.rol.lower() in ['turista', 'administrador']

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        rol = getattr(request.user, 'rol', None)
        if rol and rol.rol.lower() == 'administrador':
            return True
        return obj.usuario == request.user


# RESEÑAS
class ResenaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/resenas/                            → todas las reseñas (público)
    GET    /api/resenas/?establecimiento=1          → reseñas de un establecimiento
    GET    /api/resenas/mias/                       → mis reseñas (autenticado)
    GET    /api/resenas/promedio/?establecimiento=1 → promedio y total
    POST   /api/resenas/                            → crear reseña (turista)
    PATCH  /api/resenas/{id}/                       → editar mi reseña
    DELETE /api/resenas/{id}/                       → borrar mi reseña
    """
    serializer_class = ResenaSerializer
    permission_classes = [EsSoloTurista]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['establecimiento', 'calificacion']
    ordering_fields = ['fecha_creacion', 'calificacion']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return Resena.objects.select_related('usuario', 'establecimiento').all()

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({'message': 'Reseña eliminada.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def mias(self, request):
        """GET /api/resenas/mias/ → mis reseñas."""
        qs = Resena.objects.filter(
            usuario=request.user
        ).select_related('establecimiento').order_by('-fecha_creacion')
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.AllowAny])
    def promedio(self, request):
        """GET /api/resenas/promedio/?establecimiento=1"""
        eid = request.query_params.get('establecimiento')
        if not eid:
            return Response(
                {'error': 'Debes pasar ?establecimiento=<id>'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = Resena.objects.filter(establecimiento_id=eid).aggregate(
            promedio=Avg('calificacion'),
            total=Count('id')
        )
        return Response({
            'establecimiento_id': eid,
            'promedio': round(data['promedio'], 1) if data['promedio'] else 0,
            'total_resenas': data['total'],
        })


# ============================================================
# FAVORITOS
# ============================================================
class FavoritoViewSet(viewsets.ModelViewSet):
    """
    GET    /api/favoritos/                      → mis favoritos (todos)
    GET    /api/favoritos/?tipo=establecimiento → solo establecimientos guardados
    GET    /api/favoritos/?tipo=noticia         → solo noticias guardadas
    POST   /api/favoritos/                      → guardar favorito
    DELETE /api/favoritos/{id}/                 → quitar favorito
    POST   /api/favoritos/toggle/               → agregar o quitar en un click ❤
    """
    serializer_class = FavoritoSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-fecha_guardado']

    def get_queryset(self):
        qs = Favorito.objects.filter(
            usuario=self.request.user
        ).select_related(
            'establecimiento', 'establecimiento__tipo',
            'noticia', 'noticia__categoria'
        )
        # Filtro por tipo: ?tipo=establecimiento o ?tipo=noticia
        tipo = self.request.query_params.get('tipo')
        if tipo == 'establecimiento':
            qs = qs.filter(establecimiento__isnull=False)
        elif tipo == 'noticia':
            qs = qs.filter(noticia__isnull=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        favorito = self.get_object()
        nombre = (
            favorito.establecimiento.nombre
            if favorito.establecimiento
            else favorito.noticia.titulo
        )
        favorito.delete()
        return Response(
            {'message': f'"{nombre}" eliminado de tus favoritos.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def toggle(self, request):
        """
        POST /api/favoritos/toggle/

        Para establecimiento:  {"establecimiento": 1}
        Para noticia:          {"noticia": 3}

        Si ya está guardado → lo quita  (guardado: false)
        Si no está guardado → lo agrega (guardado: true)
        """
        establecimiento_id = request.data.get('establecimiento')
        noticia_id         = request.data.get('noticia')

        if not establecimiento_id and not noticia_id:
            return Response(
                {'error': 'Envía {"establecimiento": <id>} o {"noticia": <id>}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if establecimiento_id and noticia_id:
            return Response(
                {'error': 'Envía solo uno: "establecimiento" o "noticia".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar si ya existe
        if establecimiento_id:
            favorito = Favorito.objects.filter(
                usuario=request.user,
                establecimiento_id=establecimiento_id
            ).first()
        else:
            favorito = Favorito.objects.filter(
                usuario=request.user,
                noticia_id=noticia_id
            ).first()

        # Toggle
        if favorito:
            favorito.delete()
            return Response(
                {'guardado': False, 'message': 'Eliminado de favoritos.'},
                status=status.HTTP_200_OK
            )
        else:
            data = {}
            if establecimiento_id:
                data['establecimiento_id'] = establecimiento_id
            else:
                data['noticia_id'] = noticia_id

            nuevo = Favorito.objects.create(usuario=request.user, **data)
            serializer = FavoritoSerializer(nuevo, context={'request': request})
            return Response(
                {'guardado': True, 'message': 'Agregado a favoritos.', 'favorito': serializer.data},
                status=status.HTTP_201_CREATED
            )