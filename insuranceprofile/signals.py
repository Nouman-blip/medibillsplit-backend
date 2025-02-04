# insurance/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Coverage
from notifications.models import Notification

@receiver(post_save, sender=Coverage)
def notify_coverage_change(sender, instance, created, **kwargs):
    if not created:
        Notification.objects.create(
            member=instance.insurance_profile.member,
            notification_type='INSURANCE',
            message=f"Your {instance.service_type} coverage changed",
            priority='MEDIUM',
            metadata={
                'coverage_id': instance.id,
                'old_value': instance.tracker.previous('coverage_percentage')
            }
        )