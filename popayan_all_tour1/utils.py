# popayan_all_tour1/utils.py
from django.apps import apps
from django import forms


def get_modelo(tipo):
    """Obtiene el modelo correspondiente según el tipo de establecimiento"""
    
    # Normalizar: convertir a minúscula y quitar 's' si existe
    tipo_normalizado = tipo.lower().rstrip('s')
    
    modelos = {
        'hotel': 'Hotel',
        'restaurante': 'Restaurante',
        'museo': 'Museos',
        'iglesia': 'Iglesias',
    }
    
    if tipo_normalizado not in modelos:
        raise ValueError(f"Tipo de establecimiento no válido: {tipo}")

    # Obtener la clase del modelo
    Modelo = apps.get_model('popayan_all_tour1', modelos[tipo_normalizado])

    if Modelo is None:
        raise LookupError(f"No se encontró el modelo '{modelos[tipo_normalizado]}' en la app 'popayan_all_tour1'.")

    return Modelo


def get_establecimiento_form(tipo):
    """Genera un formulario dinámico para cualquier tipo de establecimiento"""
    try:
        modelo = get_modelo(tipo)
    except ValueError:
        class DummyForm(forms.Form):
            pass
        return DummyForm

    class EstablecimientoForm(forms.ModelForm):
        class Meta:
            model = modelo
            fields = ['nombre', 'descripcion', 'horario_aten', 'direccion', 'imagen', 'url_mas_info']
            widgets = {
                'nombre': forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'Ingrese el nombre del {tipo}'
                }),
                'descripcion': forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': f'Descripción detallada del {tipo}'
                }),
                'horario_aten': forms.TextInput(attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': f'Horario de atención del {tipo}'
                }),
                'direccion': forms.TextInput(attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': f'Direccion del {tipo}'
                }),
                'imagen': forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }),
                'url_mas_info': forms.URLInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'https://ejemplo.com'
                })
            }

    return EstablecimientoForm