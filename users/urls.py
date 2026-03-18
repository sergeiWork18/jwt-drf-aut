from django.urls import path
from . import views, mock_views

urlpatterns = [
    # Mock бизнес-объекты
    path('api/articles/', mock_views.list_articles, name='list_articles'),
    path('api/articles/create/', mock_views.create_article, name='create_article'),
    path('api/comments/', mock_views.list_comments, name='list_comments'),
    path('api/comments/create/', mock_views.create_comment, name='create_comment'),

    # Аутентификация
    path('api/auth/register/', views.register, name='register'),
    path('api/auth/login/', views.login, name='login'),
    path('api/auth/logout/', views.logout_view, name='logout'),
    
    # Управление профилем
    path('api/users/profile/', views.update_profile, name='update_profile'),
    path('api/users/profile/', views.get_profile, name='get_profile'),  # Добавлен эндпоинт для GET
    path('api/users/profile/delete/', views.delete_profile_view, name='delete_profile'),
    

]