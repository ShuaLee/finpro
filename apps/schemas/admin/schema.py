from django.contrib import admin
from django.http import HttpResponse

from schemas.models import Schema
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from schemas.services.queries import SchemaQueryService


@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = ("identifier", "title", "data_type", "is_system")
    list_filter = ("data_type", "is_system")
    search_fields = ("identifier", "title")
    ordering = ("identifier",)
    readonly_fields = ("identifier", "is_system")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(SchemaColumnTemplateBehaviour)
class SchemaColumnTemplateBehaviourAdmin(admin.ModelAdmin):
    list_display = ("template", "asset_type", "source", "formula_definition")
    list_filter = ("asset_type", "source")
    search_fields = ("template__identifier", "formula_definition__identifier")


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio", "account_type")
    list_filter = ("account_type",)
    search_fields = ("portfolio__profile__user__email",)

    def dependency_graph(self, request, schema_id):
        schema = Schema.objects.get(id=schema_id)
        graph = SchemaQueryService.dependency_graph(schema=schema)

        lines = ["digraph SchemaColumnDependencies {"]
        for src, targets in graph.items():
            for target in sorted(targets):
                lines.append(f'    "{src}" -> "{target}";')
        lines.append("}")

        return HttpResponse("\n".join(lines), content_type="text/plain")

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom = [
            path(
                "dependency-graph/<int:schema_id>/",
                self.admin_site.admin_view(self.dependency_graph),
                name="schema_dependency_graph",
            ),
        ]
        return custom + urls
