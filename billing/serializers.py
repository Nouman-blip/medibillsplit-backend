# billing/serializers.py
from rest_framework import serializers
from .models import Bill, LineItem, BillShare, PaymentHistory, Dispute, CharityRoundUp

class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = '__all__'
        read_only_fields = ['covered_service']

class BillSerializer(serializers.ModelSerializer):
    line_items = LineItemSerializer(many=True)
    
    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at']

    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        bill = Bill.objects.create(**validated_data)
        for item_data in line_items_data:
            LineItem.objects.create(bill=bill, **item_data)
        return bill

class BillShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillShare
        fields = '__all__'
        read_only_fields = ['original_amount', 'insurance_covered']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = '__all__'
        read_only_fields = ['payment_date']

class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = ['created_at', 'resolved_at']

class CharityRoundUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharityRoundUp
        fields = '__all__'