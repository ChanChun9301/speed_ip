from .models import TrafficLog
import time
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse

class TrafficMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        duration = time.time() - request.start_time
        # Log the request info and response time to the database
        TrafficLog.objects.create(
            method=request.method,
            path=request.path,
            duration=duration
        )
        return response

class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = reverse('login')  # Или reverse('register')
        self.allowed_paths = [self.login_url, reverse('register'), reverse('admin:login')] # Разрешенные пути

    def __call__(self, request):
        if not request.user.is_authenticated and request.path_info not in self.allowed_paths:
            return redirect(self.login_url)
        response = self.get_response(request)
        return response