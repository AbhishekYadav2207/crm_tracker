from django.contrib import admin
from .models import AuditLog, Notification

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'table_name', 'timestamp')
    list_filter = ('action_type', 'table_name', 'timestamp')
    search_fields = ('user__username', 'table_name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title')
