# billing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Bill, CharityRoundUp, LineItem, BillShare, PaymentHistory, Dispute
from .serializers import (
    BillSerializer, CharityRoundUpSerializer, LineItemSerializer,
    BillShareSerializer, PaymentSerializer,
    DisputeSerializer
)
from .calculators import BillSplitter

class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            primary_account__user=self.request.user
        )

    @action(detail=True, methods=['post'])
    def split(self, request, pk=None):
        bill = self.get_object()
        splitter = BillSplitter(bill)
        try:
            splitter.calculate_shares()
            return Response(
                {"status": "Bill split calculated successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def add_line_item(self, request, pk=None):
        bill = self.get_object()
        serializer = LineItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(bill=bill)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = PaymentHistory.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            bill_share__member__primary_account__user=self.request.user
        )

class DisputeViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeSerializer
    queryset = Dispute.objects.all()

    def perform_create(self, serializer):
        serializer.save(initiator=self.request.user.member)

class CharityViewSet(viewsets.ModelViewSet):
    serializer_class = CharityRoundUpSerializer
    queryset = CharityRoundUp.objects.all()