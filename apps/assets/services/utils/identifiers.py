from assets.models.asset_core import AssetIdentifier


def get_primary_ticker(asset):
    ident = asset.identifiers.filter(
        id_type=AssetIdentifier.IdentifierType.TICKER,
        is_primary=True,
    ).first()
    return ident.value if ident else None


def hydrate_identifiers(asset, identifiers: dict):
    """
    identifiers = {
        "TICKER": "...",
        "ISIN": "...",
        "CUSIP": "...",
        "CIK": "..."
    }
    """

    map_ = {
        "ISIN": AssetIdentifier.IdentifierType.ISIN,
        "CUSIP": AssetIdentifier.IdentifierType.CUSIP,
        "CIK": AssetIdentifier.IdentifierType.CIK,
    }

    for key, id_type in map_.items():
        val = identifiers.get(key)
        if not val:
            continue

        AssetIdentifier.objects.get_or_create(
            asset=asset, id_type=id_type, value=val
        )
