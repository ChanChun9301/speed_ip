from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User  # Import the User model

class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries',null=True)
    text_input = models.CharField(max_length=255)
    dork_command = models.CharField(max_length=255, blank=True, null=True)
    full_query = models.TextField()
    search_date = models.DateTimeField(auto_now_add=True)
    results_count = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name="Gozleg"
        verbose_name_plural="Gozlegler"

    def __str__(self):
        return f"{self.full_query} (by {self.user.username})"
class ExploitDbDork(models.Model):
    category = models.CharField(max_length=255)
    description = models.TextField()
    dork_command = models.CharField(max_length=255, unique=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.category}: {self.dork_command}"

class SpeedTestResult(models.Model):
    ip_address = models.CharField(max_length=100)
    ping_ms = models.FloatField(null=True, blank=True)
    download_speed_kbps = models.FloatField(null=True, blank=True)
    upload_speed_kbps = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Результат для {self.ip_address} от {self.timestamp}"


class Commands(models.Model):
    command = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.command}: {self.description}"

class TrafficLog(models.Model):
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    duration = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.path} - {self.duration:.2f}s"