from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'middle_name')
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)  # Хеширование пароля
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа пользователя (только данные)
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя (только публичные поля)
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'middle_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'email', 'created_at', 'updated_at')


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка пользователей
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'created_at')
        read_only_fields = fields

    def get_full_name(self, obj):
        """Собирает полное имя пользователя"""
        parts = filter(None, [obj.last_name, obj.first_name, obj.middle_name])
        return ' '.join(parts) if parts else obj.email