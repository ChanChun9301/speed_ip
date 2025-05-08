from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from .views import start_netstat_capture_thread  # Adjust the import
        start_netstat_capture_thread()
