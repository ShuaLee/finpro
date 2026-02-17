# Users + Profiles Production Completion Notes

Date: 2026-02-17
Scope: `apps/users` and `apps/profiles`

## Goal
Harden authentication, account lifecycle, and profile management toward a production-ready baseline while preserving your existing architecture (separate `users` and `profiles` apps).

## What Was Implemented

### 1. Password reset domain model
- Added `apps/users/models/password_reset.py` with `PasswordResetToken`.
- Added export in `apps/users/models/__init__.py`.
- Added migration `apps/users/migrations/0002_passwordresettoken.py`.

Why:
- Password reset should use one-time, expiring, server-stored token hashes, not plaintext tokens.
- Supports secure recovery flow and token revocation.

### 2. Password reset service
- Added `apps/users/services/password_reset_service.py`.
- Exported in `apps/users/services/__init__.py`.

What it does:
- Issues reset tokens with cooldown.
- Invalidates prior active reset tokens on new issue.
- Sends reset email with frontend reset link.
- Validates token and resets password.
- Clears lockout counters after successful reset.

Why:
- Prevent token spam and race conditions.
- Keep reset flow idempotent and secure.

### 3. Email verification hardening
- Updated `apps/users/services/email_verification_service.py`.

What changed:
- Added resend cooldown setting support.
- Invalidates old active verification tokens when issuing a new one.
- Kept verification idempotent/safe.

Why:
- Prevent verification email abuse.
- Ensure only the latest token remains valid.

### 4. Auth service enhancement
- Updated `apps/users/services/auth_service.py`.

What changed:
- Added `change_password(user, current_password, new_password)`.
- Existing register/login/lockout logic retained.
- Registration keeps profile bootstrap + initial verification email.

Why:
- Password change is core account security behavior.

### 5. Auth serializers expansion
- Updated `apps/users/serializers/auth.py` and `apps/users/serializers/__init__.py`.

Added:
- `ForgotPasswordSerializer`
- `ResetPasswordSerializer`
- `ChangePasswordSerializer`

Also tightened:
- `ResendVerificationSerializer.email` is required.

Why:
- Explicit, validated contracts for each auth endpoint.

### 6. Auth API endpoints expanded
- Updated `apps/users/views/auth.py` and `apps/users/views/__init__.py`.
- Updated `apps/users/urls/auth_urls.py`.

Added endpoints:
- `forgot-password/`
- `reset-password/`
- `change-password/`
- `me/`
- `status/`

Other hardening:
- Logout now reads refresh cookie key from settings.
- Logout endpoint allows requests even if access token is expired/missing and still clears cookies.
- Resend/forgot responses stay generic for non-enumeration.

Why:
- Completes common auth lifecycle and improves UX/safety.

### 7. Cookie JWT auth security hardening
- Updated `apps/users/authentication.py`.

What changed:
- Added CSRF enforcement for non-safe HTTP methods when authenticating via cookie JWT.

Why:
- Cookie-based auth without CSRF checks is vulnerable to CSRF attacks.
- This is a production-critical protection.

### 8. Admin improvements
- Added `apps/users/admin/password_reset_admin.py`.
- Updated `apps/users/admin/verification_admin.py`.
- Updated `apps/users/admin/user_admin.py`.
- Updated `apps/users/admin/__init__.py`.

What changed:
- Password reset token admin visibility.
- Resend verification action in token and user admin.
- Unlock account admin action.
- Better user list display (failed attempts / lock status).

Why:
- Operational controls and support tooling for account lifecycle issues.

### 9. Token cleanup management command
- Added:
  - `apps/users/management/__init__.py`
  - `apps/users/management/commands/__init__.py`
  - `apps/users/management/commands/cleanup_user_tokens.py`

Why:
- Allows periodic pruning of consumed/expired tokens to reduce table bloat.

### 10. Profile serializer hardening
- Updated `apps/profiles/serializers/profile.py`.

What changed:
- Added language normalization/length validation.
- Added timezone validation against `zoneinfo.available_timezones()`.
- Locked down privileged profile fields as read-only:
  - `plan`
  - `account_type`
  - `onboarding_status`
  - `onboarding_step`

Why:
- Prevents users from self-escalating plan/account type via profile patch.
- Improves data quality for locale fields.

### 11. Profile endpoint resilience
- Updated `apps/profiles/views/profile.py`.

What changed:
- If `request.user.profile` is missing, endpoint auto-bootstraps profile instead of failing.

Why:
- Avoids brittle runtime failures and supports recovery from edge cases.

## Security/Architecture Notes
- Registration still bootstraps a profile immediately (correct for your architecture).
- Token flows use hashed tokens in DB.
- Generic responses were preserved where account enumeration risk exists.
- Cookie JWT auth now includes CSRF enforcement for state-changing requests.

## What I Could Not Verify In-Session
I could not run Django tests/migrations in this shell because Django was not available in the active environment:
- Error: `ModuleNotFoundError: No module named 'django'`

## Required Local Verification (run in your venv)
1. `python manage.py makemigrations`
2. `python manage.py migrate`
3. `python manage.py test apps.users.tests.test_auth_flow apps.profiles.tests`

## Remaining Items to Call It Fully Production-Complete
These are mostly settings/ops-level completion items:
- Move secrets and environment-specific values in `finpro/settings.py` to env vars.
- Set secure production cookie settings by environment (`Secure`, `SameSite`, CSRF/Session settings).
- Configure production email backend + sender domain and deliverability checks.
- Add auth throttling/rate limiting (DRF throttles or edge rate limiting) for login/reset/resend routes.
- Add scheduled execution for `cleanup_user_tokens`.
- Expand tests for new flows (`forgot/reset/change/me/status`, CSRF behavior).

## Files Touched (Users/Profiles Scope)
- `apps/users/models/password_reset.py`
- `apps/users/models/__init__.py`
- `apps/users/migrations/0002_passwordresettoken.py`
- `apps/users/services/password_reset_service.py`
- `apps/users/services/email_verification_service.py`
- `apps/users/services/auth_service.py`
- `apps/users/services/__init__.py`
- `apps/users/serializers/auth.py`
- `apps/users/serializers/__init__.py`
- `apps/users/views/auth.py`
- `apps/users/views/__init__.py`
- `apps/users/urls/auth_urls.py`
- `apps/users/authentication.py`
- `apps/users/admin/password_reset_admin.py`
- `apps/users/admin/verification_admin.py`
- `apps/users/admin/user_admin.py`
- `apps/users/admin/__init__.py`
- `apps/users/management/__init__.py`
- `apps/users/management/commands/__init__.py`
- `apps/users/management/commands/cleanup_user_tokens.py`
- `apps/profiles/serializers/profile.py`
- `apps/profiles/views/profile.py`

## Summary
Users/profiles were upgraded from a functional baseline to a hardened baseline with secure token lifecycle, complete password flows, improved admin operability, stricter profile update boundaries, and CSRF protection for cookie JWT auth.
