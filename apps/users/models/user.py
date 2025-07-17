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

    def create_user(self, email, password, **extra_fields):
        """
        Create and return a regular user.

        Args:
            email (str): User's email (required, unique).
            password (str): Password (hashed before saving).
            extra_fields (dict): Additional model fields.

        Raises:
            ValueError: If required fields are missing.
        """

        if not email:
            raise ValueError("The Email field must be set.")
        if not password:
            raise ValueError("Password must be set.")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin privileges.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email instead of username for authentication.

    Fields:
        email (unique): Primary identifier.
        first_name, last_name: User's personal details.
    """
    username = None

    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.email}'
