from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'CREATE'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('APPROVE', 'APPROVE'),
        ('REJECT', 'REJECT'),
        ('LOGIN', 'LOGIN'),
        ('LOGOUT', 'LOGOUT'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=50, blank=True, null=True)
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.table_name}"

    class Meta:
        ordering = ['-timestamp']

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, blank=True, null=True)
    related_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user}"
