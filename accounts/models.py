# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class PrimaryAccount(models.Model):
    """
    Represents the main family account that manages multiple members
    """
    user = models.OneToOneField(
        'User', 
        on_delete=models.CASCADE,
        related_name='primary_account'
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Family Account"
        verbose_name_plural = "Family Accounts"

    def __str__(self):
        return f"{self.name} ({self.user.email})"

class Member(models.Model):
    """
    Represents individual family members under a primary account
    """
    RELATIONSHIP_CHOICES = [
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('OTHER', 'Other'),
    ]

    ACCESS_LEVELS = [
        ('ADMIN', 'Admin'),
        ('CONTRIBUTOR', 'Contributor'),
        ('VIEWER', 'Viewer'),
    ]

    primary_account = models.ForeignKey(
        PrimaryAccount, 
        on_delete=models.CASCADE,
        related_name='members_account'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    relationship = models.CharField(
        max_length=20, 
        choices=RELATIONSHIP_CHOICES
    )
    access_level = models.CharField(
        max_length=20, 
        choices=ACCESS_LEVELS,
        default='VIEWER'
    )
    active_status = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('primary_account', 'email')

    def __str__(self):
        return f"{self.name} ({self.relationship})"

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    """
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')],
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email