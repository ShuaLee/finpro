"""
Custom exceptions for the accounts app.

These domain-specific exceptions provide better error handling
and clearer error messages throughout the application.
"""


class AccountError(Exception):
    """Base exception for all account-related errors."""
    pass


class AccountInitializationError(AccountError):
    """Raised when account initialization fails."""
    pass


class SchemaTemplateNotFoundError(AccountInitializationError):
    """Raised when SchemaTemplate doesn't exist for account type."""
    pass


class HoldingError(Exception):
    """Base exception for all holding-related errors."""
    pass


class InvalidAssetTypeError(HoldingError):
    """Raised when asset type is not allowed for the account."""
    pass


class SchemaNotFoundError(HoldingError):
    """Raised when account doesn't have an active schema."""
    pass
