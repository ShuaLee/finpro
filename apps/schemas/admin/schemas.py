from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from schemas.models import (
    Schema,
)
from schemas.services.schema_deletion import delete_schema_if_allowed


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "created_at")
    list_filter = ("schema_type",)
    search_fields = ["name"]
    readonly_fields = ("schema_type", "content_type", "object_id", "created_at")
    fields = ("name", "schema_type", "content_type", "object_id", "created_at")

    actions = ["delete_selected_safely"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        try:
            delete_schema_if_allowed(obj)
            obj.delete()
            self.message_user(request, f"✅ Deleted schema: {obj}", level=messages.SUCCESS)
        except ValidationError as e:
            self.message_user(request, f"❌ Could not delete schema '{obj}': {e.messages[0]}", level=messages.ERROR)
    
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
                failed.append(f"❌ Could not delete schema '{schema}': {e.messages[0]}")

        if deleted:
            self.message_user(request, f"✅ Deleted {deleted} schemas successfully.", level=messages.SUCCESS)

        for msg in failed:
            self.message_user(request, msg, level=messages.ERROR)