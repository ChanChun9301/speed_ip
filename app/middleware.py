from .models import TrafficLog
import time
from django.utils.deprecation import MiddlewareMixin

class TrafficMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    # def process_response(self, request, response):
    #     duration = time.time() - request.start_time
    #     # Log the request info and response time to the database
    #     TrafficLog.objects.create(
    #         method=request.method,
    #         path=request.path,
    #         duration=duration
    #     )
    #     return response