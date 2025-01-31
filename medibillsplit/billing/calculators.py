# billing/calculators.py
from decimal import Decimal
from billing.models import BillShare
from insuranceprofile.calculators import InsuranceCalculator

class BillSplitter:
    def __init__(self, bill):
        self.bill = bill
        self.members = bill.primary_account.members.all()
        self.total_insurance = Decimal('0.00')
        self.total_personal = Decimal('0.00')

    def calculate_shares(self):
        # Clear existing shares
        self.bill.shares.all().delete()
        
        
        
        # Calculate insurance coverage per line item
        for line_item in self.bill.line_items.all():
            calculator = InsuranceCalculator(
                member_id=line_item.member.id,
                service_type=line_item.procedure_code,
                provider_npi=self.bill.provider_npi,
                service_date=self.bill.service_date,
                billed_amount=line_item.amount
            )
            result = calculator.calculate()
            
            insurance_covered = result['total_covered']
            personal_share = result['patient_responsibility']
            
            self.total_insurance += insurance_covered
            self.total_personal += personal_share
            
            # Create or update line item coverage
            line_item.insurance_coverage = result['primary_policy']
            line_item.covered_service = insurance_covered > 0
            line_item.save()

        # Create bill shares based on account rules
        split_rules = self.bill.primary_account.split_rules_json
        if split_rules.get('method') == 'EQUAL':
            self._split_equal(self.total_personal)
        elif split_rules.get('method') == 'PERCENTAGE':
            self._split_by_percentage(self.total_personal, split_rules['percentages'])
        else:
            self._split_default(self.total_personal)

    def _split_default(self, total_personal):
        # Default split: equal among adults
        adults = self.members.filter(relationship__in=['PRIMARY', 'SPOUSE'])
        share = self.total_personal / adults.count()
    
        for member in adults:
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )

    def _split_equal(self, total_personal):
        # Equal split among all members
        share = self.total_personal / self.members.count()
        for member in self.members:
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )

    def _split_by_percentage(self, total_personal, percentages):
        # Percentage-based split
        for member in self.members:
            percentage = percentages.get(str(member.id), 0) / 100
            share = self.total_personal * Decimal(percentage)
            BillShare.objects.create(
                bill=self.bill,
                member=member,
                original_amount=share,
                insurance_covered=self.total_insurance,
                personal_responsibility=share
            )