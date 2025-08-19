from django.apps import apps
from collections import defaultdict

ACCOUNT_MODEL_MAP = defaultdict(dict)

for model in apps.get_models():
    if hasattr(model, "asset_type") and hasattr(model, "account_variant"):
        ACCOUNT_MODEL_MAP[model.asset_type][model.account_variant] = model
