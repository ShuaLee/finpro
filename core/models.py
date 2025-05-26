from datetime import date
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email, password, first_name, last_name, birth_date, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        if not first_name:
            raise ValueError("The First Name field must be set.")
        if not last_name:
            raise ValueError("The Last Name field must be set.")
        if not birth_date:
            raise ValueError("Birth date is required.")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        # Create Profile (without birth_date, as it's now in User)
        Profile.objects.get_or_create(user=user)
        return user

    def create_superuser(self, email, password, first_name, last_name, birth_date=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Use a default birth_date for superusers to avoid terminal issues
        birth_date = birth_date or date(1970, 1, 1)
        return self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            **extra_fields
        )


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    birth_date = models.DateField(blank=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'birth_date']

    def __str__(self):
        return f'{self.email} - {self.first_name} {self.last_name}'


class Profile(models.Model):
    ACCOUNT_TYPES = [
        ('individual', 'Individual'),
        ('manager', 'Manager'),
    ]
    PLAN_TIERS = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='individual')
    plan = models.CharField(max_length=20, choices=PLAN_TIERS, default='free')
    language = models.CharField(max_length=30, blank=False, default="en")
    currency = models.CharField(max_length=10, blank=False, default="USD")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    is_asset_manager = models.BooleanField(default=False)
    receive_email_updates = models.BooleanField(default=True)
    profile_setup_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email