from rest_framework import serializers
from .models import CategoriaNoticia, Noticia, VisitaNoticia, ImagenNoticia


class CategoriaNoticiaSerializer(serializers.ModelSerializer):
    total_noticias = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaNoticia
        fields = ['id', 'nombre', 'slug', 'descripcion', 'color', 'activo', 'total_noticias']
        read_only_fields = ['slug']

    def get_total_noticias(self, obj):
        return obj.noticias.filter(publicada=True).count()


class ImagenNoticiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenNoticia
        fields = ['id', 'imagen', 'descripcion', 'orden']


class NoticiaListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listados (sin contenido completo)."""
    categoria = CategoriaNoticiaSerializer(read_only=True)
    autor_nombre = serializers.CharField(source='autor.nombre_completo', read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Noticia
        fields = [
            'id', 'titulo', 'slug', 'subtitulo', 'resumen',
            'categoria', 'autor_nombre', 'imagen_url', 'pie_imagen',
            'fecha_publicacion', 'fecha_creacion',
            'publicada', 'destacada', 'visitas_totales',
        ]

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen_principal and request:
            return request.build_absolute_uri(obj.imagen_principal.url)
        return None


class NoticiaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de noticia."""
    categoria = CategoriaNoticiaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaNoticia.objects.all(),
        source='categoria',
        write_only=True,
        required=False,
        allow_null=True,
    )
    autor_nombre = serializers.CharField(source='autor.nombre_completo', read_only=True)
    autor_avatar = serializers.SerializerMethodField()
    imagenes_adicionales = ImagenNoticiaSerializer(many=True, read_only=True)
    visitas_unicas = serializers.IntegerField(read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Noticia
        fields = [
            'id', 'titulo', 'slug', 'subtitulo', 'contenido', 'resumen',
            'categoria', 'categoria_id',
            'imagen_principal', 'imagen_url', 'pie_imagen',
            'autor_nombre', 'autor_avatar',
            'fecha_creacion', 'fecha_actualizacion', 'fecha_publicacion',
            'publicada', 'destacada',
            'visitas_totales', 'visitas_unicas',
            'imagenes_adicionales',
        ]
        read_only_fields = ['slug', 'fecha_creacion', 'fecha_actualizacion', 'visitas_totales']

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen_principal and request:
            return request.build_absolute_uri(obj.imagen_principal.url)
        return None

    def get_autor_avatar(self, obj):
        if obj.autor:
            return obj.autor.get_imagen_perfil()
        return None