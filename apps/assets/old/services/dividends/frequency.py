"""
Dividend frequency utilities.

This module provides a thin, provider-agnostic layer for interpreting
dividend frequency strings into numerical multipliers.

It intentionally performs *no validation* and *no persistence*.
Unknown frequencies return None and are handled upstream.
"""

from typing import Optional

# Canonical multipliers used for forward dividend calculations
FREQUENCY_MULTIPLIERS: dict[str, int] = {
    "Monthly": 12,
    "Quarterly": 4,
    "Semi-Annual": 2,
    "SemiAnnual": 2,
    "Annual": 1,
}


def normalize_frequency(value: Optional[str]) -> Optional[str]:
    """
    Normalize a frequency string into a consistent display form.

    This does NOT guarantee the value is supported for calculations.
    It exists only to reduce cosmetic variation.
    """
    if not value:
        return None

    return value.strip()


def frequency_multiplier(value: Optional[str]) -> Optional[int]:
    """
    Return the annualization multiplier for a dividend frequency.

    Returns None for:
    - unknown frequencies
    - irregular dividends
    - missing values

    Callers must decide how to handle unsupported frequencies.
    """
    if not value:
        return None

    return FREQUENCY_MULTIPLIERS.get(value.strip())
