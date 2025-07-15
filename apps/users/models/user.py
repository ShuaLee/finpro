"""
users.models.user
~~~~~~~~~~~~~~~~~
Defines the custom User model and its manager for authentication.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager for User model with helper methods to create users and superusers.
    """

    def create_user(self, email, password, first_name, last_name=None, is_over_13=False, **extra_fields):
        """
        Create and return a regular user.

        Args:
            email (str): User's email (required, unique).
            password (str): Password (hashed before saving).
            first_name (str): First name.
            last_name (str): Last name (optional).
            is_over_13 (bool): Age confirmation.
            extra_fields (dict): Additional model fields.

        Raises:
            ValueError: If required fields are missing.
        """

        if not email:
            raise ValueError("The Email field must be set.")
        if not first_name:
            raise ValueError("The First Name field must be set.")
        if not is_over_13:
            raise ValueError("User must confirm they are over 13 years old.")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name or '',
            is_over_13=is_over_13,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name, last_name=None, **extra_fields):
        """
        Create and return a superuser with admin privileges.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Superusers bypass age confirmation
        return self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name or '',
            is_over_13=True,  # Always true for superusers
            **extra_fields
        )


class User(AbstractUser):
    """
    Custom User model using email instead of username for authentication.

    Fields:
        email (unique): Primary identifier.
        first_name, last_name: User's personal details.
        is_over_13: Boolean for legal compliance (COPPA/GDPR-lite).
    """
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    is_over_13 = models.BooleanField(default=False)  # ✅ New field
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']  # ✅ Only first name required now

    def __str__(self):
        return f'{self.email} - {self.first_name} {self.last_name or ""}'
