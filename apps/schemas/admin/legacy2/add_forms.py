# schemas/admin_forms.py
from django import forms
from schemas.models import SchemaColumnTemplate, SubPortfolioSchemaLink


class AddFromTemplateForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=SchemaColumnTemplate.objects.none())

    def __init__(self, schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Find which account model this schema is linked to
        link = SubPortfolioSchemaLink.objects.filter(schema=schema).first()
        if link:
            self.fields["template"].queryset = SchemaColumnTemplate.objects.filter(
                schema_type=schema.schema_type,
                account_model_ct=link.account_model_ct
            )


class AddCustomColumnForm(forms.Form):
    title = forms.CharField(max_length=100)
    data_type = forms.ChoiceField(
        choices=[("decimal", "Decimal"), ("string", "String")])
    decimal_places = forms.ChoiceField(
        choices=[("0", "0"), ("2", "2"), ("4", "4"), ("8", "8")],
        required=False
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned["data_type"] == "decimal" and not cleaned.get("decimal_places"):
            raise forms.ValidationError(
                "Decimal places required for decimals.")
        return cleaned

class AddCalculatedColumnForm(forms.Form):
    title = forms.CharField(max_length=100, help_text="Name of the new calculated column")

    expression = forms.CharField(
        widget=forms.Textarea,
        help_text="Enter a formula using identifiers of existing numeric columns (e.g. 'price * cool_ratio / quantity').",
    )

    def __init__(self, schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate available numeric columns
        numeric_cols = schema.columns.filter(data_type="decimal")
        choices = [(col.identifier, f"{col.title} ({col.identifier})") for col in numeric_cols]
        self.fields["available_columns"] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
            help_text="Available numeric columns you can use in your formula",
        )