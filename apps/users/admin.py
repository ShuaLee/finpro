"""
users.admin
~~~~~~~~~~~
Registers custom User and Profile models with the Django admin interface,
including useful list displays and filters for better manageability.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from portfolios.models import Portfolio
from .models import User, Profile, FXRate


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin configuration for the User model.

    Features:
    - Displays key identity fields (email, name, active status).
    - Enables quick search by email and name.
    """
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
         'fields': ('first_name', 'last_name', 'birth_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'birth_date'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

    # Update ordering to use 'email' instead of 'username'
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            profile, _ = Profile.objects.get_or_create(user=obj)
            Portfolio.objects.get_or_create(profile=profile)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Profile model.

    Features:
    - Displays user and account type.
    - Allows filtering by plan and account type.
    """
    list_display = ('user',)
    search_fields = ('user__email',)
