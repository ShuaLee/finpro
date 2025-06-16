from .stocks import fetch_stock_data, apply_fmp_stock_data
import logging

logger = logging.getLogger(__name__)

def fetch_asset_data(asset_obj, asset_type: str, *, verify_custom=False) -> bool:
    """
    Centralized fetcher for any asset type (e.g. stock, precious_metal).
    Updates the asset in place based on external data.
    """
    if asset_type == 'stock':
        if asset_obj.is_custom and not verify_custom:
            logger.info(f"Skipping fetch for custom stock: {asset_obj.ticker}")
            return True
        
        data = fetch_stock_data(asset_obj.ticker)
        if not data:
            if verify_custom:
                asset_obj.is_custom = True
            return False
        
        success = apply_fmp_stock_data(asset_obj, data['quote'], data['profile'])
        if success:
            asset_obj.is_custom = False
        return success
    
    raise NotImplementedError(f"Unsupported asset type: {asset_type}")