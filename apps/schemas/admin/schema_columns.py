from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from schemas.models import (
    SchemaColumn,

)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "identifier", "schema", "source",
                    "data_type", "display_order", "is_system")
    list_filter = ("source", "data_type", "is_system", "schema")
    search_fields = ("title", "schema__name")
    autocomplete_fields = ["schema"]
    readonly_fields = ("created_at",)

    def get_readonly_fields(self, request, obj=None):
        base = super().get_readonly_fields(request, obj)
        readonly = (
            "display_order",  # Always readonly
            "title", "schema", "data_type", "source", "source_field",
            "field_path", "constraints",
            "formula",   # ✅ keep FK, drop old fields
            "is_system", "is_editable", "is_deletable", "created_at",
        )
        if obj and obj.is_system:
            return base + readonly
        return base + ("display_order",)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:  # 🔒 Remove default
            del actions["delete_selected"]
        return actions

    @admin.action(description="Delete selected schema columns safely")
    def delete_selected_safely(self, request, queryset):
        deleted = 0
        failed = []
        for obj in queryset:
            try:
                obj.delete()  # ✅ runs our overridden delete()
                deleted += 1
            except ValidationError as e:
                failed.append(f"❌ {obj.title}: {e.messages[0]}")

        if deleted:
            self.message_user(
                request, f"✅ Deleted {deleted} schema columns successfully.", level=messages.SUCCESS
            )
        for msg in failed:
            self.message_user(request, msg, level=messages.ERROR)

    actions = ["delete_selected_safely"]

    def delete_model(self, request, obj):
        try:
            obj.delete()  # ✅ runs dependency check
            self.message_user(
                request, f"✅ Deleted column: {obj.title}", level=messages.SUCCESS)
        except ValidationError as e:
            self.message_user(
                request, f"❌ {e.messages[0]}", level=messages.ERROR)
