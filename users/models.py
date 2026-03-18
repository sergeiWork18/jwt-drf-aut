from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели User"""
    
    def get_queryset(self):
        """Исключаем удаленных по умолчанию"""
        return super().get_queryset().filter(is_deleted=False)
    
    def all_with_deleted(self):
        """Все пользователи включая удаленных"""
        return super().get_queryset()
    
    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email обязателен')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user'
    )
    """Кастомная модель пользователя"""
    
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    
    # Флаги состояния
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Менеджеры
    objects = UserManager()
    all_objects = models.Manager()  # Стандартный менеджер для админки
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email и password уже требуются
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]

    
    def __str__(self):
        return self.email
    
    def delete(self, using=None, keep_parents=False):
        """Мягкое удаление"""
        if self.is_deleted:
            return
        
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    
    def hard_delete(self, using=None, keep_parents=False):
        """Жесткое удаление"""
        super().delete(using, keep_parents)
    
    def restore(self):
        """Восстановление"""
        if not self.is_deleted:
            return
        
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    
    @property
    def full_name(self):
        """Полное имя"""
        parts = filter(None, [self.last_name, self.first_name, self.middle_name])
        return ' '.join(parts) or self.email
    
    def has_permission(self, action, resource):
        """
        Проверка наличия у пользователя права на действие с ресурсом
        """
        from django.db import models
        
        return self.user_roles.filter(
            role__role_permissions__permission__action=action,
            role__role_permissions__permission__resource=resource,
            role__role_permissions__permission__is_active=True,
            role__is_active=True
        ).exists()


class Role(models.Model):
    """Роль"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'роль'
        verbose_name_plural = 'роли'
    
    def __str__(self):
        return self.name


class Permission(models.Model):
    """Право доступа"""
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('read', 'Чтение'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('manage', 'Управление'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'permissions'
        unique_together = ['action', 'resource']
        verbose_name = 'право доступа'
        verbose_name_plural = 'права доступа'
    
    def __str__(self):
        return f"{self.get_action_display()} {self.resource}"


class RolePermission(models.Model):
    """Связь роли и права"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
        verbose_name = 'право роли'
        verbose_name_plural = 'права ролей'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission}"


class UserRole(models.Model):
    """Связь пользователя и роли"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='assigned_users'
    )
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        verbose_name = 'роль пользователя'
        verbose_name_plural = 'роли пользователей'
    
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"