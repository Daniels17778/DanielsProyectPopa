from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import Roles, TipoEstablecimiento, Usuario, Establecimiento
from .serializer import (
    RolSerializer, TipoEstablecimientoSerializer,
    UsuarioSerializer, EstablecimientoSerializer,
)


# ============================================================
# PERMISOS PERSONALIZADOS
# ============================================================
class EsAdminOSoloLectura(permissions.BasePermission):
    """Solo administradores pueden crear/editar/borrar. Todos pueden ver."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            hasattr(request.user, 'rol') and
            request.user.rol.rol.lower() == 'administrador'
        )


class EsEmpresarioOAdmin(permissions.BasePermission):
    """Empresarios pueden gestionar sus propios establecimientos. Admin puede todo."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'rol'):
            return False
        rol = request.user.rol.rol.lower()
        return rol in ['administrador', 'empresario']

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not hasattr(request.user, 'rol'):
            return False
        rol = request.user.rol.rol.lower()
        if rol == 'administrador':
            return True
        if rol == 'empresario':
            return obj.empresario == request.user
        return False


# ============================================================
# VIEWSETS
# ============================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolSerializer
    permission_classes = [EsAdminOSoloLectura]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rol"]
    search_fields = ["rol"]
    ordering_fields = ["rol", "id"]
    ordering = ["rol"]


class TipoEstablecimientoViewSet(viewsets.ModelViewSet):
    queryset = TipoEstablecimiento.objects.all()
    serializer_class = TipoEstablecimientoSerializer
    permission_classes = [EsAdminOSoloLectura]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["nombre"]
    search_fields = ["nombre"]
    ordering_fields = ["nombre", "id"]
    ordering = ["nombre"]


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdminOSoloLectura]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rol", "tipo_establecimiento", "is_active"]
    search_fields = ["nombre_completo", "email", "identificacion"]
    ordering_fields = ["nombre_completo", "fecha_nacimiento"]
    ordering = ["nombre_completo"]


class EstablecimientoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para establecimientos.
    GET    /api/establecimientos/          → listar todos
    GET    /api/establecimientos/?tipo=hotel → filtrar por tipo
    GET    /api/establecimientos/{id}/     → detalle
    POST   /api/establecimientos/          → crear (empresario/admin)
    PATCH  /api/establecimientos/{id}/     → editar parcial (dueño/admin)
    DELETE /api/establecimientos/{id}/     → eliminar (dueño/admin)
    GET    /api/establecimientos/estadisticas/ → estadísticas generales
    """
    serializer_class = EstablecimientoSerializer
    permission_classes = [EsEmpresarioOAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo", "empresario", "tipo"]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["fecha_creacion", "nombre"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        queryset = Establecimiento.objects.select_related('tipo', 'empresario')

        # Turistas y no autenticados solo ven activos
        if not self.request.user.is_authenticated:
            return queryset.filter(activo=True)

        if hasattr(self.request.user, 'rol'):
            rol = self.request.user.rol.rol.lower()
            if rol == 'administrador':
                return queryset  # admin ve todo
            elif rol == 'empresario':
                # empresario ve todos los activos + los suyos inactivos
                return queryset.filter(activo=True) | queryset.filter(
                    empresario=self.request.user)

        return queryset.filter(activo=True)

    def perform_create(self, serializer):
        """Al crear, asignar automáticamente el empresario si es empresario."""
        if (hasattr(self.request.user, 'rol') and
                self.request.user.rol.rol.lower() == 'empresario'):
            serializer.save(empresario=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Soft delete: desactiva en lugar de borrar."""
        obj = self.get_object()
        obj.activo = False
        obj.save()
        return Response(
            {'message': f'"{obj.nombre}" desactivado correctamente.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def estadisticas(self, request):
        """
        GET /api/establecimientos/estadisticas/
        Devuelve estadísticas generales o del empresario autenticado.
        """
        if not hasattr(request.user, 'rol'):
            return Response({'error': 'Sin rol'}, status=status.HTTP_403_FORBIDDEN)

        rol = request.user.rol.rol.lower()

        if rol == 'administrador':
            tipos = TipoEstablecimiento.objects.all()
            por_tipo = {
                tipo.nombre.lower(): Establecimiento.objects.filter(
                    tipo=tipo, activo=True).count()
                for tipo in tipos
            }
            return Response({
                'total_establecimientos': Establecimiento.objects.filter(activo=True).count(),
                'por_tipo': por_tipo,
                'total_usuarios': Usuario.objects.filter(is_active=True).count(),
                'turistas': Usuario.objects.filter(rol__rol='turista', is_active=True).count(),
                'empresarios': Usuario.objects.filter(rol__rol='empresario', is_active=True).count(),
                'visitas': 0,
            })

        elif rol == 'empresario':
            tipo_obj = request.user.tipo_establecimiento
            establecimientos = Establecimiento.objects.filter(
                empresario=request.user, activo=True)
            return Response({
                'tipo': tipo_obj.nombre if tipo_obj else None,
                'total_activos': establecimientos.count(),
                'total_inactivos': Establecimiento.objects.filter(
                    empresario=request.user, activo=False).count(),
                'establecimientos': [
                    {'id': e.id, 'nombre': e.nombre, 'visitas': 0}
                    for e in establecimientos
                ]
            })

        return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['patch'], permission_classes=[EsEmpresarioOAdmin])
    def activar(self, request, pk=None):
        """PATCH /api/establecimientos/{id}/activar/ → reactiva un establecimiento"""
        obj = self.get_object()
        obj.activo = True
        obj.save()
        return Response({'message': f'"{obj.nombre}" activado correctamente.'})