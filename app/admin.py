from django.contrib import admin
from .models import *

@admin.register(SpeedTestResult)
class SpeedTestResultAdmin(admin.ModelAdmin):
    list_display = ('ip_address','destination_ip', 'ping_ms', 'download_speed_kbps', 'upload_speed_kbps', 'timestamp')
    list_filter = ('timestamp', 'ip_address')
    search_fields = ('ip_address',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

    fieldsets = (
        ('Информация об IP-адресе', {
            'fields': ('ip_address','destination_ip',)
        }),
        ('Результаты теста скорости', {
            'fields': ('ping_ms', 'download_speed_kbps', 'upload_speed_kbps')
        }),
        ('Временная информация', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('full_query', 'search_date', 'results_count')
    list_filter = ('search_date','dork_command',)
    search_fields = ('text_input', 'dork_command', 'full_query')
    date_hierarchy = 'search_date'
    readonly_fields = ('search_date', 'full_query')
    ordering = ('-search_date',)

    fieldsets = (
        ('Информация о поисковом запросе', {
            'fields': ('text_input', 'dork_command')
        }),
        ('Полный поисковый запрос', {
            'fields': ('full_query',)
        }),
        ('Информация о времени', {
            'fields': ('search_date',)
        }),
        ('Дополнительная информация', {
            'fields': ('results_count',)
        }),
    )

admin.site.register(Commands)
admin.site.register(TrafficLog)
