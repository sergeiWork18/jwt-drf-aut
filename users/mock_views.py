from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Импорт кастомных разрешений
from .permissions import IsAdminOrManager

# Mock данные для бизнес-объектов
MOCK_ARTICLES = [
    {"id": 1, "title": "Статья 1", "author": "admin@example.com", "status": "published"},
    {"id": 2, "title": "Статья 2", "author": "user1@example.com", "status": "draft"},
    {"id": 3, "title": "Статья 3", "author": "manager1@example.com", "status": "published"}
]

MOCK_COMMENTS = [
    {"id": 1, "article_id": 1, "author": "user1@example.com", "text": "Комментарий 1"},
    {"id": 2, "article_id": 1, "author": "manager1@example.com", "text": "Комментарий 2"},
    {"id": 3, "article_id": 2, "author": "admin@example.com", "text": "Комментарий 3"},
]


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Список статей',
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'author': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        ),
        401: 'Не авторизован'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_articles(request):
    """Получение списка статей (доступно всем авторизованным)"""
    return Response(MOCK_ARTICLES)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            'Список комментариев',
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'article_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'author': openapi.Schema(type=openapi.TYPE_STRING),
                        'text': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        ),
        401: 'Не авторизован'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_comments(request):
    """Получение списка комментариев (доступно всем авторизованным)"""
    return Response(MOCK_COMMENTS)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'content': openapi.Schema(type=openapi.TYPE_STRING)
        },
        required=['title']
    ),
    responses={
        201: 'Статья создана',
        401: 'Не авторизован',
        403: 'Доступ запрещен'
    }
)
@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def create_article(request):
    """Создание статьи (доступно только пользователям с ролью admin или manager)"""
    user = request.user
    
    # Генерация уникального ID для новой статьи
    new_id = max(article['id'] for article in MOCK_ARTICLES) + 1 if MOCK_ARTICLES else 1
    article = {
        "id": new_id,
        "title": request.data.get('title'),
        "author": user.email,
        "status": "draft"
    }
    # Добавляем статью в начало списка
    MOCK_ARTICLES.insert(0, article)
    return Response(article, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'article_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'text': openapi.Schema(type=openapi.TYPE_STRING)
        },
        required=['article_id', 'text']
    ),
    responses={
        201: 'Комментарий создан',
        401: 'Не авторизован',
        403: 'Доступ запрещен'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request):
    """Создание комментария (доступно всем авторизованным пользователям)"""
    article_id = request.data.get('article_id')
    
    # Проверка на существование статьи
    if not any(article['id'] == article_id for article in MOCK_ARTICLES):
        return Response(
            {'error': f'Статья с id {article_id} не существует'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
    comment = {
        "id": len(MOCK_COMMENTS) + 1,
        "article_id": article_id,
        "author": request.user.email,
        "text": request.data.get('text')
    }
    MOCK_COMMENTS.append(comment)
    return Response(comment, status=status.HTTP_201_CREATED)
