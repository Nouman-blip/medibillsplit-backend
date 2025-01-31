# notifications/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationPreferencesSerializer
)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            member__primary_account__user=self.request.user
        )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'All notifications marked read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked read'})

    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        member = request.user.member
        if request.method == 'GET':
            serializer = NotificationPreferencesSerializer(member.notification_prefs)
            return Response(serializer.data)
        
        serializer = NotificationPreferencesSerializer(
            data=request.data,
            context={'member': member}
        )
        if serializer.is_valid():
            member.notification_prefs = serializer.validated_data
            member.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)