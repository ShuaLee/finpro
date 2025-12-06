from django.utils.safestring import mark_safe
from django.urls import reverse


class SchemaPreviewMixin:
    """
    Mixin that adds:
    - schema_preview (HTML list of columns)
    - schema_link (button to open Schema admin page)
    - collapsible fieldset for schema display
    """

    readonly_fields = ("schema_preview", "schema_link")

    # -----------------------------
    # 1️⃣ Render schema columns
    # -----------------------------
    def schema_preview(self, account):
        schema = account.active_schema
        if not schema:
            return mark_safe("<i>No schema found for this account type.</i>")

        cols = schema.columns.order_by("display_order")

        html = [
            "<div style='padding:6px 0;'>",
            "<b>Schema Columns:</b>",
            "<ul style='margin-left:0.75rem;'>",
        ]

        for c in cols:
            html.append(
                f"<li><b>{c.title}</b> "
                f"(<code>{c.data_type}</code>) "
                f"- source: <i>{c.source}</i></li>"
            )

        html.append("</ul></div>")

        return mark_safe("\n".join(html))

    schema_preview.short_description = "Schema Columns"

    # -----------------------------
    # 2️⃣ Link to open full Schema admin page
    # -----------------------------
    def schema_link(self, account):
        schema = account.active_schema
        if not schema:
            return ""

        url = reverse("admin:schemas_schema_change", args=[schema.id])

        return mark_safe(
            f"<a href='{url}' class='button' target='_blank' "
            f"style='padding:4px 8px; background:#4a7bd8; "
            f"color:white; border-radius:4px; text-decoration:none;'>"
            f"Open Schema</a>"
        )

    schema_link.short_description = "Open Schema"

    # -----------------------------
    # 3️⃣ Optional collapsible fieldsets
    # -----------------------------
    schema_fieldset = (
        "Schema (Read-Only)",
        {
            "fields": ("schema_preview", "schema_link"),
            "classes": ("collapse",),
        },
    )
