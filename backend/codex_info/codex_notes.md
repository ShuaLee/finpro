# Codex Notes - FinPro Rebuild Handoff

## Context
This file captures the work decisions and architecture direction discussed in this chat so the project can continue consistently on another computer/session.

Current date context when this was written: February 2026.

---

## 1. High-Level Product Direction
You are building a **portfolio analyst backend** with a future frontend.

Core goal:
- Users create accounts and holdings across asset types.
- Some values come from market/provider data, others from manual input.
- `SchemaColumnValue (SCV)` is the central computed/user value layer.
- Analytics and allocation/targets are the differentiator:
  - portfolio composition breakdowns
  - cross-asset exposures (e.g. physical gold + ETF gold exposure)
  - weighted breakdowns and target-vs-actual gap analysis

Key architectural direction settled in chat:
- Keep a **modular monolith** (separate apps by domain), not one giant foundational app.
- Keep **analytics** and **allocations** separate concerns.
- Build from lower-level apps upward first (users/profiles/subscriptions/fx/portfolios).

---

## 2. App Structure Decisions

### Keep separate apps (recommended)
- `users` -> authentication identity + auth flows
- `profiles` -> personalization + base currency/country + onboarding + subscription refs
- `subscriptions` -> plans, account types, entitlements/defaults
- `fx` -> currencies/rates reference infra
- `portfolios` -> portfolio containers
- higher-level apps (`assets`, `accounts`, `schemas`, `analytics`, `allocations`) consume the above

### Why this structure
- Clear dependency direction
- Easier testing and refactoring
- Lower risk of circular imports
- Better long-term professional practice than one combined base app

---

## 3. Analytics/Allocations Direction (important summary)

### Analytics
- Designed for **actual-state** computation (what user currently holds).
- Uses SCV/value layer for aggregation.
- Percentages should be computed in analytics output, not stored as canonical SCVs.

### Allocations
- Separate app for **target-state** policy (what user wants).
- Compare actual vs target (percent + value + gap + rebalance suggestions).

### Rationale for split
- `analytics`: "What do I have?"
- `allocations`: "What do I want?"

This split was explicitly affirmed as the right approach.

---

## 4. Users + Profiles Rebuild Summary

This was the core implementation focus in this session.

## 4.1 Users app intent
`users` owns:
- custom `User` model (email login)
- auth services (register/login/logout)
- email verification token lifecycle
- auth endpoints and cookie/JWT behavior

### Implemented/confirmed pieces
- `users.models.User` with `email` as username field
- security/meta fields such as `email_verified_at`, `locked_until`
- `EmailVerificationToken` model
- auth + verification services
- auth serializers and auth views
- auth URL module
- cookie utility + JWT cookie authentication

### Important design decision
**Registration orchestration belongs in `users` service layer**, while profile data initialization logic belongs in `profiles` service layer.

This means:
- `AuthService.register_user(...)` creates user
- calls `ProfileBootstrapService.bootstrap(user=...)`
- then issues/sends verification token

### Email verification decision
Verification service should only:
- validate token
- mark email verified
- consume token

Profile bootstrap was removed from verification flow (correctly) so verification remains single-purpose.

---

## 4.2 Profiles app intent
`profiles` owns:
- `Profile` model (1:1 to user)
- base currency/country/language/timezone
- onboarding status
- profile APIs
- bootstrap defaults

### Implemented/confirmed pieces
- `profiles.models.Profile`
- bootstrap service (`ProfileBootstrapService`)
- profile serializer + onboarding serializer
- profile views and profile URLs
- profile admin package

### Important profile decisions made
- `currency` is required base valuation currency (set to required in model)
- bootstrap sets defaults:
  - USD currency (required)
  - US country (if present)
  - free plan (required)
  - individual account type (required)
  - language/timezone defaults
- bootstrap ensures main portfolio exists

---

## 4.3 Registration Flow (final intended behavior)

1. `POST /api/v1/auth/register/`
2. `AuthService.register_user(...)`
3. create user
4. bootstrap profile (and main portfolio)
5. issue + send email verification token

Then:
- `POST /api/v1/auth/verify-email/` marks verified
- `POST /api/v1/auth/login/` only succeeds for verified users

---

## 4.4 URLs and settings state in this session
Root URLs were wired to:
- `api/v1/auth/` -> users auth URLs
- `api/v1/user/` -> profiles URLs
- `api/v1/subscriptions/` -> subscriptions URLs

`profiles` was added to installed apps for rebuild.

---

## 5. Files changed/created during this session (high-level)

### Users
- authentication updated to read cookie key from settings (`AUTH_COOKIE`)
- auth service updated to call profile bootstrap in registration
- email verification service cleaned to verification-only behavior
- users serializer package exports fixed
- users views package exports cleaned

### Profiles
- profile model enforced required base currency
- bootstrap service hardened with stricter default checks and clearer error behavior
- profile API/admin/service structure reviewed and aligned

### Project config
- root `finpro/urls.py` wired to active foundational endpoints

### Allocations (also scaffolded earlier in this thread)
- created `allocations` app domain models/admin/services
- later split allocations models into `models/` package
- split allocations admin into `admin/` package

(Allocations work exists but current rebuild focus has moved to foundational apps.)

---

## 6. Remaining work before declaring users/profiles fully production-ready

1. Regenerate clean migrations for rebuilt apps
- especially `users` and `profiles`
- current conversation repeatedly noted migration reset/rebuild is expected

2. Ensure bootstrap prerequisites are seeded before first registration
- `subscriptions.Plan(slug='free')`
- `subscriptions.AccountType(slug='individual')`
- `fx.FXCurrency(code='USD')`
- optional `fx.Country(code='US')`

3. Keep startup order deterministic
- fx/subscription defaults available before auth registration is used

4. Smoke tests to run after migration
- register -> profile exists
- verify email
- login sets cookies
- profile endpoint works authenticated

---

## 7. Subscriptions app next (agreed next focus)

Planned next step in chat:
- finalize `subscriptions` next, since profile bootstrap depends on its defaults.

Priority for subscriptions completion:
1. stable models (`Plan`, `AccountType`, maybe `Subscription` lifecycle later)
2. deterministic defaults seeding (`free`, `individual`)
3. centralized entitlement service
4. admin protection for required defaults
5. simple read endpoints for frontend

---

## 8. Broader architectural guidance captured in this session

- Keep SCV as canonical value layer for higher computations.
- Keep analytics and allocations separate.
- Add transactions later with dual mode (transaction + direct edits) and provenance/reconciliation, rather than forcing transaction-only too early.
- Consider dedicated valuation layer/app in future for numeraires (currency, BTC, AAPL-equivalent views).

---

## 9. Current practical status snapshot

- Foundation rebuild is in progress.
- Users/profiles structure is mostly stabilized and much cleaner than before.
- URL wiring for auth/profile/subscriptions is in place.
- Next critical app to finalize: `subscriptions`.

---

## 10. Suggested next-session starting checklist

1. Confirm `subscriptions` models/default seeds and management command behavior.
2. Confirm `fx` seeds and bootstrap command order.
3. Regenerate migrations for enabled foundational apps from clean state.
4. Run full auth/profile smoke path.
5. Lock base contracts before reintroducing higher apps (`assets`, `accounts`, `schemas`, etc.).

---

## 11. Update From Today (February 17, 2026)

### 11.1 What was completed today
- Rebuilt and hardened `users` + `profiles` flow to production-ready baseline.
- Added login lockout behavior in `AuthService`:
  - tracks failed attempts
  - locks after threshold (default 5 attempts)
  - lock duration default 15 minutes
  - resets counters on successful login
- Fixed logout flow to read refresh cookie key from settings (`AUTH_COOKIE_REFRESH`) instead of hardcoded `"refresh"`.
- Fixed portfolio/profile dependency bug for bootstrap path:
  - changed portfolio imports from `users.models.Profile` to `profiles.models.Profile`.
- Fixed `ProfileBootstrapService` creation bug:
  - `currency` is required, so bootstrap now resolves defaults first and passes them into `get_or_create(defaults=...)`.
  - this removed `IntegrityError: Column 'currency_id' cannot be null` during registration/tests.

### 11.2 Tests run and status
Command run:
- `python manage.py test apps.users.tests.test_auth_flow apps.profiles.tests -v 2`

Result:
- `Ran 6 tests ... OK`
- Verified flows:
  - register -> profile bootstrap -> main portfolio creation
  - unverified login blocked
  - failed login lockout
  - profile get/patch
  - onboarding completion

Known warning:
- MySQL warning `models.W036` on `portfolios.Portfolio` conditional unique constraint.
- Not a blocker for current users/profiles completion.
- Expected to be resolved naturally when moving to PostgreSQL.

### 11.3 Users/Profiles status after today
- `users` and `profiles` are considered complete for this rebuild phase.
- Core lifecycle is now test-backed and passing.

---

## 12. Subscriptions Planning Notes (next build focus)

### 12.1 Product direction agreed
Planned plan tiers:
- `free`
- paid main tier (individual advanced)
- `wealth_manager`

Entitlements should cover:
- holdings limits
- custom asset/custom type permissions
- number/type of portfolios (personal + client portfolios for wealth manager)

### 12.2 Recommended subscriptions design
1. Keep `Plan` as a catalog of available plan definitions.
2. Add a profile-scoped `Subscription` lifecycle model (current/effective state):
- status (`active`, `past_due`, `canceled`, etc.)
- current plan
- period start/end
- cancel-at-period-end flag
- ended/reactivated timestamps
3. Move feature/limit logic into centralized entitlement resolution service:
- one place to answer "can user do X?" and "what are limits?"

### 12.3 Wealth manager recommendation
- Do **not** fork into a separate portfolio model yet.
- Keep portfolio model extensible; add portfolio role/kind semantics later if needed (personal vs client).
- Gate manager capabilities through subscription entitlements first.

### 12.4 Cancel / downgrade / reactivate policy
- Never delete user data on cancel/downgrade.
- On loss of paid access:
  - block creation of new paid-only resources
  - block actions requiring paid entitlements
  - keep existing data readable
- On reactivation:
  - restore entitlements immediately
  - existing data becomes usable again without restoration jobs

### 12.5 Important dependency cleanup before deep subscription gating
While reviewing `assets`, several inconsistencies were found that should be cleaned before strict entitlement enforcement:
- Legacy profile imports still point at `users.Profile` in multiple assets/accounts files (needs migration to `profiles.Profile` references).
- Crypto asset type mismatch:
  - factory uses `asset_type_slug = "cryptocurrency"`
  - model validation expects slug `"crypto"`.
- Real estate factory passes `estimated_value` but model does not define that field.
- Custom asset validation references `asset.owner_id`, but `Asset` model has no owner field.

These are not part of users/profiles completion, but they will affect subscription-driven feature gating in assets/accounts flows.

---

End of handoff notes.
