# insurance/models.py
from django.db import models
from accounts.models import Member
from django.core.validators import MinValueValidator,MaxValueValidator

class InsuranceProfile(models.Model):
    """
    Represents an insurance policy for a member
    """
    INSURANCE_TYPES = [
        ('HDHP', 'High Deductible Health Plan'),
        ('PPO', 'Preferred Provider Organization'),
        ('HMO', 'Health Maintenance Organization'),
        ('MEDICARE', 'Medicare'),
        ('MEDICAID', 'Medicaid'),
    ]
    
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE,
        related_name='insurance_profiles'
    )
    provider_name = models.CharField(max_length=255)
    policy_number = models.CharField(max_length=50)
    effective_date = models.DateField()
    expiration_date = models.DateField()
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPES)
    is_primary = models.BooleanField(default=False)
    deductible = models.DecimalField(max_digits=10, decimal_places=2)
    out_of_pocket_max = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_accumulated = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0
    )

    class Meta:
        unique_together = ('member', 'policy_number')
        ordering = ['-is_primary', 'effective_date']

    def __str__(self):
        return f"{self.provider_name} ({self.get_insurance_type_display()})"

# insurance/models.py
class Coverage(models.Model):
    SERVICE_CATEGORIES = [
        ('GENERAL', 'General Medical'),
        ('EMERGENCY', 'Emergency Care'),
        ('PHARMACY', 'Pharmacy'),
        ('SPECIALIST', 'Specialist Care'),
        ('DIAGNOSTIC', 'Diagnostic Services'),
        ('CUSTOM', 'Custom Service'),
    ]
    
    insurance_profile = models.ForeignKey(
        InsuranceProfile,
        on_delete=models.CASCADE,
        related_name='coverages'
    )
    service_type = models.CharField(max_length=255)  # Customizable field
    service_category = models.CharField(
        max_length=20,
        choices=SERVICE_CATEGORIES,
        default='GENERAL'
    )
    coverage_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    copay_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    requires_preauth = models.BooleanField(default=False)
    network_tier = models.CharField(
        max_length=20,
        choices=[('IN', 'In-Network'), ('OUT', 'Out-of-Network')]
    )

    class Meta:
        unique_together = ('insurance_profile', 'service_type', 'network_tier')

    def __str__(self):
        return f"{self.get_service_type_display()} {self.get_network_tier_display()}"

class NetworkProvider(models.Model):
    """
    Links providers to insurance networks
    """
    insurance_profile = models.ForeignKey(
        InsuranceProfile,
        on_delete=models.CASCADE,
        related_name='network_providers'
    )
    provider_npi = models.CharField(max_length=15)  # National Provider Identifier
    network_status = models.CharField(
        max_length=20,
        choices=[('IN', 'In-Network'), ('OUT', 'Out-of-Network')]
    )
    contract_start = models.DateField()
    contract_end = models.DateField()

    class Meta:
        unique_together = ('insurance_profile', 'provider_npi')

    def __str__(self):
        return f"{self.provider_npi} ({self.get_network_status_display()})"