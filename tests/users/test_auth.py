from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, Role, Permission, RolePermission, UserRole


class UserAuthTest(APITestCase):
    """Тесты аутентификации"""

    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.profile_url = '/api/users/profile/'

        # Создаем роль и права для тестов
        self.user_role = Role.objects.create(name='user')
        create_perm = Permission.objects.create(action='create', resource='Article')
        read_perm = Permission.objects.create(action='read', resource='Article')
        
        # Назначаем права роли
        RolePermission.objects.create(role=self.user_role, permission=create_perm)
        RolePermission.objects.create(role=self.user_role, permission=read_perm)

        # Создаем пользователя
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Назначаем роль пользователю
        UserRole.objects.create(user=self.user, role=self.user_role)

    def test_register_success(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

    def test_register_password_mismatch(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'wrongpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_login_success(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')

    def test_login_invalid_credentials(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_protected_view(self):
        # Получаем токен
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Устанавливаем заголовок авторизации
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')

    def test_update_profile(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Updated')

    def test_delete_profile(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        data = {'refresh': str(refresh)}
        response = self.client.delete('/api/users/profile/delete/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что пользователь помечен как удаленный
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
