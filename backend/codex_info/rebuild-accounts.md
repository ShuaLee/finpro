# Rebuild Accounts Handoff

Date: 2026-02-18
Project: finpro

## Purpose
This file is a handoff summary of the rebuild direction and implementation progress across users/profiles/portfolios/assets/external_data/accounts, with focus on the new `accounts` rebuild state.

## Product Direction We Agreed On
- Keep architecture extensible for future wealth-manager workflows.
- Portfolio model supports:
  - `personal` portfolio (one per profile)
  - `client` portfolios (for future advisor/wealth-manager use)
- Accounts should be generic and reusable (not hardcoded into old stock/metals account subclasses).
- Schemas/formulas are deferred for now. Accounts must work safely without schemas enabled.
- Subscriptions will eventually gate capabilities (limits/features), likely tiers:
  - free
  - main/pro
  - wealth_manager
- MySQL is temporary; PostgreSQL is target. Conditional unique constraints are accepted for now despite MySQL warnings.

## Users + Profiles + Portfolios Status
- User/profile onboarding flow was stabilized and tests passed.
- Profile bootstrap now ensures required defaults (notably currency/plan) and personal portfolio creation.
- Portfolio design now centered around `kind` (`personal`/`client`) and one personal portfolio per profile.

## Assets Direction (Discussed)
- Built-in + custom asset types:
  - built-ins are strict/system-owned
  - user-created types are private to the creator profile
- Holdings should survive market-asset churn from external providers.
- You chose a pragmatic refresh strategy (periodic rebuild of reference asset DB), not long-term historical persistence for now.
- If provider asset disappears, holdings should remain safe and be flagged/untracked instead of breaking.

## External Data Direction (Discussed)
- External data is FMP-first and production-hardening focused.
- Development can proceed without worrying about full paid-tier API coverage yet.
- Failure handling should include retries/timeouts/provider-down behavior and graceful degradation.

## Accounts Rebuild: What Was Changed

### 1) Core Models normalized
Files:
- `apps/accounts/models/account.py`
- `apps/accounts/models/account_type.py`
- `apps/accounts/models/account_classification.py`
- `apps/accounts/models/holding.py`
- `apps/accounts/models/__init__.py`

Key changes:
- Fixed profile FK references to `profiles.Profile`.
- `AccountType` validation hardened:
  - system types cannot have owners
  - custom types must have owners
  - name/slug conflict checks improved
- `Account.active_schema` now resolves schemas lazily via `apps.get_model(...)` and returns `None` if schemas app is disabled.
- Holding validation keeps type compatibility and numeric integrity.

### 2) Services made schema-optional
Files:
- `apps/accounts/services/account_service.py`
- `apps/accounts/services/holding_service.py`
- `apps/accounts/services/account_deletion_service.py`
- `apps/accounts/services/__init__.py`

Key changes:
- Account initialization always sets classification.
- Schema bootstrap/orchestration only runs if schemas services are importable.
- Account deletion only cleans related schema rows when schemas app exists.

### 3) Admin hardened
Files:
- `apps/accounts/admin/account.py`
- `apps/accounts/admin/holding.py`

Key changes:
- Schema actions are now best-effort optional (no crash if schemas disabled).
- Account creation flow requires definition on create and initializes via service.
- Safer search/filter and validation behavior.

### 4) Legacy serializer breakage removed
Files:
- `apps/accounts/serializers/stocks.py`
- `apps/accounts/serializers/metals.py`
- `apps/accounts/serializers/__init__.py`

Key changes:
- Removed dependence on deleted legacy models (`SelfManagedAccount`, `ManagedAccount`, etc).
- Replaced with generic serializers for current `Account` and `Holding` models.

### 5) Seed command aligned with current asset slugs
File:
- `apps/accounts/management/commands/seed_system_account_types.py`

Key changes:
- Uses current canonical asset type slugs and safer seed behavior.

### 6) Tests rewritten for current architecture
File:
- `apps/accounts/tests/test_account_admin.py`

Key changes:
- Replaced stale schema-coupled tests with generic account workflow tests.
- Tests now bootstrap required baseline data (USD, US, free plan) before profile bootstrap.
- Confirms idempotent initialization, uniqueness behavior, and schema-optional operation.

### 7) Migrations
- Added initial accounts migration:
  - `apps/accounts/migrations/0001_initial.py`
- `makemigrations --check --dry-run` shows no pending model changes.

## Current Validation Results
- `python manage.py check` -> passes.
- `python manage.py test accounts.tests.test_account_admin -v 2` -> passes (5 tests).
- MySQL warning remains for conditional unique constraints (`models.W036`) and is expected until PostgreSQL migration.

## Known Caveats / Debt
- Accounts API views/URLs are still mostly legacy/commented stubs and should be rebuilt against the new generic models.
- Some old docs/comments still mention previous account patterns.
- Conditional DB-level uniqueness is not enforced by MySQL; app-level validation currently carries most protection.

## What Needs To Happen Next

### Immediate
1. Rebuild accounts API endpoints on top of current models/services:
   - accounts CRUD
   - holdings CRUD
   - permissions tied to `portfolio.profile.user`
2. Add service/API tests for authorization and edge cases.
3. Add management command bootstrap checks for required baseline data (currency/plan/country).

### After Accounts API
1. Revisit schemas app integration and re-enable intentionally.
2. Rebuild formulas/schemas orchestration only after stable account flows are in place.
3. Wire subscriptions to real entitlement checks:
   - max portfolios/accounts/holdings
   - client portfolio allowance
   - custom asset/type access

### Medium-term
1. PostgreSQL migration.
2. Replace conditional uniqueness reliance with DB-enforced constraints in Postgres.
3. Add operational jobs for asset refresh + dropped-asset handling notifications.

## Commands Used Recently
- `python manage.py check`
- `python manage.py test accounts.tests.test_account_admin -v 2`
- `python manage.py makemigrations --check --dry-run`

## Resume Checklist (On Other Computer)
1. Pull latest branch and install dependencies.
2. Ensure `accounts` is enabled in `INSTALLED_APPS`.
3. Run migrations.
4. Run `manage.py check` and accounts tests.
5. Start accounts API rebuild (views/urls/serializers + tests).
