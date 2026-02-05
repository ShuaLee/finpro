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
                "source_field": "quantity",
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
                "source_field": "extension__currency__code",
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
                "source_field": "price__price",
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
    # DIVIDENDS / CASH FLOW (EQUITY ONLY — NO FORMULAS)
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
                "source_field": source_field,
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
        "equity_dividend__trailing_dividend_income",
    )
