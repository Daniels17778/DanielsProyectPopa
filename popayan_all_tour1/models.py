from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings


# ============================================================
# ROLES
# ============================================================
class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    rol = models.CharField(max_length=50, unique=True, verbose_name='Rol')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.rol


# ============================================================
# TIPO DE ESTABLECIMIENTO
# ============================================================
class TipoEstablecimiento(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Establecimiento")

    class Meta:
        db_table = "tipo_establecimiento"
        verbose_name = "Tipo de Establecimiento"
        verbose_name_plural = "Tipos de Establecimiento"

    def __str__(self):
        return self.nombre


# ============================================================
# USUARIO
# ============================================================
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)

        rol = extra_fields.get("rol")
        if rol and isinstance(rol, int):
            extra_fields["rol"] = Roles.objects.get(pk=rol)

        tipo = extra_fields.get("tipo_establecimiento")
        if tipo and isinstance(tipo, int):
            extra_fields["tipo_establecimiento"] = TipoEstablecimiento.objects.get(pk=tipo)

        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if "fecha_nacimiento" not in extra_fields:
            extra_fields["fecha_nacimiento"] = "2000-08-07"

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        if "identificacion" not in extra_fields or not extra_fields["identificacion"]:
            extra_fields["identificacion"] = f"admin-{email}"

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre completo")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    profesion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profesión")
    identificacion = models.CharField(max_length=50, unique=True, verbose_name="Identificación")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")

    imagen_perfil = models.ImageField(
        upload_to="usuarios/perfiles/",
        blank=True, null=True,
        verbose_name="Imagen de perfil"
    )
    avatar_url = models.URLField(
        blank=True, null=True,
        verbose_name="Avatar predeterminado",
        help_text="URL de Cloudinary para avatar predeterminado"
    )

    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, verbose_name="Rol")
    tipo_establecimiento = models.ForeignKey(
        TipoEstablecimiento,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Tipo de Establecimiento"
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre_completo", "rol"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre_completo} ({self.email})"

    def clean(self):
        if self.rol and self.rol.rol.lower() == "empresario" and not self.tipo_establecimiento:
            raise ValidationError("Un empresario debe tener un tipo de establecimiento asignado.")

    def get_imagen_perfil(self):
        if self.imagen_perfil:
            return self.imagen_perfil.url
        elif self.avatar_url:
            return self.avatar_url
        return "https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505287/avatar_naranja_ofufi8.png"


# ============================================================
# ESTABLECIMIENTO (modelo unificado para sitios turísticos)
# ============================================================
class Establecimiento(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    horario_aten = models.TextField(max_length=200, verbose_name="Horario de Atención")
    direccion = models.TextField(max_length=200, verbose_name="Dirección")

    # Imagen local (compatibilidad)
    imagen = models.ImageField(
        upload_to="establecimientos/",
        blank=True, null=True,
        verbose_name="Imagen"
    )
    # Imagen en Cloudinary
    imagen_url = models.URLField(
        blank=True, null=True,
        verbose_name="URL de Imagen (Cloudinary)"
    )

    url_mas_info = models.URLField(verbose_name="URL para más información")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # Tipo de establecimiento (Hotel, Restaurante, Museo, Iglesia, etc.)
    tipo = models.ForeignKey(
        TipoEstablecimiento,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Establecimiento",
        related_name="establecimientos"
    )

    # Empresario responsable
    empresario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="establecimientos",
        limit_choices_to={"rol__rol": "empresario"},
        verbose_name="Empresario"
    )

    class Meta:
        verbose_name = "Establecimiento"
        verbose_name_plural = "Establecimientos"
        ordering = ['-fecha_creacion']


    def __str__(self):
        empresario_nombre = self.empresario.nombre_completo if self.empresario else 'Sin empresario'
        return f"{self.nombre} ({self.tipo}) - {empresario_nombre}"

    def get_imagen_url(self):
        """Devuelve la URL de imagen disponible (Cloudinary primero, luego local)"""
        if self.imagen_url:
            return self.imagen_url
        elif self.imagen:
            return self.imagen.url
        return None


# ============================================================
# NOTICIAS
# ============================================================
class CategoriaNoticia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#000000', help_text='Color en formato hexadecimal')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoría de Noticia'
        verbose_name_plural = 'Categorías de Noticias'
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    subtitulo = models.CharField(max_length=300, blank=True, null=True)
    contenido = models.TextField(help_text='Contenido completo de la noticia')
    resumen = models.TextField(max_length=500, blank=True, null=True,
                               help_text='Resumen breve para vista previa')

    categoria = models.ForeignKey(
        CategoriaNoticia, on_delete=models.SET_NULL,
        null=True, related_name='noticias'
    )

    imagen_principal = models.ImageField(upload_to='noticias/', help_text='Imagen principal de la noticia')
    pie_imagen = models.CharField(max_length=200, blank=True, null=True, help_text='Descripción de la imagen')

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='noticias_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(blank=True, null=True)

    publicada = models.BooleanField(default=False)
    destacada = models.BooleanField(default=False, help_text='Marcar como noticia destacada')
    visitas_totales = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-fecha_publicacion', '-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_publicacion']),
            models.Index(fields=['-visitas_totales']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('detalle_noticia', kwargs={'slug': self.slug})

    @property
    def visitas_unicas(self):
        return self.visitas.count()

    def incrementar_visita(self, usuario):
        if usuario.is_authenticated:
            visita, creada = VisitaNoticia.objects.get_or_create(noticia=self, usuario=usuario)
            if creada:
                self.visitas_totales += 1
                self.save(update_fields=['visitas_totales'])
            return creada
        return False

    def ha_visitado(self, usuario):
        if usuario.is_authenticated:
            return self.visitas.filter(usuario=usuario).exists()
        return False


class VisitaNoticia(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='visitas')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='noticias_visitadas'
    )
    fecha_visita = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Visita a Noticia'
        verbose_name_plural = 'Visitas a Noticias'
        unique_together = ['noticia', 'usuario']
        ordering = ['-fecha_visita']
        indexes = [
            models.Index(fields=['noticia', 'usuario']),
        ]

    def __str__(self):
        return f'{self.usuario.email} - {self.noticia.titulo}'


class ImagenNoticia(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='imagenes_adicionales')
    imagen = models.ImageField(upload_to='noticias/adicionales/')
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Imagen Adicional'
        verbose_name_plural = 'Imágenes Adicionales'
        ordering = ['orden']

    def __str__(self):
        return f'Imagen de {self.noticia.titulo}'
    
# RESEÑAS

class Resena(models.Model):
    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='resenas',
        verbose_name='Establecimiento'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resenas',
        verbose_name='Usuario'
    )
    calificacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Calificación (1-5)'
    )
    comentario = models.TextField(
        blank=True, null=True,
        verbose_name='Comentario'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-fecha_creacion']
        # ── Una sola reseña por usuario por establecimiento ──
        # Si quieres permitir múltiples reseñas, comenta la línea de abajo:
        unique_together = ['establecimiento', 'usuario']
        # ────────────────────────────────────────────────────

    def __str__(self):
        return f'{self.usuario.nombre_completo} → {self.establecimiento.nombre} ({self.calificacion}★)'



# FAVORITOS  (establecimientos + noticias)

class Favorito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favoritos',
        verbose_name='Usuario'
    )
    # ── Solo uno de los dos campos estará lleno ──
    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.CASCADE,
        related_name='favoritos',
        verbose_name='Establecimiento',
        null=True, blank=True,
    )
    noticia = models.ForeignKey(
        'Noticia',
        on_delete=models.CASCADE,
        related_name='favoritos',
        verbose_name='Noticia',
        null=True, blank=True,
    )
    fecha_guardado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-fecha_guardado']
        # Evita duplicados por combinación usuario+establecimiento y usuario+noticia
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'establecimiento'],
                condition=models.Q(establecimiento__isnull=False),
                name='unique_favorito_establecimiento'
            ),
            models.UniqueConstraint(
                fields=['usuario', 'noticia'],
                condition=models.Q(noticia__isnull=False),
                name='unique_favorito_noticia'
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        # Debe tener exactamente uno de los dos
        if not self.establecimiento and not self.noticia:
            raise ValidationError('Debes indicar un establecimiento o una noticia.')
        if self.establecimiento and self.noticia:
            raise ValidationError('Un favorito no puede ser establecimiento y noticia al mismo tiempo.')

    def __str__(self):
        objetivo = self.establecimiento.nombre if self.establecimiento else self.noticia.titulo
        return f'{self.usuario.nombre_completo} ❤ {objetivo}'