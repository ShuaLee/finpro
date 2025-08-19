from django.apps import apps
from collections import defaultdict

ACCOUNT_MODEL_MAP = defaultdict(dict)

for model in apps.get_models():
    if hasattr(model, "asset_type") and hasattr(model, "account_variant"):
        ACCOUNT_MODEL_MAP[model.asset_type][model.account_variant] = model

# ---- Optional: Manual Registration for Custom/Virtual Accounts ----
# These accounts may not exist as DB models, or may be created by the user

# CUSTOM_ACCOUNT_REGISTRY = defaultdict(dict)

# def register_custom_account(asset_type: str, account_variant: str, class_reference):
#     """
#     Register a non-model or runtime-defined account type.
#     """
#     CUSTOM_ACCOUNT_REGISTRY[asset_type][account_variant] = class_reference

def get_account_model_map(asset_type: str) -> dict:
    """
    Get a combined map of all account model classes for an asset type.
    """
    combined = {}
    combined.update(ACCOUNT_MODEL_MAP.get(asset_type, {}))
    # combined.update(CUSTOM_ACCOUNT_REGISTRY.get(asset_type, {}))
    return {
        cls: variant.replace("_", " ").title()
        for variant, cls in combined.items()
    }