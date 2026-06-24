from rest_framework import serializers
from .models import Roles, TipoEstablecimiento, Usuario, Establecimiento


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = "__all__"


class TipoEstablecimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEstablecimiento
        fields = "__all__"


class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(), source="rol", write_only=True
    )
    tipo_establecimiento = TipoEstablecimientoSerializer(read_only=True)
    tipo_establecimiento_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoEstablecimiento.objects.all(),
        source="tipo_establecimiento",
        write_only=True,
        required=False
    )

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "nombre_completo", "telefono", "profesion",
            "identificacion", "fecha_nacimiento", "direccion", "imagen_perfil",
            "rol", "rol_id", "tipo_establecimiento", "tipo_establecimiento_id", "is_active",
        ]


class EstablecimientoSerializer(serializers.ModelSerializer):
    empresario = UsuarioSerializer(read_only=True)
    empresario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source="empresario",
        write_only=True,
        required=False
    )
    tipo = TipoEstablecimientoSerializer(read_only=True)
    tipo_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoEstablecimiento.objects.all(),
        source="tipo",
        write_only=True,
        required=False
    )
    imagen_display = serializers.SerializerMethodField()

    class Meta:
        model = Establecimiento
        fields = [
            "id", "nombre", "descripcion", "horario_aten", "direccion",
            "imagen", "imagen_url", "imagen_display", "url_mas_info",
            "fecha_creacion", "activo",
            "tipo", "tipo_id",
            "empresario", "empresario_id",
        ]

    def get_imagen_display(self, obj):
        return obj.get_imagen_url()