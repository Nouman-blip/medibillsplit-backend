# insurance/tests.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import Member
from .models import InsuranceProfile, Coverage, NetworkProvider

class InsuranceProfileModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username='testuser', email='test@example.com')
        self.insurance_data = {
            'member': self.member,
            'provider_name': 'Test Provider',
            'policy_number': 'POL123',
            'effective_date': '2023-01-01',
            'expiration_date': '2024-01-01',
            'insurance_type': 'HDHP',
            'is_primary': True,
            'deductible': 1500.00,
            'out_of_pocket_max': 5000.00,
        }

    def test_create_insurance_profile(self):
        insurance_profile = InsuranceProfile.objects.create(**self.insurance_data)
        self.assertEqual(insurance_profile.provider_name, 'Test Provider')
        self.assertEqual(insurance_profile.policy_number, 'POL123')

    def test_yearly_accumulated_default(self):
        data = self.insurance_data.copy()
        del data['yearly_accumulated']
        insurance_profile = InsuranceProfile.objects.create(**data)
        self.assertEqual(insurance_profile.yearly_accumulated, 0.00)

    def test_unique_member_policy_number_constraint(self):
        InsuranceProfile.objects.create(**self.insurance_data)
        with self.assertRaises(IntegrityError):
            InsuranceProfile.objects.create(**self.insurance_data)

    def test_insurance_profile_str(self):
        insurance_profile = InsuranceProfile.objects.create(**self.insurance_data)
        expected_str = f"{insurance_profile.provider_name} ({insurance_profile.get_insurance_type_display()})"
        self.assertEqual(str(insurance_profile), expected_str)

    def test_meta_ordering(self):
        profile1 = InsuranceProfile.objects.create(
            member=self.member,
            provider_name='Provider A',
            policy_number='POL1',
            effective_date='2023-01-01',
            expiration_date='2024-01-01',
            insurance_type='HDHP',
            is_primary=True,
            deductible=1000,
            out_of_pocket_max=3000,
        )
        profile2 = InsuranceProfile.objects.create(
            member=self.member,
            provider_name='Provider B',
            policy_number='POL2',
            effective_date='2022-01-01',
            expiration_date='2023-01-01',
            insurance_type='PPO',
            is_primary=False,
            deductible=500,
            out_of_pocket_max=2000,
        )
        profile3 = InsuranceProfile.objects.create(
            member=self.member,
            provider_name='Provider C',
            policy_number='POL3',
            effective_date='2023-06-01',
            expiration_date='2024-06-01',
            insurance_type='HMO',
            is_primary=True,
            deductible=2000,
            out_of_pocket_max=4000,
        )
        profiles = InsuranceProfile.objects.all()
        self.assertEqual(list(profiles), [profile1, profile3, profile2])


class CoverageModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username='testuser', email='test@example.com')
        self.insurance_profile = InsuranceProfile.objects.create(
            member=self.member,
            provider_name='Test Provider',
            policy_number='POL123',
            effective_date='2023-01-01',
            expiration_date='2024-01-01',
            insurance_type='HDHP',
            is_primary=True,
            deductible=1500.00,
            out_of_pocket_max=5000.00,
        )
        self.coverage_data = {
            'insurance_profile': self.insurance_profile,
            'service_type': 'X-Ray',
            'service_category': 'DIAGNOSTIC',
            'coverage_percentage': 80.00,
            'copay_amount': None,
            'requires_preauth': False,
            'network_tier': 'IN',
        }

    def test_create_coverage(self):
        coverage = Coverage.objects.create(**self.coverage_data)
        self.assertEqual(coverage.service_type, 'X-Ray')
        self.assertEqual(coverage.coverage_percentage, 80.00)

    def test_coverage_percentage_validators(self):
        self.coverage_data['coverage_percentage'] = 101.00
        coverage = Coverage(**self.coverage_data)
        with self.assertRaises(ValidationError):
            coverage.full_clean()

        self.coverage_data['coverage_percentage'] = -5.00
        coverage = Coverage(**self.coverage_data)
        with self.assertRaises(ValidationError):
            coverage.full_clean()

    def test_unique_together_constraint(self):
        Coverage.objects.create(**self.coverage_data)
        with self.assertRaises(IntegrityError):
            Coverage.objects.create(**self.coverage_data)

    def test_coverage_str(self):
        coverage = Coverage.objects.create(**self.coverage_data)
        expected_str = f"{coverage.service_type} In-Network"
        self.assertEqual(str(coverage), expected_str)

    def test_service_category_default(self):
        del self.coverage_data['service_category']
        coverage = Coverage.objects.create(**self.coverage_data)
        self.assertEqual(coverage.service_category, 'GENERAL')

    def test_requires_preauth_default(self):
        del self.coverage_data['requires_preauth']
        coverage = Coverage.objects.create(**self.coverage_data)
        self.assertFalse(coverage.requires_preauth)

    def test_coverage_without_coverage_or_copay(self):
        self.coverage_data['coverage_percentage'] = None
        self.coverage_data['copay_amount'] = None
        coverage = Coverage.objects.create(**self.coverage_data)
        self.assertIsNone(coverage.coverage_percentage)
        self.assertIsNone(coverage.copay_amount)


class NetworkProviderModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username='testuser', email='test@example.com')
        self.insurance_profile = InsuranceProfile.objects.create(
            member=self.member,
            provider_name='Test Provider',
            policy_number='POL123',
            effective_date='2023-01-01',
            expiration_date='2024-01-01',
            insurance_type='HDHP',
            is_primary=True,
            deductible=1500.00,
            out_of_pocket_max=5000.00,
        )
        self.network_provider_data = {
            'insurance_profile': self.insurance_profile,
            'provider_npi': '1234567890',
            'network_status': 'IN',
            'contract_start': '2023-01-01',
            'contract_end': '2024-01-01',
        }

    def test_create_network_provider(self):
        provider = NetworkProvider.objects.create(**self.network_provider_data)
        self.assertEqual(provider.provider_npi, '1234567890')
        self.assertEqual(provider.network_status, 'IN')

    def test_unique_together_constraint(self):
        NetworkProvider.objects.create(**self.network_provider_data)
        with self.assertRaises(IntegrityError):
            NetworkProvider.objects.create(**self.network_provider_data)

    def test_network_provider_str(self):
        provider = NetworkProvider.objects.create(**self.network_provider_data)
        expected_str = f"{provider.provider_npi} (In-Network)"
        self.assertEqual(str(provider), expected_str)