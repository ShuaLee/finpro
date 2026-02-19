from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from schemas.models.schema_column_category import SchemaColumnCategory
from assets.models.core import AssetType


def seed_system_column_catalog():
    """
    Seed global system SchemaColumnTemplates.

    These define WHAT columns exist in the system.
    Asset-type applicability is defined exclusively
    by SchemaColumnTemplateBehaviour.
    """

    equity = AssetType.objects.get(slug="equity")
    crypto = AssetType.objects.get(slug="crypto")

    # --------------------------------------------------
    # Categories (must already be seeded)
    # --------------------------------------------------
    meta = SchemaColumnCategory.objects.get(identifier="meta")
    valuation = SchemaColumnCategory.objects.get(identifier="valuation")
    cash_flow = SchemaColumnCategory.objects.get(identifier="cash_flow")

    # ==================================================
    # QUANTITY (META)
    # ==================================================

    quantity, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="quantity",
        defaults={
            "title": "Quantity",
            "description": "Number of units held",
            "data_type": "decimal",
            "is_system": True,
            "category": meta,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=quantity,
            asset_type=asset_type,
            defaults={
                "source": "holding",
                "formula_identifier": None,
                "source_field": "quantity",
                "constant_value": None,
            },
        )

    # ==================================================
    # ASSET CURRENCY (META)
    # ==================================================

    asset_currency, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="asset_currency",
        defaults={
            "title": "Asset Currency",
            "description": "Currency the asset is denominated in",
            "data_type": "string",
            "is_system": True,
            "category": meta,
            "constraint_overrides": {"enum": "fx_currency"},
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=asset_currency,
            asset_type=asset_type,
            defaults={
                "source": "asset",
                "formula_identifier": None,
                "source_field": "extension__currency__code",
                "constant_value": None,
            },
        )

    # ==================================================
    # PRICE (VALUATION)
    # ==================================================

    price, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="price",
        defaults={
            "title": "Price",
            "description": "Current asset price",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=price,
            asset_type=asset_type,
            defaults={
                "source": "asset",
                "formula_identifier": None,
                "source_field": "price__price",
                "constant_value": None,
            },
        )

    # ==================================================
    # AVERAGE PURCHASE PRICE (VALUATION)
    # ==================================================

    average_purchase_price, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="average_purchase_price",
        defaults={
            "title": "Average Purchase Price",
            "description": "Average purchase price per unit in asset currency.",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=average_purchase_price,
            asset_type=asset_type,
            defaults={
                "source": "holding",
                "formula_identifier": None,
                "source_field": "average_purchase_price",
                "constant_value": None,
            },
        )

    # ==================================================
    # MARKET VALUE (FORMULA)
    # ==================================================

    market_value, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="market_value",
        defaults={
            "title": "Market Value",
            "description": "Market value in asset currency",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=market_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_identifier": "market_value",
                "source_field": None,
                "constant_value": None,
            },
        )

    # ==================================================
    # CURRENT VALUE (FORMULA)
    # ==================================================

    current_value, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="current_value",
        defaults={
            "title": "Current Value",
            "description": "Market value converted to profile currency",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=current_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_identifier": "current_value",
                "source_field": None,
                "constant_value": None,
            },
        )

    # ==================================================
    # COST BASIS (FORMULA, PROFILE CURRENCY)
    # ==================================================

    cost_basis, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="cost_basis",
        defaults={
            "title": "Cost Basis",
            "description": "Cost basis converted to profile currency.",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=cost_basis,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_identifier": "cost_basis",
                "source_field": None,
                "constant_value": None,
            },
        )

    # ==================================================
    # UNREALIZED GAIN (FORMULA, PROFILE CURRENCY)
    # ==================================================

    unrealized_gain, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="unrealized_gain",
        defaults={
            "title": "Unrealized Gain",
            "description": "Current value minus cost basis in profile currency.",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=unrealized_gain,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_identifier": "unrealized_gain",
                "source_field": None,
                "constant_value": None,
            },
        )

    # ==================================================
    # UNREALIZED GAIN PERCENT (FORMULA)
    # ==================================================

    unrealized_gain_pct, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="unrealized_gain_pct",
        defaults={
            "title": "Unrealized Gain %",
            "description": "Unrealized gain divided by cost basis.",
            "data_type": "percent",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=unrealized_gain_pct,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_identifier": "unrealized_gain_pct",
                "source_field": None,
                "constant_value": None,
            },
        )

    # ==================================================
    # DIVIDENDS / CASH FLOW (EQUITY ONLY - NO FORMULAS)
    # ==================================================

    def asset_column(identifier, title, description, data_type, source_field):
        template, _ = SchemaColumnTemplate.objects.update_or_create(
            identifier=identifier,
            defaults={
                "title": title,
                "description": description,
                "data_type": data_type,
                "is_system": True,
                "category": cash_flow,
            },
        )
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=template,
            asset_type=equity,
            defaults={
                "source": "asset",
                "formula_identifier": None,
                "source_field": source_field,
                "constant_value": None,
            },
        )

    # ---- Last Dividend ----
    asset_column(
        "last_dividend_amount",
        "Last Dividend",
        "Most recent dividend payment",
        "decimal",
        "equity_dividend__last_dividend_amount",
    )
    asset_column(
        "last_dividend_date",
        "Last Dividend Date",
        "Date of the most recent dividend",
        "date",
        "equity_dividend__last_dividend_date",
    )
    asset_column(
        "last_dividend_frequency",
        "Dividend Frequency",
        "Frequency of the most recent dividend",
        "string",
        "equity_dividend__last_dividend_frequency",
    )
    asset_column(
        "last_dividend_is_special",
        "Special Dividend",
        "Whether the last dividend was special or irregular",
        "boolean",
        "equity_dividend__last_dividend_is_special",
    )

    # ---- Regular Dividend ----
    asset_column(
        "regular_dividend_amount",
        "Regular Dividend",
        "Most recent regular dividend amount",
        "decimal",
        "equity_dividend__regular_dividend_amount",
    )
    asset_column(
        "regular_dividend_date",
        "Regular Dividend Date",
        "Date of the most recent regular dividend",
        "date",
        "equity_dividend__regular_dividend_date",
    )
    asset_column(
        "regular_dividend_frequency",
        "Regular Dividend Frequency",
        "Frequency of regular dividend payments",
        "string",
        "equity_dividend__regular_dividend_frequency",
    )

    # ---- Trailing / Forward ----
    asset_column(
        "trailing_12m_dividend",
        "Trailing 12M Dividend",
        "Sum of regular dividends over the last 12 months",
        "decimal",
        "equity_dividend__trailing_12m_dividend",
    )
    asset_column(
        "trailing_12m_cashflow",
        "Trailing 12M Cash Flow",
        "Total dividends paid in the last 12 months",
        "decimal",
        "equity_dividend__trailing_12m_cashflow",
    )
    asset_column(
        "forward_annual_dividend",
        "Forward Annual Dividend",
        "Estimated forward 12-month dividend",
        "decimal",
        "equity_dividend__forward_annual_dividend",
    )
    asset_column(
        "dividend_yield",
        "Dividend Yield (Trailing)",
        "Trailing 12-month dividend yield",
        "percent",
        "equity_dividend__trailing_dividend_yield",
    )
    asset_column(
        "forward_dividend_yield",
        "Forward Dividend Yield",
        "Estimated forward dividend yield",
        "percent",
        "equity_dividend__forward_dividend_yield",
    )
    asset_column(
        "trailing_dividend_income",
        "Trailing Dividend Income",
        "Dividend income over the last 12 months",
        "decimal",
        "equity_dividend__trailing_12m_cashflow",
    )
