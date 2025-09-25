from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries', null=True)
    text_input = models.CharField(max_length=255)
    dork_command = models.CharField(max_length=255, blank=True, null=True)
    full_query = models.TextField()
    search_date = models.DateTimeField(auto_now_add=True)
    results_count = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Gozleg"
        verbose_name_plural = "Gozlegler"

    def __str__(self):
        return f"{self.full_query} (от {self.user.username if self.user else 'Аноним'})"


class ExploitExample(models.Model):
    category = models.CharField(max_length=255)
    description = models.TextField()
    exploit_filename = models.CharField(max_length=255)
    url = models.URLField()
    
    def __str__(self):
        return f"{self.category}: {self.description[:50]}"

    class Meta:
        verbose_name = "Exploit buýruk"
        verbose_name_plural = "Exploit buýruklar"


class SpeedTestResult(models.Model):
    ip_address = models.CharField(max_length=100)
    destination_ip = models.CharField(max_length=100, null=True, blank=True)
    ping_ms = models.FloatField(null=True, blank=True)
    download_speed_kbps = models.FloatField(null=True, blank=True)
    upload_speed_kbps = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Результат {self.ip_address} от {self.timestamp}"

    class Meta:
        verbose_name = "Tizlik"
        verbose_name_plural = "Tizliklerin netijesi"


class Commands(models.Model):
    command = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.command}: {self.description}"

    class Meta:
        verbose_name = "Buýruk"
        verbose_name_plural = "Buýruklar"


class TrafficLog(models.Model):
    method = models.CharField(max_length=50)
    path = models.CharField(max_length=255)
    duration = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.path} - {self.duration:.2f}s"

    class Meta:
        verbose_name = "Trafika"
        verbose_name_plural = "Trafikalar"
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
