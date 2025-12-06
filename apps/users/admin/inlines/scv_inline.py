import nested_admin
from django import forms
from schemas.models import SchemaColumnValue


class SCVInline(nested_admin.NestedTabularInline):
    """
    Horizontal SCV layout:
    - One SCV per column instead of one SCV per row
    - Small input widths
    - No labels in rows
    - Column titles appear as table headers
    """

    model = SchemaColumnValue
    fk_name = "holding"

    extra = 0
    can_delete = False
    show_change_link = False
    classes = ("collapse",)

    # fields in each SCV "cell"
    fields = ("column_title", "value", "is_edited")
    readonly_fields = ("column_title",)

    verbose_name_plural = "Schema Column Values (Horizontal)"

    # -------------------------------------------
    # Render the column name as a header
    # -------------------------------------------
    def column_title(self, obj):
        return obj.column.title
    column_title.short_description = ""

    # -------------------------------------------
    # Custom formset with smaller input widgets
    # -------------------------------------------
    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        BaseForm = FormSet.form

        class SCVForm(BaseForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # Ensure widgets small
                if "value" in self.fields:
                    self.fields["value"].widget = forms.TextInput(
                        attrs={"size": 8, "style": "width:60px;"}
                    )

                if "is_edited" in self.fields:
                    self.fields["is_edited"].widget.attrs.update(
                        {"style": "width:20px;"}
                    )

                # Safe early-exit for nested-admin construction passes
                if "column_title" not in self.fields:
                    return

                scv = self.instance
                col = scv.column if scv and scv.pk else None

                # New SCVs shouldn't appear anyway
                if not col:
                    for f in self.fields.values():
                        f.disabled = True
                    return

                # READONLY rules:
                if col.source == "formula" or not col.is_editable:
                    self.fields["value"].disabled = True
                    self.fields["is_edited"].disabled = True
                else:
                    # Editable columns
                    self.fields["column_title"].disabled = True

        FormSet.form = SCVForm
        return FormSet

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
