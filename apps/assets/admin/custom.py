from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from assets.models.core import AssetPrice
from assets.models.custom.custom_asset import CustomAsset
from assets.models.custom.custom_asset_type import CustomAssetType
from assets.models.custom.custom_asset_field import CustomAssetField
from assets.services.custom import CustomAssetFactory


# =====================================================
# Inlines
# =====================================================

class CustomAssetFieldInline(admin.TabularInline):
    model = CustomAssetField
    extra = 1


# =====================================================
# CustomAssetType
# =====================================================

@admin.register(CustomAssetType)
class CustomAssetTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by")
    search_fields = ("name",)
    inlines = (CustomAssetFieldInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user.profile)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


# =====================================================
# Forms
# =====================================================

class CustomAssetAdminForm(forms.ModelForm):
    price = forms.DecimalField(
        max_digits=20,
        decimal_places=6,
        required=False,
        help_text="Current estimated value.",
    )

    price_source = forms.CharField(
        max_length=50,
        required=False,
        initial="MANUAL",
    )

    class Meta:
        model = CustomAsset
        exclude = ("attributes",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        custom_type = None

        if self.instance.pk:
            custom_type = self.instance.custom_type
        else:
            custom_type_id = self.data.get("custom_type")
            if custom_type_id:
                custom_type = CustomAssetType.objects.filter(id=custom_type_id).first()

        if not custom_type:
            return

        for field in custom_type.fields.all():
            field_name = f"attr_{field.name}"

            if field.field_type == CustomAssetField.TEXT:
                form_field = forms.CharField(
                    label=field.label,
                    required=field.required,
                )

            elif field.field_type == CustomAssetField.DECIMAL:
                form_field = forms.DecimalField(
                    label=field.label,
                    required=field.required,
                    max_digits=20,
                    decimal_places=6,
                )

            elif field.field_type == CustomAssetField.BOOLEAN:
                form_field = forms.BooleanField(
                    label=field.label,
                    required=False,
                )

            elif field.field_type == CustomAssetField.DATE:
                form_field = forms.DateField(
                    label=field.label,
                    required=field.required,
                    widget=forms.DateInput(attrs={"type": "date"}),
                )

            elif field.field_type == CustomAssetField.CHOICE:
                form_field = forms.ChoiceField(
                    label=field.label,
                    required=field.required,
                    choices=[(c, c) for c in (field.choices or [])],
                )

            else:
                continue

            self.fields[field_name] = form_field

            if self.instance.pk:
                self.fields[field_name].initial = self.instance.attributes.get(field.name)

    def clean(self):
        cleaned = super().clean()

        custom_type = cleaned.get("custom_type")
        owner = cleaned.get("owner")

        if custom_type and owner and custom_type.created_by != owner:
            raise ValidationError(
                "You cannot use another user's custom asset type."
            )

        if not custom_type:
            return cleaned

        attrs = {}
        for field in custom_type.fields.all():
            key = f"attr_{field.name}"
            if key in self.cleaned_data:
                attrs[field.name] = self.cleaned_data[key]

        cleaned["attributes"] = attrs
        return cleaned



# =====================================================
# CustomAsset
# =====================================================

@admin.register(CustomAsset)
class CustomAssetAdmin(admin.ModelAdmin):
    form = CustomAssetAdminForm

    list_display = (
        "name",
        "custom_type",
        "owner",
        "currency",
        "display_price",
        "updated_at",
    )

    list_filter = ("custom_type", "currency")
    search_fields = ("name", "description")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": (
                "owner",
                "custom_type",
                "name",
                "description",
            )
        }),
        ("Attributes", {
            "fields": (),
        }),
        ("Valuation", {
            "fields": (
                "currency",
                "price",
                "price_source",
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "custom_type" and not request.user.is_superuser:
            kwargs["queryset"] = CustomAssetType.objects.filter(
                created_by=request.user.profile
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # -------------------------------------------------
    # Save hooks
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        if not change:
            created = CustomAssetFactory.create(
                owner=form.cleaned_data["owner"],
                custom_type=form.cleaned_data["custom_type"],
                name=form.cleaned_data["name"],
                description=form.cleaned_data.get("description", ""),
                currency=form.cleaned_data["currency"],
                attributes=form.cleaned_data.get("attributes"),
                price=form.cleaned_data.get("price"),
                price_source=form.cleaned_data.get("price_source"),
            )
            obj.pk = created.pk
            return

        super().save_model(request, obj, form, change)

    # -------------------------------------------------
    # Derived fields
    # -------------------------------------------------
    def display_price(self, obj):
        if obj.asset_id and hasattr(obj.asset, "price"):
            return obj.asset.price.price
        return "—"

    display_price.short_description = "Value"
