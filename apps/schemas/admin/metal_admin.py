from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from assets.constants import ASSET_SCHEMA_CONFIG
from schemas.models import MetalPortfolioSchema, MetalPortfolioSC, MetalPortfolioSCV


class PredefinedMetalSCForm(forms.ModelForm):
    predefined_column = forms.ChoiceField(
        label="Predefined Column",
        help_text="Select from the available predefined schema columns",
        choices=[],
        required=True,
    )

    class Meta:
        model = MetalPortfolioSC
        fields = ['title', 'schema']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        asset_type = getattr(self._meta.model, 'ASSET_TYPE', None)
        config = ASSET_SCHEMA_CONFIG.get(asset_type, {})

        choices = []
        for source, fields in config.items():
            for field, _field_config in fields.items():
                display = f"{source} - {field}"
                value = f"{source}:{field}"
                choices.append((value, display))

        self.fields['predefined_column'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data['predefined_column']
        source, source_field = selected.split(":", 1)

        field_config = ASSET_SCHEMA_CONFIG.get(
            instance.ASSET_TYPE, {}).get(source, {}).get(source_field, {})

        instance.source = source
        instance.source_field = source_field
        instance.data_type = field_config.get('data_type')
        instance.editable = field_config.get('editable', True)
        instance.formula = field_config.get('formula', '')
        instance.decimal_spaces = field_config.get('decimal_spaces')

        if commit:
            instance.save()
        return instance


class MetalPortfolioSCVAdminForm(forms.ModelForm):
    class Meta:
        model = MetalPortfolioSCV
        fields = ['column', 'holding', 'value', 'is_edited']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column = getattr(self.instance, 'column', None)
        if column:
            if column.source == 'holding':
                self.fields['value'].help_text = "Updates the MetalHolding field directly."
                self.fields['is_edited'].widget = forms.HiddenInput()
                self.fields['is_edited'].disabled = True
            if not column.editable:
                self.fields['value'].disabled = True
                self.fields['value'].help_text = "This column is not editable."
                self.fields['is_edited'].disabled = True
                self.fields['is_edited'].widget = forms.HiddenInput()


@admin.register(MetalPortfolioSchema)
class MetalPortfolioSchemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'metal_portfolio_link', 'created_at', 'updated_at']
    list_filter = [
        'metal_portfolio__portfolio__profile__user__email', 'created_at']
    search_fields = [
        'name', 'metal_portfolio__portfolio__profile__user__email']
    fields = ['name', 'metal_portfolio']
    autocomplete_fields = ['metal_portfolio']

    def metal_portfolio_link(self, obj):
        url = reverse('admin:portfolios_metalportfolio_change',
                      args=[obj.metal_portfolio.id])
        return format_html('<a href="{}">{}</a>', url, obj.metal_portfolio)
    metal_portfolio_link.short_description = 'Metal Portfolio'

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.metal_portfolio.schemas.count() <= 1:
            messages.error(
                request, "Cannot delete the last schema for this MetalPortfolio.")
            return HttpResponseRedirect(reverse('admin:schemas_metalportfolioschema_changelist'))
        return super().delete_view(request, object_id, extra_context)


@admin.register(MetalPortfolioSC)
class MetalPortfolioSchemaColumnAdmin(admin.ModelAdmin):
    form = PredefinedMetalSCForm
    list_display = ['title', 'schema', 'source',
                    'source_field', 'data_type', 'editable']
    list_filter = ['schema__metal_portfolio',
                   'data_type', 'source', 'is_deletable']
    search_fields = ['title', 'schema__name']
    fields = ['title', 'schema', 'predefined_column']
    readonly_fields = ['is_deletable']
    autocomplete_fields = ['schema']

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_deletable:
            messages.error(
                request, f"Cannot delete '{obj.title}' — it's a mandatory column.")
            return HttpResponseRedirect(reverse('admin:schemas_metalportfolioschemacolumn_changelist'))
        return super().delete_view(request, object_id, extra_context)


@admin.register(MetalPortfolioSCV)
class MetalPortfolioSchemaColumnValueAdmin(admin.ModelAdmin):
    form = MetalPortfolioSCVAdminForm
    list_display = ['column', 'holding', 'get_value', 'is_edited']
    list_filter = ['column__schema__metal_portfolio',
                   'column__source', 'is_edited']
    search_fields = ['column__title', 'holding__precious_metal__symbol']
    fields = ['column', 'holding', 'value', 'is_edited']
    readonly_fields = ['get_value']
    autocomplete_fields = ['column', 'holding']

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.column.source == 'holding' or not obj.column.editable):
            return self.readonly_fields + ['column', 'holding', 'is_edited']
        return self.readonly_fields
