from django import forms
from .models import Usuario, Roles, TipoEstablecimiento, Establecimiento, Noticia, CategoriaNoticia, ImagenNoticia, TipoEstablecimiento 
from datetime import date
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from .avatares import AVATARES_PREDETERMINADOS, get_avatar_url
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

# ============================================================
# FORMULARIO DE REGISTRO
# ============================================================
class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    avatar_predeterminado = forms.ChoiceField(
        choices=[('', 'Seleccionar avatar...')] + [(av['id'], av['nombre']) for av in AVATARES_PREDETERMINADOS],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'avatar-selector'}),
        label='Elige tu avatar'
    )
        # 🔐 CAPTCHA AQUÍ
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = Usuario
        fields = [
            "email", "telefono", "password", "profesion",
            "nombre_completo", "identificacion", "fecha_nacimiento",
            "rol", "direccion", "tipo_establecimiento"
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].queryset = Roles.objects.exclude(rol__iexact="administrador")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Correo ya registrado")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")
        if Usuario.objects.filter(telefono=telefono).exists():
            raise forms.ValidationError("Numero de teléfono en uso")
        if len(telefono) < 7:
            raise forms.ValidationError("Al menos 7 digitos")
        return telefono

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get("identificacion")
        if Usuario.objects.filter(identificacion=identificacion).exists():
            raise forms.ValidationError("Identificación ya registrada")
        return identificacion

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if len(password) < 5:
            raise forms.ValidationError("Al menos 5 caracteres")
        return password

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get("fecha_nacimiento")
        if fecha_nacimiento:
            edad = (date.today() - fecha_nacimiento).days // 365
            if edad < 16:
                raise forms.ValidationError("Debe ser mayor de 16 años")
        return fecha_nacimiento

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        avatar_id = self.cleaned_data.get('avatar_predeterminado')
        if avatar_id:
            user.avatar_url = get_avatar_url(avatar_id)
        if commit:
            user.save()
        return user


# ============================================================
# FORMULARIO BÁSICO DE USUARIO
# ============================================================
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["email", "password", "nombre_completo", "direccion", "telefono", "imagen_perfil"]
        widgets = {
            "password": forms.PasswordInput(render_value=True),
        }


# ============================================================
# FORMULARIO DE ESTABLECIMIENTO (modelo unificado)
# ============================================================
class EstablecimientoForm(forms.ModelForm):
    """
    Formulario único para crear/editar cualquier tipo de establecimiento.
    El tipo se selecciona desde TipoEstablecimiento.
    """

    class Meta:
        model = Establecimiento
        fields = ['nombre', 'tipo', 'descripcion', 'horario_aten', 'direccion', 'imagen', 'url_mas_info']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del establecimiento'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Descripción detallada'
            }),
            'horario_aten': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lunes a Viernes 8am - 6pm'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'url_mas_info': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com'
            }),
        }

    def __init__(self, *args, tipo_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tipo_id:
            self.fields['tipo'].queryset = TipoEstablecimiento.objects.filter(pk=tipo_id)
            self.fields['tipo'].widget = forms.HiddenInput()
            self.initial['tipo'] = tipo_id

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            if imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede ser mayor a 5MB.")
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(imagen.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Solo se permiten imágenes (jpg, jpeg, png, gif).")
        return imagen


# ============================================================
# FORMULARIO DE EDICIÓN DE PERFIL
# ============================================================
class EditarPerfilForm(forms.ModelForm):

    nueva_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar en blanco para mantener la actual'}),
        required=False,
        label='Nueva Contraseña'
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar nueva contraseña'}),
        required=False,
        label='Confirmar Contraseña'
    )
    avatar_predeterminado = forms.ChoiceField(
        choices=[('', 'Mantener actual')] + [(av['id'], av['nombre']) for av in AVATARES_PREDETERMINADOS],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'avatar-selector'}),
        label='Cambiar avatar'
    )
    eliminar_avatar = forms.BooleanField(
        required=False,
        label='Usar icono por defecto (eliminar avatar actual)'
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'nombre_completo', 'fecha_nacimiento',
            'direccion', 'telefono', 'profesion', 'identificacion',
            'rol', 'tipo_establecimiento', 'imagen_perfil'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'nombre_completo': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dirección completa'}),
            'telefono': forms.TextInput(attrs={'placeholder': '312 456 7890'}),
            'profesion': forms.TextInput(attrs={'placeholder': 'Profesión u ocupación'}),
            'identificacion': forms.TextInput(attrs={'placeholder': 'Número de identificación'}),
            'imagen_perfil': forms.FileInput(attrs={'accept': 'image/*', 'style': 'display: none;'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_staff:
            self.fields['rol'].disabled = True
            self.fields['tipo_establecimiento'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk:
            if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este correo ya está registrado por otro usuario')
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            if len(telefono) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos')
            if self.instance and self.instance.pk:
                if Usuario.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Este teléfono ya está registrado por otro usuario')
        return telefono

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get('identificacion')
        if identificacion and self.instance and self.instance.pk:
            if Usuario.objects.filter(identificacion=identificacion).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Esta identificación ya está registrada')
        return identificacion

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            edad = (date.today() - fecha_nacimiento).days // 365
            if edad < 16:
                raise ValidationError('Debes ser mayor de 16 años')
        return fecha_nacimiento

    def clean_imagen_perfil(self):
        imagen = self.cleaned_data.get('imagen_perfil')
        if imagen:
            if hasattr(imagen, 'size') and imagen.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede ser mayor a 5MB')
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(imagen.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Solo se permiten imágenes (jpg, jpeg, png, gif, webp)')
        return imagen

    def clean(self):
        cleaned_data = super().clean()
        nueva_password = cleaned_data.get('nueva_password')
        confirmar_password = cleaned_data.get('confirmar_password')

        if nueva_password:
            if len(nueva_password) < 5:
                raise ValidationError('La contraseña debe tener al menos 5 caracteres')
            if nueva_password != confirmar_password:
                raise ValidationError('Las contraseñas no coinciden')

        rol = cleaned_data.get('rol')
        tipo_establecimiento = cleaned_data.get('tipo_establecimiento')
        if rol and rol.rol.lower() == 'empresario' and not tipo_establecimiento:
            raise ValidationError('Un empresario debe tener un tipo de establecimiento asignado')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva_password = self.cleaned_data.get('nueva_password')
        if nueva_password:
            user.set_password(nueva_password)

        avatar_id = self.cleaned_data.get('avatar_predeterminado')
        eliminar_avatar = self.cleaned_data.get('eliminar_avatar')

        if eliminar_avatar:
            if user.imagen_perfil:
                user.imagen_perfil.delete(save=False)
            user.avatar_url = None
        elif avatar_id:
            user.avatar_url = get_avatar_url(avatar_id)
            if user.imagen_perfil:
                user.imagen_perfil.delete(save=False)

        if commit:
            user.save()
        return user


# ============================================================
# FORMULARIOS DE NOTICIAS
# ============================================================
class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = [
            'titulo', 'subtitulo', 'categoria', 'resumen', 'contenido',
            'imagen_principal', 'pie_imagen', 'fecha_publicacion', 'publicada', 'destacada'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia', 'maxlength': '200'}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subtítulo (opcional)', 'maxlength': '300'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Resumen breve (máximo 500 caracteres)', 'rows': 3, 'maxlength': '500'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contenido completo de la noticia', 'rows': 10}),
            'pie_imagen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la imagen', 'maxlength': '200'}),
            'fecha_publicacion': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'publicada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destacada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titulo': 'Título *', 'subtitulo': 'Subtítulo', 'categoria': 'Categoría *',
            'resumen': 'Resumen', 'contenido': 'Contenido Completo *',
            'imagen_principal': 'Imagen Principal *', 'pie_imagen': 'Descripción de la Imagen',
            'fecha_publicacion': 'Fecha de Publicación',
            'publicada': '¿Publicar ahora?', 'destacada': '¿Noticia destacada?'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['fecha_publicacion'].initial = timezone.now()

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 10:
            raise forms.ValidationError('El título debe tener al menos 10 caracteres')
        return titulo

    def clean_imagen_principal(self):
        imagen = self.cleaned_data.get('imagen_principal')
        if imagen:
            if hasattr(imagen, 'size') and imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no puede ser mayor a 5MB')
            if hasattr(imagen, 'content_type') and not imagen.content_type.startswith('image/'):
                raise forms.ValidationError('El archivo debe ser una imagen')
        return imagen


class CategoriaNoticiaForm(forms.ModelForm):
    class Meta:
        model = CategoriaNoticia
        fields = ['nombre', 'descripcion', 'color', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ImagenNoticiaForm(forms.ModelForm):
    class Meta:
        model = ImagenNoticia
        fields = ['imagen', 'descripcion', 'orden']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la imagen'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
from .models import TipoEstablecimiento  # ajusta el modelo según corresponda

class TipoEstablecimientoForm(forms.ModelForm):
    class Meta:
        model = TipoEstablecimiento
        fields = '__all__'


#google

class CompletarPerfilGoogleForm(forms.Form):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de nacimiento'
    )
    telefono = forms.CharField(
        max_length=20,
        label='Teléfono'
    )
    direccion = forms.CharField(
        max_length=255,
        label='Dirección'
    )
    identificacion = forms.CharField(
        max_length=50,
        label='Número de identificación'
    )