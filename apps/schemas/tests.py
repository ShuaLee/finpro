from django.test import SimpleTestCase

from schemas.policies.default_schema_policy import DefaultSchemaPolicy
from schemas.services.formula_bridge import is_implicit_identifier


class SchemaPolicyTests(SimpleTestCase):
    def test_default_policy_supports_crypto_slug_variants(self):
        expected = [
            "quantity",
            "average_purchase_price",
            "price",
            "asset_currency",
            "market_value",
            "current_value",
            "cost_basis",
            "unrealized_gain",
            "unrealized_gain_pct",
        ]
        self.assertEqual(
            DefaultSchemaPolicy.default_identifiers_for_account_type(
                type("T", (), {"slug": "crypto-wallet"})()
            ),
            expected,
        )
        self.assertEqual(
            DefaultSchemaPolicy.default_identifiers_for_account_type(
                type("T", (), {"slug": "crypto_wallet"})()
            ),
            expected,
        )
        self.assertEqual(
            DefaultSchemaPolicy.default_identifiers_for_account_type(
                type("T", (), {"slug": "crypto"})()
            ),
            expected,
        )

    def test_implicit_formula_identifier_registry(self):
        self.assertTrue(is_implicit_identifier("fx_rate"))
        self.assertFalse(is_implicit_identifier("quantity"))
