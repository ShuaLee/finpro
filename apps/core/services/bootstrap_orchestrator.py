from __future__ import annotations

from dataclasses import dataclass

from django.core.management import call_command
from django.core.management.base import CommandError


@dataclass(frozen=True)
class BootstrapStep:
    label: str
    command: str
    kwargs: dict


class FinproBootstrapOrchestrator:
    @staticmethod
    def build_steps(
        *,
        include_migrate: bool,
        skip_market_data: bool,
        portfolio_ids: list[int] | None,
    ) -> list[BootstrapStep]:
        analytics_kwargs = {}
        portfolio_kwargs = {}
        if portfolio_ids:
            analytics_kwargs["portfolio_id"] = portfolio_ids
            portfolio_kwargs["portfolio_id"] = portfolio_ids

        steps = []
        if include_migrate:
            steps.append(BootstrapStep("Migrations", "migrate", {}))

        steps.extend([
            BootstrapStep("FX", "bootstrap_fx", {}),
            BootstrapStep("Subscriptions", "bootstrap_subscriptions", {}),
            BootstrapStep("Assets", "bootstrap_assets", {"skip_market_data": skip_market_data}),
            BootstrapStep("Accounts", "bootstrap_accounts", {}),
            BootstrapStep("Formulas", "bootstrap_formulas", {}),
            BootstrapStep("Schemas", "bootstrap_schemas", {}),
            BootstrapStep("Portfolios", "bootstrap_portfolios", portfolio_kwargs),
            BootstrapStep("Analytics", "bootstrap_analytics", analytics_kwargs),
            BootstrapStep("Allocations", "bootstrap_allocations", {}),
        ])
        return steps

    @staticmethod
    def run(
        *,
        stdout,
        style,
        include_migrate: bool = False,
        skip_market_data: bool = False,
        portfolio_ids: list[int] | None = None,
    ):
        steps = FinproBootstrapOrchestrator.build_steps(
            include_migrate=include_migrate,
            skip_market_data=skip_market_data,
            portfolio_ids=portfolio_ids,
        )

        stdout.write(style.SUCCESS("Starting FinPro bootstrap..."))
        for step in steps:
            stdout.write(style.WARNING(f"[{step.label}] `{step.command}`"))
            try:
                call_command(step.command, **step.kwargs)
            except Exception as exc:
                raise CommandError(
                    f"Bootstrap failed at step '{step.label}' ({step.command}): {exc}. "
                    "If this is a fresh database, run with --with-migrate."
                ) from exc
        stdout.write(style.SUCCESS("FinPro bootstrap complete."))
