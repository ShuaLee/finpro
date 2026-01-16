from django.contrib import admin
from django.db import models
from django import forms

from assets.models.custom.custom_asset import CustomAsset
from assets.models.core import Asset, AssetType
from users.models.profile import Profile


# =====================================================
# Forms
# =====================================================

class CustomAssetAdminForm(forms.ModelForm):
    """
    Admin form that allows selecting an AssetType
    when creating a CustomAsset.
    """

    asset_type = forms.ModelChoiceField(
        queryset=AssetType.objects.all(),
        required=True,
        help_text="Asset type for this custom asset.",
    )

    class Meta:
        model = CustomAsset
        fields = (
            "owner",
            "name",
            "currency",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Editing existing CustomAsset → prefill asset_type
        if self.instance.pk and self.instance.asset_id:
            self.fields["asset_type"].initial = (
                self.instance.asset.asset_type
            )

    def clean(self):
        cleaned = super().clean()

        asset_type = cleaned.get("asset_type")
        owner = cleaned.get("owner")

        if not asset_type or not owner:
            return cleaned

        # User may only use:
        # - system asset types (created_by = NULL)
        # - their own asset types
        if (
            asset_type.created_by is not None
            and asset_type.created_by != owner
        ):
            raise forms.ValidationError(
                "You cannot use another user's asset type."
            )

        return cleaned


# =====================================================
# Admin
# =====================================================

@admin.register(CustomAsset)
class CustomAssetAdmin(admin.ModelAdmin):
    form = CustomAssetAdminForm

    list_display = (
        "name",
        "owner",
        "asset_type",
        "currency",
        "created_at",
        "asset_id_display",
    )

    list_filter = (
        "currency",
    )

    search_fields = (
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "asset_id_display",
    )

    fieldsets = (
        (None, {
            "fields": (
                "asset_id_display",
                "owner",
                "name",
                "asset_type",
                "currency",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # -------------------------------------------------
    # Queryset scoping
    # -------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(owner=request.user.profile)

    # -------------------------------------------------
    # AssetType scoping
    # -------------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            form.base_fields["asset_type"].queryset = (
                AssetType.objects.filter(
                    models.Q(created_by__isnull=True)
                    | models.Q(created_by=request.user.profile)
                )
            )

        return form

    # -------------------------------------------------
    # Save hook
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Ensure backing Asset exists before saving CustomAsset.
        """
        if not change:
            asset = Asset.objects.create(
                asset_type=form.cleaned_data["asset_type"]
            )
            obj.asset = asset

        super().save_model(request, obj, form, change)

    def asset_id_display(self, obj):
        return obj.asset_id

    asset_id_display.short_description = "Asset ID"

    # -------------------------------------------------
    # Derived fields
    # -------------------------------------------------
    def asset_type(self, obj):
        return obj.asset.asset_type.name

    asset_type.short_description = "Asset Type"
