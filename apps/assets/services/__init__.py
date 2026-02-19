from __future__ import annotations

from importlib import import_module

__all__ = [
    "AssetPolicyService",
    "CustomAssetService",
    "RealEstateAssetService",
    "RealEstateTypeService",
]


def __getattr__(name: str):
    if name == "AssetPolicyService":
        return import_module("assets.services.policy").AssetPolicyService
    if name == "CustomAssetService":
        return import_module("assets.services.custom").CustomAssetService
    if name == "RealEstateAssetService":
        return import_module("assets.services.real_estate").RealEstateAssetService
    if name == "RealEstateTypeService":
        return import_module("assets.services.real_estate").RealEstateTypeService
    raise AttributeError(f"module 'assets.services' has no attribute '{name}'")
