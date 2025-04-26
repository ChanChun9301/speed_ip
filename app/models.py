from django.db import models
from django.utils import timezone

class SpeedTestResult(models.Model):
    ip_address = models.CharField(max_length=100)
    ping_ms = models.FloatField(null=True, blank=True)
    download_speed_kbps = models.FloatField(null=True, blank=True)
    upload_speed_kbps = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Результат для {self.ip_address} от {self.timestamp}"