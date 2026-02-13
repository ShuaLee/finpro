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

End of handoff notes.
