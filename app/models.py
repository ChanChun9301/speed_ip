from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------- История dork-поиска ----------
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


# ---------- Примеры эксплойтов ----------
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


# ---------- Результаты speedtest ----------
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


# ---------- Команды (dork commands) ----------
class Commands(models.Model):
    command = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.command}: {self.description}"

    class Meta:
        verbose_name = "Buýruk"
        verbose_name_plural = "Buýruklar"


# ---------- Логи сетевого трафика ----------
class TrafficLog(models.Model):
    ip_address = models.CharField(max_length=45, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.IntegerField()
    duration = models.FloatField(help_text="Время в секундах")
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Trafik logy"
        verbose_name_plural = "Trafik loglary"

    def __str__(self):
        return f"{self.ip_address} {self.method} {self.path} [{self.status_code}]"


# ===============================================================
# ---------- Новые модели (расширения проекта) ----------
# ===============================================================

# Категории для команд
class DorkCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# Шаблоны dork-команд
class DorkTemplate(models.Model):
    title = models.CharField(max_length=255)
    template_text = models.CharField(max_length=500)
    category = models.ForeignKey(DorkCategory, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


# Избранное
class FavoriteItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dork = models.ForeignKey(Commands, on_delete=models.CASCADE, null=True, blank=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Избранное ({self.user.username})"


# PING результаты (не speedtest)
class PingResult(models.Model):
    ip = models.CharField(max_length=100)
    ping_ms = models.FloatField(null=True)
    status = models.CharField(max_length=50)  # success / failed
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ping {self.ip}: {self.status}"


# Комментарии к тестам скорости и dork-поискам
class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    speedtest = models.ForeignKey(SpeedTestResult, null=True, blank=True, on_delete=models.CASCADE)
    search = models.ForeignKey(SearchQuery, null=True, blank=True, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заметка {self.user.username}"

class PingCheck(models.Model):
    ip_address = models.CharField(max_length=100)
    status = models.CharField(max_length=20)  # success / fail
    response_ms = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Ping проверка"
        verbose_name_plural = "Ping проверки"

    def __str__(self):
        return f"{self.ip_address} - {self.response_ms} ms ({self.status})"
