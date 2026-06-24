from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializer import UsuarioSerializer, EstablecimientoSerializer
from .models import Establecimiento, TipoEstablecimiento


class AuthViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]  # ← sin SessionAuthentication
    permission_classes = [AllowAny]  # ← login es público

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'message': 'Login exitoso',
                'token': token.key,
                'user': UsuarioSerializer(user).data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Correo o contraseña incorrectos'
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        if request.user.is_authenticated:
            try:
                request.user.auth_token.delete()
            except:
                pass
        return Response({'success': True, 'message': 'Sesión cerrada correctamente'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        if request.user.is_authenticated:
            return Response({'success': True, 'user': UsuarioSerializer(request.user).data})
        return Response({'success': False, 'message': 'No autenticado'},
                        status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data.get('password'))
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'message': 'Registro exitoso',
                'token': token.key,
                'user': UsuarioSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Error de validación',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EstablecimientoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EstablecimientoSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        queryset = Establecimiento.objects.filter(activo=True).select_related('tipo', 'empresario')
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo__nombre__iexact=tipo)
        return queryset.order_by('-fecha_creacion')