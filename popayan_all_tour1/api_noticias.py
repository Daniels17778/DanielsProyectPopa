from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend

from .models import CategoriaNoticia, Noticia, ImagenNoticia
from .serializer_noticias import (
    CategoriaNoticiaSerializer,
    NoticiaListSerializer,
    NoticiaDetailSerializer,
    ImagenNoticiaSerializer,
)


# ============================================================
# PERMISOS
# ============================================================
class EsAdminOSoloLectura(permissions.BasePermission):
    """Solo administradores pueden crear/editar/borrar. Todos pueden leer."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            hasattr(request.user, 'rol') and
            request.user.rol.rol.lower() == 'administrador'
        )


# ============================================================
# CATEGORIAS
# ============================================================
class CategoriaNoticiaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/categorias-noticias/         → listar categorías activas
    GET    /api/categorias-noticias/{id}/    → detalle
    POST   /api/categorias-noticias/         → crear (admin)
    PATCH  /api/categorias-noticias/{id}/    → editar (admin)
    DELETE /api/categorias-noticias/{id}/    → eliminar (admin)
    """
    serializer_class = CategoriaNoticiaSerializer
    permission_classes = [EsAdminOSoloLectura]
    authentication_classes = [TokenAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'id']
    ordering = ['nombre']

    def get_queryset(self):
        # Público solo ve activas; admin ve todas
        if (self.request.user.is_authenticated and
                hasattr(self.request.user, 'rol') and
                self.request.user.rol.rol.lower() == 'administrador'):
            return CategoriaNoticia.objects.all()
        return CategoriaNoticia.objects.filter(activo=True)


# ============================================================
# NOTICIAS
# ============================================================
class NoticiaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/noticias/                    → listar noticias publicadas
    GET    /api/noticias/?destacada=true     → solo destacadas
    GET    /api/noticias/?categoria=1        → filtrar por categoría
    GET    /api/noticias/{id}/               → detalle + registra visita
    GET    /api/noticias/{slug}/             → detalle por slug
    POST   /api/noticias/                    → crear (admin)
    PATCH  /api/noticias/{id}/               → editar (admin)
    DELETE /api/noticias/{id}/               → eliminar (admin)
    GET    /api/noticias/destacadas/         → últimas 5 destacadas
    GET    /api/noticias/recientes/          → últimas 10 publicadas
    """
    permission_classes = [EsAdminOSoloLectura]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['publicada', 'destacada', 'categoria']
    search_fields = ['titulo', 'subtitulo', 'contenido', 'resumen']
    ordering_fields = ['fecha_publicacion', 'fecha_creacion', 'visitas_totales', 'titulo']
    ordering = ['-fecha_publicacion', '-fecha_creacion']
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'list':
            return NoticiaListSerializer
        return NoticiaDetailSerializer

    def get_queryset(self):
        qs = Noticia.objects.select_related('categoria', 'autor').prefetch_related(
            'imagenes_adicionales', 'visitas'
        )
        # Público y no autenticados solo ven publicadas
        if not self.request.user.is_authenticated:
            return qs.filter(publicada=True)

        if hasattr(self.request.user, 'rol'):
            if self.request.user.rol.rol.lower() == 'administrador':
                return qs  # admin ve todo (borradores también)

        return qs.filter(publicada=True)

    def perform_create(self, serializer):
        """Asigna automáticamente el autor al crear."""
        serializer.save(autor=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Detalle: registra visita si el usuario está autenticado."""
        instance = self.get_object()
        if request.user.is_authenticated:
            instance.incrementar_visita(request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Elimina la noticia definitivamente (solo admin)."""
        instance = self.get_object()
        titulo = instance.titulo
        instance.delete()
        return Response(
            {'message': f'Noticia "{titulo}" eliminada correctamente.'},
            status=status.HTTP_200_OK
        )

    # ── Acciones extra ─────────────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def destacadas(self, request):
        """GET /api/noticias/destacadas/ → últimas 5 noticias destacadas publicadas."""
        noticias = Noticia.objects.filter(
            publicada=True, destacada=True
        ).select_related('categoria', 'autor').order_by('-fecha_publicacion')[:5]
        serializer = NoticiaListSerializer(noticias, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def recientes(self, request):
        """GET /api/noticias/recientes/ → últimas 10 noticias publicadas."""
        noticias = Noticia.objects.filter(
            publicada=True
        ).select_related('categoria', 'autor').order_by('-fecha_publicacion')[:10]
        serializer = NoticiaListSerializer(noticias, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny],
            url_path='por-slug/(?P<slug>[^/.]+)', url_name='por-slug')
    def por_slug(self, request, slug=None, **kwargs):
        """GET /api/noticias/{id}/por-slug/{slug}/ — alternativa: buscar por slug."""
        try:
            noticia = Noticia.objects.get(slug=slug, publicada=True)
        except Noticia.DoesNotExist:
            return Response({'error': 'Noticia no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        if request.user.is_authenticated:
            noticia.incrementar_visita(request.user)
        serializer = NoticiaDetailSerializer(noticia, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[EsAdminOSoloLectura])
    def publicar(self, request, pk=None):
        """PATCH /api/noticias/{id}/publicar/ → publica o despublica una noticia."""
        noticia = self.get_object()
        publicar = request.data.get('publicada', True)
        noticia.publicada = publicar
        if publicar and not noticia.fecha_publicacion:
            from django.utils import timezone
            noticia.fecha_publicacion = timezone.now()
        noticia.save()
        estado = 'publicada' if publicar else 'despublicada'
        return Response({'message': f'Noticia "{noticia.titulo}" {estado} correctamente.'})


# ============================================================
# IMÁGENES ADICIONALES
# ============================================================
class ImagenNoticiaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/imagenes-noticias/?noticia=1  → imágenes de una noticia
    POST   /api/imagenes-noticias/→ subir imagen (admin)
    DELETE /api/imagenes-noticias/{id}/       → eliminar imagen (admin)
    """
    serializer_class = ImagenNoticiaSerializer
    permission_classes = [EsAdminOSoloLectura]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['noticia']
    ordering_fields = ['orden']
    ordering = ['orden']

    def get_queryset(self):
        return ImagenNoticia.objects.select_related('noticia').all()