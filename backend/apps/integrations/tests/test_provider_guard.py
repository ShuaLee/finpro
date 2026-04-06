from django.test import SimpleTestCase

from apps.integrations.exceptions import InvalidProviderResponse, ProviderUnavailable
from apps.integrations.shared.provider_guard import ProviderGuard


class ProviderGuardTests(SimpleTestCase):
    def test_unknown_exceptions_are_normalized_and_counted_as_failures(self):
        class BrokenProvider:
            def explode(self):
                raise RuntimeError("boom")

        guard = ProviderGuard(name="Broken", provider=BrokenProvider())

        with self.assertRaises(ProviderUnavailable):
            guard.explode()

        self.assertEqual(guard.consecutive_failures, 1)

    def test_domain_errors_pass_through_without_incrementing_failures(self):
        class SemanticProvider:
            def fail(self):
                raise InvalidProviderResponse("bad payload")

        guard = ProviderGuard(name="Semantic", provider=SemanticProvider())

        with self.assertRaises(InvalidProviderResponse):
            guard.fail()

        self.assertEqual(guard.consecutive_failures, 0)
