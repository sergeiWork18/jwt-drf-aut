# Схема базы данных для системы аутентификации и авторизации

## Описание

Схема реализует систему аутентификации и авторизации с поддержкой ролей, прав доступа и мягкого удаления пользователей. Используется модель RBAC (Role-Based Access Control) с возможностью гибкой настройки прав на уровне ресурсов.

## Таблицы

### 1. Пользователи (users)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_users_email ON users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_active ON users(is_active) WHERE is_deleted = FALSE;
```

### 2. Роли (roles)

```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Стандартные роли
-- INSERT INTO roles(name, description) VALUES ('admin', 'Администратор системы');
-- INSERT INTO roles(name, description) VALUES ('user', 'Обычный пользователь');
-- INSERT INTO roles(name, description) VALUES ('manager', 'Менеджер');
```

### 3. Права доступа (permissions)

```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'read', 'update', 'delete')), -- Тип действия
    resource VARCHAR(100) NOT NULL, -- Ресурс (например, 'Article', 'Comment')
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(action, resource)
);

-- Примеры прав
-- INSERT INTO permissions(action, resource, description) VALUES ('create', 'Article', 'Создание статей');
-- INSERT INTO permissions(action, resource, description) VALUES ('read', 'Article', 'Чтение статей');
-- INSERT INTO permissions(action, resource, description) VALUES ('update', 'Article', 'Редактирование статей');
-- INSERT INTO permissions(action, resource, description) VALUES ('delete', 'Article', 'Удаление статей');
```

### 4. Связь Ролей и Прав (role_permissions)

```sql
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- Индекс для быстрого поиска прав по роли
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
```

### 5. Связь Пользователей и Ролей (user_roles)

```sql
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id), -- Кто назначил роль
    PRIMARY KEY (user_id, role_id)
);

-- Индекс для быстрого поиска ролей по пользователю
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
```

## Логика работы системы прав

1. **Аутентификация**: Пользователь вводит email и пароль. Система проверяет наличие активного пользователя с таким email и правильность хэша пароля.

2. **Авторизация**: При попытке доступа к ресурсу система:
   - Находит все роли пользователя
   - Находит все права, связанные с этими ролями
   - Проверяет, есть ли у пользователя право на нужное действие (action) для конкретного ресурса (resource)

3. **Гибкость**: Можно создавать новые ресурсы и действия без изменения структуры таблиц. Например, добавить права для ресурса "Comment".

4. **Мягкое удаление**: Пользователь помечается как удаленный (is_deleted = TRUE), но его данные остаются в БД. Это позволяет сохранять историю действий и легко восстанавливать аккаунты.

5. **Нормализация**: Данные разделены на логические сущности без дублирования. Связи реализованы через промежуточные таблицы.

## Тестовые данные (fixtures)

```sql
-- Создание прав
INSERT INTO permissions(action, resource, description) VALUES 
('create', 'Article', 'Создание статей'),
('read', 'Article', 'Чтение статей'),
('update', 'Article', 'Редактирование статей'),
('delete', 'Article', 'Удаление статей'),
('create', 'Comment', 'Создание комментариев'),
('read', 'Comment', 'Чтение комментариев'),
('update', 'Comment', 'Редактирование комментариев'),
('delete', 'Comment', 'Удаление комментариев');

-- Создание ролей
INSERT INTO roles(name, description) VALUES 
('admin', 'Администратор системы'),
('user', 'Обычный пользователь'),
('manager', 'Менеджер');

-- Назначение прав ролям
-- Админ имеет все права
INSERT INTO role_permissions(role_id, permission_id)
SELECT 1, id FROM permissions;

-- Менеджер может создавать, читать и обновлять статьи и комментарии, но не может удалять
INSERT INTO role_permissions(role_id, permission_id)
SELECT 3, id FROM permissions WHERE action IN ('create', 'read', 'update');

-- Обычный пользователь может читать статьи и создавать/читать комментарии
INSERT INTO role_permissions(role_id, permission_id)
SELECT 2, id FROM permissions WHERE (resource = 'Article' AND action = 'read') 
   OR (resource = 'Comment' AND action IN ('create', 'read'));

-- Создание пользователей
-- Хэши паролей условные, в реальности должны генерироваться bcrypt/scrypt
INSERT INTO users(email, password_hash, first_name, last_name, is_active) VALUES 
('admin@example.com', 'hashed_password_admin', 'Админ', 'Админов', TRUE),
('user1@example.com', 'hashed_password_user1', 'Иван', 'Иванов', TRUE),
('manager1@example.com', 'hashed_password_manager1', 'Петр', 'Петров', TRUE),
('deleted_user@example.com', 'hashed_password_deleted', 'Удаленный', 'Пользователь', FALSE);

-- Помечаем последнего пользователя как удаленного
UPDATE users SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP WHERE email = 'deleted_user@example.com';

-- Назначение ролей пользователям
INSERT INTO user_roles(user_id, role_id, assigned_at, assigned_by) VALUES 
-- Админ
((SELECT id FROM users WHERE email = 'admin@example.com'), (SELECT id FROM roles WHERE name = 'admin'), CURRENT_TIMESTAMP, NULL),
-- Обычный пользователь
((SELECT id FROM users WHERE email = 'user1@example.com'), (SELECT id FROM roles WHERE name = 'user'), CURRENT_TIMESTAMP, NULL),
-- Менеджер
((SELECT id FROM users WHERE email = 'manager1@example.com'), (SELECT id FROM roles WHERE name = 'manager'), CURRENT_TIMESTAMP, NULL);
```

## Django Models (альтернативное представление)

```python
from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.password:
            self.password_hash = make_password(self.password)
            self.password = None  # Удаляем из памяти
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'users'


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'


class Permission(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
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


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_users')

    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
```
