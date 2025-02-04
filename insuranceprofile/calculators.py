# insurance/calculators.py
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from accounts.models import Member
from .models import InsuranceProfile, Coverage, NetworkProvider

class InsuranceCalculator:
    """
    Calculates insurance coverage for medical services based on multiple policies
    
    Handles:
    - Deductible calculations
    - Copay and coinsurance
    - Out-of-pocket maximums
    - Network status checks
    - Coordination of benefits between multiple policies
    
    Usage Example:
    --------------
    calculator = InsuranceCalculator(
        member_id=123,
        service_type="MRI",
        provider_npi="1234567890",
        service_date="2024-03-15",
        billed_amount=Decimal("1500.00")
    )
    result = calculator.calculate()
    """
    
    def __init__(self, member_id, service_type, provider_npi, service_date, billed_amount):
        """
        Initialize calculator with claim details
        
        :param member_id: ID of the member receiving service
        :param service_type: Type of medical service (e.g., "MRI", "ER Visit")
        :param provider_npi: National Provider Identifier of service provider
        :param service_date: Date of service (YYYY-MM-DD)
        :param billed_amount: Total amount billed for the service
        """
        self.member_id = member_id
        self.service_type = service_type
        self.provider_npi = provider_npi
        self.service_date = service_date
        self.billed_amount = billed_amount
        self._member = None  # Will be loaded in validation
        self._policies = None  # Will store ordered policies
        self._provider_network_status = {}  # Cache network status per policy

    def calculate(self):
        """
        Main method to calculate insurance coverage
        
        Returns:
            dict: {
                "total_billed": Decimal,
                "coverages": [policy_coverage_details],
                "patient_responsibility": Decimal
            }
            
        Raises:
            ValueError: If invalid input or no active policies
        """
        self._validate_inputs()
        coverage_results = []
        remaining_amount = self.billed_amount
        
        # Process policies in priority order (primary first)
        for policy in self._get_ordered_policies():
            if remaining_amount <= 0:
                break
                
            policy_coverage = self._calculate_policy_coverage(policy, remaining_amount)
            coverage_results.append(policy_coverage)
            remaining_amount -= policy_coverage['total_covered']
            
        return {
            'total_billed': self.billed_amount,
            'coverages': coverage_results,
            'patient_responsibility': remaining_amount
        }

    def _get_ordered_policies(self):
        """
        Get active policies ordered by:
        1. Primary policy first
        2. Effective date (most recent first)
        
        Filters policies active on service date
        """
        return self._member.insurance_profiles.filter(
            effective_date__lte=self.service_date,
            expiration_date__gte=self.service_date
        ).order_by('-is_primary', '-effective_date')

    def _calculate_policy_coverage(self, policy, remaining_amount):
        """
        Calculate coverage for a single policy
        
        Edge Cases Handled:
        - Provider out-of-network
        - Deductible already met
        - OOP max reached
        - No matching coverage rules
        """
        network_status = self._get_network_status(policy)
        coverage = self._find_best_coverage(policy, network_status)
        
        if not coverage:
            return self._empty_coverage_result(policy)

        # Initialize calculation variables
        deductible_applied = Decimal('0.00')
        copay_applied = Decimal('0.00')
        coinsurance_applied = Decimal('0.00')
        patient_responsibility = Decimal('0.00')

        # 1. Apply Deductible
        deductible_available = max(policy.deductible - policy.yearly_accumulated, 0)
        deductible_applied = min(deductible_available, remaining_amount)
        remaining_after_deductible = remaining_amount - deductible_applied

        # 2. Apply Copay
        if coverage.copay_amount and coverage.copay_amount > 0:
            copay_applied = min(coverage.copay_amount, remaining_after_deductible)
            patient_responsibility += copay_applied
            remaining_after_copay = remaining_after_deductible - copay_applied
        else:
            remaining_after_copay = remaining_after_deductible

        # 3. Apply Coinsurance
        if coverage.coverage_percentage and remaining_after_copay > 0:
            insurance_share = remaining_after_copay * (coverage.coverage_percentage / 100)
            patient_share = remaining_after_copay - insurance_share
            
            # 4. Apply Out-of-Pocket Max
            potential_total = policy.yearly_accumulated + deductible_applied + patient_share
            if potential_total > policy.out_of_pocket_max:
                patient_share = max(policy.out_of_pocket_max - 
                                   policy.yearly_accumulated - 
                                   deductible_applied, 0)
                insurance_share = remaining_after_copay - patient_share
            
            coinsurance_applied = insurance_share
            patient_responsibility += patient_share
        else:
            patient_responsibility += remaining_after_copay

        total_covered = deductible_applied + coinsurance_applied
        
        return {
            'policy_id': policy.id,
            'provider_name': policy.provider_name,
            'network_status': network_status,
            'deductible_applied': deductible_applied,
            'copay_applied': copay_applied,
            'coinsurance_applied': coinsurance_applied,
            'patient_responsibility': patient_responsibility,
            'total_covered': total_covered,
            'remaining_deductible': max(policy.deductible - 
                                      (policy.yearly_accumulated + 
                                       deductible_applied), 0)
        }

    def _find_best_coverage(self, policy, network_status):
        """
        Find best matching coverage using fallback logic:
        1. Exact service type match
        2. Service category match
        3. General coverage
        
        Example:
        Service Type: "Advanced MRI" → 
        Fallback to "Diagnostic Services" category → 
        Fallback to General coverage
        """
        # Exact service type match
        coverage = Coverage.objects.filter(
            insurance_profile=policy,
            service_type=self.service_type,
            network_tier=network_status
        ).first()

        # Category match (if service_category provided)
        if not coverage and hasattr(self, 'service_category'):
            coverage = Coverage.objects.filter(
                insurance_profile=policy,
                service_category=self.service_category,
                network_tier=network_status
            ).first()

        # General coverage fallback
        if not coverage:
            coverage = Coverage.objects.filter(
                insurance_profile=policy,
                service_category='GENERAL',
                network_tier=network_status
            ).first()

        return coverage

    def _get_network_status(self, policy):
        """Determine if provider is in-network for this policy"""
        if policy.id not in self._provider_network_status:
            network_provider = NetworkProvider.objects.filter(
                insurance_profile=policy,
                provider_npi=self.provider_npi,
                contract_start__lte=self.service_date,
                contract_end__gte=self.service_date
            ).first()
            
            self._provider_network_status[policy.id] = (
                network_provider.network_status if network_provider else 'OUT'
            )
        return self._provider_network_status[policy.id]

    def _validate_inputs(self):
        """Ensure valid calculation parameters"""
        try:
            self._member = Member.objects.get(id=self.member_id)
        except Member.DoesNotExist:
            raise ValueError("Member does not exist")

        if not self._member.insurance_profiles.exists():
            raise ValueError("Member has no active insurance policies")
            
        if self.service_date > timezone.now().date():
            raise ValueError("Service date cannot be in the future")

        if self.billed_amount <= 0:
            raise ValueError("Billed amount must be positive")

    def _empty_coverage_result(self, policy):
        """Return default result when no coverage found"""
        return {
            'policy_id': policy.id,
            'provider_name': policy.provider_name,
            'network_status': 'OUT',
            'deductible_applied': Decimal('0.00'),
            'copay_applied': Decimal('0.00'),
            'coinsurance_applied': Decimal('0.00'),
            'patient_responsibility': Decimal('0.00'),
            'total_covered': Decimal('0.00'),
            'remaining_deductible': policy.deductible - policy.yearly_accumulated
        }