from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from .constants import METALS_SCHEMA_CONFIG
from .models import MetalsPortfolio, PreciousMetalHolding, MetalPortfolioSchema, MetalPortfolioSchemaColumn, MetalPortfolioSchemaColumnValue, StorageFacility

# ---------------------------- forms -------------------------- #


class PredefinedSchemaColumnForm(forms.ModelForm):
    predefined_column = forms.ChoiceField(
        label="Predefined Column",
        help_text="Select from the available predefined schema columns",
        choices=[],
        required=True,
    )

    class Meta:
        model = MetalPortfolioSchemaColumn
        fields = ['title', 'schema']  # You only show title + schema + dropdown

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build dropdown choices from SCHEMA_COLUMN_CONFIG
        choices = []
        for source, fields in METALS_SCHEMA_CONFIG.items():
            for field, config in fields.items():
                display = f"{source} - {field}"
                value = f"{source}:{field}"
                choices.append((value, display))
        self.fields['predefined_column'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data['predefined_column']
        source, source_field = selected.split(":", 1)
        config = METALS_SCHEMA_CONFIG[source][source_field]

        # Set the rest of the values automatically
        instance.source = source
        instance.source_field = source_field
        instance.data_type = config['data_type']
        instance.editable = config.get('editable', True)
        instance.formula = config.get('formula', '')
        if commit:
            instance.save()
        return instance


class MetalPortfolioSchemaColumnValueAdminForm(forms.ModelForm):
    class Meta:
        model = MetalPortfolioSchemaColumnValue
        # Explicitly include is_edited
        fields = ['column', 'holding', 'value', 'is_edited']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        column_source = None
        column_editable = True
        # Determine column source and editable status
        if 'column' in self.data:
            try:
                column_id = self.data.get('column')
                column = MetalPortfolioSchemaColumn.objects.get(id=column_id)
                column_source = column.source
                column_editable = column.editable
            except (ValueError, MetalPortfolioSchemaColumn.DoesNotExist):
                pass
        elif self.initial.get('column'):
            try:
                column = MetalPortfolioSchemaColumn.objects.get(
                    id=self.initial['column'])
                column_source = column.source
                column_editable = column.editable
            except MetalPortfolioSchemaColumn.DoesNotExist:
                pass
        elif self.instance and hasattr(self.instance, 'column') and self.instance.column:
            column_source = self.instance.column.source
            column_editable = self.instance.column.editable
        # Apply holding-specific logic
        if column_source == 'holding':
            self.fields[
                'value'].help_text = "Updates the MetalHolding field directly (e.g., quantity, purchase_price)."
            if 'is_edited' in self.fields:
                self.fields['is_edited'].widget = forms.HiddenInput()
                self.fields['is_edited'].disabled = True
            self.fields['value'].initial = None
        # Apply non-editable logic
        if not column_editable:
            self.fields['value'].disabled = True
            self.fields['value'].help_text = "This column is not editable."
            if 'is_edited' in self.fields:
                self.fields['is_edited'].disabled = True
                self.fields['is_edited'].widget = forms.HiddenInput()

# ---------------------------- schemas ------------------------------ #


@admin.register(MetalPortfolioSchema)
class MetalPortfolioSchemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'metal_portfolio_link', 'created_at', 'updated_at']
    list_filter = [
        'metal_portfolio__portfolio__profile__user__email', 'created_at'
    ]
    search_fields = [
        'name', 'metal_portfolio__portfolio__profile__user__email'
    ]
    list_per_page = 50
    fields = ['name', 'metal_portfolio']
    autocomplete_fields = ['metal_portfolio']

    def metal_portfolio_link(self, obj):
        url = reverse('admin:metal_portfolio_metalportfolio_change',
                      args=[obj.metal_portfolio.id])
        return format_html('<a href="{}">{}</a>', url, obj.metal_portfolio)
    metal_portfolio_link.short_description = 'Metal Portfolio'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('metal_portfolio__portfolio__profile__user')

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.metal_portfolio.schemas.count() <= 1:
            # Clear all messages
            storage = messages.get_messages(request)
            storage.used = True
            # Add error message
            self.message_user(
                request,
                "Cannot delete the last schema for a MetalPortfolio.",
                level=messages.ERROR
            )
            # Redirect to list view
            return HttpResponseRedirect(reverse('admin:metal_portfolio_metalportfolioschema_changelist'))
        return super().delete_view(request, object_id, extra_context)

    def delete_queryset(self, request, queryset):
        blocked_schemas = [
            obj.name for obj in queryset if obj.metal_portfolio.schemas.count() <= 1]
        if blocked_schemas:
            storage = messages.get_messages(request)
            storage.used = True
            self.message_user(
                request,
                f"Cannot delete schema(s) {', '.join(blocked_schemas)} as they are the last schemas for their MetalPortfolio.",
                level=messages.ERROR
            )
            return
        super().delete_queryset(request, queryset)

    def delete_selected(self, request, queryset):
        if request.POST.get('post'):  # Confirmation page submitted
            blocked_schemas = [
                obj.name for obj in queryset if obj.metal_portfolio.schemas.count() <= 1]
            if blocked_schemas:
                storage = messages.get_messages(request)
                storage.used = True
                self.message_user(
                    request,
                    f"Cannot delete schema(s) {', '.join(blocked_schemas)} as they are the last schemas for their MetalPortfolio.",
                    level=messages.ERROR
                )
                return HttpResponseRedirect(reverse('admin:metal_portfolio_metalportfolioschema_changelist'))
            return super().delete_selected(request, queryset)
        # Render confirmation page for GET or initial POST
        return super().delete_selected(request, queryset)


@admin.register(MetalPortfolioSchemaColumn)
class MetalPortfolioSchemaColumnAdmin(admin.ModelAdmin):
    form = PredefinedSchemaColumnForm
    list_display = ['title', 'schema', 'source',
                    'source_field', 'data_type', 'editable']
    list_filter = ['schema__metal_portfolio',
                   'data_type', 'source', 'is_deletable']
    search_fields = ['title', 'schema__name']
    # Show only necessary inputs
    fields = ['title', 'schema', 'predefined_column']
    readonly_fields = ['is_deletable']
    autocomplete_fields = ['schema']

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_deletable:
            self.message_user(
                request,
                f"Cannot delete '{obj.title}' as it is a mandatory column.",
                level=messages.ERROR
            )
            return HttpResponseRedirect(reverse('admin:metal_portfolio_metalportfolioschemacolumn_changelist'))
        return super().delete_view(request, object_id, extra_context)

    def delete_queryset(self, request, queryset):
        blocked_columns = [
            obj.title for obj in queryset if not obj.is_deletable]
        if blocked_columns:
            self.message_user(
                request,
                f"Cannot delete column(s) {', '.join(blocked_columns)} as they are mandatory.",
                level=messages.ERROR
            )
            return
        super().delete_queryset(request, queryset)

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.is_deletable:
            return self.readonly_fields + ['title', 'data_type', 'source', 'formula', 'editable']
        return self.readonly_fields


@admin.register(MetalPortfolioSchemaColumnValue)
class MetalPortfolioSchemaColumnValueAdmin(admin.ModelAdmin):
    form = MetalPortfolioSchemaColumnValueAdminForm
    list_display = ['column', 'holding', 'get_value', 'is_edited']
    list_filter = ['column__schema__metal_portfolio',
                   'column__source', 'is_edited']
    search_fields = ['column__title', 'holding__metal__symbol']
    fields = ['column', 'holding', 'value', 'is_edited']
    readonly_fields = ['get_value']
    autocomplete_fields = ['column', 'holding']

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.column.source == 'holding' or not obj.column.editable):
            return self.readonly_fields + ['column', 'holding', 'is_edited']
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['warning'] = "Column values are automatically created when a MetalHolding is added. Only edit if necessary."
        return super().add_view(request, form_url, extra_context)

# ------------------------------ models ------------------------------ #


@admin.register(StorageFacility)
class StorageFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email',
                    'metal_portfolio', 'created_at', 'last_synced')
    list_filter = ('created_at',)
    search_fields = ('name', 'metal_portfolio__name',
                     'metal_portfolio__portfolio__profile__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_synced')

    def get_user_email(self, obj):
        try:
            return obj.metal_portfolio.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "metal_portfolio__portfolio__profile__user__email"


@admin.register(MetalsPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
