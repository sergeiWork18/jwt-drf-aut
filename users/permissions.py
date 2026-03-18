from rest_framework import permissions

class HasPermission(permissions.BasePermission):
    """
    Проверка прав пользователя через систему ролей и прав
    """
    def has_permission(self, request, view):
        # Проверяем, авторизован ли пользователь
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Получаем действие и ресурс из view
        action = getattr(view, 'required_action', None)
        resource = getattr(view, 'required_resource', None)
        
        if not action or not resource:
            return False
        
        # Проверяем права пользователя
        return request.user.has_permission(action, resource)


class IsAdminOrManager(permissions.BasePermission):
    """
    Проверка, является ли пользователь администратором или менеджером
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Получаем все роли пользователя
        user_roles = request.user.user_roles.select_related('role').all()
        
        # Проверяем, есть ли среди ролей 'admin' или 'manager'
        role_names = [user_role.role.name for user_role in user_roles]
        return 'admin' in role_names or 'manager' in role_names