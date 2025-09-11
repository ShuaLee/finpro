from django.contrib import admin
from assets.models.proxies import RealEstateAsset
from assets.models.details.real_estate_detail import RealEstateDetail


class RealEstateDetailInline(admin.StackedInline):
    model = RealEstateDetail
    can_delete = False
    extra = 0


@admin.register(RealEstateAsset)
class RealEstateAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    inlines = [RealEstateDetailInline]

    def save_model(self, request, obj, form, change):
        obj.asset_type = "real_estate"
        super().save_model(request, obj, form, change)
