# billing/tests/test_models.py
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User, PrimaryAccount, Member
from insuranceprofile.models import InsuranceProfile
from billing.models import Bill, LineItem, BillShare, PaymentHistory, Dispute, CharityRoundUp

class BillModelTest(TestCase):
    """Test cases for the Bill model"""
    
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.primary_account = PrimaryAccount.objects.create(
            user=self.user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )

    def test_create_bill_with_valid_data(self):
        """Test creating a bill with all required fields"""
        bill = Bill.objects.create(
            primary_account=self.primary_account,
            provider_name="City Hospital",
            provider_npi="123456789012345",
            total_amount=Decimal("1500.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )
        
        self.assertEqual(bill.status, 'DRAFT')
        self.assertEqual(bill.provider_name, "City Hospital")
        self.assertEqual(bill.primary_account, self.primary_account)

    def test_bill_status_choices(self):
        """Test validation of status field choices"""
        bill = Bill(
            primary_account=self.primary_account,
            provider_name="Invalid Status",
            provider_npi="1234567890",
            total_amount=Decimal("100.00"),
            service_date="2023-10-01",
            due_date="2023-11-01",
            status="INVALID"
        )
        
        with self.assertRaises(ValidationError):
            bill.full_clean()

    def test_provider_npi_max_length(self):
        """Test provider_npi field length validation"""
        bill = Bill(
            primary_account=self.primary_account,
            provider_name="NPI Test",
            provider_npi="1" * 16,  # Exceeds max_length=15
            total_amount=Decimal("100.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )
        
        with self.assertRaises(ValidationError):
            bill.full_clean()

    def test_total_amount_precision(self):
        """Test max_digits and decimal_places constraints"""
        bill = Bill(
            primary_account=self.primary_account,
            provider_name="Precision Test",
            provider_npi="1234567890",
            total_amount=Decimal("999999999999.99"),  # 12 digits, 2 decimals
            service_date="2023-10-01",
            due_date="2023-11-01"
        )
        bill.full_clean()  # Should not raise error
        
        bill.total_amount = Decimal("1000000000000.00")  # Exceeds max_digits
        with self.assertRaises(ValidationError):
            bill.full_clean()

class LineItemModelTest(TestCase):
    """Test cases for the LineItem model"""
    
    def setUp(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.primary_account = PrimaryAccount.objects.create(
            user=user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        self.bill = Bill.objects.create(
            primary_account=self.primary_account,
            provider_name="Test Provider",
            provider_npi="1234567890",
            total_amount=Decimal("1000.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )
        self.insurance = InsuranceProfile.objects.create(
            name="Test Insurance",
            policy_number="POL123"
        )

    def test_create_line_item(self):
        """Test creating a line item with insurance coverage"""
        line_item = LineItem.objects.create(
            bill=self.bill,
            procedure_code="CPT123",
            description="Test Procedure",
            amount=Decimal("200.00"),
            insurance_coverage=self.insurance,
            covered_service=True
        )
        
        self.assertEqual(line_item.bill, self.bill)
        self.assertFalse(line_item.requires_preauth)

    def test_line_item_ordering(self):
        """Test Meta class ordering by amount descending"""
        LineItem.objects.create(
            bill=self.bill,
            procedure_code="LOW",
            amount=Decimal("100.00"),
            description="Low amount"
        )
        LineItem.objects.create(
            bill=self.bill,
            procedure_code="HIGH",
            amount=Decimal("500.00"),
            description="High amount"
        )
        
        items = LineItem.objects.all()
        self.assertEqual(items[0].procedure_code, "HIGH")
        self.assertEqual(items[1].procedure_code, "LOW")

    def test_insurance_coverage_nullable(self):
        """Test insurance_coverage can be null"""
        line_item = LineItem(
            bill=self.bill,
            procedure_code="NULLTEST",
            amount=Decimal("100.00"),
            description="Null insurance test"
        )
        line_item.full_clean()  # Should not raise error

class BillShareModelTest(TestCase):
    """Test cases for the BillShare model"""
    
    def setUp(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.primary_account = PrimaryAccount.objects.create(
            user=user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        self.member = Member.objects.create(
            primary_account=self.primary_account,
            name="Test Member",
            email="member@example.com",
            relationship="CHILD"
        )
        self.bill = Bill.objects.create(
            primary_account=self.primary_account,
            provider_name="Test Provider",
            provider_npi="1234567890",
            total_amount=Decimal("1000.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )

    def test_create_bill_share(self):
        """Test creating a bill share with calculated responsibility"""
        share = BillShare.objects.create(
            bill=self.bill,
            member=self.member,
            original_amount=Decimal("500.00"),
            insurance_covered=Decimal("300.00"),
            personal_responsibility=Decimal("200.00")
        )
        
        self.assertEqual(share.status, "PENDING")
        self.assertEqual(share.personal_responsibility, Decimal("200.00"))

    def test_negative_amount_validation(self):
        """Test negative amounts raise validation errors"""
        share = BillShare(
            bill=self.bill,
            member=self.member,
            original_amount=Decimal("-100.00"),
            insurance_covered=Decimal("0.00"),
            personal_responsibility=Decimal("-100.00")
        )
        
        with self.assertRaises(ValidationError):
            share.full_clean()

class PaymentHistoryModelTest(TestCase):
    """Test cases for the PaymentHistory model"""
    
    def setUp(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        primary_account = PrimaryAccount.objects.create(
            user=user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        member = Member.objects.create(
            primary_account=primary_account,
            name="Test Member",
            email="member@example.com",
            relationship="CHILD"
        )
        bill = Bill.objects.create(
            primary_account=primary_account,
            provider_name="Test Provider",
            provider_npi="1234567890",
            total_amount=Decimal("1000.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )
        self.share = BillShare.objects.create(
            bill=bill,
            member=member,
            original_amount=Decimal("500.00"),
            insurance_covered=Decimal("300.00"),
            personal_responsibility=Decimal("200.00")
        )

    def test_payment_creation(self):
        """Test creating a payment record"""
        payment = PaymentHistory.objects.create(
            bill_share=self.share,
            amount=Decimal("100.00"),
            payment_method="Credit Card",
            transaction_id="TX123456"
        )
        
        self.assertIsNotNone(payment.payment_date)
        self.assertEqual(payment.status, "PENDING")

    def test_transaction_id_uniqueness(self):
        """Test transaction_id should be unique"""
        PaymentHistory.objects.create(
            bill_share=self.share,
            amount=Decimal("100.00"),
            payment_method="Credit Card",
            transaction_id="UNIQUE123"
        )
        
        duplicate = PaymentHistory(
            bill_share=self.share,
            amount=Decimal("50.00"),
            payment_method="Credit Card",
            transaction_id="UNIQUE123"
        )
        
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

class DisputeModelTest(TestCase):
    """Test cases for the Dispute model"""
    
    def setUp(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        primary_account = PrimaryAccount.objects.create(
            user=user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        self.member = Member.objects.create(
            primary_account=primary_account,
            name="Test Member",
            email="member@example.com",
            relationship="CHILD"
        )
        self.bill = Bill.objects.create(
            primary_account=primary_account,
            provider_name="Test Provider",
            provider_npi="1234567890",
            total_amount=Decimal("1000.00"),
            service_date="2023-10-01",
            due_date="2023-11-01"
        )

    def test_create_dispute(self):
        """Test creating a dispute with valid data"""
        dispute = Dispute.objects.create(
            bill=self.bill,
            initiator=self.member,
            reason="Incorrect charges"
        )
        
        self.assertEqual(dispute.status, "OPEN")
        self.assertIsNone(dispute.resolved_at)

    def test_dispute_status_flow(self):
        """Test updating dispute status and resolution timestamp"""
        dispute = Dispute.objects.create(
            bill=self.bill,
            initiator=self.member,
            reason="Test dispute"
        )
        
        dispute.status = "RESOLVED"
        dispute.save()
        dispute.refresh_from_db()
        
        self.assertIsNotNone(dispute.resolved_at)

   