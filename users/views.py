from .decorators import swagger_with_auth, swagger_public
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, logout
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer, 
    UserListSerializer
)
from .models import User
from drf_yasg import openapi

@swagger_public('post', UserRegistrationSerializer, {
    201: UserProfileSerializer,
    400: "Ошибка валидации"
})
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.save()
    return _get_user_response(user)


@swagger_public('post', UserLoginSerializer, {
    200: UserProfileSerializer,
    401: "Неверные учетные данные",
    403: "Учетная запись деактивирована"
})
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(email=email)
        
        if not user.check_password(password):
            return Response(
                {'error': 'Неверные учетные данные'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active or user.is_deleted:
            return Response(
                {'error': 'Учетная запись деактивирована'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Неверные учетные данные'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    return _get_user_response(user)


@swagger_with_auth('post', openapi.Schema(  # Вместо None
    type=openapi.TYPE_OBJECT,
    required=['refresh'],
    properties={
        'refresh': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Refresh token"
        )
    }
), {
    200: "Successfully logged out",
    400: "Refresh token required / Invalid token"
})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RefreshToken(refresh_token)
        try:
            token.blacklist()
        except AttributeError:
            pass  # blacklisting не поддерживается, если не установлен blacklist app
    except Exception as e:
        return Response(
            {'error': f'Invalid token: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logout(request)
    return Response({'message': 'Successfully logged out'})


@swagger_with_auth('put', UserProfileSerializer, {
    200: UserProfileSerializer,
    400: "Ошибка валидации"
})
@swagger_with_auth('patch', UserProfileSerializer, {
    200: UserProfileSerializer,
    400: "Ошибка валидации"
})
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserProfileSerializer(
        request.user, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response({
        'user': serializer.data
    })


@swagger_with_auth('delete', None, {
    200: "Account successfully deleted"
})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_view(request):  # Renamed to avoid conflict
    """Мягкое удаление профиля"""
    user = request.user
    
    user.is_active = False
    user.is_deleted = True
    user.save(update_fields=['is_active', 'is_deleted'])
    
    refresh_token = request.data.get('refresh')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            # token.blacklist() # Отключен из-за отсутствия blacklist в библиотеке
        except (TokenError, AttributeError):
            pass  # Пропускаем ошибки, как раньше
    
    logout(request)
    return Response({'message': 'Account successfully deleted'})


def _get_user_response(user):
    """Возвращает ответ с данными пользователя и токенами"""
    refresh = RefreshToken.for_user(user)
    tokens = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    return Response({
        'user': UserProfileSerializer(user).data,
        'tokens': tokens
    })