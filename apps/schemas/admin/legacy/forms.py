# from django import forms
# from django.core.exceptions import ValidationError
# from django.db import models
# from django.utils.text import slugify
# from schemas.config.mappers import build_column_defaults_from_spec
# from schemas.config.utils import get_column_constraints
# from schemas.models import (
#     Schema,
#     SchemaColumn,
#     SchemaColumnValue,
# )
# from .widgets import DisabledOptionSelect
# from .utils import build_builtin_choices_for_schema, next_display_order
# from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


# class AddBuiltInColumnForm(forms.Form):
#     catalog_item = forms.ChoiceField(label="Built-in column")

#     def __init__(self, *args, schema: Schema, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.schema = schema
#         choices, disabled, _ = build_builtin_choices_for_schema(schema)
#         self.fields['catalog_item'].widget = DisabledOptionSelect(
#             disabled_values=disabled)
#         self.fields['catalog_item'].choices = choices

#     def create_column(self):
#         key = self.cleaned_data['catalog_item']
#         source, source_field = key.split(":", 1)
#         _, _, config = build_builtin_choices_for_schema(self.schema)
#         spec = config[source][source_field]
#         defaults = build_column_defaults_from_spec(
#             spec, display_order=next_display_order(self.schema))

#         obj, created = SchemaColumn.objects.get_or_create(
#             schema=self.schema,
#             source=source,
#             source_field=source_field,
#             defaults=defaults
#         )
#         return obj, created


# class SchemaColumnInlineForm(forms.ModelForm):
#     built_in = forms.ChoiceField(label="Built-in column", required=False)

#     class Meta:
#         model = SchemaColumn
#         fields = (
#             "custom_title",                 # only editable for system rows
#             "title", "data_type",
#             "source", "source_field", "field_path",
#             "editable", "is_deletable",
#             "is_system", "scope",
#             "display_order", "investment_theme",
#         )

#     _builtin_choices = []
#     _builtin_disabled = set()
#     _config = None

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['built_in'].widget = DisabledOptionSelect(
#             disabled_values=getattr(self, "_builtin_disabled", set())
#         )
#         self.fields['built_in'].choices = getattr(self, "_builtin_choices", [])

#         inst = self.instance
#         if inst and inst.pk:
#             if inst.is_system:
#                 # system: lock structure; allow custom_title only
#                 keep = {"custom_title"}
#                 for name, field in self.fields.items():
#                     if name not in keep:
#                         field.disabled = True
#             self.fields['built_in'].widget = forms.HiddenInput()
#         else:
#             # new row: fields will be populated by built-in config
#             for name in ("title", "data_type", "source", "source_field", "field_path",
#                          "editable", "is_deletable", "is_system"):
#                 if name in self.fields:
#                     self.fields[name].disabled = True
#                     # 🔥 prevent validation error
#                     self.fields[name].required = False

#     def clean(self):
#         cleaned = super().clean()
#         bi = cleaned.get("built_in")
#         is_new = not self.instance.pk

#         if is_new and bi:
#             if bi in getattr(self, "_builtin_disabled", set()):
#                 raise forms.ValidationError(
#                     "This built-in column already exists in this schema.")
#             source, source_field = bi.split(":", 1)
#             spec = self._config[source][source_field]
#             spec_defaults = build_column_defaults_from_spec(spec, display_order=next_display_order(
#                 self.instance.schema or self.cleaned_data.get("schema")))
#             model_fields = [f.name for f in SchemaColumn._meta.fields]
#             cleaned.update({
#                 "source": source,
#                 "source_field": source_field,
#                 **{k: v for k, v in spec_defaults.items() if k in model_fields and k != "display_order"},
#             })
#         return cleaned

#     def save(self, commit=True):
#         obj = super().save(commit=False)
#         if not self.instance.pk and (obj.display_order in (None, 0)):
#             max_order = SchemaColumn.objects.filter(schema=obj.schema).aggregate(
#                 models.Max("display_order"))["display_order__max"] or 0
#             obj.display_order = max_order + 1
#         if commit:
#             obj.save()
#         return obj


# class SchemaColumnCustomAddForm(forms.ModelForm):
#     # ✅ Explicit data_type field so it always renders
#     data_type = forms.ChoiceField(
#         choices=[("string", "String"), ("decimal",
#                                         "Decimal"), ("number", "Number")],
#         required=True,
#         label="Data type",
#     )

#     # DECIMAL/NUMBER constraints
#     decimal_places = forms.IntegerField(
#         required=False, min_value=0, max_value=8, initial=2)
#     dec_min = forms.DecimalField(required=False)
#     dec_max = forms.DecimalField(required=False)

#     # STRING constraints
#     character_minimum = forms.IntegerField(
#         required=False, min_value=0, initial=0)
#     character_limit = forms.IntegerField(
#         required=False, min_value=1, initial=25)
#     all_caps = forms.BooleanField(required=False, initial=False)

#     class Meta:
#         model = SchemaColumn
#         fields = (
#             "schema",
#             "title",
#             "data_type",
#             "editable",
#             "scope",
#             "display_order",
#             "investment_theme",
#         )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if not self.fields["decimal_places"].initial:
#             self.fields["decimal_places"].initial = 2
#         self.fields["character_minimum"].help_text = "Minimum characters (default: 0)."
#         self.fields["character_limit"].help_text = "Maximum characters (default: 25)."
#         self.fields["all_caps"].help_text = "Force uppercase input."

#     def clean(self):
#         cleaned = super().clean()
#         dt_raw = cleaned.get("data_type") or ""
#         dt = dt_raw.lower()
#         if dt == "number":
#             dt = "decimal"
#             cleaned["data_type"] = "decimal"

#         constraints = {}

#         if dt == "decimal":
#             dp = cleaned.get("decimal_places")
#             if dp is None:
#                 self.add_error("decimal_places",
#                                "Required for decimal/number columns.")
#             elif not (0 <= int(dp) <= 8):
#                 self.add_error("decimal_places", "Must be between 0 and 8.")

#             dec_min = cleaned.get("dec_min")
#             dec_max = cleaned.get("dec_max")
#             if dec_min is not None and dec_max is not None and dec_min > dec_max:
#                 self.add_error("dec_max", "Max must be ≥ Min.")

#             constraints["decimal_places"] = dp
#             if dec_min is not None:
#                 constraints["min"] = dec_min
#             if dec_max is not None:
#                 constraints["max"] = dec_max

#         elif dt == "string":
#             char_min = cleaned.get("character_minimum")
#             char_max = cleaned.get("character_limit")
#             char_min = 0 if char_min is None else int(char_min)
#             char_max = 25 if char_max is None else int(char_max)
#             if char_min > char_max:
#                 self.add_error("character_limit",
#                                "Max characters must be ≥ Min characters.")
#             constraints["character_minimum"] = char_min
#             constraints["character_limit"] = char_max
#             if cleaned.get("all_caps"):
#                 constraints["all_caps"] = True
#             cleaned["decimal_places"] = None
#         else:
#             cleaned["decimal_places"] = None

#         cleaned["_constraints"] = constraints
#         return cleaned

#     def save(self, commit=True):
#         obj: SchemaColumn = super().save(commit=False)

#         # Always custom & deletable for this form
#         obj.source = "custom"
#         obj.is_system = False
#         obj.is_deletable = True
#         obj.field_path = None
#         obj.formula_method = None
#         obj.formula_expression = None

#         constraints = self.cleaned_data.get("_constraints", {}) or {}
#         # If your model has a JSONField for constraints:
#         if hasattr(obj, "constraints"):
#             obj.constraints = constraints

#         obj.decimal_places = constraints.get(
#             "decimal_places") if obj.data_type == "decimal" else None

#         if not obj.source_field:
#             base = slugify(self.cleaned_data.get(
#                 "title") or "") or "custom_field"
#             sf = base
#             i = 1
#             while SchemaColumn.objects.filter(schema=obj.schema, source="custom", source_field=sf).exists():
#                 i += 1
#                 sf = f"{base}_{i}"
#             obj.source_field = sf

#         if commit:
#             obj.save()
#         return obj

#     class Media:
#         js = ("admin/schemas/column_constraints_toggle.js",)  # optional UX


# class SchemaColumnValueAdminForm(forms.ModelForm):
#     class Meta:
#         model = SchemaColumnValue
#         fields = "__all__"

#     def _to_decimal(self, raw):
#         if raw is None:
#             return None
#         if isinstance(raw, Decimal):
#             return raw
#         if isinstance(raw, (int, float)):
#             return Decimal(str(raw))
#         if isinstance(raw, str):
#             s = raw.strip()
#             if s == "":
#                 return None
#             s = s.replace(",", "")
#             return Decimal(s)
#         raise InvalidOperation("Unsupported type")

#     def clean(self):
#         cleaned = super().clean()
#         obj = self.instance
#         col = obj.column
#         if not col:
#             return cleaned

#         # 🔒 Non-editable columns: never accept overrides
#         if not col.editable:
#             # hard-stop the admin form with an error message
#             self.add_error("value", "This column is not editable.")
#             cleaned["is_edited"] = False
#             return cleaned

#         val = cleaned.get("value")
#         is_edited = cleaned.get("is_edited")

#         # -- pull constraints from config --
#         # Get schema type from the holding's schema (column.schema.schema_type)
#         schema_type = col.schema.schema_type if col and col.schema else None
#         constraints = get_column_constraints(
#             schema_type, col.source, col.source_field) if schema_type else {}

#         # --- type-specific rules ---
#         if col.data_type == "decimal" and val is not None:
#             # you already quantize using col.decimal_places
#             # add min/max if present:
#             try:
#                 dec = self._to_decimal(val)
#                 if dec is not None:
#                     min_ = constraints.get("min")
#                     max_ = constraints.get("max")
#                     if min_ is not None and dec < Decimal(str(min_)):
#                         self.add_error("value", f"Must be ≥ {min_}.")
#                     if max_ is not None and dec > Decimal(str(max_)):
#                         self.add_error("value", f"Must be ≤ {max_}.")
#             except InvalidOperation:
#                 pass

#         elif col.data_type == "string" and val is not None:
#             s = str(val)
#             # character limits
#             limit = constraints.get("character_limit")
#             minimum = constraints.get("character_minimum")
#             if minimum is not None and len(s) < int(minimum):
#                 self.add_error(
#                     "value", f"Must be at least {minimum} characters.")
#             if limit is not None and len(s) > int(limit):
#                 self.add_error("value", f"Must be at most {limit} characters.")
#             # all caps transform
#             if constraints.get("all_caps"):
#                 cleaned["value"] = s.upper()

#         # 1) Normalize decimals (round instead of reject)
#         if col.data_type == "decimal" and val is not None:
#             try:
#                 dec = self._to_decimal(val)
#                 if dec is not None:
#                     # Prefer constraint decimal_places, fallback to 4
#                     places = (col.constraints or {}).get("decimal_places", 4)
#                     quant = Decimal(1).scaleb(-places)
#                     dec = dec.quantize(quant, rounding=ROUND_HALF_UP)
#                 cleaned["value"] = dec
#                 val = dec
#             except (InvalidOperation, ValueError, TypeError):
#                 self.add_error("value", "Invalid decimal format.")
#                 return cleaned

#         # 2) Holding SCVs: never use is_edited; push to model later
#         if col.source == "holding":
#             cleaned["is_edited"] = False
#             # Validate on Holding with the normalized (rounded) value
#             model = obj.account_ct.model_class()
#             holding = model.objects.filter(pk=obj.account_id).first()
#             if holding:
#                 try:
#                     setattr(holding, col.source_field, val)
#                     holding.full_clean()  # e.g. reject negative quantity
#                 except ValidationError as ve:
#                     self.add_error("value", "; ".join(ve.messages))
#             return cleaned

#         # 3) Asset SCVs: apply override semantics
#         if col.source == "asset":
#             # If blank value -> remove override
#             if val in (None, ""):
#                 cleaned["is_edited"] = False
#                 # we will overwrite from source in save_model
#                 return cleaned

#             # If user forgot to tick is_edited but typed a value,
#             # we DO NOT auto-toggle. Keep strict rule:
#             # is_edited must be True to accept an override.
#             if not is_edited:
#                 # Keep as not edited; value will be ignored and reverted to source
#                 cleaned["is_edited"] = False
#                 return cleaned

#             # is_edited == True: require a value for override
#             if is_edited and val is None:
#                 self.add_error(
#                     "value", "Provide a value, or clear and uncheck override.")
#                 return cleaned

#             return cleaned

#         # 4) Calculated/other: do nothing special here
#         return cleaned
