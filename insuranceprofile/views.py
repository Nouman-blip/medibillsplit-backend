# insurance/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db import transaction
from .models import InsuranceProfile, Coverage, NetworkProvider
from .serializers import (
    InsuranceProfileSerializer,
    CoverageCalculationSerializer
)
from .calculators import InsuranceCalculator

class InsuranceProfileViewSet(viewsets.ModelViewSet):
    serializer_class = InsuranceProfileSerializer
    queryset = InsuranceProfile.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            member__primary_account__user=self.request.user
        )

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        with transaction.atomic():
            # Clear existing primary
            InsuranceProfile.objects.filter(
                member=self.get_object().member
            ).update(is_primary=False)
            
            # Set new primary
            profile = self.get_object()
            profile.is_primary = True
            profile.save()
            
        return Response({'status': 'primary insurance updated'})

class CoverageCalculationView(APIView):
    """
    Calculate insurance coverage for a medical service
    """
    def post(self, request):
        serializer = CoverageCalculationSerializer(data=request.data)
        if serializer.is_valid():
            calculator = InsuranceCalculator(
                member_id=serializer.validated_data['member_id'],
                service_type=serializer.validated_data['service_type'],
                provider_npi=serializer.validated_data['provider_npi'],
                service_date=serializer.validated_data['service_date'],
                billed_amount=serializer.validated_data['billed_amount']
            )
            
            try:
                result = calculator.calculate()
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)