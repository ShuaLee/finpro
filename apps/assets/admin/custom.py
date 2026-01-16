from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from assets.models.core import Asset, AssetPrice, AssetType
from assets.models.custom.custom_asset import CustomAsset
from assets.models.custom.custom_asset_type import CustomAssetType
from assets.models.custom.custom_asset_field import CustomAssetField


# =====================================================
# Inlines
# =====================================================

class CustomAssetFieldInline(admin.TabularInline):
    """
    Inline for defining schema fields on a CustomAssetType.
    """
    model = CustomAssetField
    extra = 1


# =====================================================
# CustomAssetType Admin
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
# CustomAsset Admin Form (DYNAMIC SCHEMA LIVES HERE)
# =====================================================

class CustomAssetAdminForm(forms.ModelForm):
    """
    Admin form that dynamically renders CustomAssetField
    definitions as real form fields.
    """

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
        exclude = ("attributes",)  # IMPORTANT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._schema_fields = []

        custom_type = None

        # Existing object
        if self.instance.pk:
            custom_type = self.instance.custom_type

        # New object (type selected in POST)
        else:
            type_id = self.data.get("custom_type")
            if type_id:
                custom_type = CustomAssetType.objects.filter(
                    id=type_id).first()

        if not custom_type:
            return

        for field in custom_type.fields.all():
            field_name = f"attr_{field.name}"
            self.fields[field_name] = self._build_form_field(field)
            self._schema_fields.append(field)

            if self.instance.pk:
                self.fields[field_name].initial = (
                    self.instance.attributes.get(field.name)
                )

    def _build_form_field(self, field: CustomAssetField):
        if field.field_type == "text":
            return forms.CharField(
                label=field.label,
                required=field.required,
            )

        if field.field_type == "number":
            return forms.DecimalField(
                label=field.label,
                required=field.required,
            )

        if field.field_type == "boolean":
            return forms.BooleanField(
                label=field.label,
                required=False,
            )

        if field.field_type == "date":
            return forms.DateField(
                label=field.label,
                required=field.required,
            )

        if field.field_type == "choice":
            return forms.ChoiceField(
                label=field.label,
                choices=[(k, v) for k, v in field.choices.items()],
                required=field.required,
            )

        raise ValueError(f"Unknown field type: {field.field_type}")

    def clean(self):
        cleaned = super().clean()

        # Ownership validation
        custom_type = cleaned.get("custom_type")
        owner = cleaned.get("owner")

        if custom_type and owner and custom_type.created_by != owner:
            raise ValidationError(
                "You cannot use another user's custom asset type."
            )

        # Build attributes JSON
        attrs = {}
        for field in self._schema_fields:
            key = f"attr_{field.name}"
            if key in cleaned:
                attrs[field.name] = cleaned[key]

        cleaned["attributes"] = attrs
        return cleaned


# =====================================================
# CustomAsset Admin
# =====================================================

@admin.register(CustomAsset)
class CustomAssetAdmin(admin.ModelAdmin):
    form = CustomAssetAdminForm

    list_display = (
        "name",
        "custom_type",
        "owner",
        "currency",
        "updated_at",
    )

    list_filter = (
        "custom_type",
        "currency",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "asset",  # optional: good to show but not edit
    )

    def get_form(self, request, obj=None, **kwargs):
        # Critical: Force modelform_factory to NOT enforce a fields list from fieldsets
        # This prevents the early validation of attr_* names against the model
        # or '__all__' — either works, but None is cleaner here
        kwargs['fields'] = None

        # Optional: you can still compute dynamic names if you want early filtering,
        # but it's usually unnecessary since form init handles it
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                "fields": (
                    "owner",
                    "custom_type",
                    "name",
                    "description",
                    "currency",
                )
            }),
            ("Valuation", {
                "fields": (
                    "price",
                    "price_source",
                )
            }),
        ]

        dynamic_fields = []
        custom_type = None

        if obj:  # Editing
            custom_type = obj.custom_type
        elif request.method == "POST" and "custom_type" in request.POST:
            try:
                type_id = int(request.POST.get("custom_type"))
                custom_type = CustomAssetType.objects.filter(
                    id=type_id).first()
            except (ValueError, TypeError):
                pass

        if custom_type:
            dynamic_fields = [
                f"attr_{f.name}" for f in custom_type.fields.all()]

        if dynamic_fields:
            fieldsets.insert(1, ("Attributes", {"fields": dynamic_fields}))

        # Timestamps as read-only section
        fieldsets.append(("Timestamps (read-only)", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }))

        return fieldsets

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
    # Save lifecycle (CRITICAL)
    # -------------------------------------------------

    def save_model(self, request, obj, form, change):
        """
        Create backing Asset if needed, then save CustomAsset.
        """

        if not change:
            asset_type = AssetType.objects.get(slug="custom")
            obj.asset = Asset.objects.create(asset_type=asset_type)

        # Attach attributes built by form
        obj.attributes = form.cleaned_data.get("attributes", {})

        super().save_model(request, obj, form, change)

        # Persist AssetPrice
        price = form.cleaned_data.get("price")
        source = form.cleaned_data.get("price_source") or "MANUAL"

        if price is not None:
            AssetPrice.objects.update_or_create(
                asset=obj.asset,
                defaults={
                    "price": price,
                    "source": source,
                },
            )
