from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Roles, TipoEstablecimiento, Usuario, Establecimiento,
    CategoriaNoticia, Noticia, VisitaNoticia, ImagenNoticia
)


@admin.register(Roles)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "rol", "cantidad_usuarios")
    search_fields = ("rol",)
    readonly_fields = ("cantidad_usuarios",)

    def cantidad_usuarios(self, obj):
        count = obj.usuario_set.count()
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{}</span>', count
        )
    cantidad_usuarios.short_description = "Usuarios con este rol"


@admin.register(TipoEstablecimiento)
class TipoEstablecimientoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "cantidad_establecimientos")
    search_fields = ("nombre",)
    readonly_fields = ("cantidad_establecimientos",)

    def cantidad_establecimientos(self, obj):
        count = obj.establecimientos.count()
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">{}</span>', count
        )
    cantidad_establecimientos.short_description = "Establecimientos"


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "id", "email", "nombre_completo", "rol",
        "tipo_establecimiento", "telefono", "ver_imagen",
        "estado_activo", "es_staff"
    )
    list_filter = ("rol", "is_active", "is_staff", "tipo_establecimiento")
    search_fields = ("email", "nombre_completo", "identificacion", "telefono")
    readonly_fields = ("ver_imagen_grande", "last_login")

    fieldsets = (
        ("Información de Acceso", {
            "fields": ("email", "password", "is_active", "is_staff", "is_superuser")
        }),
        ("Información Personal", {
            "fields": (
                "nombre_completo", "identificacion", "fecha_nacimiento",
                "telefono", "direccion", "profesion"
            )
        }),
        ("Imagen de Perfil", {
            "fields": ("imagen_perfil", "avatar_url", "ver_imagen_grande")
        }),
        ("Rol y Establecimiento", {
            "fields": ("rol", "tipo_establecimiento")
        }),
        ("Información Adicional", {
            "fields": ("last_login",),
            "classes": ("collapse",)
        }),
    )

    def ver_imagen(self, obj):
        url = obj.get_imagen_perfil()
        if url:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                url
            )
        return "Sin imagen"
    ver_imagen.short_description = "Imagen"

    def ver_imagen_grande(self, obj):
        url = obj.get_imagen_perfil()
        if url:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 10px;" />',
                url
            )
        return "Sin imagen de perfil"
    ver_imagen_grande.short_description = "Vista previa"

    def estado_activo(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Activo</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactivo</span>')
    estado_activo.short_description = "Estado"

    def es_staff(self, obj):
        return obj.is_staff
    es_staff.boolean = True
    es_staff.short_description = "Staff"


@admin.register(Establecimiento)
class EstablecimientoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nombre", "tipo", "empresario", "direccion",
        "ver_imagen", "estado_activo", "fecha_creacion"
    )
    list_filter = ("activo", "tipo", "fecha_creacion")
    search_fields = ("nombre", "descripcion", "direccion", "empresario__nombre_completo")
    readonly_fields = ("ver_imagen_grande", "fecha_creacion", "url_imagen_cloudinary")
    date_hierarchy = "fecha_creacion"

    fieldsets = (
        ("Información Básica", {
            "fields": ("nombre", "tipo", "descripcion", "empresario")
        }),
        ("Ubicación y Horarios", {
            "fields": ("direccion", "horario_aten")
        }),
        ("Imágenes", {
            "fields": ("imagen", "imagen_url", "ver_imagen_grande", "url_imagen_cloudinary")
        }),
        ("Enlaces y Estado", {
            "fields": ("url_mas_info", "activo")
        }),
        ("Información Adicional", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",)
        }),
    )

    def ver_imagen(self, obj):
        url = obj.get_imagen_url()
        if url:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: cover;" />',
                url
            )
        return "Sin imagen"
    ver_imagen.short_description = "Imagen"

    def ver_imagen_grande(self, obj):
        url = obj.get_imagen_url()
        if url:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 10px;" />',
                url
            )
        return "Sin imagen"
    ver_imagen_grande.short_description = "Vista previa"

    def url_imagen_cloudinary(self, obj):
        if obj.imagen_url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.imagen_url, obj.imagen_url
            )
        return "No hay URL de Cloudinary"
    url_imagen_cloudinary.short_description = "URL Cloudinary"

    def estado_activo(self, obj):
        if obj.activo:
            return format_html('<span style="color: green; font-weight: bold;">✓ Activo</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactivo</span>')
    estado_activo.short_description = "Estado"


@admin.register(CategoriaNoticia)
class CategoriaNoticiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'activo', 'total_noticias']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}

    def total_noticias(self, obj):
        return obj.noticias.count()
    total_noticias.short_description = 'Total Noticias'


class ImagenNoticiaInline(admin.TabularInline):
    model = ImagenNoticia
    extra = 1
    fields = ['imagen', 'descripcion', 'orden']


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'categoria', 'autor', 'fecha_publicacion',
        'publicada', 'destacada', 'visitas_totales', 'visitas_unicas_display'
    ]
    list_filter = ['publicada', 'destacada', 'categoria', 'fecha_creacion']
    search_fields = ['titulo', 'subtitulo', 'contenido']
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'fecha_publicacion'
    readonly_fields = ['visitas_totales']
    inlines = [ImagenNoticiaInline]

    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'slug', 'subtitulo', 'categoria')
        }),
        ('Contenido', {
            'fields': ('resumen', 'contenido')
        }),
        ('Imagen', {
            'fields': ('imagen_principal', 'pie_imagen')
        }),
        ('Publicación', {
            'fields': ('autor', 'fecha_publicacion', 'publicada', 'destacada')
        }),
        ('Estadísticas', {
            'fields': ('visitas_totales',),
            'classes': ('collapse',)
        }),
    )

    def visitas_unicas_display(self, obj):
        return obj.visitas_unicas
    visitas_unicas_display.short_description = 'Visitas Únicas'

    def save_model(self, request, obj, form, change):
        if not obj.autor:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


@admin.register(VisitaNoticia)
class VisitaNoticiaAdmin(admin.ModelAdmin):
    list_display = ['noticia', 'usuario', 'fecha_visita']
    list_filter = ['fecha_visita']
    search_fields = ['noticia__titulo', 'usuario__email']
    date_hierarchy = 'fecha_visita'
    readonly_fields = ['noticia', 'usuario', 'fecha_visita']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False