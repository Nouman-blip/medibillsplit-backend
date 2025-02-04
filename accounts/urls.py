# accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PrimaryAccountViewSet,
    RegistrationAPI,
    LoginAPI,
    LogoutAPI
)

router = DefaultRouter()
router.register(r'accounts', PrimaryAccountViewSet, basename='account')

urlpatterns = [
    path('register/', RegistrationAPI.as_view(), name='register'),
    path('login/', LoginAPI.as_view(), name='login'),
    path('logout/', LogoutAPI.as_view(), name='logout'),
    path('', include(router.urls)),
]