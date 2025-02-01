# billing/calculators.py
from decimal import Decimal
from billing.models import BillShare
from insuranceprofile.calculators import InsuranceCalculator

class BillSplitter:
    """
    Handles splitting medical bills among family members based on:
    - Insurance coverage calculations
    - Family account split rules
    
    Key Features:
    - Supports multiple split methods (equal, percentage, default)
    - Integrates with InsuranceCalculator for coverage details
    - Tracks insurance-covered vs personal responsibility amounts
    
    Usage Example:
    --------------
    bill = Bill.objects.get(id=123)
    splitter = BillSplitter(bill)
    splitter.calculate_shares()
    """
    
    def __init__(self, bill):
        """
        Initialize with a Bill instance
        
        :param bill: Bill object to split
        """
        self.bill = bill
        self.members = bill.primary_account.members.all()
        self.total_insurance = Decimal('0.00')  # Total insurance coverage
        self.total_personal = Decimal('0.00')   # Total personal responsibility

    def calculate_shares(self):
        """
        Calculate and create bill shares for all members
        
        Steps:
        1. Clear existing shares
        2. Calculate insurance coverage per line item
        3. Apply split rules to personal responsibility
        4. Create BillShare records
        
        Edge Cases Handled:
        - No members in account
        - Zero personal responsibility
        - Missing split rules
        """
        # Clear existing shares to avoid duplicates
        self.bill.shares.all().delete()
        
        # Calculate insurance coverage for each line item
        for line_item in self.bill.line_items.all():
            self._process_line_item(line_item)
        
        # Apply split rules to personal responsibility
        self._apply_split_rules()

    def _process_line_item(self, line_item):
        """
        Calculate insurance coverage for a single line item
        
        :param line_item: LineItem instance to process
        """
        calculator = InsuranceCalculator(
            member_id=line_item.member.id,
            service_type=line_item.procedure_code,
            provider_npi=self.bill.provider_npi,
            service_date=self.bill.service_date,
            billed_amount=line_item.amount
        )
        result = calculator.calculate()
        
        # Update totals
        self.total_insurance += result['total_covered']
        self.total_personal += result['patient_responsibility']
        
        # Update line item with coverage details
        line_item.insurance_coverage = result['primary_policy']
        line_item.covered_service = result['total_covered'] > 0
        line_item.save()

    def _apply_split_rules(self):
        """
        Apply account split rules to personal responsibility
        
        Rules:
        - EQUAL: Split equally among all members
        - PERCENTAGE: Split based on predefined percentages
        - DEFAULT: Split equally among adults only
        """
        split_rules = self.bill.primary_account.split_rules_json
        
        if split_rules.get('method') == 'EQUAL':
            self._split_equal(self.total_personal)
        elif split_rules.get('method') == 'PERCENTAGE':
            self._split_by_percentage(self.total_personal, split_rules['percentages'])
        else:
            self._split_default(self.total_personal)

    def _split_default(self, total_personal):
        """
        Default split: Equal among adults only
        
        :param total_personal: Total personal responsibility amount
        """
        adults = self.members.filter(relationship__in=['PRIMARY', 'SPOUSE'])
        if not adults.exists():
            raise ValueError("No adults found for default split")
            
        share = total_personal / adults.count()
        
        for member in adults:
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )

    def _split_equal(self, total_personal):
        """
        Equal split: Divide equally among all members
        
        :param total_personal: Total personal responsibility amount
        """
        if not self.members.exists():
            raise ValueError("No members found for equal split")
            
        share = total_personal / self.members.count()
        
        for member in self.members:
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )

    def _split_by_percentage(self, total_personal, percentages):
        """
        Percentage-based split: Divide based on predefined percentages
        
        :param total_personal: Total personal responsibility amount
        :param percentages: Dict of member_id → percentage (e.g., {"1": 60, "2": 40})
        """
        if not percentages:
            raise ValueError("No percentages provided for split")
            
        total_percentage = sum(percentages.values())
        if total_percentage != 100:
            raise ValueError("Percentages must sum to 100")
            
        for member in self.members:
            percentage = percentages.get(str(member.id), 0) / 100
            share = total_personal * Decimal(percentage)
            
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )