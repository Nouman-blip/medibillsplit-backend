# insurance/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import InsuranceProfileViewSet, CoverageCalculationView

router = DefaultRouter()
router.register(r'profiles', InsuranceProfileViewSet,
                 basename='insurance-profile')

urlpatterns = [
    path('calculate-coverage/', CoverageCalculationView.as_view(),
          name='calculate-coverage'),
] + router.urls