from schemas.models import SchemaColumn, SchemaColumnTemplate, SubPortfolioSchemaLink
from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import path
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnTemplate,
    SchemaColumnVisibility,
    SubPortfolioSchemaLink,
    CustomAssetSchemaConfig,
)
from schemas.services.schema_deletion import delete_schema_if_allowed


# Inlines


class SchemaColumnInline(admin.TabularInline):  # or StackedInline
    model = SchemaColumn
    extra = 0
    fields = ("title", "data_type", "field_path", "is_default", "is_system")
    readonly_fields = ("created_at",)

# Forms


class AddSchemaColumnForm(forms.Form):
    MODE_CHOICES = [
        ("template", "From Template"),
        ("custom", "Custom Column"),
    ]
    mode = forms.ChoiceField(choices=MODE_CHOICES, widget=forms.RadioSelect)

    template = forms.ModelChoiceField(
        queryset=SchemaColumnTemplate.objects.none(),
        required=False
    )

    # Custom input fields
    title = forms.CharField(required=False)
    data_type = forms.ChoiceField(
        choices=SchemaColumn._meta.get_field("data_type").choices,
        required=False,
    )

    def __init__(self, *args, schema=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema

        if schema:
            # Find all account models linked to this schema
            links = SubPortfolioSchemaLink.objects.filter(schema=schema)
            account_model_cts = [link.account_model_ct for link in links]

            # Which (source, source_field) pairs are already in use
            used_pairs = set(
                schema.columns.values_list("source", "source_field")
            )

            # Grab templates for those account models
            templates = SchemaColumnTemplate.objects.filter(
                account_model_ct__in=account_model_cts,
                schema_type=schema.schema_type,
            ).order_by("display_order")

            # Tag them as used or not
            for tpl in templates:
                tpl.is_used = (tpl.source, tpl.source_field) in used_pairs

            self.fields["template"].queryset = templates


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "get_user_email",
                    "get_portfolio_type", "created_at")
    list_filter = ("schema_type", "content_type")
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    actions = ["delete_selected_safely"]

    change_form_template = "admin/schemas/schema/change_form.html"
    inlines = [SchemaColumnInline]

    def get_user_email(self, obj):
        try:
            return obj.content_object.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"

    def get_portfolio_type(self, obj):
        try:
            return obj.content_object.__class__.__name__
        except AttributeError:
            return "-"
    get_portfolio_type.short_description = "Subportfolio Type"

    def delete_model(self, request, obj):
        """
        Prevent deletion if it's the last schema for a portfolio/account type.
        """
        try:
            delete_schema_if_allowed(obj)
            obj.delete()
            self.message_user(
                request, f"✅ Deleted schema: {obj}", level=messages.SUCCESS)
        except ValidationError as e:
            self.message_user(
                request, f"❌ Could not delete schema '{obj}': {e.messages[0]}", level=messages.ERROR)

    @admin.action(description="Delete selected schemas with validation")
    def delete_selected_safely(self, request, queryset):
        deleted = 0
        failed = []

        for schema in queryset:
            try:
                delete_schema_if_allowed(schema)
                schema.delete()
                deleted += 1
            except ValidationError as e:
                failed.append(
                    f"❌ Could not delete schema '{schema}': {e.messages[0]}")

        if deleted:
            self.message_user(
                request, f"✅ Deleted {deleted} schemas successfully.", level=messages.SUCCESS)

        for error in failed:
            self.message_user(request, error, level=messages.ERROR)

    @admin.action(description="Delete orphaned schemas (no subportfolio link)")
    def delete_orphaned_schemas(self, request, queryset):
        from schemas.models import SubPortfolioSchemaLink

        orphaned = queryset.exclude(
            id__in=SubPortfolioSchemaLink.objects.values_list(
                "schema_id", flat=True)
        )

        count = orphaned.count()
        for schema in orphaned:
            schema.delete()

        self.message_user(request, f"✅ Deleted {count} orphaned schemas.")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:schema_id>/add-column/',
                self.admin_site.admin_view(self.add_column_view),
                name='schemas_schema_add_column',
            ),
        ]
        return custom_urls + urls

    def add_column_view(self, request, schema_id):
        schema = Schema.objects.get(pk=schema_id)

        if request.method == 'POST':
            form = AddSchemaColumnForm(request.POST, schema=schema)
            if form.is_valid():
                mode = form.cleaned_data['mode']
                if mode == 'template':
                    template = form.cleaned_data['template']
                    if template:
                        # Check if schema already has a column with this source + source_field
                        exists = schema.columns.filter(
                            source=template.source,
                            source_field=template.source_field
                        ).exists()

                        if exists:
                            messages.error(
                                request, f"Column from template '{template.title}' is already in this schema.")
                        else:
                            SchemaColumn.objects.create(
                                schema=schema,
                                title=template.title,
                                data_type=template.data_type,
                                source=template.source,
                                source_field=template.source_field,
                                field_path=template.field_path,
                                is_system=template.is_system,
                                is_default=template.is_default,
                                is_editable=template.is_editable,
                                is_deletable=template.is_deletable,
                                constraints=template.constraints,
                            )
                            messages.success(
                                request, f"Added column from template: {template.title}")

                    else:
                        messages.error(
                            request, "This template is already in use.")
                elif mode == 'custom':
                    SchemaColumn.objects.create(
                        schema=schema,
                        title=form.cleaned_data['title'],
                        data_type=form.cleaned_data['data_type'],
                        source="custom",          # 🔒 always custom
                        source_field=None,        # 🔒 force None
                        is_system=False,
                        is_editable=True,
                        is_deletable=True,
                    )
                    messages.success(
                        request, f"Added custom column: {form.cleaned_data['title']}")

                return redirect('admin:schemas_schema_change', schema_id)
        else:
            form = AddSchemaColumnForm(schema=schema)

        return render(request, 'admin/schemas/schema/add_schema_column.html', {
            'form': form,
            'schema': schema,
            'opts': self.model._meta,
            'title': 'Add Schema Column',
        })


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "schema", "source",
                    "data_type", "display_order", "is_system")
    list_filter = ("source", "data_type", "is_system")
    search_fields = ("title", "schema__name")
    autocomplete_fields = ["schema"]
    readonly_fields = ("created_at",)


@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = ["get_account_model_name", "title",
                    "source", "source_field", "data_type", "is_default"]
    list_filter = ["source", "is_default", "is_system"]
    search_fields = ["title", "source_field"]
    ordering = ["display_order"]
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "source", "source_field",
                "data_type", "field_path",
                "editable", "is_default", "is_deletable", "is_system",
                "formula_method", "formula_expression",
                "constraints",
                "display_order", "investment_theme", "created_at"
            )
        }),
    )

    @admin.display(description="Account Model")
    def get_account_model_name(self, obj):
        return obj.account_model_ct.model_class().__name__ if obj.account_model_ct else "-"


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "value", "get_account", "get_user_email")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
    list_filter = ("column__schema",)

    def get_account(self, obj):
        try:
            holding_or_account = obj.account
            return getattr(holding_or_account, "account", None)
        except Exception as e:
            return f"(err: {e})"

    get_account.short_description = "Account"

    def get_user_email(self, obj):
        try:
            # Try to resolve the full chain: holding → account → portfolio → profile → user
            target = obj.account
            account = getattr(target, "account", None)

            # Support both account and holding types
            if hasattr(account, "stock_portfolio"):
                profile = account.stock_portfolio.portfolio.profile
            elif hasattr(account, "precious_metal_portfolio"):
                profile = account.precious_metal_portfolio.portfolio.profile
            elif hasattr(account, "portfolio"):  # fallback if directly attached
                profile = account.portfolio.profile
            else:
                return "(no profile)"

            return profile.user.email if profile and profile.user else "(no user)"
        except Exception as e:
            return f"(err: {e})"

    get_user_email.short_description = "User Email"


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)


@admin.register(SubPortfolioSchemaLink)
class SubPortfolioSchemaLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "subportfolio", "account_model", "schema")
    list_filter = ("schema__schema_type",)
    autocomplete_fields = ("schema",)
    search_fields = ("subportfolio_id", "account_model_id")


@admin.register(CustomAssetSchemaConfig)
class CustomAssetSchemaConfigAdmin(admin.ModelAdmin):
    list_display = ['asset_type', 'created_at', 'updated_at']
    search_fields = ['asset_type']
