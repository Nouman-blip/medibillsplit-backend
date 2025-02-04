 #notifications/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from views import NotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('notifications/preferences/', 
         NotificationViewSet.as_view({'get': 'preferences', 'put': 'preferences'}),
         name='notification-preferences'),
] + router.urls