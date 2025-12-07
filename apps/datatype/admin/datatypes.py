from django.contrib import admin
from datatype.models import DataType


@admin.register(DataType)
class DataTypeAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "slug",
        "supports_length",
        "supports_decimals",
        "supports_numeric_limits",
        "supports_regex",
        "is_system",
    )

    list_filter = (
        "supports_length",
        "supports_decimals",
        "supports_numeric_limits",
        "supports_regex",
        "is_system",
    )

    search_fields = ("name", "slug", "description")
    ordering = ("slug",)

    readonly_fields = ("is_system",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "slug", "description")
        }),
        ("Capabilities", {
            "fields": (
                "supports_length",
                "supports_decimals",
                "supports_numeric_limits",
                "supports_regex",
            )
        }),
        ("System", {
            "fields": ("is_system",),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Prevent editing slug or capabilities on system-defined types.
        """
        ro = list(self.readonly_fields)
        if obj and obj.is_system:
            ro += [
                "slug",
                "supports_length",
                "supports_decimals",
                "supports_numeric_limits",
                "supports_regex",
            ]
        return ro
