# from django.contrib import admin, messages
# from django.contrib.contenttypes.admin import GenericTabularInline
# from django.core.exceptions import ValidationError
# from schemas.models import (
#     SchemaColumnValue,
# )
# from schemas.services.holding_sync_service import apply_base_scv_to_holding, recalc_calculated_for_holding
# from schemas.services.schema_engine import HoldingSchemaEngine
# from .forms import SchemaColumnValueAdminForm


# class SchemaColumnValueInline(GenericTabularInline):
#     model = SchemaColumnValue
#     extra = 0
#     fields = ("column", "value", "is_edited")
#     readonly_fields = ("is_edited",)
#     autocomplete_fields = ("column",)


# @admin.register(SchemaColumnValue)
# class SchemaColumnValueAdmin(admin.ModelAdmin):
#     form = SchemaColumnValueAdminForm
#     list_display = ("id", "column", "account", "value", "is_edited")
#     list_filter = ("column__schema", "is_edited")
#     search_fields = ("column__title",)
#     autocomplete_fields = ("column",)
#     actions = ("reset_overrides",)

#     def get_readonly_fields(self, request, obj=None):
#         ro = list(super().get_readonly_fields(request, obj))
#         if obj and obj.column:
#             # Calculated: never editable
#             if obj.column.source == "calculated":
#                 ro += ["value", "is_edited"]
#             # Holding: is_edited is irrelevant
#             elif obj.column.source == "holding":
#                 ro += ["is_edited"]
#             # 🔒 Non-editable column: fully lock SCV editing
#             if not obj.column.editable:
#                 ro += ["value", "is_edited"]
#         return ro

#     @staticmethod
#     def _get_engine_for_obj(obj):
#         model = obj.account_ct.model_class()
#         holding = model.objects.filter(pk=obj.account_id).first()
#         if holding:
#             return HoldingSchemaEngine(holding, holding.get_asset_type()), holding
#         return None, None

#     def save_model(self, request, obj: SchemaColumnValue, form, change):
#         col = obj.column
#         super().save_model(request, obj, form, change)

#         # 🔒 Non-editable: always revert value/is_edited
#         if not col.editable:
#             engine, holding = self._get_engine_for_obj(obj)
#             if engine:
#                 obj.is_edited = False
#                 obj.value = None
#                 obj.save(update_fields=["is_edited", "value"])
#                 engine.sync_column(col)
#                 messages.info(
#                     request, f"{col.title} is not editable; reverted to source.")
#             return

#         # HOLDING: push into model, never keep edited flag
#         if col.source == "holding":
#             if obj.is_edited:  # enforce False
#                 obj.is_edited = False
#                 obj.save(update_fields=["is_edited"])
#             try:
#                 # holding.save() will sync + recalc
#                 apply_base_scv_to_holding(obj)
#                 messages.success(
#                     request, f"Updated {col.title} on holding and recalculated.")
#             except ValidationError as ve:
#                 messages.error(request, "; ".join(ve.messages))
#             return

#         # ASSET: revert if not edited; otherwise keep override
#         if col.source == "asset":
#             engine, holding = self._get_engine_for_obj(obj)
#             if engine:
#                 if not obj.is_edited:
#                     engine.sync_column(col)
#                     messages.info(
#                         request, f"Reverted {col.title} to asset value.")
#                 recalc_calculated_for_holding(holding)
#             return

#         # CALCULATED/other: nothing special
#         return

#     def reset_overrides(self, request, queryset):
#         updated = queryset.update(is_edited=False, value=None)
#         self.message_user(request, f"Reset {updated} override(s).")
#     reset_overrides.short_description = "Reset edited values to defaults"
