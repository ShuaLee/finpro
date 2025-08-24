from django.core.exceptions import ValidationError
from schemas.models import SubPortfolioSchemaLink


def delete_schema_if_allowed(schema):
    """
    Allows deletion if:
    - The schema is orphaned (not referenced by any SubPortfolioSchemaLink)
    - It is not the last schema for its (subportfolio_ct, subportfolio_id, account_model_ct) group.
    """
    links = SubPortfolioSchemaLink.objects.filter(schema=schema)

    if not links.exists():
        # ✅ Safe: no links to this schema
        print(f"[DEBUG] Schema {schema} is orphaned. Allowing deletion.")
        return

    print(
        f"[DEBUG] Schema {schema} has {links.count()} links. Validating each link...")

    for link in links:
        ct = link.subportfolio_ct
        obj_id = link.subportfolio_id
        model_ct = link.account_model_ct

        count = SubPortfolioSchemaLink.objects.filter(
            subportfolio_ct=ct,
            subportfolio_id=obj_id,
            account_model_ct=model_ct
        ).count()

        print(
            f"[DEBUG] Found {count} total schemas for ({ct}, {obj_id}, {model_ct})")

        if count <= 1:
            raise ValidationError(
                "Cannot delete the last schema for this portfolio/account type.")
