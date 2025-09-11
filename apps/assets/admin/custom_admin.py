from django.contrib import admin
from assets.models.proxies import CustomAsset
from assets.models.details.custom_detail import CustomDetail


class CustomDetailInline(admin.StackedInline):
    model = CustomDetail
    can_delete = False
    extra = 0


@admin.register(CustomAsset)
class CustomAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    inlines = [CustomDetailInline]

    def save_model(self, request, obj, form, change):
        obj.asset_type = "custom"
        super().save_model(request, obj, form, change)
