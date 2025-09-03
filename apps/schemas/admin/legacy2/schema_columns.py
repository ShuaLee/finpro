from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import path, reverse
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

    # --- Dynamic readonly fields ---
    def get_readonly_fields(self, request, obj=None):
        base = super().get_readonly_fields(request, obj)
        always_readonly = ("display_order", "identifier", "schema", "data_type", "source",
                           "source_field", "field_path", "constraints",
                           "formula", "is_system", "is_editable", "is_deletable",
                           "created_at")
        return base + always_readonly

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
            
    def reset_title_view(self, request, column_id):
        column = SchemaColumn.objects.get(pk=column_id)
        if column.is_system and column.template:
            column.title = column.template.title
            column.save(update_fields=["title"])
            self.message_user(
                request,
                f"✅ Reset title to default: {column.title}",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "❌ Cannot reset: column has no template.",
                level=messages.ERROR,
            )
        return redirect("admin:schemas_schemacolumn_change", column.id)
    
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:column_id>/reset-title/",
                self.admin_site.admin_view(self.reset_title_view),
                name="schemas_schemacolumn_reset_title",  # ✅ use full name
            ),
        ]
        return custom + urls
    
    def change_view(self, request, object_id, form_url="", extra_context=None):
        column = SchemaColumn.objects.get(pk=object_id)
        extra_context = extra_context or {}
        if column.is_system and column.template:
            extra_context["reset_title_url"] = reverse(
                "admin:schemas_schemacolumn_reset_title", args=[object_id]
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)