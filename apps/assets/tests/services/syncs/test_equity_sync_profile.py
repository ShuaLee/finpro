import pytest
from unittest.mock import patch
from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from assets.services.syncs.equity_sync import EquitySyncService
from core.types import DomainType


@pytest.mark.django_db
class TestSyncProfile:
    def make_asset(self, ticker: str | None = "TEST", is_custom: bool = False, status: str = "PENDING") -> Asset:
        asset = Asset.objects.create(
            asset_type=DomainType.EQUITY,
            name="Test Corp",
            currency="USD",
            is_custom=is_custom,
        )
        if ticker:
            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=ticker,
                is_primary=True,
            )
        EquityDetail.objects.create(asset=asset, listing_status=status)
        return asset

    # --- Happy path ---

    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_valid_ticker_success(self, mock_fetch):
        mock_fetch.return_value = {
            "companyName": "Apple Inc", "currency": "USD"}
        asset = self.make_asset("AAPL")
        result = EquitySyncService.sync_profile(asset)
        asset.refresh_from_db()
        detail = asset.equity_detail
        assert result is True
        assert asset.name == "Apple Inc"
        assert asset.currency == "USD"
        assert detail.listing_status == "ACTIVE"

    # --- No profile ---
    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_no_data_marks_delisted_non_custom(self, mock_fetch):
        mock_fetch.return_value = None
        asset = self.make_asset("MISSING")
        result = EquitySyncService.sync_profile(asset)
        detail = asset.equity_detail
        detail.refresh_from_db()
        assert result is False
        assert detail.listing_status == "DELISTED"

    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_no_data_custom_not_delisted(self, mock_fetch):
        mock_fetch.return_value = None
        asset = self.make_asset("MISSING", is_custom=True, status="CUSTOM")
        result = EquitySyncService.sync_profile(asset)
        detail = asset.equity_detail
        assert result is False
        assert detail.listing_status == "CUSTOM"  # stays unchanged

    def test_no_ticker_no_identifier_delists_non_custom(self):
        asset = self.make_asset(ticker=None)
        result = EquitySyncService.sync_profile(asset)
        detail = asset.equity_detail
        detail.refresh_from_db()
        assert result is False
        assert detail.listing_status == "DELISTED"

    # --- Identifier fallback ---
    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    @patch("assets.services.syncs.equity_sync.fetch_equity_by_isin")
    def test_fallback_via_isin(self, mock_by_isin, mock_profile):
        mock_profile.return_value = None
        mock_by_isin.return_value = {
            "symbol": "NEW", "companyName": "New Corp"}
        asset = self.make_asset(ticker="OLD")
        AssetIdentifier.objects.create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.ISIN,
            value="ISIN123",
        )
        result = EquitySyncService.sync_profile(asset)
        asset.refresh_from_db()
        detail = asset.equity_detail
        assert result is True
        assert asset.identifiers.filter(value="NEW", is_primary=True).exists()
        assert asset.name == "New Corp"
        assert detail.listing_status == "ACTIVE"

    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    @patch("assets.services.syncs.equity_sync.fetch_equity_by_cusip")
    def test_fallback_via_cusip(self, mock_by_cusip, mock_profile):
        mock_profile.return_value = None
        mock_by_cusip.return_value = {"symbol": "CUSIPSYM"}
        asset = self.make_asset("OLD")
        AssetIdentifier.objects.create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.CUSIP,
            value="CUSIP123",
        )
        result = EquitySyncService.sync_profile(asset)
        assert result is True
        assert asset.identifiers.filter(
            value="CUSIPSYM", is_primary=True).exists()

    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    @patch("assets.services.syncs.equity_sync.fetch_equity_by_cik")
    def test_fallback_via_cik(self, mock_by_cik, mock_profile):
        mock_profile.return_value = None
        mock_by_cik.return_value = {"symbol": "CIKSYM"}
        asset = self.make_asset("OLD")
        AssetIdentifier.objects.create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.CIK,
            value="CIK123",
        )
        result = EquitySyncService.sync_profile(asset)
        assert result is True
        assert asset.identifiers.filter(
            value="CIKSYM", is_primary=True).exists()

    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    @patch("assets.services.syncs.equity_sync.fetch_equity_by_isin")
    def test_identifier_fails_marks_delisted(self, mock_by_isin, mock_profile):
        mock_profile.return_value = None
        mock_by_isin.return_value = None
        asset = self.make_asset("OLD")
        AssetIdentifier.objects.create(
            asset=asset,
            id_type=AssetIdentifier.IdentifierType.ISIN,
            value="ISIN123",
        )
        result = EquitySyncService.sync_profile(asset)
        detail = asset.equity_detail
        detail.refresh_from_db()
        assert result is False
        assert detail.listing_status == "DELISTED"

    # --- Ticker healing ---
    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_profile_reveals_new_symbol(self, mock_fetch):
        mock_fetch.return_value = {
            "symbol": "NEW", "companyName": "Renamed Corp"}
        asset = self.make_asset("OLD")
        result = EquitySyncService.sync_profile(asset)
        assert result is True
        assert asset.identifiers.filter(value="NEW", is_primary=True).exists()
        assert not asset.identifiers.filter(
            value="OLD", is_primary=True).exists()
        assert asset.name == "Renamed Corp"

    # --- Company name update ---
    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_profile_updates_company_name(self, mock_fetch):
        mock_fetch.return_value = {"companyName": "Updated Corp"}
        asset = self.make_asset("AAPL")
        EquitySyncService.sync_profile(asset)
        asset.refresh_from_db()
        assert asset.name == "Updated Corp"

    # --- Partial profile ---
    @patch("assets.services.syncs.equity_sync.fetch_equity_profile")
    def test_profile_partial_fields(self, mock_fetch):
        mock_fetch.return_value = {"currency": "EUR"}
        asset = self.make_asset("AAPL")
        EquitySyncService.sync_profile(asset)
        detail = asset.equity_detail
        assert asset.currency == "EUR"
