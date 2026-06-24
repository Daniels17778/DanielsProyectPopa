"""
URL configuration para el proyecto Popayán All Tour.
Documentación Django: https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import include, path
from popayan_all_tour1.urls import router as api_router

from popayan_all_tour1.views import (
    # ── Autenticación ──────────────────────────────────────────────────────
    registro,
    login_view,
    logout_view,
    completar_perfil_google,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,

    # ── Páginas generales ──────────────────────────────────────────────────
    home,
    terminos,
    entretenimiento,
    perfilUser,
    eliminar_imagen_perfil,

    # ── Semana Santa ───────────────────────────────────────────────────────
    semanas,
    procesiones,

    # ── Historia ───────────────────────────────────────────────────────────
    historia,
    historia_1601_view,
    historia_1701_view,
    historia_1801_view,
    historia_1831_view,
    historia_1885_view,
    historia_1937_view,
    historia_1983_view,
    descargar_historia_completa_pdf,
    descargar_historia_año_pdf,

    # ── Juegos / entretenimiento ───────────────────────────────────────────
    memory,

    # ── Establecimientos — público ─────────────────────────────────────────
    listar_establecimientos_publicos,
    registrar_visita,

    # ── Establecimientos — gestión (empresario) ────────────────────────────
    agregar_establecimiento,
    editar_establecimiento,
    eliminar_establecimiento,
    reactivar_establecimiento,
    eliminar_permanente_establecimiento,
    estadisticas_establecimiento,

    # ── Dashboard administrador ────────────────────────────────────────────
    dashboard_administrador,
    redirect_by_role,

    # ── Gestión de usuarios (administrador) ───────────────────────────────
    crear_rol,
    crear_tipo_establecimiento,
    suspender_usuario,
    activar_usuario,
    editar_usuario,

    # ── Noticias — públicas ────────────────────────────────────────────────
    noticia,
    ListaNoticiasView,
    DetalleNoticiaView,
    noticias_populares_view,
    noticias_por_categoria_view,

    # ── Noticias — administración ──────────────────────────────────────────
    crear_noticia,
    editar_noticia,
    eliminar_noticia,
    mis_noticias,
    toggle_publicar_noticia,
    lista_categorias,
    crear_categoria,

    # cambios noticias - admin
    ajax_suspender_noticia,       # ← nuevo
    ajax_reactivar_noticia,       # ← nuevo
    ajax_eliminar_noticia_definitivo,  # ← nuevo

    #categirias noticias 
    ajax_editar_categoria,
    ajax_toggle_categoria,
    ajax_eliminar_categoria,
    
    # ── Exportaciones PDF / Excel ──────────────────────────────────────────
    exportar_estadisticas_empresario_pdf,
    exportar_estadisticas_empresario_excel,
    exportar_estadisticas_admin_pdf,
    exportar_estadisticas_admin_excel,

    # ── API JSON ───────────────────────────────────────────────────────────
    api_establecimientos_visitas,

    # ── API AJAX — usuarios ────────────────────────────────────────────────
    ajax_eliminar_usuario,
    ajax_suspender_usuario,
    ajax_activar_usuario,
    ajax_editar_usuario,

    # ── API AJAX — establecimientos ────────────────────────────────────────
    ajax_eliminar_establecimiento,
    ajax_activar_establecimiento,

    # ── API AJAX — stats ───────────────────────────────────────────────────
    ajax_dashboard_stats,

    # ── Conversor de divisas ───────────────────────────────────────────────
    converter_view,
    convert_api,

    #resenas dashboard
    ajax_eliminar_resena,
    ajax_lista_resenas,
)

urlpatterns = [

    # ══════════════════════════════════════════════════════════════════════
    # DJANGO ADMIN
    # ══════════════════════════════════════════════════════════════════════
    path('admin/', admin.site.urls),

    # ══════════════════════════════════════════════════════════════════════
    # AUTENTICACIÓN
    # ══════════════════════════════════════════════════════════════════════
    path('', login_view, name='login'),
    path('registro', registro, name='registro'),
    path('logout/', logout_view, name='logout'),

    # Recuperación de contraseña
    path('recuperar/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('recuperar/completado/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Google OAuth
    path('auth/', include('social_django.urls', namespace='social')),
    path('completar-perfil/', completar_perfil_google, name='completar_perfil_google'),

    # ══════════════════════════════════════════════════════════════════════
    # PÁGINAS GENERALES
    # ══════════════════════════════════════════════════════════════════════
    path('home', home, name='home'),
    path('terminos', terminos, name='terminos'),
    path('entretenimiento', entretenimiento, name='entretenimiento'),
    path('redirect-by-role/', redirect_by_role, name='redirect_by_role'),

    # ══════════════════════════════════════════════════════════════════════
    # PERFIL DE USUARIO
    # ══════════════════════════════════════════════════════════════════════
    path('perfil/', perfilUser, name='perfilUser'),
    path('eliminar-imagen-perfil/', eliminar_imagen_perfil, name='eliminar_imagen_perfil'),

    # ══════════════════════════════════════════════════════════════════════
    # ESTABLECIMIENTOS — Listados públicos
    # (rutas específicas antes que las genéricas con <str:tipo>)
    # ══════════════════════════════════════════════════════════════════════
    path('hoteles/', listar_establecimientos_publicos, {'tipo': 'hotel'}, name='listar_hoteles'),
    path('restaurantes/', listar_establecimientos_publicos, {'tipo': 'restaurante'}, name='listar_restaurantes'),
    path('museos/', listar_establecimientos_publicos, {'tipo': 'museo'}, name='listar_museos'),
    path('iglesias/', listar_establecimientos_publicos, {'tipo': 'iglesia'}, name='listar_iglesias'),

    # Registrar visita y redirigir a URL externa
    path('visita/<str:tipo>/<int:id>/', registrar_visita, name='registrar_visita'),

    # ══════════════════════════════════════════════════════════════════════
    # ESTABLECIMIENTOS — Gestión (empresario)
    # ══════════════════════════════════════════════════════════════════════
    path('<str:tipo>/agregar/', agregar_establecimiento, name='agregar_establecimiento'),
    path('<str:tipo>/<int:id>/editar/', editar_establecimiento, name='editar_establecimiento'),
    path('empresario/eliminar/<str:tipo>/<int:id>/', eliminar_establecimiento, name='eliminar_establecimiento'),
    path('empresario/reactivar/<str:tipo>/<int:id>/', reactivar_establecimiento, name='reactivar_establecimiento'),
    path('empresario/eliminar-permanente/<str:tipo>/<int:id>/', eliminar_permanente_establecimiento, name='eliminar_permanente_establecimiento'),
    path('empresario/estadisticas/', estadisticas_establecimiento, name='estadisticas_establecimiento'),

    # ══════════════════════════════════════════════════════════════════════
    # DASHBOARD ADMINISTRADOR
    # ══════════════════════════════════════════════════════════════════════
    path('dashboard-administrador/', dashboard_administrador, name='dashboard_administrador'),

    # Gestión de usuarios desde el dashboard
    path('admin-panel/crear-rol/', crear_rol, name='crear_rol'),
    path('admin-panel/crear-tipo/', crear_tipo_establecimiento, name='crear_tipo_establecimiento'),
    path('admin-panel/suspender/<int:user_id>/', suspender_usuario, name='suspender_usuario'),
    path('admin-panel/activar/<int:user_id>/', activar_usuario, name='activar_usuario'),
    path('admin-panel/editar-usuario/<int:user_id>/', editar_usuario, name='editar_usuario'),

    # ══════════════════════════════════════════════════════════════════════
    # NOTICIAS — Administración  (rutas específicas PRIMERO)
    # ══════════════════════════════════════════════════════════════════════
    path('noticias/crear/',                      crear_noticia,                    name='crear_noticia'),
    path('noticias/mis-noticias/',               mis_noticias,                     name='mis_noticias'),
    path('noticias/editar/<slug:slug>/',         editar_noticia,                   name='editar_noticia'),
    path('noticias/eliminar/<slug:slug>/',       eliminar_noticia,                 name='eliminar_noticia'),
    path('noticias/toggle-publicar/<slug:slug>/',toggle_publicar_noticia,          name='toggle_publicar_noticia'),

    # ══════════════════════════════════════════════════════════════════════
    # NOTICIAS — Públicas  (la ruta con <slug> siempre AL FINAL)
    # ══════════════════════════════════════════════════════════════════════
    path('noticia/',                             noticia,                          name='noticia'),
    path('noticias/populares/',                  noticias_populares_view,          name='noticias_populares'),
    path('noticias/categoria/<slug:slug>/',      noticias_por_categoria_view,      name='noticias_categoria'),
    path('noticias/categorias/',                 lista_categorias,                 name='lista_categorias'),
    path('noticias/categorias/crear/',           crear_categoria,                  name='crear_categoria'),

    # ═══ API AJAX — Noticias ══════════════════════════════════════════════
    path('ajax/noticias/<slug:slug>/suspender/', ajax_suspender_noticia,           name='ajax_suspender_noticia'),
    path('ajax/noticias/<slug:slug>/reactivar/', ajax_reactivar_noticia,           name='ajax_reactivar_noticia'),
    path('ajax/noticias/<slug:slug>/eliminar/',  ajax_eliminar_noticia_definitivo, name='ajax_eliminar_noticia_definitivo'),

    # ⚠️  Esta va SIEMPRE AL FINAL — captura cualquier /noticias/<slug>/
    path('noticias/<slug:slug>/',                DetalleNoticiaView.as_view(),     name='detalle_noticia'),

    # ══════════════════════════════════════════════════════════════════════
    # HISTORIA DE POPAYÁN
    # ══════════════════════════════════════════════════════════════════════
    path('histori/', historia, name='historia_1537'),
    path('historia-1601/', historia_1601_view, name='historia_1601'),
    path('historia-1701/', historia_1701_view, name='historia_1701'),
    path('historia-1801/', historia_1801_view, name='historia_1801'),
    path('historia-1831/', historia_1831_view, name='historia_1831'),
    path('historia-1885/', historia_1885_view, name='historia_1885'),
    path('historia-1937/', historia_1937_view, name='historia_1937'),
    path('historia-1983/', historia_1983_view, name='historia_1983'),

    # Descarga PDFs de historia
    path('historia/pdf/completa/', descargar_historia_completa_pdf, name='pdf_historia_completa'),
    path('historia/pdf/<int:ano>/', descargar_historia_año_pdf, name='pdf_historia_año'),

    # ══════════════════════════════════════════════════════════════════════
    # SEMANA SANTA
    # ══════════════════════════════════════════════════════════════════════
    path('semana/', semanas, name='semanaSanta'),
    path('procesiones/', procesiones, name='procesiones'),

    # ══════════════════════════════════════════════════════════════════════
    # JUEGOS / ENTRETENIMIENTO
    # ══════════════════════════════════════════════════════════════════════
    path('popares', memory, name='popares'),
    path('juegaso/', lambda request: render(request, 'juegaso/juego.html'), name='juegaso'),
    path('menu/', lambda request: render(request, 'juegaso/menu.html'), name='menu'),
    path('creditos/', lambda request: render(request, 'juegaso/creditos.html'), name='creditos'),
    path('ciroGoal/', lambda request: render(request, 'CiroGoal/CiroGoal/index.html'), name='CiroGoal'),

    # ══════════════════════════════════════════════════════════════════════
    # EXPORTACIONES PDF / EXCEL
    # ══════════════════════════════════════════════════════════════════════
    path('exportar/empresario/pdf/', exportar_estadisticas_empresario_pdf, name='exportar_empresario_pdf'),
    path('exportar/empresario/excel/', exportar_estadisticas_empresario_excel, name='exportar_empresario_excel'),
    path('exportar/admin/pdf/', exportar_estadisticas_admin_pdf, name='exportar_admin_pdf'),
    path('exportar/admin/excel/', exportar_estadisticas_admin_excel, name='exportar_admin_excel'),

    # ══════════════════════════════════════════════════════════════════════
    # CONVERSOR DE DIVISAS
    # ══════════════════════════════════════════════════════════════════════
    path('conversor/', converter_view, name='converter'),
    path('conversor/api/', convert_api, name='convert_api'),

    # ══════════════════════════════════════════════════════════════════════
    # API JSON
    # ══════════════════════════════════════════════════════════════════════
    path('api/establecimientos-visitas/', api_establecimientos_visitas, name='api_establecimientos_visitas'),

    # ══════════════════════════════════════════════════════════════════════
    # API AJAX — Usuarios
    # ══════════════════════════════════════════════════════════════════════
    path('ajax/usuarios/<int:user_id>/eliminar/', ajax_eliminar_usuario, name='ajax_eliminar_usuario'),
    path('ajax/usuarios/<int:user_id>/suspender/', ajax_suspender_usuario, name='ajax_suspender_usuario'),
    path('ajax/usuarios/<int:user_id>/activar/', ajax_activar_usuario, name='ajax_activar_usuario'),
    path('ajax/usuarios/<int:user_id>/editar/', ajax_editar_usuario, name='ajax_editar_usuario'),

    # ══════════════════════════════════════════════════════════════════════
    # API AJAX — Establecimientos
    # ══════════════════════════════════════════════════════════════════════
    path('ajax/establecimientos/<int:estab_id>/eliminar/', ajax_eliminar_establecimiento, name='ajax_eliminar_establecimiento'),
    path('ajax/establecimientos/<int:estab_id>/activar/', ajax_activar_establecimiento, name='ajax_activar_establecimiento'),

    # ══════════════════════════════════════════════════════════════════════
    # API AJAX — Stats en tiempo real
    # ══════════════════════════════════════════════════════════════════════
    path('ajax/dashboard/stats/', ajax_dashboard_stats, name='ajax_dashboard_stats'),

    path('ajax/categorias/<int:cat_id>/editar/',  ajax_editar_categoria,   name='ajax_editar_categoria'),
    path('ajax/categorias/<int:cat_id>/toggle/',  ajax_toggle_categoria,    name='ajax_toggle_categoria'),
    path('ajax/categorias/<int:cat_id>/eliminar/',ajax_eliminar_categoria,  name='ajax_eliminar_categoria'),
    # ══════════════════════════════════════════════════════════════════════
    # URLs INTERNAS DE LA APP
    # ══════════════════════════════════════════════════════════════════════
    #path("", include("popayan_all_tour1.urls")),

    #resenas dashboard
    path('ajax/resenas/', ajax_lista_resenas, name='ajax_lista_resenas'),
    path('ajax/resenas/<int:resena_id>/eliminar/', ajax_eliminar_resena, name='ajax_eliminar_resena'),

    path('api/', include(api_router.urls)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)