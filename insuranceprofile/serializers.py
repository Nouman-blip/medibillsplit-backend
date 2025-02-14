# insurance/serializers.py
from rest_framework import serializers

from accounts.models import Member
from .models import InsuranceProfile, Coverage, NetworkProvider

class NetworkProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkProvider
        fields = [
            'provider_npi', 'network_status',
            'contract_start', 'contract_end'
        ]

class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = [
            'service_type', 'coverage_percentage',
            'copay_amount', 'requires_preauth', 'network_tier'
        ]

class InsuranceProfileSerializer(serializers.ModelSerializer):
    coverages = CoverageSerializer(many=True, required=False)
    network_providers = NetworkProviderSerializer(many=True, required=False)

    class Meta:
        model = InsuranceProfile
        fields = [
            'id', 'provider_name', 'policy_number',
            'effective_date', 'expiration_date',
            'insurance_type', 'is_primary',
            'deductible', 'out_of_pocket_max',
            'yearly_accumulated', 'coverages',
            'network_providers'
        ]
        read_only_fields = ['yearly_accumulated']

    def validate(self, data):
        if data['effective_date'] > data['expiration_date']:
            raise serializers.ValidationError(
                "Expiration date must be after effective date"
            )
        return data

class CoverageCalculationSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
    billed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    service_type = serializers.ChoiceField(
        max_lenght=255
    )
    service_category=serializers.CharField(
        choices=Coverage.service_category,
        required=False
    )
    provider_npi = serializers.CharField(max_length=15)
    service_date = serializers.DateField()

    def validate_member_id(self, value):
        if not Member.objects.filter(id=value).exists():
            raise serializers.ValidationError("Member does not exist")
        return value