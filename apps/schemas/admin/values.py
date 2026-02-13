from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect

from schemas.models import SchemaColumnValue
from schemas.services.mutations import SchemaMutationService
from schemas.services.queries import SchemaQueryService


class SchemaColumnValueAdminForm(forms.ModelForm):
    class Meta:
        model = SchemaColumnValue
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        scv = self.instance
        if not scv.pk:
            return

        enum_constraint = scv.column.constraints.filter(name="enum").first()
        if enum_constraint:
            choices = SchemaQueryService.resolve_enum_values(
                enum_constraint,
                column=scv.column,
                holding=scv.holding,
            )
            self.fields["value"].widget = forms.Select(
                choices=[(c, c) for c in choices])

        if scv.column.data_type == "boolean":
            self.fields["value"].widget = forms.CheckboxInput()

    def clean_value(self):
        value = self.cleaned_data.get("value")
        scv = self.instance
        column = scv.column

        if value in ("", None):
            return None

        enum_constraint = column.constraints.filter(name="enum").first()
        if enum_constraint:
            allowed = SchemaQueryService.resolve_enum_values(
                enum_constraint,
                column=column,
                holding=scv.holding,
            )
            if value not in allowed:
                raise forms.ValidationError(
                    f"Value must be one of: {', '.join(allowed)}")

        try:
            if column.data_type == "decimal":
                Decimal(str(value))
            elif column.data_type == "percent":
                raw = str(value).strip()
                if raw.endswith("%"):
                    raw = raw[:-1].strip()
                Decimal(raw)
            elif column.data_type == "boolean":
                if not isinstance(value, bool):
                    raise ValueError()
            elif column.data_type == "date":
                str(value)
            else:
                str(value)
        except Exception:
            raise forms.ValidationError(
                f"Invalid value for type '{column.data_type}'.")

        for constraint in column.constraints.all():
            try:
                constraint.validate(value)
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages)

        return value


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("column", "holding", "display_value", "source")
    form = SchemaColumnValueAdminForm
    change_form_template = "admin/schemas/schemacolumnvalue/change_form.html"

    def display_value(self, obj):
        return obj.value

    display_value.short_description = "Value"

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ("column", "holding", "source")
        if obj.column.is_editable:
            return ("column", "holding", "source")
        return ("column", "holding", "source", "value")

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        try:
            SchemaMutationService.set_value(
                scv=obj,
                raw_value=form.cleaned_data["value"],
            )
        except ValidationError as exc:
            self.message_user(request, exc.messages[0], level=messages.ERROR)

    def response_change(self, request, obj):
        if "_revert_to_system" in request.POST:
            if obj.source == SchemaColumnValue.Source.USER:
                SchemaMutationService.revert_value(scv=obj)
                self.message_user(request, "Reverted to system value.")
            else:
                self.message_user(
                    request,
                    "This value is already using the system source.",
                    level=messages.INFO,
                )
            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)

    def render_change_form(self, request, context, *args, **kwargs):
        context["show_revert_button"] = True
        return super().render_change_form(request, context, *args, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return True
