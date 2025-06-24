from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Portfolio, FXRate

# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'birth_date')}),
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
    list_display = ('user',)
    search_fields = ('user__email',)


@admin.register(Portfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created_at',]
    # inlines = [StockPortfolioInline]

@admin.register(FXRate)
class FXRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency',
                    'rate', 'updated_at', 'is_stale')
    search_fields = ('from_currency', 'to_currency')
    list_filter = ('from_currency', 'to_currency', 'updated_at')
    readonly_fields = ('updated_at',)

    def is_stale(self, obj):
        return obj.is_stale()
    is_stale.boolean = True
    is_stale.short_description = "Stale (>24h)"