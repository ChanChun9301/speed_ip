from django.contrib import admin
from .models import (
    SearchQuery, ExploitExample, SpeedTestResult, Commands,
    TrafficLog, DorkCategory, DorkTemplate, FavoriteItem,
    PingResult, UserNote, PingCheck
)

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'text_input', 'dork_command', 'search_date')
    search_fields = ('text_input', 'dork_command', 'full_query')


@admin.register(ExploitExample)
class ExploitExampleAdmin(admin.ModelAdmin):
    list_display = ('category', 'exploit_filename', 'url')
    search_fields = ('category', 'description')


@admin.register(SpeedTestResult)
class SpeedTestResultAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'destination_ip', 'ping_ms', 'timestamp')
    search_fields = ('ip_address',)


@admin.register(Commands)
class CommandsAdmin(admin.ModelAdmin):
    list_display = ('command', 'description')
    search_fields = ('command',)


@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'path', 'timestamp')
    search_fields = ('path',)


@admin.register(DorkCategory)
class DorkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(DorkTemplate)
class DorkTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author')
    search_fields = ('title', 'template_text')


@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'dork', 'ip', 'note')
    search_fields = ('ip',)


@admin.register(PingResult)
class PingResultAdmin(admin.ModelAdmin):
    list_display = ('ip', 'status', 'ping_ms', 'timestamp')


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'get_type')

    def get_type(self, obj):
        if obj.speedtest:
            return "SpeedTest"
        if obj.search:
            return "SearchQuery"
        return "—"

admin.site.register(PingCheck)