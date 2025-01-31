# insurance/calculators.py
from django.utils import timezone

from accounts.models import Member
from .models import InsuranceProfile, Coverage, NetworkProvider

class InsuranceCalculator:
    def __init__(self, member_id, service_type, provider_npi, 
                 service_date, billed_amount):
        self.member_id = member_id
        self.service_type = service_type
        self.provider_npi = provider_npi
        self.service_date = service_date
        self.billed_amount = billed_amount
        self._member = None
        self._policies = None
        self._provider_network_status = {}

    def calculate(self):
        self._validate_inputs()
        coverage_results = []
        remaining_amount = self.billed_amount
        
        for policy in self._get_ordered_policies():
            if remaining_amount <= 0:
                break
                
            policy_coverage = self._calculate_policy_coverage(policy, 
                                                              remaining_amount)
            coverage_results.append(policy_coverage)
            remaining_amount -= policy_coverage['covered_amount']
            
        return {
            'total_billed': self.billed_amount,
            'coverages': coverage_results,
            'patient_responsibility': remaining_amount
        }

    def _get_ordered_policies(self):
        return self._member.insurance_profiles.filter(
            effective_date__lte=self.service_date,
            expiration_date__gte=self.service_date
        ).order_by('-is_primary', 'effective_date')

  
    def _calculate_policy_coverage(self, policy, remaining_amount):
        network_status = self._get_network_status(policy)
        
        # Find matching coverage - exact match or category fallback
        coverage = self._find_best_coverage(policy, network_status)
        
        if not coverage:
            return self._empty_coverage_result(policy)

        # Track amounts
        patient_responsibility = 0
        insurance_paid = 0
        
        # 1. Apply Deductible
        deductible_applied = min(
            max(policy.deductible - policy.yearly_accumulated, 0),
            remaining_amount
        )
        remaining_after_deductible = remaining_amount - deductible_applied
        
        # 2. Apply Copay if exists
        if coverage.copay_amount and coverage.copay_amount > 0:
            copay_applied = min(coverage.copay_amount, remaining_after_deductible)
            patient_responsibility += copay_applied
            remaining_after_copay = remaining_after_deductible - copay_applied
        else:
            copay_applied = 0
            remaining_after_copay = remaining_after_deductible

        # 3. Apply Coinsurance
        if coverage.coverage_percentage and remaining_after_copay > 0:
            insurance_share = remaining_after_copay * (coverage.coverage_percentage / 100)
            patient_share = remaining_after_copay - insurance_share
            
            # 4. Apply OOP Max
            potential_total = (
                policy.yearly_accumulated + 
                deductible_applied +
                patient_share
            )
            
            if potential_total > policy.out_of_pocket_max:
                patient_share = max(
                    policy.out_of_pocket_max - 
                    policy.yearly_accumulated - 
                    deductible_applied, 
                    0
                )
                insurance_share = remaining_after_copay - patient_share
            
            patient_responsibility += patient_share
            insurance_paid = deductible_applied + insurance_share
        else:
            insurance_paid = deductible_applied
            patient_responsibility += remaining_after_copay

        total_covered = deductible_applied + (insurance_paid - 
                                              deductible_applied)
        
        return {
            'policy_id': policy.id,
            'provider_name': policy.provider_name,
            'network_status': network_status,
            'deductible_applied': deductible_applied,
            'copay_applied': copay_applied,
            'coinsurance_applied': insurance_paid - deductible_applied,
            'patient_responsibility': patient_responsibility,
            'total_covered': total_covered,
            'remaining_deductible': max(policy.deductible - 
                                        (policy.yearly_accumulated +
                                          deductible_applied), 0)
        }

    def _find_best_coverage(self, policy, network_status):
        """Find best matching coverage with fallback logic"""
        # Try exact service type match
        coverage = Coverage.objects.filter(
            insurance_profile=policy,
            service_type=self.service_type,
            network_tier=network_status
        ).first()

        # Try category match
        if not coverage and self.service_category:
            coverage = Coverage.objects.filter(
                insurance_profile=policy,
                service_category=self.service_category,
                network_tier=network_status
            ).first()

        # Try general fallback
        if not coverage:
            coverage = Coverage.objects.filter(
                insurance_profile=policy,
                service_category='GENERAL',
                network_tier=network_status
            ).first()

        return coverage
    def _get_network_status(self, policy):
        if policy.id not in self._provider_network_status:
            self._provider_network_status[policy.id] = NetworkProvider.objects.filter(
                insurance_profile=policy,
                provider_npi=self.provider_npi,
                contract_start__lte=self.service_date,
                contract_end__gte=self.service_date
            ).first().network_status if NetworkProvider.objects.filter(
                insurance_profile=policy,
                provider_npi=self.provider_npi
            ).exists() else 'OUT'
        return self._provider_network_status[policy.id]

    def _validate_inputs(self):
        self._member = Member.objects.get(id=self.member_id)
        if not self._member.insurance_profiles.exists():
            raise ValueError("Member has no active insurance policies")
            
        if self.service_date > timezone.now().date():
            raise ValueError("Service date cannot be in the future")

    def _empty_coverage_result(self, policy):
        return {
            'policy_id': policy.id,
            'provider_name': policy.provider_name,
            'network_status': 'OUT',
            'deductible_applied': 0,
            'coinsurance_applied': 0,
            'covered_amount': 0,
            'remaining_deductible': policy.deductible - policy.yearly_accumulated
        }