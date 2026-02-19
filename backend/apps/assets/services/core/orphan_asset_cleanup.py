from assets.models.core import Asset


def cleanup_orphan_assets():
    Asset.objects.filter(
        asset_type__slug__in=["crypto", "equity"],
        crypto__isnull=True,
        equity__isnull=True,
    ).delete()