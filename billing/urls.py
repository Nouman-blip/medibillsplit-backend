# billing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet, PaymentViewSet, DisputeViewSet, CharityViewSet

router = DefaultRouter()
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'disputes', DisputeViewSet, basename='dispute')
router.register(r'charity', CharityViewSet, basename='charity')

urlpatterns = [
    path('', include(router.urls)),
]