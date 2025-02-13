from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from accounts.models import User, PrimaryAccount, Member


class UserModelTest(TestCase):
    """Test cases for the custom User model."""

    def test_create_user_with_email(self):
        """Test creating a user with an email and password succeeds."""
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_user_has_no_username(self):
        """Test that the username field is None for new users."""
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.assertIsNone(user.username)

    def test_email_uniqueness(self):
        """Test that creating users with duplicate emails raises an error."""
        User.objects.create_user(email="test@example.com", password="testpass123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="test@example.com", password="testpass123")

    def test_phone_validation_valid(self):
        """Test that valid phone numbers pass validation."""
        valid_numbers = ["+1234567890", "1234567890", "+123456789012345"]
        user = User(email="test@example.com", password="testpass123")
        
        for number in valid_numbers:
            user.phone = number
            user.full_clean()  # Should not raise ValidationError

    def test_phone_validation_invalid(self):
        """Test that invalid phone numbers fail validation."""
        invalid_numbers = ["invalid", "123", "+1234567890123456"]  # Invalid formats
        user = User(email="test@example.com", password="testpass123")
        
        for number in invalid_numbers:
            user.phone = number
            with self.assertRaises(ValidationError):
                user.full_clean()

    def test_required_fields(self):
        """Test that USERNAME_FIELD and REQUIRED_FIELDS are configured correctly."""
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, [])


class PrimaryAccountModelTest(TestCase):
    """Test cases for the PrimaryAccount model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="primary@example.com",
            password="testpass123"
        )

    def test_create_primary_account(self):
        """Test creating a PrimaryAccount with valid data succeeds."""
        account = PrimaryAccount.objects.create(
            user=self.user,
            name="Smith Family",
            phone="+1234567890",
            address="123 Main St"
        )

        self.assertEqual(account.name, "Smith Family")
        self.assertEqual(account.phone, "+1234567890")
        self.assertEqual(account.user, self.user)
        self.assertTrue(account.is_active)

    def test_primary_account_user_relationship(self):
        """Test the OneToOne relationship between User and PrimaryAccount."""
        account = PrimaryAccount.objects.create(
            user=self.user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        
        # Check reverse relation from User to PrimaryAccount
        self.assertEqual(self.user.primary_account, account)

    def test_phone_validation(self):
        """Test that invalid phone numbers fail validation."""
        account = PrimaryAccount(
            user=self.user,
            name="Invalid Phone",
            phone="invalid",
            address="Test Address"
        )
        
        with self.assertRaises(ValidationError):
            account.full_clean()

    def test_str_representation(self):
        """Test the string representation of PrimaryAccount."""
        account = PrimaryAccount.objects.create(
            user=self.user,
            name="Smith Family",
            phone="+1234567890",
            address="123 Main St"
        )
        self.assertEqual(str(account), f"Smith Family ({self.user.email})")

    def test_auto_timestamps(self):
        """Test that created_at and updated_at are auto-populated."""
        account = PrimaryAccount.objects.create(
            user=self.user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )
        
        self.assertIsNotNone(account.created_at)
        self.assertIsNotNone(account.updated_at)


class MemberModelTest(TestCase):
    """Test cases for the Member model."""

    def setUp(self):
        # Create a primary account to associate with members
        self.user = User.objects.create_user(
            email="primary@example.com",
            password="testpass123"
        )
        self.primary_account = PrimaryAccount.objects.create(
            user=self.user,
            name="Test Family",
            phone="+1234567890",
            address="Test Address"
        )

    def test_create_member(self):
        """Test creating a Member with valid data succeeds."""
        member = Member.objects.create(
            primary_account=self.primary_account,
            name="John Doe",
            email="john@example.com",
            relationship="CHILD",
            access_level="VIEWER"
        )

        self.assertEqual(member.name, "John Doe")
        self.assertEqual(member.relationship, "CHILD")
        self.assertEqual(member.access_level, "VIEWER")
        self.assertTrue(member.active_status)

    def test_member_email_uniqueness(self):
        """Test that the same email cannot be used across multiple members (unique=True)."""
        Member.objects.create(
            primary_account=self.primary_account,
            name="John Doe",
            email="john@example.com",
            relationship="CHILD"
        )
        
        # Attempt to create another member with the same email in a different primary account
        another_account = PrimaryAccount.objects.create(
            user=User.objects.create_user(email="another@example.com", password="testpass123"),
            name="Another Family",
            phone="+0987654321",
            address="Another Address"
        )
        
        with self.assertRaises(IntegrityError):
            Member.objects.create(
                primary_account=another_account,
                name="John Doe",
                email="john@example.com",
                relationship="CHILD"
            )

    def test_unique_together_primary_account_email(self):
        """Test that the same email cannot be reused within the same primary account."""
        Member.objects.create(
            primary_account=self.primary_account,
            name="John Doe",
            email="john@example.com",
            relationship="CHILD"
        )
        
        with self.assertRaises(IntegrityError):
            Member.objects.create(
                primary_account=self.primary_account,
                name="John Doe Duplicate",
                email="john@example.com",
                relationship="CHILD"
            )

    def test_relationship_choices(self):
        """Test that invalid relationship choices raise a validation error."""
        member = Member(
            primary_account=self.primary_account,
            name="Invalid Relationship",
            email="invalid@example.com",
            relationship="INVALID",
            access_level="VIEWER"
        )
        
        with self.assertRaises(ValidationError):
            member.full_clean()

    def test_access_level_default(self):
        """Test that the default access level is set to VIEWER."""
        member = Member.objects.create(
            primary_account=self.primary_account,
            name="Jane Doe",
            email="jane@example.com",
            relationship="SPOUSE"
        )
        self.assertEqual(member.access_level, "VIEWER")

    def test_str_representation(self):
        """Test the string representation of Member."""
        member = Member.objects.create(
            primary_account=self.primary_account,
            name="Jane Doe",
            email="jane@example.com",
            relationship="SPOUSE"
        )
        self.assertEqual(str(member), "Jane Doe (SPOUSE)")

    def test_access_level_choices_valid(self):
        """Test that valid access levels pass validation."""
        valid_access_levels = ["ADMIN", "CONTRIBUTOR", "VIEWER"]
        
        for level in valid_access_levels:
            member = Member(
                primary_account=self.primary_account,
                name=f"Test {level}",
                email=f"test_{level}@example.com",
                relationship="CHILD",
                access_level=level
            )
            member.full_clean()  # Should not raise ValidationError

    def test_access_level_choices_invalid(self):
        """Test that invalid access levels raise a validation error."""
        member = Member(
            primary_account=self.primary_account,
            name="Invalid Access Level",
            email="invalid@example.com",
            relationship="CHILD",
            access_level="INVALID"
        )
        
        with self.assertRaises(ValidationError):
            member.full_clean()