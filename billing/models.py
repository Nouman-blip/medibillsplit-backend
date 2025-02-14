from django.db import models

# Create your models here.
# billing/models.py
from django.db import models
from accounts.models import PrimaryAccount, Member
from insuranceprofile.models import InsuranceProfile

class Bill(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Payment'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('DISPUTED', 'Under Dispute'),
    ]
    
    primary_account = models.ForeignKey(
        PrimaryAccount,
        on_delete=models.CASCADE,
        related_name='bills'
    )
    provider_name = models.CharField(max_length=255)
    provider_npi = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    service_date = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill #{self.id} - {self.provider_name}"

class LineItem(models.Model):
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    procedure_code = models.CharField(max_length=20)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    insurance_coverage = models.ForeignKey(
        InsuranceProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    covered_service = models.BooleanField(default=False)
    requires_preauth = models.BooleanField(default=False)

    class Meta:
        ordering = ['-amount']

class BillShare(models.Model):
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    original_amount = models.DecimalField(max_digits=12, decimal_places=2)
    insurance_covered = models.DecimalField(max_digits=12, decimal_places=2)
    personal_responsibility = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('DISPUTED', 'Disputed')
        ],
        default='PENDING'
    )

class PaymentHistory(models.Model):
    bill_share = models.ForeignKey(
        BillShare,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )

class Dispute(models.Model):
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    initiator = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('UNDER_REVIEW', 'Under Review'),
            ('RESOLVED', 'Resolved')
        ],
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

class CharityRoundUp(models.Model):
    payment = models.OneToOneField(
        PaymentHistory,
        on_delete=models.CASCADE,
        related_name='charity_roundup'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    charity_name = models.CharField(max_length=255)
    tax_deductible = models.BooleanField(default=True)
    donation_receipt = models.URLField(null=True, blank=True)