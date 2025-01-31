# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'is_read']

class NotificationPreferencesSerializer(serializers.Serializer):
    email = serializers.BooleanField(default=True)
    push = serializers.BooleanField(default=True)
    sms = serializers.BooleanField(default=False)
    types = serializers.MultipleChoiceField(
        choices=Notification.NOTIFICATION_TYPES
    )