from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import cloudinary.uploader
import base64
from django.core.files.base import ContentFile


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_imagen(request):
    """
    Endpoint para subir imagen desde móvil
    Acepta: base64 o multipart/form-data
    
    Uso desde móvil:
    POST /api/upload-imagen/
    Headers: Authorization: Token <token>
    Body (opción 1): {"imagen_base64": "data:image/jpeg;base64,...", "formato": "jpg"}
    Body (opción 2): FormData con campo "imagen"
    """
    try:
        # Opción 1: Imagen en base64
        if 'imagen_base64' in request.data:
            imagen_data = request.data['imagen_base64']
            
            # Si viene con el prefijo data:image/...
            if 'base64,' in imagen_data:
                imagen_data = imagen_data.split('base64,')[1]
            
            formato = request.data.get('formato', 'jpg')
            
            # Decodificar base64
            imagen_decoded = base64.b64decode(imagen_data)
            
            # Subir a Cloudinary
            resultado = cloudinary.uploader.upload(
                ContentFile(imagen_decoded, name=f'temp.{formato}'),
                folder="popayan/uploads",
                resource_type="image"
            )
        
        # Opción 2: Archivo directo (FormData desde móvil)
        elif 'imagen' in request.FILES:
            archivo = request.FILES['imagen']
            
            resultado = cloudinary.uploader.upload(
                archivo,
                folder="popayan/uploads",
                resource_type="image"
            )
        
        else:
            return Response(
                {'error': 'No se envió ninguna imagen. Usa "imagen" o "imagen_base64"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'url': resultado['secure_url'],
            'public_id': resultado['public_id'],
            'width': resultado.get('width'),
            'height': resultado.get('height'),
            'format': resultado.get('format')
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'detail': 'Error al subir imagen a Cloudinary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )