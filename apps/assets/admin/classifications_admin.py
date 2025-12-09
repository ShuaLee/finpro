from django.contrib import admin
from assets.models.classifications.sector import Sector
from assets.models.classifications.industry import Industry
from django.core.exceptions import ValidationError


# -------------------------------------------------------------------
# Base admin with shared behavior
# -------------------------------------------------------------------
class ClassificationAdminBase(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "owner")
    list_filter = ("is_system",)
    search_fields = ("name", "slug")
    ordering = ("name",)
    readonly_fields = ("slug",)

    def has_delete_permission(self, request, obj=None):
        # Block deletion of system classifications
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Ensure system objects cannot be renamed
        if change and obj.is_system:
            original = type(obj).objects.get(pk=obj.pk)
            if original.name != obj.name:
                raise ValidationError(
                    "System classifications cannot be renamed.")
        super().save_model(request, obj, form, change)


# -------------------------------------------------------------------
# Sector Admin
# -------------------------------------------------------------------
@admin.register(Sector)
class SectorAdmin(ClassificationAdminBase):
    pass


# -------------------------------------------------------------------
# Industry Admin
# -------------------------------------------------------------------
@admin.register(Industry)
class IndustryAdmin(ClassificationAdminBase):
    pass
