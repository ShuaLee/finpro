import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import {
  changePassword,
  deleteAccount,
  getMe,
  getProfile,
  type MeResponse,
  type ProfileResponse,
  updateEmail,
  updateProfile,
  verifyPendingEmailChange,
} from "../api/settings";
import { ApiError } from "../api/http";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../context/AuthContext";

export type SettingsTab = "profile" | "security" | "billing" | "danger";

type SettingsPageProps = {
  embedded?: boolean;
  activeSection?: SettingsTab | null;
  onSectionChange?: (section: SettingsTab | null) => void;
};

export function SettingsPage({ embedded = false, activeSection, onSectionChange }: SettingsPageProps) {
  const { refreshAuth, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<MeResponse | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [emailSubmitting, setEmailSubmitting] = useState(false);
  const [emailMessage, setEmailMessage] = useState<string | null>(null);
  const [pendingEmailChange, setPendingEmailChange] = useState<string | null>(null);
  const [emailCode, setEmailCode] = useState("");
  const [verifySubmitting, setVerifySubmitting] = useState(false);
  const [verifyMessage, setVerifyMessage] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [language, setLanguage] = useState("en");
  const [timezone, setTimezone] = useState("UTC");
  const [country, setCountry] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [profileSubmitting, setProfileSubmitting] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);
  const [internalActiveTab, setInternalActiveTab] = useState<SettingsTab | null>(null);
  const activeTab = activeSection ?? internalActiveTab ?? "profile";

  const setActiveTab = (next: SettingsTab) => {
    onSectionChange?.(next);
    if (activeSection === undefined) {
      setInternalActiveTab(next);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setGlobalError(null);
      try {
        await refreshAuth();
        const [meData, profileData] = await Promise.all([getMe(), getProfile()]);
        setMe(meData);
        setProfile(profileData);

        setEmail(meData.user.email);
        setFullName(profileData.full_name ?? "");
        setLanguage(profileData.language ?? "en");
        setTimezone(profileData.timezone ?? "UTC");
        setCountry(profileData.country ?? "");
        setCurrency(profileData.currency ?? "USD");
      } catch (caught) {
        if (caught instanceof ApiError) {
          setGlobalError(caught.message);
        } else {
          setGlobalError("Failed to load settings.");
        }
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [refreshAuth]);

  if (authLoading) {
    return <div className="grid min-h-[70vh] place-items-center text-sm text-muted-foreground">Loading settings...</div>;
  }

  const onUpdateEmail = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setEmailSubmitting(true);
    setEmailMessage(null);
    setVerifyMessage(null);
    setGlobalError(null);

    try {
      const res = await updateEmail(email.trim(), emailPassword);
      setPendingEmailChange(res.target_email);
      setEmailPassword("");
      setEmailCode("");
      setEmailMessage(res.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not update email.");
      }
    } finally {
      setEmailSubmitting(false);
    }
  };

  const onVerifyEmailChange = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!pendingEmailChange) {
      return;
    }
    setVerifySubmitting(true);
    setVerifyMessage(null);
    setGlobalError(null);

    try {
      const res = await verifyPendingEmailChange(pendingEmailChange, emailCode.trim());
      setEmail(res.email);
      setPendingEmailChange(null);
      setEmailCode("");
      setVerifyMessage(res.detail);
      setEmailMessage(null);
      await refreshAuth();
      const meData = await getMe();
      setMe(meData);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not verify email change.");
      }
    } finally {
      setVerifySubmitting(false);
    }
  };

  const onChangePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordMessage(null);
    setGlobalError(null);

    if (newPassword !== confirmPassword) {
      setGlobalError("New password and confirmation do not match.");
      return;
    }

    setPasswordSubmitting(true);
    try {
      const res = await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMessage(res.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not change password.");
      }
    } finally {
      setPasswordSubmitting(false);
    }
  };

  const onSaveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProfileSubmitting(true);
    setProfileMessage(null);
    setGlobalError(null);

    try {
      const updated = await updateProfile({
        full_name: fullName.trim(),
        language: language.trim().toLowerCase(),
        timezone: timezone.trim(),
        country: country.trim().toUpperCase(),
        currency: currency.trim().toUpperCase(),
      });
      setProfile(updated);
      setProfileMessage("Profile updated successfully.");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not save profile settings.");
      }
    } finally {
      setProfileSubmitting(false);
    }
  };

  const onDeleteAccount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setDeleteSubmitting(true);
    setDeleteMessage(null);
    setGlobalError(null);

    try {
      const response = await deleteAccount(deletePassword, deleteConfirmation);
      setDeleteMessage(response.detail);
      setDeletePassword("");
      setDeleteConfirmation("");
      await refreshAuth();
      navigate("/signup", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not delete account.");
      }
    } finally {
      setDeleteSubmitting(false);
    }
  };

  if (loading) {
    return <div className="grid min-h-[70vh] place-items-center text-sm text-muted-foreground">Loading settings...</div>;
  }

  if (!me || !profile) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-destructive">{globalError ?? "Unable to load user settings."}</p>
          </CardContent>
        </Card>
      </main>
    );
  }

  const content = (
    <main className={`mx-auto w-full ${embedded ? "max-w-none px-0 py-0" : "max-w-6xl px-4 py-8 sm:px-6 lg:px-8"}`}>
      <header className={`mb-7 border-b border-border pb-4 ${embedded ? "pt-5" : ""}`}>
        <h1 className="text-[2rem] font-semibold tracking-tight text-foreground">Settings</h1>
      </header>
      <div className="grid gap-8 lg:grid-cols-[190px_minmax(0,1fr)] xl:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="min-w-0">
          <div className="sticky top-24 space-y-3">
            <nav className="flex gap-2 overflow-x-auto pb-2 lg:block lg:space-y-1 lg:overflow-visible lg:pb-0" aria-label="Settings sections">
              <SettingsSideNavButton label="Account information" active={activeTab === "profile"} onClick={() => setActiveTab("profile")} />
              <SettingsSideNavButton label="Login and security" active={activeTab === "security"} onClick={() => setActiveTab("security")} />
              <SettingsSideNavButton label="Billing" active={activeTab === "billing"} onClick={() => setActiveTab("billing")} />
              <SettingsSideNavButton label="Delete account" active={activeTab === "danger"} onClick={() => setActiveTab("danger")} />
            </nav>
          </div>
        </aside>

        <section className="min-w-0">
          {globalError ? <p className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">{globalError}</p> : null}

          {activeTab === "profile" ? (
            <SettingsPanel
              title="Account information"
              description="Manage the user and profile fields currently supported by your account."
              actions={(
                <>
                  <Button type="button" variant="outline" className="h-8 rounded-full px-4 text-xs">Cancel</Button>
                  <Button type="submit" form="settings-profile-form" className="h-8 rounded-full px-4 text-xs" disabled={profileSubmitting}>
                    {profileSubmitting ? "Saving..." : "Save Changes"}
                  </Button>
                </>
              )}
            >
              <form id="settings-profile-form" className="divide-y divide-border" onSubmit={onSaveProfile}>
                <SettingsFormRow title="User" description="Read-only account fields from the user model.">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FieldGroup label="Email address">
                      <Input className="h-10 rounded-xl bg-white text-muted-foreground" value={me.user.email} disabled readOnly />
                    </FieldGroup>
                    <FieldGroup label="Email status">
                      <Input className="h-10 rounded-xl bg-white text-muted-foreground" value={me.user.is_email_verified ? "Verified" : "Not verified"} disabled readOnly />
                    </FieldGroup>
                    <FieldGroup label="Account status">
                      <Input className="h-10 rounded-xl bg-white text-muted-foreground" value={me.user.is_active ? "Active" : "Inactive"} disabled readOnly />
                    </FieldGroup>
                    <FieldGroup label="Date joined">
                      <Input className="h-10 rounded-xl bg-white text-muted-foreground" value={formatSettingsDate(me.user.date_joined)} disabled readOnly />
                    </FieldGroup>
                  </div>
                </SettingsFormRow>
                <SettingsFormRow title="Full name" description="Stored on your profile and shown across the app.">
                  <Input id="full-name" className="h-10 rounded-xl bg-white" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </SettingsFormRow>
                <SettingsFormRow title="Profile defaults" description="Used for localization, reporting, and valuation defaults.">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FieldGroup label="Language">
                      <Input id="language" className="h-10 rounded-xl bg-white" value={language} onChange={(e) => setLanguage(e.target.value)} required />
                    </FieldGroup>
                    <FieldGroup label="Timezone">
                      <Input id="timezone" className="h-10 rounded-xl bg-white" value={timezone} onChange={(e) => setTimezone(e.target.value)} required />
                    </FieldGroup>
                    <FieldGroup label="Country code">
                      <Input id="country" className="h-10 rounded-xl bg-white" placeholder="US" value={country} onChange={(e) => setCountry(e.target.value)} />
                    </FieldGroup>
                    <FieldGroup label="Currency code">
                      <Input id="currency" className="h-10 rounded-xl bg-white" placeholder="USD" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
                    </FieldGroup>
                  </div>
                </SettingsFormRow>
                {profileMessage ? <p className="pt-4 text-sm text-primary">{profileMessage}</p> : null}
              </form>
            </SettingsPanel>
          ) : null}

          {activeTab === "security" ? (
            <SettingsPanel title="Login and security" description="Manage your email and password.">
              <div className="space-y-8">
                <form className="divide-y divide-border" onSubmit={onUpdateEmail}>
                  <SettingsFormRow title="Email address" description="A verification code will be sent to the new address.">
                    <div className="grid gap-4 md:grid-cols-2">
                      <FieldGroup label="Email">
                        <Input id="settings-email" className="h-10 rounded-xl bg-white" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="Current password">
                        <Input id="settings-email-password" className="h-10 rounded-xl bg-white" type="password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} required />
                      </FieldGroup>
                    </div>
                  </SettingsFormRow>
                  <div className="flex items-center gap-3 pt-5">
                    <Button type="submit" className="rounded-full px-5" disabled={emailSubmitting}>{emailSubmitting ? "Saving..." : "Update email"}</Button>
                    {emailMessage ? <span className="text-sm text-primary">{emailMessage}</span> : null}
                  </div>
                </form>

                {pendingEmailChange ? (
                  <form className="rounded-2xl border border-border bg-secondary/20 p-5" onSubmit={onVerifyEmailChange}>
                    <p className="text-sm text-muted-foreground">
                      Verification code sent to <span className="font-semibold text-foreground">{pendingEmailChange}</span>.
                    </p>
                    <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
                      <FieldGroup label="6-digit verification code">
                        <Input
                          id="email-change-code"
                          className="h-10 rounded-xl bg-white"
                          inputMode="numeric"
                          pattern="[0-9]{6}"
                          maxLength={6}
                          value={emailCode}
                          onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                          required
                        />
                      </FieldGroup>
                      <Button type="submit" className="rounded-full px-5" disabled={verifySubmitting || emailCode.length !== 6}>
                        {verifySubmitting ? "Verifying..." : "Verify"}
                      </Button>
                    </div>
                    {verifyMessage ? <p className="mt-3 text-sm text-primary">{verifyMessage}</p> : null}
                  </form>
                ) : null}

                <form className="divide-y divide-border" onSubmit={onChangePassword}>
                  <SettingsFormRow title="Password" description="Use a strong password and rotate it whenever needed.">
                    <div className="grid gap-4 md:grid-cols-3">
                      <FieldGroup label="Current password">
                        <Input id="current-password" className="h-10 rounded-xl bg-white" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="New password">
                        <Input id="new-password" className="h-10 rounded-xl bg-white" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
                      </FieldGroup>
                      <FieldGroup label="Confirm password">
                        <Input id="confirm-password" className="h-10 rounded-xl bg-white" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
                      </FieldGroup>
                    </div>
                  </SettingsFormRow>
                  <div className="flex items-center gap-3 pt-5">
                    <Button type="submit" className="rounded-full px-5" disabled={passwordSubmitting}>{passwordSubmitting ? "Saving..." : "Change password"}</Button>
                    {passwordMessage ? <span className="text-sm text-primary">{passwordMessage}</span> : null}
                  </div>
                </form>
              </div>
            </SettingsPanel>
          ) : null}

          {activeTab === "billing" ? (
            <SettingsPanel title="Payment information" description="Subscription and billing controls for your account.">
              <SettingsFormRow title="Manage subscription" description="This will connect to your billing portal once subscriptions are wired.">
                <div className="rounded-2xl border border-border bg-secondary/20 p-5 text-sm text-muted-foreground">
                  Subscription management is not connected yet. This section is reserved for your future billing portal flow.
                </div>
              </SettingsFormRow>
            </SettingsPanel>
          ) : null}

          {activeTab === "danger" ? (
            <SettingsPanel title="Terms and account actions" description="Destructive account-level actions.">
              <form className="divide-y divide-border" onSubmit={onDeleteAccount}>
                <SettingsFormRow title="Delete account" description="Account deletion is permanent in the current build.">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FieldGroup label="Current password">
                      <Input id="delete-account-password" className="h-10 rounded-xl bg-white" type="password" value={deletePassword} onChange={(e) => setDeletePassword(e.target.value)} required />
                    </FieldGroup>
                    <FieldGroup label='Type "DELETE" to confirm'>
                      <Input id="delete-account-confirmation" className="h-10 rounded-xl bg-white" value={deleteConfirmation} onChange={(e) => setDeleteConfirmation(e.target.value.toUpperCase())} required />
                    </FieldGroup>
                  </div>
                </SettingsFormRow>
                <div className="flex items-center gap-3 pt-5">
                  <Button type="submit" variant="outline" className="rounded-full border-destructive/40 px-5 text-destructive hover:bg-destructive/10 hover:text-destructive" disabled={deleteSubmitting}>
                    {deleteSubmitting ? "Deleting..." : "Delete account"}
                  </Button>
                  {deleteMessage ? <span className="text-sm text-primary">{deleteMessage}</span> : null}
                </div>
              </form>
            </SettingsPanel>
          ) : null}
        </section>
      </div>
    </main>
  );
  if (embedded) {
    return <div className="px-5 pt-0">{content}</div>;
  }

  return content;
}

function SettingsSideNavButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full shrink-0 rounded-md px-3 py-2 text-left text-xs transition-colors lg:block ${
        active
          ? "bg-[#f8f6f1] font-medium text-foreground"
          : "text-foreground/68 hover:bg-[#f8f6f1]/70 hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

function SettingsPanel({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="min-w-0">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-foreground">{title}</h2>
          <p className="mt-1 text-xs text-foreground/64">{description}</p>
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

function SettingsFormRow({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-4 py-5 first:pt-0 md:grid-cols-[190px_minmax(0,1fr)] md:items-start xl:grid-cols-[230px_minmax(0,1fr)]">
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description ? <p className="mt-1 max-w-[13rem] text-xs leading-5 text-foreground/60">{description}</p> : null}
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
function FieldGroup({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium text-foreground">{label}</span>
      {children}
    </label>
  );
}

function formatSettingsDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}


