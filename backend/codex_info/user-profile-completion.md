# FinPro Rebuild Completion Notes (Users, Profiles, Subscriptions, Portfolios)

Date: 2026-02-17
Scope updated in this session:
- `apps/users`
- `apps/profiles`
- `apps/subscriptions`
- `apps/portfolios`
- `finpro/settings.py`

---

## 1. Users + Profiles hardening completed

### 1.1 Password reset foundation
Added:
- `apps/users/models/password_reset.py` (`PasswordResetToken`)
- `apps/users/services/password_reset_service.py`
- `apps/users/admin/password_reset_admin.py`
- `apps/users/migrations/0002_passwordresettoken.py`
- exports in model/service/admin packages

Why:
- Production-safe password recovery requires one-time, expiring, hashed reset tokens.

### 1.2 Email verification hardening
Updated:
- `apps/users/services/email_verification_service.py`

What changed:
- resend cooldown support
- invalidation of prior active verification tokens on reissue

Why:
- Prevent abuse and keep token lifecycle deterministic.

### 1.3 Auth endpoints and serializers expanded
Updated:
- `apps/users/serializers/auth.py`
- `apps/users/views/auth.py`
- `apps/users/urls/auth_urls.py`
- package exports

Added endpoints/flows:
- forgot password
- reset password
- change password
- me
- auth status

Why:
- Complete account lifecycle and frontend-ready auth surface.

### 1.4 Cookie JWT authentication security
Updated:
- `apps/users/authentication.py`

What changed:
- CSRF enforcement for state-changing requests when auth is cookie-based.

Why:
- Cookie JWT without CSRF checks is vulnerable in production.

### 1.5 Dev toggle for email verification requirement
Updated:
- `apps/users/services/auth_service.py`
- `finpro/settings.py`

What changed:
- Added `AUTH_REQUIRE_EMAIL_VERIFICATION` toggle.
- Set to `False` currently for development speed.

Why:
- Keep production-safe behavior available while unblocking local development.

### 1.6 Profile API hardening and resilience
Updated:
- `apps/profiles/serializers/profile.py`
- `apps/profiles/views/profile.py`

What changed:
- language and timezone validation
- read-only protection for privileged fields (`plan`, `account_type`, onboarding state)
- auto-bootstrap profile if missing instead of failing

Why:
- Prevent privilege escalation via profile patch.
- Avoid brittle runtime failures.

---

## 2. Subscriptions rebuild (bare-bones tiers + lifecycle)

### 2.1 Plan model expanded to tier/limits/features
Updated:
- `apps/subscriptions/models/plan.py`

Added:
- tier enum: `free`, `pro`, `wealth_manager`
- coarse limits (portfolio/account/holding caps)
- feature flags (`custom_*`, `advanced_analytics_enabled`, `allocations_enabled`, `client_mode_enabled`, etc.)
- `is_public`

Why:
- Support product-tier gating without overbuilding schema-level policies yet.

### 2.2 Profile-scoped subscription model
Added:
- `apps/subscriptions/models/subscription.py`
- export in `apps/subscriptions/models/__init__.py`

Model:
- one-to-one with profile
- current plan + status + period fields

Why:
- `Plan` is catalog; `Subscription` is per-user effective state.

### 2.3 Subscription services
Added:
- `apps/subscriptions/services/subscription_service.py`
- `apps/subscriptions/services/access_service.py`
- `apps/subscriptions/services/__init__.py`

Capabilities:
- ensure default subscription
- change plan
- downgrade to free
- resolve effective plan and enforce portfolio creation permissions

Why:
- Centralized entitlement and lifecycle logic.

### 2.4 Subscription API + serializer
Added/updated:
- `apps/subscriptions/views/subscription.py`
- `apps/subscriptions/views/__init__.py`
- `apps/subscriptions/serializers/subscription.py`
- `apps/subscriptions/serializers/plan.py`
- `apps/subscriptions/serializers/__init__.py`
- `apps/subscriptions/urls.py`

New endpoint:
- `GET /api/v1/subscriptions/me/`

Why:
- Frontend needs current tier/status view.

### 2.5 Default seed tiers updated
Updated:
- `apps/subscriptions/signals.py`

Now seeds/updates:
- `free`
- `pro`
- `wealth-manager`
- account types: `individual`, `wealth_manager`

Why:
- Deterministic defaults required for bootstrap and entitlement checks.

### 2.6 Subscription admin controls
Updated:
- `apps/subscriptions/admin.py`

Added:
- Subscription admin registration
- actions: set to Free/Pro/Wealth Manager

Why:
- Manual operational control during development and support.

### 2.7 Migration added
Added:
- `apps/subscriptions/migrations/0002_subscription_and_plan_limits.py`

---

## 3. Portfolio updates (personal/client support + guarantees)

### 3.1 Portfolio model extended
Updated:
- `apps/portfolios/models/portfolio.py`

Added:
- `kind` (`personal`, `client`)
- `client_name`
- `related_name='portfolios'`
- index on `(profile, kind)`
- constraints:
  - one main portfolio per profile
  - profile/name uniqueness
  - client portfolio requires non-empty `client_name`
  - main portfolio must be personal and not client-named

Why:
- Keep one model for both personal and client tracking while preserving integrity.

### 3.2 Portfolio manager enforcement
Updated:
- `apps/portfolios/services/portfolio_manager.py`
- `apps/portfolios/services/__init__.py`

Added:
- `create_portfolio(...)` with entitlement checks via subscription service
- `ensure_main_portfolio(...)` now self-heals malformed main portfolio

Why:
- Enforce tier limits and keep foundational portfolio consistent.

### 3.3 Portfolio model lifecycle guards
Updated:
- `apps/portfolios/models/portfolio.py`

Added:
- `clean()` and `save()` full validation
- prevent deleting main portfolio
- prevent removing only main portfolio

Why:
- Avoid invalid states even outside service-layer usage.

### 3.4 Portfolio admin cleanup
Updated:
- `apps/portfolios/admin/admin.py`

What changed:
- expose `kind` and `client_name`
- remove invalid `username` search assumption

### 3.5 Migrations added
Added:
- `apps/portfolios/migrations/0003_portfolio_kind_and_client_fields.py`
- `apps/portfolios/migrations/0004_main_portfolio_constraint.py`

---

## 4. Guaranteed foundations (new behavior)

### 4.1 On user creation (including admin-created users)
Added:
- `apps/users/signals.py`
- `apps/users/apps.py` ready hook

Behavior:
- user create triggers profile bootstrap after commit.

### 4.2 On profile creation
Added:
- `apps/profiles/signals.py`
- `apps/profiles/apps.py` ready hook

Behavior:
- ensures subscription + main portfolio after commit.

### 4.3 Backfill existing users
Added:
- `apps/users/management/commands/backfill_user_foundations.py`

Behavior:
- iterates all users and enforces profile/subscription/main portfolio via bootstrap.

---

## 5. Tests/verification notes

- Python compile checks passed for edited modules.
- In this shell, Django runtime was unavailable (`ModuleNotFoundError: No module named 'django'`), so migrations/tests were not executed here.

Run locally in your venv:
1. `python manage.py migrate`
2. `python manage.py backfill_user_foundations`
3. `python manage.py test`

---

## 6. Current practical outcome

- New users are now designed to be provisioned with:
  - Profile
  - Free-tier subscription
  - Main personal portfolio
- Tier upgrades/downgrades now have service/admin pathways.
- Portfolio model supports client portfolios without splitting into a second class.
- Core data-integrity protections are in both service and model/database layers.

---

## 7. Latest Update (After Prior Entry) - February 17, 2026

### 7.1 Subscriptions + Portfolio foundation hardening
What changed:
- Added portfolio kind support (`personal` / `client`) and client metadata in `portfolios.Portfolio`.
- Added entitlement-aware portfolio creation checks via `SubscriptionAccessService`.
- Added profile-scoped `Subscription` model and service flows for ensuring/changing/downgrading plans.
- Added admin actions to move subscriptions between `free`, `pro`, `wealth-manager`.

Why:
- Keep one Portfolio model while enabling wealth-manager client workflows.
- Centralize tier enforcement so future apps can reuse one access policy layer.

### 7.2 Foundational guarantees tightened
What changed:
- Added user creation signal to trigger profile bootstrap automatically.
- Added profile creation signal to ensure subscription + main portfolio.
- Added management command `backfill_user_foundations`.
- Hardened main portfolio integrity rules (must be personal; cannot delete main).

Why:
- Eliminate null/missing foundational records for active users.
- Support both API-created and admin-created users safely.

### 7.3 FX app production hardening
What changed:
- Removed brittle FX model side effects that imported disabled apps (`schemas`, `accounts`) at save-time.
- Added `is_active` support for `FXCurrency` and `Country`.
- Added safer FX constraints/indexes and tightened `FXCurrency.code` length to 3.
- Updated FX seeders to support scalable reconciliation:
  - upsert behavior
  - optional `deactivate_missing` mode
  - reactivation tracking
- Updated `bootstrap_fx` command to support `--deactivate-missing` and structured summary output.
- Updated fetchers to fail explicitly when `FMP_API_KEY` is missing.
- Aligned profile currency/country validation and bootstrap to active FX records only.

Why:
- Make FX reference data refreshable over time (create/update/deactivate) without destructive churn.
- Prevent runtime crashes from cross-app coupling while foundational apps are isolated.

### 7.4 AccountType removal decision + implementation
Decision:
- Removed `AccountType` because plan/subscription tier is now the single source of capability control.

What changed:
- Removed `Profile.account_type` field usage from model, serializer, admin, and bootstrap flow.
- Removed account-type API route and view/serializer modules in subscriptions.
- Removed account-type admin and seed logic.
- Added migrations to:
  - drop `Profile.account_type`
  - delete `subscriptions.AccountType` model
- Updated users/profiles tests that depended on account types.

Why:
- Reduce model bloat and duplicated semantics.
- Keep entitlement model clean: `Plan` + `Subscription` only.

### 7.5 Auth/dev testing clarifications applied
What changed:
- Confirmed register/login/me/profile path behavior and endpoint methods.
- Clarified email verification token behavior:
  - DB stores token hash
  - endpoint requires raw token from console email output.
- Added/used dev toggle to bypass login verification requirement when desired.

Why:
- Speed up local iteration without changing production-oriented architecture.

### 7.6 Logging behavior clarification
Observed:
- Duplicate "Not Found" lines appeared for one 404 request.

Conclusion:
- This is logger output duplication (warning + access logging), not duplicated request execution.

### 7.7 Operational command sequence (current baseline)
Recommended sequence after code sync:
1. `python manage.py migrate`
2. `python manage.py bootstrap_fx` (or `--deactivate-missing`)
3. `python manage.py backfill_user_foundations`
4. run users/profiles/subscriptions smoke tests

### 7.8 Current architecture state
- Foundations now centered on:
  - `users` (identity/auth)
  - `profiles` (user context)
  - `subscriptions` (tier + lifecycle + entitlements)
  - `fx` (reference currencies/countries/rates infra)
  - `portfolios` (personal/client container layer)
- Account capability semantics are now subscription-tier driven, not account-type driven.


---

## 8. Handoff Synopsis (Most Recent Changes)

### Core architecture simplification
- Removed `AccountType` as an active concept.
- Capability/limits are now driven only by `Plan` + `Subscription`.
- Profile bootstrap no longer depends on account-type seed data.

Why:
- `AccountType` overlapped with subscription tier semantics and added maintenance bloat.

### Bootstrap strategy changed: explicit services over signals
- Removed user/profile post-save bootstrap signals.
- Kept foundational creation explicit in service/admin paths:
  - API registration (`AuthService.register_user`) bootstraps foundations.
  - Admin user creation now explicitly calls profile bootstrap.
  - `backfill_user_foundations` remains the repair path for legacy/manual records.

Why:
- Explicit orchestration is easier to reason about and test than hidden signal side effects.

### Portfolio model semantics finalized
- Enforced one personal portfolio per profile.
- Additional portfolios are for `client` kind only (subscription-gated).
- Removed `is_main` field and replaced its role with the personal-portfolio invariant.
- Updated portfolio services to use personal-first methods (`ensure_personal_portfolio`, `get_personal_portfolio`).

Why:
- Matches product direction (one primary investment container per user) while preserving wealth-manager client support.

### Superuser foundation gap fixed
- `create_superuser` now bootstraps profile/subscription/personal portfolio.

Why:
- Ensures admin-created superusers are not left in partial state.

### FX app hardening for production-style sync
- Removed brittle FX save-time coupling to disabled apps.
- Added active/inactive lifecycle for currency/country records.
- Added safer FX constraints and refreshed sync behavior (upsert/reactivate/optional deactivate missing).
- `bootstrap_fx` now supports scalable reconciliation behavior and cleaner command output.

Why:
- Makes reference data refreshable and resilient as provider datasets evolve.

### Current invariant targets
- Every active user should have:
  1. one `Profile`
  2. one `Subscription` (default free when bootstrapped)
  3. one personal `Portfolio`
- Tier changes are handled through subscription services/admin actions.

### Operational order after pull
1. `python manage.py migrate`
2. `python manage.py bootstrap_fx` (optionally `--deactivate-missing`)
3. `python manage.py backfill_user_foundations`
4. run smoke tests for auth/profile/subscription flows

