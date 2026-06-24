from rest_framework import serializers
from .models import Resena, Favorito, Establecimiento, Noticia


# ============================================================
# RESEÑAS
# ============================================================
class ResenaSerializer(serializers.ModelSerializer):
    usuario_nombre  = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    usuario_avatar  = serializers.SerializerMethodField()
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)

    class Meta:
        model = Resena
        fields = [
            'id',
            'establecimiento', 'establecimiento_nombre',
            'usuario_nombre', 'usuario_avatar',
            'calificacion', 'comentario',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def get_usuario_avatar(self, obj):
        return obj.usuario.get_imagen_perfil()

    def validate_calificacion(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('La calificación debe ser entre 1 y 5.')
        return value

    def validate(self, data):
        request = self.context.get('request')
        establecimiento = data.get('establecimiento')
        # ── Una sola reseña por usuario por establecimiento ──
        # Si quieres permitir múltiples, comenta el bloque de abajo:
        if request and establecimiento and not self.instance:
            if Resena.objects.filter(
                usuario=request.user,
                establecimiento=establecimiento
            ).exists():
                raise serializers.ValidationError(
                    'Ya dejaste una reseña en este establecimiento.'
                )
        # ────────────────────────────────────────────────────
        return data


# ============================================================
# FAVORITOS
# ============================================================
class FavoritoSerializer(serializers.ModelSerializer):
    # ── Campos de establecimiento (solo si aplica) ──
    establecimiento_nombre = serializers.SerializerMethodField()
    establecimiento_imagen = serializers.SerializerMethodField()
    establecimiento_tipo   = serializers.SerializerMethodField()

    # ── Campos de noticia (solo si aplica) ──
    noticia_titulo  = serializers.SerializerMethodField()
    noticia_imagen  = serializers.SerializerMethodField()
    noticia_resumen = serializers.SerializerMethodField()

    # ── Tipo de favorito para que el frontend sepa qué es ──
    tipo = serializers.SerializerMethodField()

    class Meta:
        model = Favorito
        fields = [
            'id', 'tipo', 'fecha_guardado',
            # establecimiento
            'establecimiento', 'establecimiento_nombre',
            'establecimiento_imagen', 'establecimiento_tipo',
            # noticia
            'noticia', 'noticia_titulo',
            'noticia_imagen', 'noticia_resumen',
        ]
        read_only_fields = ['fecha_guardado']
        extra_kwargs = {
            'establecimiento': {'required': False, 'allow_null': True},
            'noticia':         {'required': False, 'allow_null': True},
        }

    # ── Getters establecimiento ──────────────────────────
    def get_tipo(self, obj):
        return 'establecimiento' if obj.establecimiento else 'noticia'

    def get_establecimiento_nombre(self, obj):
        return obj.establecimiento.nombre if obj.establecimiento else None

    def get_establecimiento_imagen(self, obj):
        return obj.establecimiento.get_imagen_url() if obj.establecimiento else None

    def get_establecimiento_tipo(self, obj):
        return obj.establecimiento.tipo.nombre if obj.establecimiento else None

    # ── Getters noticia ──────────────────────────────────
    def get_noticia_titulo(self, obj):
        return obj.noticia.titulo if obj.noticia else None

    def get_noticia_imagen(self, obj):
        if not obj.noticia:
            return None
        if obj.noticia.imagen_url:
            return obj.noticia.imagen_url
        if obj.noticia.imagen_principal:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.noticia.imagen_principal.url)
        return None

    def get_noticia_resumen(self, obj):
        return obj.noticia.resumen if obj.noticia else None

    # ── Validaciones ─────────────────────────────────────
    def validate(self, data):
        establecimiento = data.get('establecimiento')
        noticia         = data.get('noticia')
        request         = self.context.get('request')

        # Debe venir exactamente uno
        if not establecimiento and not noticia:
            raise serializers.ValidationError(
                'Debes enviar "establecimiento" o "noticia".'
            )
        if establecimiento and noticia:
            raise serializers.ValidationError(
                'Envía solo "establecimiento" o solo "noticia", no los dos.'
            )

        # No duplicados
        if request and establecimiento:
            if Favorito.objects.filter(
                usuario=request.user, establecimiento=establecimiento
            ).exists():
                raise serializers.ValidationError(
                    'Este establecimiento ya está en tus favoritos.'
                )
        if request and noticia:
            if Favorito.objects.filter(
                usuario=request.user, noticia=noticia
            ).exists():
                raise serializers.ValidationError(
                    'Esta noticia ya está en tus favoritos.'
                )

        return data