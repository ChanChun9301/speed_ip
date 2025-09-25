import logging
import time
from django.shortcuts import redirect
from django.urls import reverse
from .models import TrafficLog

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)


class TrafficMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - getattr(request, 'start_time', time.time())
        try:
            TrafficLog.objects.create(
                method=request.method,
                path=request.path,
                duration=duration
            )
        except Exception as e:
            logger.error(f"Ошибка при логировании трафика: {e}")
        return response


class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('login')
        allowed_paths = [login_url, reverse('register'), reverse('admin:login')]
        if not request.user.is_authenticated and request.path_info not in allowed_paths:
            return redirect(login_url)
        return self.get_response(request)
