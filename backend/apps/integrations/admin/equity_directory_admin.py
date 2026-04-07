from django.contrib import admin

from apps.integrations.models import EquityDirectoryEntry, EquityDirectorySnapshot


class EquityDirectoryEntryInline(admin.TabularInline):
    model = EquityDirectoryEntry
    extra = 0
    fields = ("symbol", "name", "exchange", "currency", "is_actively_traded")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(EquityDirectorySnapshot)
class EquityDirectorySnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "is_active", "row_count", "created_at")
    list_filter = ("provider", "is_active")
    readonly_fields = ("id", "provider", "is_active", "row_count", "created_at")
    inlines = (EquityDirectoryEntryInline,)


@admin.register(EquityDirectoryEntry)
class EquityDirectoryEntryAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "name",
        "exchange",
        "currency",
        "is_actively_traded",
        "snapshot",
    )
    list_filter = ("snapshot__provider", "snapshot__is_active", "is_actively_traded", "exchange")
    search_fields = ("symbol", "name")
    readonly_fields = ("snapshot",)
