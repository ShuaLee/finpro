# Final App Revisions Handoff

Date: 2026-02-19  
Project: `finpro`

This is the consolidated handoff for the latest rebuild cycle across core apps.  
Use this as the starting context for the next chat/session.

---

## 1) What Was Completed

### Users + Profiles
- Registration/login/verification/profile flows were stabilized and tested.
- Profile bootstrap was hardened to always set required defaults (currency, plan, country fallback, etc.).
- Main personal portfolio bootstrapping is enforced from profile bootstrap.
- Auth lockout flow (failed login throttling/lock window) is in place.

### Subscriptions
- Tiered plan structure established (`free`, paid/pro-style, `wealth_manager` direction).
- Subscription lifecycle/service path implemented so entitlement logic is centralized.
- Baseline seed behavior exists for default plan usage.

### Portfolios
- Portfolio model supports `personal` + `client`.
- One personal portfolio per profile enforced.
- Guardrails added:
  - personal portfolio cannot be deleted
  - personal portfolio kind/name/client_name cannot be mutated into invalid states
- Portfolio tests added for guardrail behavior.
- Portfolio valuation feature set added (snapshots/denominations path for total-value representation).

### Assets
- App rebuilt to production-oriented model/service/API structure with system + private/custom behavior.
- Asset type strategy supports strict built-ins and user-private custom types.
- Equity market refresh/snapshot pattern operational.
- Real estate cashflow direction simplified toward direct fields (no overcomplicated side-models unless needed).

### External Data
- FMP integration hardened for provider-style usage and failure boundaries.
- Error paths and guardrails improved for unavailable/downstream failures.
- App positioned as FMP-first provider layer for current scope.

### Accounts
- Rebuilt around generic account + holding architecture (instead of fragmented legacy account subclasses).
- Ownership and privacy constraints enforced along profile/portfolio/account/holding chain.
- Reconciliation and sync patterns integrated with assets/external-data direction.

### Schemas + Formulas
- Both apps rebuilt toward production-grade baseline:
  - schema column templates/behaviors
  - formula-driven computed columns
  - system vs user input separation
- Key requirement enforced in design: `current_value` must resolve in profile currency.

### Analytics
- Analytics app implemented to summarize holdings exposure/groupings from schema-driven values.
- Starter analytics templates were added as requested.

### Allocations
- Allocations app implemented for user target ratios/goals (distinct from analytics actual-state summaries).
- Designed to reference schema-level classification headers similarly to analytics.

### Core Bootstrap
- Central `bootstrap_finpro` orchestration and app-level bootstraps were wired/refined.
- Direction: each app has local bootstrap logic, core orchestrator controls order.

---

## 2) Major Architecture Decisions Confirmed

1. Keep `portfolio` model unified with `personal` and `client` kinds.
2. Keep one personal portfolio invariant per user/profile.
3. Wealth-manager capability should be entitlement/subscription-driven, not a separate user system.
4. Keep analytics (actual state) separate from allocations (target state).
5. Keep schemas account-based, with per-account visibility controls (hide/show columns) rather than schema forks.
6. Use snapshot-based market-asset refreshes; preserve holdings even when provider universe changes.

---

## 3) Critical Fixes Done Most Recently (Today)

## Equity reseed -> SCV update failure
Problem observed:
- After `seed_equities`, then running sync commands, holdings/SCVs were not refreshing with new price/dividend data.

Root cause:
- Snapshot cleanup converted stale holdings to custom market assets instead of relinking them to newly seeded active market assets when ticker still existed.
- `full_equity_sync` command was not actually a true full-universe sync.

Fixes implemented:
- `apps/assets/services/base/snapshot_cleanup_base.py`
  - relink stale holdings to active market assets first (ticker/name match strategy per extension config)
  - merge duplicate holdings safely if relink target already exists
  - recovery pass to relink previously converted `MARKET` custom assets back to market assets when ticker returns
- `apps/assets/management/commands/full_equity_sync.py`
  - rebuilt to run profile + price + dividend sync across active snapshot (or optional single ticker)
- `apps/assets/tests.py`
  - added regression tests for relink and market-custom recovery scenarios

Follow-up bug fixed:
- `CustomAsset` has no `id` field (PK is `asset`), so cleanup ordering/filter logic was corrected to use `asset_id`/`pk`.

---

## 4) Current Operational Sequence

After pulling this branch on another machine:
1. `python manage.py migrate`
2. `python manage.py bootstrap_finpro`
3. `python manage.py seed_equities`
4. `python manage.py full_equity_sync`
5. run focused tests for changed domains (`assets`, `users/profiles`, `portfolios`, `schemas/formulas`, `analytics/allocations` as needed)

If you reseed equities periodically:
- run `seed_equities` first
- then run `full_equity_sync` to refresh profile/price/dividend data and downstream schema values

---

## 5) Known Notes / Constraints

- MySQL warning on conditional unique constraints (`models.W036`) is expected and accepted for now.
- Planned DB target remains PostgreSQL (where conditional constraints are fully supported).
- FMP key handling is currently temporarily hardcoded by choice during development; move back to env secret before production.

---

## 6) What To Do Next

1. Validate end-to-end SCV refresh after equity reseed in your real dataset (especially `price`, `asset_currency`, `trailing_12m_dividend`, `dividend_yield`, and formula columns like `current_value`).
2. Run a full regression pass for schemas/formulas/analytics/allocations interactions.
3. Finish subscription entitlement enforcement hooks across all creation/update paths (limits/features).
4. Add/confirm admin/API UX for “asset no longer tracked / requires review” flows.
5. Prepare final PostgreSQL migration plan once model churn slows.

---

## 7) Key Files Changed in Latest Round (high-signal)

- `apps/assets/services/base/snapshot_cleanup_base.py`
- `apps/assets/management/commands/full_equity_sync.py`
- `apps/assets/tests.py`
- `apps/portfolios/models/portfolio.py`
- `apps/portfolios/tests/test_portfolio_guardrails.py`
- `apps/core/services/bootstrap_orchestrator.py`
- `apps/core/management/commands/bootstrap_finpro.py`

Also includes broad migration regeneration across apps (`users`, `profiles`, `subscriptions`, `fx`, `assets`, `accounts`, `schemas`, `formulas`, `analytics`, `allocations`, `portfolios`).

