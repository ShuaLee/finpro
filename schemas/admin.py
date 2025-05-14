from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from stock_portfolio.models import StockPortfolio
from .models import Schema

# Register your models here.


class SchemaAdminForm(forms.ModelForm):
    # Dropdown for selecting StockPortfolio
    sub_portfolio = forms.ModelChoiceField(
        queryset=StockPortfolio.objects.all(),
        label="Portfolio",
        required=True
    )

    class Meta:
        model = Schema
        fields = ['sub_portfolio', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_portfolio_ct = ContentType.objects.get_for_model(
            StockPortfolio)

        # Set initial sub_portfolio for existing instances
        if self.instance.pk and self.instance.base_asset_portfolio:
            self.initial['sub_portfolio'] = self.instance.base_asset_portfolio

    def clean(self):
        cleaned_data = super().clean()
        sub_portfolio = cleaned_data.get('sub_portfolio')
        if sub_portfolio:
            cleaned_data['sub_portfolio_content_type'] = self.stock_portfolio_ct
            # Fixed typo
            cleaned_data['sub_portfolio_object_id'] = sub_portfolio.id
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sub_portfolio_content_type = self.cleaned_data['sub_portfolio_content_type']
        instance.sub_portfolio_object_id = self.cleaned_data['sub_portfolio_object_id']
        if commit:
            instance.save()
        return instance


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    form = SchemaAdminForm

    list_display = ['name', 'get_portfolio', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = [
        'name', 'base_asset_portfolio__portfolio__profile__user__email']

    fieldsets = (
        (None, {
            'fields': ('sub_portfolio', 'name')
        }),
    )

    def get_portfolio(self, obj):
        return str(obj.base_asset_portfolio) if obj.base_asset_portfolio else "-"
    get_portfolio.short_description = "Portfolio"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sub_portfolio_content_type'
        ).prefetch_related('base_asset_portfolio')
