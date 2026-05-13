import { useEffect, useMemo, useState } from "react";

import {
  changePassword,
  deleteAccount,
  getProfile,
  getProfileOptions,
  type ProfileOptionsResponse,
  type ProfileResponse,
  updateEmail as requestEmailChangeApi,
  updateProfile,
  verifyPendingEmailChange,
} from "./api/settings";
import { ApiError } from "./api/http";
import { useAuth } from "./context/AuthContext";

type ProfileDraft = {
  fullName: string;
  language: string;
  timezone: string;
  country: string;
  currency: string;
};

const LANGUAGE_OPTIONS = [
  { code: "en", name: "English" },
  { code: "fr", name: "French" },
  { code: "es", name: "Spanish" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ja", name: "Japanese" },
  { code: "zh", name: "Chinese" },
];

function toProfileDraft(profile: ProfileResponse): ProfileDraft {
  return {
    fullName: profile.full_name ?? "",
    language: profile.language ?? "en",
    timezone: profile.timezone ?? "UTC",
    country: profile.country ?? "",
    currency: profile.currency ?? "USD",
  };
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "Not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function SettingsSectionBadge({ kind }: { kind: "profile" | "preferences" | "security" | "danger" | "loading" }) {
  const commonProps = {
    className: "settings-section-icon-svg",
    focusable: "false" as const,
    "aria-hidden": "true" as const,
  };

  if (kind === "profile") {
    return (
      <svg viewBox="0 0 24 24" {...commonProps}>
        <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.2 0-7 2.15-7 4.2V20h14v-1.8c0-2.05-2.8-4.2-7-4.2Z" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
      </svg>
    );
  }

  if (kind === "preferences") {
    return (
      <svg viewBox="0 0 24 24" {...commonProps}>
        <path d="M12 3v18M4 8h8m0 8h8M8 6a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm8 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
      </svg>
    );
  }

  if (kind === "security") {
    return (
      <svg viewBox="0 0 24 24" {...commonProps}>
        <path d="M7 10V7a5 5 0 0 1 10 0v3m-9 0h8a1 1 0 0 1 1 1v8H7v-8a1 1 0 0 1 1-1Zm4 4v2" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
      </svg>
    );
  }

  if (kind === "danger") {
    return (
      <svg viewBox="0 0 24 24" {...commonProps}>
        <path d="M12 9v4m0 4h.01M10.3 3.85 2.9 17a1.5 1.5 0 0 0 1.3 2.25h15.6A1.5 1.5 0 0 0 21.1 17L13.7 3.85a1.94 1.94 0 0 0-3.4 0Z" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" {...commonProps}>
      <path d="M12 6v6l4 2" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
      <path d="M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9Z" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" />
    </svg>
  );
}

export function SettingsPage() {
  const { refreshAuth } = useAuth();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [profileOptions, setProfileOptions] = useState<ProfileOptionsResponse | null>(null);
  const [draft, setDraft] = useState<ProfileDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const [generalSaving, setGeneralSaving] = useState(false);
  const [generalNotice, setGeneralNotice] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  const [emailDraft, setEmailDraft] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [emailRequesting, setEmailRequesting] = useState(false);
  const [emailVerifying, setEmailVerifying] = useState(false);
  const [emailNotice, setEmailNotice] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordNotice, setPasswordNotice] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);
  const [deleteNotice, setDeleteNotice] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSettings() {
      try {
        setLoading(true);
        setLoadingError(null);
        const [profileResponse, optionsResponse] = await Promise.all([getProfile(), getProfileOptions()]);
        if (cancelled) return;
        setProfile(profileResponse);
        setProfileOptions(optionsResponse);
        setDraft(toProfileDraft(profileResponse));
        setPendingEmail(profileResponse.user.email);
      } catch (caught) {
        if (!cancelled) {
          setLoadingError(caught instanceof ApiError ? caught.message : "Unable to load settings.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSettings();

    return () => {
      cancelled = true;
    };
  }, []);

  const timezoneOptions = useMemo(() => {
    const supported = typeof Intl.supportedValuesOf === "function" ? Intl.supportedValuesOf("timeZone") : ["UTC"];
    const current = draft?.timezone?.trim();
    const set = new Set(supported);
    if (current && !set.has(current)) set.add(current);
    return Array.from(set);
  }, [draft?.timezone]);

  const languageOptions = useMemo(() => {
    const current = draft?.language?.trim();
    const base = [...LANGUAGE_OPTIONS];
    if (current && !base.some((option) => option.code === current)) {
      base.push({ code: current, name: current.toUpperCase() });
    }
    return base;
  }, [draft?.language]);

  const handleDraftChange = <K extends keyof ProfileDraft>(key: K, value: ProfileDraft[K]) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  };

  const handleSaveGeneral = async () => {
    if (!draft) return;

    try {
      setGeneralSaving(true);
      setGeneralError(null);
      setGeneralNotice(null);
      const updated = await updateProfile({
        full_name: draft.fullName,
        language: draft.language,
        timezone: draft.timezone,
        country: draft.country,
        currency: draft.currency,
      });
      setProfile(updated);
      setDraft(toProfileDraft(updated));
      await refreshAuth();
      setGeneralNotice("Settings saved.");
    } catch (caught) {
      setGeneralError(caught instanceof ApiError ? caught.message : "Unable to save settings.");
    } finally {
      setGeneralSaving(false);
    }
  };

  const handleEmailRequest = async () => {
    try {
      setEmailRequesting(true);
      setEmailError(null);
      setEmailNotice(null);
      const result = await requestEmailChangeApi(emailDraft, emailPassword);
      setPendingEmail(result.target_email);
      setEmailCode("");
      setEmailNotice(result.detail);
    } catch (caught) {
      setEmailError(caught instanceof ApiError ? caught.message : "Unable to request email change.");
    } finally {
      setEmailRequesting(false);
    }
  };

  const handleEmailVerify = async () => {
    try {
      setEmailVerifying(true);
      setEmailError(null);
      setEmailNotice(null);
      const result = await verifyPendingEmailChange(pendingEmail, emailCode);
      setEmailDraft("");
      setEmailPassword("");
      setEmailCode("");
      await refreshAuth();
      const refreshedProfile = await getProfile();
      setProfile(refreshedProfile);
      setDraft(toProfileDraft(refreshedProfile));
      setPendingEmail(result.email);
      setEmailNotice(result.detail);
    } catch (caught) {
      setEmailError(caught instanceof ApiError ? caught.message : "Unable to verify email change.");
    } finally {
      setEmailVerifying(false);
    }
  };

  const handlePasswordSave = async () => {
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      setPasswordNotice(null);
      return;
    }

    try {
      setPasswordSaving(true);
      setPasswordError(null);
      setPasswordNotice(null);
      const result = await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordNotice(result.detail);
    } catch (caught) {
      setPasswordError(caught instanceof ApiError ? caught.message : "Unable to change password.");
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      setDeleteSubmitting(true);
      setDeleteError(null);
      setDeleteNotice(null);
      const result = await deleteAccount(deletePassword, deleteConfirmation);
      setDeleteNotice(result.detail);
      await refreshAuth();
    } catch (caught) {
      setDeleteError(caught instanceof ApiError ? caught.message : "Unable to delete account.");
    } finally {
      setDeleteSubmitting(false);
    }
  };

  if (loading) {
    return (
      <section className="settings-page" aria-label="Settings">
        <div className="settings-page-body">
          <div className="settings-panel settings-panel-loading">
            <div className="settings-section-heading">
              <span className="settings-section-icon" aria-hidden="true">
                <SettingsSectionBadge kind="loading" />
              </span>
              <div className="settings-panel-intro">
                <p className="settings-status">Loading settings...</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (loadingError || !profile || !draft || !profileOptions) {
    return (
      <section className="settings-page" aria-label="Settings">
        <div className="settings-page-body">
          <div className="settings-panel settings-panel-loading">
            <div className="settings-section-heading">
              <span className="settings-section-icon" aria-hidden="true">
                <SettingsSectionBadge kind="danger" />
              </span>
              <div className="settings-panel-intro">
                <p className="settings-error">{loadingError ?? "Unable to load settings."}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="settings-page" aria-label="Settings">
      <div className="settings-page-body">
        <div className="settings-page-toolbar">
          <div className="settings-toolbar-status">
            {generalError ? <p className="settings-error">{generalError}</p> : null}
            {generalNotice ? <p className="settings-success">{generalNotice}</p> : null}
          </div>
          <button type="button" className="primary-button" onClick={() => void handleSaveGeneral()} disabled={generalSaving}>
            {generalSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>

        <div className="settings-panel settings-panel-split">
          <div className="settings-section-heading">
            <span className="settings-section-icon" aria-hidden="true">
              <SettingsSectionBadge kind="profile" />
            </span>
            <div className="settings-panel-intro">
              <h2 className="settings-panel-title">Profile</h2>
              <p className="settings-panel-copy">Update the identity details tied to your account.</p>
            </div>
          </div>
          <div className="settings-form-grid">
            <div className="settings-field-group settings-field-group-full">
              <label className="field-label" htmlFor="settings-full-name">Full name</label>
              <input
                id="settings-full-name"
                className="text-field"
                type="text"
                value={draft.fullName}
                onChange={(event) => handleDraftChange("fullName", event.target.value)}
              />
            </div>
            <div className="settings-field-group">
              <span className="field-label">Current email</span>
              <div className="settings-static-field">{profile.user.email}</div>
            </div>
            <div className="settings-field-group">
              <span className="field-label">Email status</span>
              <div className="settings-static-field">{profile.user.is_email_verified ? "Verified" : "Pending verification"}</div>
            </div>
            <div className="settings-field-group">
              <span className="field-label">Member since</span>
              <div className="settings-static-field">{formatTimestamp(profile.user.date_joined)}</div>
            </div>
            <div className="settings-field-group">
              <span className="field-label">Account state</span>
              <div className="settings-static-field">{profile.user.is_active ? "Active" : "Inactive"}</div>
            </div>
          </div>
          <div className="settings-panel-side settings-panel-side-muted">
            <p className="settings-side-note">Included in the shared save action for account details and preferences.</p>
          </div>
        </div>

        <div className="settings-panel settings-panel-split">
          <div className="settings-section-heading">
            <span className="settings-section-icon" aria-hidden="true">
              <SettingsSectionBadge kind="preferences" />
            </span>
            <div className="settings-panel-intro">
              <h2 className="settings-panel-title">Preferences</h2>
              <p className="settings-panel-copy">Control the locale and portfolio defaults used across the app.</p>
            </div>
          </div>
          <div className="settings-form-grid">
            <div className="settings-field-group">
              <label className="field-label" htmlFor="settings-language">Language</label>
              <select
                id="settings-language"
                className="text-field"
                value={draft.language}
                onChange={(event) => handleDraftChange("language", event.target.value)}
              >
                {languageOptions.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-field-group">
              <label className="field-label" htmlFor="settings-timezone">Timezone</label>
              <select
                id="settings-timezone"
                className="text-field"
                value={draft.timezone}
                onChange={(event) => handleDraftChange("timezone", event.target.value)}
              >
                {timezoneOptions.map((timezone) => (
                  <option key={timezone} value={timezone}>
                    {timezone}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-field-group">
              <label className="field-label" htmlFor="settings-country">Country</label>
              <select
                id="settings-country"
                className="text-field"
                value={draft.country}
                onChange={(event) => handleDraftChange("country", event.target.value)}
              >
                <option value="">Select a country</option>
                {profileOptions.countries.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-field-group">
              <label className="field-label" htmlFor="settings-currency">Currency</label>
              <select
                id="settings-currency"
                className="text-field"
                value={draft.currency}
                onChange={(event) => handleDraftChange("currency", event.target.value)}
              >
                {profileOptions.currencies.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.code} - {option.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="settings-panel-side settings-panel-side-muted">
            <p className="settings-side-note">Use Save Changes once after updating any profile or regional defaults.</p>
          </div>
        </div>

        <div className="settings-stack">
          <div className="settings-panel settings-panel-split">
            <div className="settings-section-heading">
              <span className="settings-section-icon" aria-hidden="true">
                <SettingsSectionBadge kind="security" />
              </span>
              <div className="settings-panel-intro">
                <h2 className="settings-panel-title">Email</h2>
                <p className="settings-panel-copy">Request a verified email change and confirm it with the code sent to you.</p>
              </div>
            </div>
            <div className="settings-form-grid">
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-new-email">New email</label>
                <input
                  id="settings-new-email"
                  className="text-field"
                  type="email"
                  value={emailDraft}
                  onChange={(event) => setEmailDraft(event.target.value)}
                />
              </div>
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-email-password">Current password</label>
                <input
                  id="settings-email-password"
                  className="text-field"
                  type="password"
                  value={emailPassword}
                  onChange={(event) => setEmailPassword(event.target.value)}
                />
              </div>
              <div className="settings-divider settings-field-group-full" />
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-pending-email">Pending email</label>
                <input
                  id="settings-pending-email"
                  className="text-field"
                  type="email"
                  value={pendingEmail}
                  onChange={(event) => setPendingEmail(event.target.value)}
                />
              </div>
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-email-code">Verification code</label>
                <input
                  id="settings-email-code"
                  className="text-field"
                  type="text"
                  value={emailCode}
                  onChange={(event) => setEmailCode(event.target.value)}
                />
              </div>
            </div>
            <div className="settings-panel-side">
              {emailError ? <p className="settings-error">{emailError}</p> : null}
              {emailNotice ? <p className="settings-success">{emailNotice}</p> : null}
              <div className="settings-actions settings-actions-rail">
                <button type="button" className="primary-button" onClick={() => void handleEmailRequest()} disabled={emailRequesting}>
                  {emailRequesting ? "Submitting..." : "Submit Email Change Request"}
                </button>
                <button type="button" className="secondary-button" onClick={() => void handleEmailVerify()} disabled={emailVerifying}>
                  {emailVerifying ? "Verifying..." : "Verify Email Change"}
                </button>
              </div>
            </div>
          </div>

          <div className="settings-panel settings-panel-split">
            <div className="settings-section-heading">
              <span className="settings-section-icon" aria-hidden="true">
                <SettingsSectionBadge kind="security" />
              </span>
              <div className="settings-panel-intro">
                <h2 className="settings-panel-title">Password</h2>
                <p className="settings-panel-copy">Change your password using your current password for confirmation.</p>
              </div>
            </div>
            <div className="settings-form-grid">
              <div className="settings-field-group settings-field-group-full">
                <label className="field-label" htmlFor="settings-current-password">Current password</label>
                <input
                  id="settings-current-password"
                  className="text-field"
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                />
              </div>
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-new-password">New password</label>
                <input
                  id="settings-new-password"
                  className="text-field"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />
              </div>
              <div className="settings-field-group">
                <label className="field-label" htmlFor="settings-confirm-password">Confirm new password</label>
                <input
                  id="settings-confirm-password"
                  className="text-field"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />
              </div>
            </div>
            <div className="settings-panel-side">
              {passwordError ? <p className="settings-error">{passwordError}</p> : null}
              {passwordNotice ? <p className="settings-success">{passwordNotice}</p> : null}
              <div className="settings-actions settings-actions-rail">
                <button type="button" className="primary-button" onClick={() => void handlePasswordSave()} disabled={passwordSaving}>
                  {passwordSaving ? "Updating..." : "Update Password"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-panel settings-panel-split settings-panel-danger">
          <div className="settings-section-heading">
            <span className="settings-section-icon settings-section-icon-danger" aria-hidden="true">
              <SettingsSectionBadge kind="danger" />
            </span>
            <div className="settings-panel-intro">
              <h2 className="settings-panel-title">Delete Account</h2>
              <p className="settings-panel-copy">This permanently removes your account and clears your active session.</p>
            </div>
          </div>
          <div className="settings-form-grid">
            <div className="settings-field-group settings-field-group-full">
              <label className="field-label" htmlFor="settings-delete-password">Current password</label>
              <input
                id="settings-delete-password"
                className="text-field"
                type="password"
                value={deletePassword}
                onChange={(event) => setDeletePassword(event.target.value)}
              />
            </div>
            <div className="settings-field-group settings-field-group-full">
              <label className="field-label" htmlFor="settings-delete-confirmation">Type DELETE to confirm</label>
              <input
                id="settings-delete-confirmation"
                className="text-field"
                type="text"
                value={deleteConfirmation}
                onChange={(event) => setDeleteConfirmation(event.target.value)}
              />
            </div>
          </div>
          <div className="settings-panel-side">
            {deleteError ? <p className="settings-error">{deleteError}</p> : null}
            {deleteNotice ? <p className="settings-success">{deleteNotice}</p> : null}
            <div className="settings-actions settings-actions-rail">
              <button type="button" className="danger-button" onClick={() => void handleDeleteAccount()} disabled={deleteSubmitting}>
                {deleteSubmitting ? "Deleting..." : "Delete Account"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
