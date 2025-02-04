# notifications/models.py
from django.db import models
from accounts.models import Member

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('PAYMENT', 'Payment Update'),
        ('DISPUTE', 'Dispute Update'),
        ('INSURANCE', 'Insurance Change'),
        ('SYSTEM', 'System Alert'),
        ('BILL', 'New Bill'),
    ]

    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'), 
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='MEDIUM'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.URLField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['member', 'is_read']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.member}"