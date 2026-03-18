from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from functools import wraps

def swagger_with_auth(method, request_body=None, responses=None):
    """
    Универсальный декоратор для swagger документации с JWT авторизацией
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        
        # Базовый параметр авторизации
        manual_params = [
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <access_token>",
                type=openapi.TYPE_STRING,
                default="Bearer ",
                required=True
            )
        ]
        
        # Добавляем Bearer для авторизации в swagger UI
        security = [{"Bearer": []}]
        
        # Стандартные responses
        default_responses = {
            401: "Не авторизован",
            403: "Доступ запрещен",
            500: "Внутренняя ошибка сервера"
        }
        if responses:
            default_responses.update(responses)
        
        return swagger_auto_schema(
            method=method,
            request_body=request_body,
            manual_parameters=manual_params,
            responses=default_responses,
            security=security
        )(wrapper)
    
    return decorator


def swagger_public(method, request_body=None, responses=None):
    """
    Декоратор для публичных эндпоинтов (без авторизации)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        
        default_responses = {
            400: "Ошибка валидации",
            500: "Внутренняя ошибка сервера"
        }
        if responses:
            default_responses.update(responses)
        
        return swagger_auto_schema(
            method=method,
            request_body=request_body,
            responses=default_responses
        )(wrapper)
    
    return decorator