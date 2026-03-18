from django.test import TestCase
from users.models import User, Role, Permission, RolePermission, UserRole


class UserModelTest(TestCase):
    """Тесты для модели User"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_deleted)

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser@example.com')

    def test_full_name_property(self):
        self.assertEqual(self.user.full_name, 'User Test')

        # Проверка без middle_name
        user2 = User.objects.create_user(email='user2@example.com', password='pass')
        self.assertEqual(user2.full_name, 'user2@example.com')

    def test_soft_delete(self):
        self.user.delete()
        self.assertTrue(self.user.is_deleted)
        self.assertIsNotNone(self.user.deleted_at)


class RoleModelTest(TestCase):
    """Тесты для модели Role"""

    def setUp(self):
        self.role = Role.objects.create(
            name='test_role',
            description='Test role description'
        )

    def test_role_creation(self):
        self.assertEqual(self.role.name, 'test_role')
        self.assertEqual(self.role.description, 'Test role description')
        self.assertTrue(self.role.is_active)

    def test_role_str(self):
        self.assertEqual(str(self.role), 'test_role')


class PermissionModelTest(TestCase):
    """Тесты для модели Permission"""

    def setUp(self):
        self.permission = Permission.objects.create(
            action='create',
            resource='Article',
            description='Create Article'
        )

    def test_permission_creation(self):
        self.assertEqual(self.permission.action, 'create')
        self.assertEqual(self.permission.resource, 'Article')
        self.assertEqual(self.permission.description, 'Create Article')
        self.assertTrue(self.permission.is_active)

    def test_permission_str(self):
        self.assertEqual(str(self.permission), 'Создание Article')

    def test_unique_constraint(self):
        Permission.objects.create(action='create', resource='Comment')
        with self.assertRaises(Exception):
            Permission.objects.create(action='create', resource='Comment')  # Должно вызвать IntegrityError


class UserRoleTest(TestCase):
    """Тесты для связей пользователей и ролей"""

    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        self.role = Role.objects.create(name='test_role')
        self.user_role = UserRole.objects.create(
            user=self.user,
            role=self.role
        )

    def test_user_role_creation(self):
        self.assertEqual(self.user_role.user, self.user)
        self.assertEqual(self.user_role.role, self.role)
        self.assertIsNotNone(self.user_role.assigned_at)

    def test_str_representation(self):
        self.assertEqual(str(self.user_role), 'user@example.com - test_role')


class RolePermissionTest(TestCase):
    """Тесты для связей ролей и прав"""

    def setUp(self):
        self.role = Role.objects.create(name='test_role')
        self.permission = Permission.objects.create(action='read', resource='Article')
        self.role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

    def test_role_permission_creation(self):
        self.assertEqual(self.role_permission.role, self.role)
        self.assertEqual(self.role_permission.permission, self.permission)
        self.assertIsNotNone(self.role_permission.granted_at)

    def test_str_representation(self):
        self.assertEqual(str(self.role_permission), 'test_role - Чтение Article')
