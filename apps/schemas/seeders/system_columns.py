from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from schemas.models.schema_column_category import SchemaColumnCategory
from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition


def seed_system_column_catalog():
    """
    Seed global system SchemaColumnTemplates.

    These define WHAT columns exist in the system.
    Asset-type applicability is defined exclusively
    by SchemaColumnTemplateBehaviour.
    """

    equity = AssetType.objects.get(slug="equity")
    crypto = AssetType.objects.get(slug="cryptocurrency")

    # --------------------------------------------------
    # Categories (must already be seeded)
    # --------------------------------------------------
    meta = SchemaColumnCategory.objects.get(identifier="meta")
    valuation = SchemaColumnCategory.objects.get(identifier="valuation")
    cash_flow = SchemaColumnCategory.objects.get(identifier="cash_flow")

    # ==================================================
    # Quantity (Meta)
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
                "source_field": "quantity",
            },
        )

    # ==================================================
    # Asset Currency (Meta)
    # ==================================================

    asset_currency, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="asset_currency",
        defaults={
            "title": "Asset Currency",
            "description": "Currency the asset is denominated in",
            "data_type": "string",
            "is_system": True,
            "category": meta,
            "constraint_overrides": {
                "enum": "fx_currency"
            },
        },
    )

    # --------------------------------------------------
    # Equity behavior
    # --------------------------------------------------
    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=asset_currency,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "extension__currency__code",
        },
    )

    # --------------------------------------------------
    # Crypto behavior
    # --------------------------------------------------
    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=asset_currency,
        asset_type=crypto,
        defaults={
            "source": "asset",
            "source_field": "extension__currency__code",
        },
    )

    # ==================================================
    # Price (Valuation)
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
                "source_field": "price__price",
            },
        )

    # ==================================================
    # Market Value (asset currency) – Valuation
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
        definition = FormulaDefinition.objects.get(
            identifier="market_value",
            asset_type=asset_type,
            owner__isnull=True,
        )

        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=market_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_definition": definition,
            },
        )

    # ==================================================
    # Current Value (profile currency) – Valuation
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
        definition = FormulaDefinition.objects.get(
            identifier="current_value",
            asset_type=asset_type,
            owner__isnull=True,
        )

        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=current_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_definition": definition,
            },
        )

    # ==================================================
    # DIVIDENDS / CASH FLOW (Equity only)
    # ==================================================

    # -------------------------
    # Last Dividend
    # -------------------------

    last_dividend_amount, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="last_dividend_amount",
        defaults={
            "title": "Last Dividend",
            "description": "Most recent dividend payment",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=last_dividend_amount,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__last_dividend_amount",
        },
    )

    last_dividend_date, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="last_dividend_date",
        defaults={
            "title": "Last Dividend Date",
            "description": "Date of the most recent dividend",
            "data_type": "date",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=last_dividend_date,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__last_dividend_date",
        },
    )

    last_dividend_frequency, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="last_dividend_frequency",
        defaults={
            "title": "Dividend Frequency",
            "description": "Frequency of the most recent dividend",
            "data_type": "string",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=last_dividend_frequency,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__last_dividend_frequency",
        },
    )

    last_dividend_is_special, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="last_dividend_is_special",
        defaults={
            "title": "Special Dividend",
            "description": "Whether the last dividend was special/irregular",
            "data_type": "boolean",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=last_dividend_is_special,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__last_dividend_is_special",
        },
    )

    # -------------------------
    # Regular Dividend (Normalized)
    # -------------------------

    regular_dividend_amount, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="regular_dividend_amount",
        defaults={
            "title": "Regular Dividend",
            "description": "Most recent regular dividend amount",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=regular_dividend_amount,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__regular_dividend_amount",
        },
    )

    regular_dividend_date, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="regular_dividend_date",
        defaults={
            "title": "Regular Dividend Date",
            "description": "Date of the most recent regular dividend",
            "data_type": "date",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=regular_dividend_date,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__regular_dividend_date",
        },
    )

    regular_dividend_frequency, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="regular_dividend_frequency",
        defaults={
            "title": "Regular Dividend Frequency",
            "description": "Frequency of regular dividend payments",
            "data_type": "string",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=regular_dividend_frequency,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__regular_dividend_frequency",
        },
    )

    # -------------------------
    # Trailing / Forward Cash Flow
    # -------------------------

    trailing_12m_dividend, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="trailing_12m_dividend",
        defaults={
            "title": "Trailing 12M Dividend",
            "description": "Sum of dividends over the last 12 months (regular only)",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=trailing_12m_dividend,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__trailing_12m_dividend",
        },
    )

    trailing_12m_cashflow, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="trailing_12m_cashflow",
        defaults={
            "title": "Trailing 12M Cash Flow",
            "description": "Total cash dividends paid in the last 12 months",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=trailing_12m_cashflow,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__trailing_12m_cashflow",
        },
    )

    forward_annual_dividend, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="forward_annual_dividend",
        defaults={
            "title": "Forward Annual Dividend",
            "description": "Estimated forward 12-month dividend",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=forward_annual_dividend,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "dividend_snapshot__forward_annual_dividend",
        },
    )

    dividend_yield, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="dividend_yield",
        defaults={
            "title": "Dividend Yield (Trailing)",
            "description": "Trailing 12-month dividend yield",
            "data_type": "percent",
            "is_system": True,
            "category": cash_flow,
        },
    )

    definition = FormulaDefinition.objects.get(
        identifier="dividend_yield",
        asset_type=equity,
        owner__isnull=True,
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=dividend_yield,
        asset_type=equity,
        defaults={
            "source": "formula",
            "formula_definition": definition,
        },
    )

    forward_dividend_yield, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="forward_dividend_yield",
        defaults={
            "title": "Forward Dividend Yield",
            "description": "Estimated forward annual dividend yield",
            "data_type": "percent",
            "is_system": True,
            "category": cash_flow,
        },
    )

    definition = FormulaDefinition.objects.get(
        identifier="forward_dividend_yield",
        asset_type=equity,
        owner__isnull=True,
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=forward_dividend_yield,
        asset_type=equity,
        defaults={
            "source": "formula",
            "formula_definition": definition,
        },
    )

    trailing_dividend_income, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="trailing_dividend_income",
        defaults={
            "title": "Trailing Dividend Income",
            "description": "Dividend income over the last 12 months",
            "data_type": "decimal",
            "is_system": True,
            "category": cash_flow,
        },
    )

    definition = FormulaDefinition.objects.get(
        identifier="trailing_dividend_income",
        asset_type=equity,
        owner__isnull=True,
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=trailing_dividend_income,
        asset_type=equity,
        defaults={
            "source": "formula",
            "formula_definition": definition,
        },
    )
