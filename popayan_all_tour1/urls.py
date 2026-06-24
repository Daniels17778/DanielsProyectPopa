from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .api import RolViewSet, TipoEstablecimientoViewSet, UsuarioViewSet, EstablecimientoViewSet
from .api_upload import upload_imagen
from .api_views import AuthViewSet
from .api_noticias import CategoriaNoticiaViewSet, NoticiaViewSet, ImagenNoticiaViewSet
from .api_resenas_favoritos import ResenaViewSet, FavoritoViewSet
# ← NUEVO: importar viewsets del panel admin
from .api_admin import DashboardViewSet, AdminUsuarioViewSet, AdminEstablecimientoViewSet

router = DefaultRouter()

# ── Auth y usuarios ───────────────────────────────────────
router.register(r'auth',                    AuthViewSet,                  basename='auth')
router.register(r'roles',                   RolViewSet)
router.register(r'usuarios',                UsuarioViewSet)

# ── Establecimientos ──────────────────────────────────────
router.register(r'tipos-establecimientos',  TipoEstablecimientoViewSet)
router.register(r'establecimientos',        EstablecimientoViewSet,       basename='establecimiento')

# ── Noticias ──────────────────────────────────────────────
router.register(r'noticias',                NoticiaViewSet,               basename='noticia')
router.register(r'categorias-noticias',     CategoriaNoticiaViewSet,      basename='categoria-noticia')
router.register(r'imagenes-noticias',       ImagenNoticiaViewSet,         basename='imagen-noticia')

# ── Reseñas y Favoritos ───────────────────────────────────
router.register(r'resenas',                 ResenaViewSet,                basename='resena')
router.register(r'favoritos',               FavoritoViewSet,              basename='favorito')

urlpatterns = [
    #path("api/", include(router.urls)),
    path("converter/", views.converter_view, name="currency_converter"),
    path("converter/convert/", views.convert_api, name="convert_api"),
    path("api/upload-imagen/", upload_imagen, name="upload_imagen"),
]

"""
═══════════════════════════════════════════════════════════════
ADMIN PANEL API  (todos requieren rol=administrador + token)
═══════════════════════════════════════════════════════════════

DASHBOARD:
  GET  /api/admin/dashboard/estadisticas/   → métricas globales

USUARIOS (admin):
  GET    /api/admin/usuarios/                    → listar todos
  GET    /api/admin/usuarios/?is_active=true     → solo activos
  GET    /api/admin/usuarios/?search=juan        → buscar
  GET    /api/admin/usuarios/{id}/               → detalle
  POST   /api/admin/usuarios/                    → crear
  PATCH  /api/admin/usuarios/{id}/               → editar parcial
  DELETE /api/admin/usuarios/{id}/               → eliminar
  PATCH  /api/admin/usuarios/{id}/suspender/     → suspender + email
  PATCH  /api/admin/usuarios/{id}/activar/       → reactivar
  PATCH  /api/admin/usuarios/{id}/cambiar_rol/   → cambiar rol

ESTABLECIMIENTOS (admin):
  GET    /api/admin/establecimientos/                  → listar todos
  GET    /api/admin/establecimientos/?activo=false     → suspendidos
  GET    /api/admin/establecimientos/{id}/             → detalle
  POST   /api/admin/establecimientos/                  → crear
  PATCH  /api/admin/establecimientos/{id}/             → editar
  DELETE /api/admin/establecimientos/{id}/             → eliminar
  PATCH  /api/admin/establecimientos/{id}/suspender/   → suspender
  PATCH  /api/admin/establecimientos/{id}/activar/     → reactivar
"""