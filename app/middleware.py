# middleware.py
import logging
import time
from django.urls import reverse
from django.shortcuts import redirect
from .models import TrafficLog

logger = logging.getLogger(__name__)


class TrafficMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Запоминаем время начала
        request._request_start_time = time.time()

        # Получаем ответ
        response = self.get_response(request)

        # Считаем длительность
        duration = time.time() - getattr(request, '_request_start_time', time.time())

        # Определяем IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')

        # User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

        # Статус код
        status_code = response.status_code

        # Сохраняем лог
        try:
            TrafficLog.objects.create(
                ip_address=ip_address,
                method=request.method,
                path=request.path,
                status_code=status_code,
                duration=round(duration, 4),
                user_agent=user_agent[:500],  # обрезаем, если слишком длинный
            )
        except Exception as e:
            logger.error(f"Ошибка при записи лога трафика: {e}")

        return response


# Авторизация — оставляем как есть
class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('login')
        allowed_paths = [
            login_url,
            reverse('register'),
            '/admin/login/',
            '/static/',  # важно — статику пропускать!
            '/media/',
        ]

        # Пропускаем статику и медиа
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        if not request.user.is_authenticated and request.path not in allowed_paths:
            return redirect(login_url + '?next=' + request.path)

        return self.get_response(request)