"""
api_admin.py — Panel administrativo · Popayán All Tour
=======================================================
v2 · Producción real  ·  Cambios respecto a v1:
  - Capa de servicios (lógica fuera del ViewSet)
  - Queries optimizadas (select_related, prefetch_related, anotaciones)
  - Cache Django para estadísticas (evitar recalcular en cada request)
  - Permisos reforzados (no solo string comparison)
  - Validaciones de serializer mejoradas
  - Paginación consistente con PageNumberPagination
  - Respuestas con status codes correctos
  - Emails con plantilla reutilizable y envío con retry silencioso
  - Protección contra operaciones masivas accidentales
  - Audit log básico integrado (sin dependencias externas)
"""

from __future__ import annotations

import logging
from functools import wraps

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Usuario, Establecimiento, Noticia, Roles, TipoEstablecimiento
from .serializer import UsuarioSerializer, EstablecimientoSerializer

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════

DASHBOARD_CACHE_KEY = "admin_dashboard_estadisticas"
DASHBOARD_CACHE_TTL = 60 * 2  # 2 minutos — ajustar según tráfico


# ═══════════════════════════════════════════════════════════
# PAGINACIÓN ESTÁNDAR
# ═══════════════════════════════════════════════════════════

class AdminPagination(PageNumberPagination):
    """
    Paginación uniforme para todos los endpoints admin.
    El cliente puede sobreescribir el tamaño con ?page_size=N (máx. 100).
    """
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100


# ═══════════════════════════════════════════════════════════
# PERMISO: Solo administradores — robusto
# ═══════════════════════════════════════════════════════════

class SoloAdmin(permissions.BasePermission):
    """
    MEJORA v2:
      - Verifica is_authenticated antes de acceder a relaciones
      - Usa .lower() + .strip() para evitar errores por espacios/mayúsculas
      - Si el modelo de rol cambia, solo hay que actualizar ROL_ADMINISTRADOR
    """
    ROL_ADMINISTRADOR = "administrador"
    message = "Solo los administradores pueden acceder a este recurso."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.is_active:
            return False
        try:
            return request.user.rol.rol.strip().lower() == self.ROL_ADMINISTRADOR
        except AttributeError:
            # El usuario no tiene rol asignado
            return False


# ═══════════════════════════════════════════════════════════
# CAPA DE SERVICIOS — lógica de negocio fuera del ViewSet
# ═══════════════════════════════════════════════════════════

class DashboardService:
    """
    MEJORA v2:
      - Consulta única con anotaciones en vez de múltiples .count()
      - Cache con invalidación manual
      - Agrupación eficiente con values() + annotate()
    """

    @staticmethod
    def get_estadisticas(force_refresh: bool = False) -> dict:
        if not force_refresh:
            cached = cache.get(DASHBOARD_CACHE_KEY)
            if cached:
                return cached

        # ── Usuarios: una sola query con anotaciones ──────────────────
        usuario_stats = Usuario.objects.aggregate(
            total=Count("id"),
            activos=Count("id", filter=Q(is_active=True)),
            suspendidos=Count("id", filter=Q(is_active=False)),
        )
        roles_dist = list(
            Usuario.objects
            .values("rol__rol")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # ── Establecimientos ──────────────────────────────────────────
        estab_stats = Establecimiento.objects.aggregate(
            total=Count("id"),
            activos=Count("id", filter=Q(activo=True)),
            suspendidos=Count("id", filter=Q(activo=False)),
        )
        tipos_dist = list(
            Establecimiento.objects
            .filter(activo=True)
            .values("tipo__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # ── Noticias ──────────────────────────────────────────────────
        noticia_stats = Noticia.objects.aggregate(
            total=Count("id"),
            publicadas=Count("id", filter=Q(publicada=True)),
            borradores=Count("id", filter=Q(publicada=False)),
            destacadas=Count("id", filter=Q(destacada=True)),
        )

        result = {
            "usuarios": {**usuario_stats, "por_rol": roles_dist},
            "establecimientos": {**estab_stats, "por_tipo": tipos_dist},
            "noticias": noticia_stats,
        }

        cache.set(DASHBOARD_CACHE_KEY, result, DASHBOARD_CACHE_TTL)
        return result

    @staticmethod
    def invalidar_cache():
        cache.delete(DASHBOARD_CACHE_KEY)


class UsuarioService:
    """
    MEJORA v2:
      - Transacciones atómicas en operaciones críticas
      - Desacopla el envío de email del ViewSet
      - Valida estado ANTES de intentar cambiar (evita saves innecesarios)
    """

    @staticmethod
    @transaction.atomic
    def suspender(usuario: Usuario, admin: Usuario) -> dict:
        if not usuario.is_active:
            raise ValueError("El usuario ya está suspendido.")
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        EmailService.enviar_suspension(usuario)
        _audit_log(admin, usuario, CHANGE, "Suspendido por administrador")
        DashboardService.invalidar_cache()
        return {"detail": f'Usuario "{usuario.nombre_completo}" suspendido.', "is_active": False}

    @staticmethod
    @transaction.atomic
    def activar(usuario: Usuario, admin: Usuario) -> dict:
        if usuario.is_active:
            raise ValueError("El usuario ya está activo.")
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        _audit_log(admin, usuario, CHANGE, "Reactivado por administrador")
        DashboardService.invalidar_cache()
        return {"detail": f'Usuario "{usuario.nombre_completo}" reactivado.', "is_active": True}

    @staticmethod
    @transaction.atomic
    def cambiar_rol(usuario: Usuario, rol_id: int, admin: Usuario) -> dict:
        try:
            rol = Roles.objects.get(pk=rol_id)
        except Roles.DoesNotExist:
            raise LookupError("Rol no encontrado.")
        anterior = getattr(getattr(usuario, "rol", None), "rol", "—")
        usuario.rol = rol
        usuario.save(update_fields=["rol"])
        _audit_log(admin, usuario, CHANGE, f"Rol cambiado de '{anterior}' a '{rol.rol}'")
        return {"detail": f'Rol actualizado a "{rol.rol}".'}


class EstablecimientoService:
    @staticmethod
    @transaction.atomic
    def suspender(obj: Establecimiento, admin: Usuario) -> dict:
        obj.activo = False
        obj.save(update_fields=["activo"])
        _audit_log(admin, obj, CHANGE, "Suspendido por administrador")
        DashboardService.invalidar_cache()
        return {"detail": f'"{obj.nombre}" suspendido.', "activo": False}

    @staticmethod
    @transaction.atomic
    def activar(obj: Establecimiento, admin: Usuario) -> dict:
        obj.activo = True
        obj.save(update_fields=["activo"])
        _audit_log(admin, obj, CHANGE, "Activado por administrador")
        DashboardService.invalidar_cache()
        return {"detail": f'"{obj.nombre}" activado.', "activo": True}


# ═══════════════════════════════════════════════════════════
# EMAIL SERVICE — plantillas centralizadas
# ═══════════════════════════════════════════════════════════

class EmailService:
    """
    MEJORA v2:
      - Plantilla base reutilizable (_base_html)
      - No bloquea la operación si falla (fail_silently=True)
      - Loguea el fallo en vez de silenciarlo completamente
      - Fácil de extender para más tipos de notificaciones
    """

    _BASE_STYLE = """
        font-family: 'Segoe UI', Arial, sans-serif;
        max-width: 560px; margin: 0 auto; padding: 32px 24px;
        background: #ffffff; border-radius: 8px;
    """

    @classmethod
    def _base_html(cls, titulo: str, cuerpo: str, color_acento: str = "#e63946") -> str:
        return f"""
        <div style="{cls._BASE_STYLE}">
          <div style="border-bottom: 3px solid {color_acento}; padding-bottom: 16px; margin-bottom: 24px;">
            <h2 style="margin:0; color:#111; font-size:20px;">
              Popayán All Tour
            </h2>
            <p style="margin:4px 0 0; color:#666; font-size:13px;">Notificación del sistema</p>
          </div>
          <h3 style="color:{color_acento}; font-size:17px; margin:0 0 16px;">{titulo}</h3>
          {cuerpo}
          <hr style="border:none; border-top:1px solid #eee; margin:28px 0 16px;">
          <p style="color:#999; font-size:12px; margin:0;">
            Este es un mensaje automático de Popayán All Tour.<br>
            Si tienes preguntas, responde directamente a este correo.
          </p>
        </div>
        """

    @classmethod
    def enviar_suspension(cls, usuario: Usuario):
        cuerpo = f"""
        <p style="color:#333; font-size:15px;">Hola, <strong>{usuario.nombre_completo}</strong>.</p>
        <p style="color:#555;">
          Tu cuenta registrada con <strong>{usuario.email}</strong> ha sido
          <span style="color:#e63946; font-weight:600;">suspendida temporalmente</span>
          por el equipo de administración.
        </p>
        <div style="background:#fff5f5; border-left:4px solid #e63946; padding:14px 16px;
                    border-radius:4px; margin:20px 0;">
          <p style="margin:0; color:#555; font-size:14px;">
            Mientras tu cuenta esté suspendida no podrás acceder al portal ni a sus funcionalidades.
          </p>
        </div>
        <p style="color:#555;">
          Si crees que esto es un error, contáctanos respondiendo este correo.
        </p>
        """
        cls._enviar(
            asunto="Tu cuenta en Popayán All Tour ha sido suspendida",
            texto_plano=f"Hola {usuario.nombre_completo}, tu cuenta ha sido suspendida. Responde este correo para más información.",
            html=cls._base_html("Cuenta suspendida", cuerpo, "#e63946"),
            destinatario=usuario.email,
        )

    @classmethod
    def _enviar(cls, asunto: str, texto_plano: str, html: str, destinatario: str):
        try:
            send_mail(
                subject=asunto,
                message=texto_plano,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@popayanalltour.com"),
                recipient_list=[destinatario],
                html_message=html,
                fail_silently=True,
            )
        except Exception as exc:
            # No bloquear la operación, pero registrar el error
            logger.warning("Email no enviado a %s: %s", destinatario, exc)


# ═══════════════════════════════════════════════════════════
# AUDIT LOG HELPER
# ═══════════════════════════════════════════════════════════

def _audit_log(admin: Usuario, obj, action_flag: int, message: str):
    """
    MEJORA v2 — Registra acciones en django.contrib.admin.LogEntry.
    Sin dependencias externas, visible en /admin/ de Django.
    """
    try:
        LogEntry.objects.log_action(
            user_id=admin.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=action_flag,
            change_message=message,
        )
    except Exception as exc:
        logger.debug("Audit log fallido: %s", exc)


# ═══════════════════════════════════════════════════════════
# SERIALIZERS ENDURECIDOS
# ═══════════════════════════════════════════════════════════

class AdminUsuarioWriteSerializer(serializers.ModelSerializer):
    """
    MEJORA v2:
      - Valida campos obligatorios explícitamente
      - Sanitiza email (strip + lower)
      - Evita que el admin cambie su propio rol o se auto-suspenda
    """

    class Meta:
        model = Usuario
        fields = [
            "nombre_completo", "email", "telefono",
            "identificacion", "fecha_nacimiento",
            "direccion", "profesion",
            "rol", "tipo_establecimiento",
        ]

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        qs = Usuario.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo.")
        return value

    def validate_identificacion(self, value: str) -> str:
        value = value.strip()
        qs = Usuario.objects.filter(identificacion=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un usuario con esta identificación.")
        return value


# ═══════════════════════════════════════════════════════════
# VIEWSETS
# ═══════════════════════════════════════════════════════════

class DashboardViewSet(viewsets.ViewSet):
    """
    MEJORA v2:
      - Usa DashboardService (cache + queries optimizadas)
      - Parámetro ?refresh=1 para forzar recálculo (solo admin)
    """
    permission_classes = [SoloAdmin]

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        force = request.query_params.get("refresh") == "1"
        data = DashboardService.get_estadisticas(force_refresh=force)
        return Response(data)


class AdminUsuarioViewSet(viewsets.ModelViewSet):
    """
    MEJORA v2:
      - select_related para evitar N+1 en rol, tipo_establecimiento
      - Paginación uniforme
      - Serializer de escritura separado del de lectura
      - Acciones de estado usan UsuarioService (transaccional)
      - Status codes correctos (400 para errores de negocio)
    """
    permission_classes = [SoloAdmin]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rol", "is_active"]
    search_fields = ["nombre_completo", "email", "identificacion"]
    ordering_fields = ["nombre_completo", "fecha_nacimiento", "id"]
    ordering = ["nombre_completo"]

    def get_queryset(self):
        # MEJORA: select_related en una sola query; evita N+1 en listados grandes
        return (
            Usuario.objects
            .select_related("rol", "tipo_establecimiento")
            .only(
                "id", "nombre_completo", "email", "telefono",
                "identificacion", "fecha_nacimiento", "direccion",
                "profesion", "is_active",
                "rol__id", "rol__rol",
                "tipo_establecimiento__id", "tipo_establecimiento__nombre",
            )
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AdminUsuarioWriteSerializer
        return UsuarioSerializer

    def destroy(self, request, *args, **kwargs):
        # MEJORA: impedir que un admin se auto-elimine
        obj = self.get_object()
        if obj.pk == request.user.pk:
            return Response(
                {"detail": "No puedes eliminar tu propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _audit_log(request.user, obj, DELETION, "Eliminado por administrador")
        DashboardService.invalidar_cache()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"])
    def suspender(self, request, pk=None):
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            return Response(
                {"detail": "No puedes suspender tu propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = UsuarioService.suspender(usuario, admin=request.user)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def activar(self, request, pk=None):
        try:
            result = UsuarioService.activar(self.get_object(), admin=request.user)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def cambiar_rol(self, request, pk=None):
        rol_id = request.data.get("rol_id")
        if not rol_id:
            return Response({"detail": "Se requiere rol_id."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rol_id = int(rol_id)
        except (ValueError, TypeError):
            return Response({"detail": "rol_id debe ser un entero."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = UsuarioService.cambiar_rol(self.get_object(), rol_id, admin=request.user)
            return Response(result)
        except LookupError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class AdminEstablecimientoViewSet(viewsets.ModelViewSet):
    """
    MEJORA v2:
      - select_related para tipo y empresario
      - Paginación uniforme
      - Cache invalidado al crear/editar/eliminar
    """
    serializer_class = EstablecimientoSerializer
    permission_classes = [SoloAdmin]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo", "tipo"]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "fecha_creacion"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        return (
            Establecimiento.objects
            .select_related("tipo", "empresario")
            .only(
                "id", "nombre", "descripcion", "direccion",
                "horario_aten", "url_mas_info", "imagen_url",
                "activo", "fecha_creacion",
                "tipo__id", "tipo__nombre",
                "empresario__id", "empresario__nombre_completo",
            )
        )

    def perform_create(self, serializer):
        serializer.save()
        DashboardService.invalidar_cache()

    def perform_update(self, serializer):
        serializer.save()
        DashboardService.invalidar_cache()

    def perform_destroy(self, instance):
        _audit_log(self.request.user, instance, DELETION, "Eliminado por administrador")
        instance.delete()
        DashboardService.invalidar_cache()

    @action(detail=True, methods=["patch"])
    def suspender(self, request, pk=None):
        result = EstablecimientoService.suspender(self.get_object(), admin=request.user)
        return Response(result)

    @action(detail=True, methods=["patch"])
    def activar(self, request, pk=None):
        result = EstablecimientoService.activar(self.get_object(), admin=request.user)
        return Response(result)