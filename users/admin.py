from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, Permission, RolePermission, UserRole


class UserAdmin(BaseUserAdmin):
    """
    Админка для модели User с отображением всех пользователей (включая удаленных)
    """
    # Поля, отображаемые в списке пользователей
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_deleted', 'created_at')
    
    # Поля, по которым можно фильтровать
    list_filter = ('is_active', 'is_deleted', 'created_at', 'is_staff', 'is_superuser')
    
    # Поля, по которым можно искать
    search_fields = ('email', 'first_name', 'last_name')
    
    # Порядок сортировки
    ordering = ('email',)
    
    # Поля, отображаемые при редактировании
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'middle_name'),
            'classes': ('wide',),
        }),
        (_('Статус'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_deleted', 'deleted_at'),
        }),
        (_('Группы и права'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Даты'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Поля для создания нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'middle_name'),
        }),
    )
    
    # Только для чтения (не редактируется)
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'deleted_at')
    
    def get_queryset(self, request):
        """
        Переопределяем queryset для отображения ВСЕХ пользователей,
        включая удаленных (is_deleted=True)
        """
        return User.all_objects.all()
    
    def save_model(self, request, obj, form, change):
        """Сохранение модели с обработкой пароля"""
        if not change:  # Новый пользователь
            # Пароль уже установлен через password1/password2 в add_fieldsets
            pass
        obj.save()


# Регистрируем модель с кастомной админкой
admin.site.register(User, UserAdmin)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Админка для ролей"""
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Статус', {'fields': ('is_active',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Админка для прав доступа"""
    list_display = ('action', 'resource', 'is_active', 'created_at')
    list_filter = ('action', 'is_active')
    search_fields = ('resource', 'description')
    fieldsets = (
        (None, {'fields': ('action', 'resource', 'description')}),
        ('Статус', {'fields': ('is_active',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Админка для связей ролей и прав"""
    list_display = ('role', 'permission', 'granted_at')
    list_filter = ('role', 'permission')
    search_fields = ('role__name', 'permission__resource')
    autocomplete_fields = ('role', 'permission')
    readonly_fields = ('granted_at',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Админка для связей пользователей и ролей"""
    list_display = ('user', 'role', 'assigned_at', 'assigned_by')
    list_filter = ('role',)
    search_fields = ('user__email', 'role__name')
    # autocomplete_fields = ('user', 'role', 'assigned_by')
    readonly_fields = ('assigned_at',)