from django.contrib import admin
from assets.models.real_estate import RealEstateAsset, RealEstateType


@admin.register(RealEstateType)
class RealEstateTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "is_system")
    search_fields = ("name",)
    list_filter = ("created_by",)

    def is_system(self, obj):
        return obj.created_by is None
    is_system.boolean = True


@admin.register(RealEstateAsset)
class RealEstateAssetAdmin(admin.ModelAdmin):
    list_display = (
        "property_type",
        "owner",
        "estimated_value",
        "currency",
        "country",
        "last_updated",
    )
    list_filter = ("country", "currency")
    search_fields = ("address", "city")
    readonly_fields = ("last_updated",)
