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

type SettingsTab = "profile" | "security" | "billing" | "danger";

export function SettingsPage({ embedded = false }: { embedded?: boolean }) {
  const { refreshAuth } = useAuth();
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
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setGlobalError(null);
      try {
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
  }, []);

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
      <div className={`space-y-8 ${embedded ? "pt-2" : ""}`}>
        <div className="space-y-1">
          <h1 className="text-[2.15rem] font-semibold tracking-tight text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground">Manage your account settings and preferences.</p>
        </div>
        <div>
          <nav className="flex flex-wrap items-center gap-3">
            <SettingsTopNavButton label="Account" active={activeTab === "profile"} onClick={() => setActiveTab("profile")} />
            <SettingsTopNavButton label="Login & security" active={activeTab === "security"} onClick={() => setActiveTab("security")} />
            <SettingsTopNavButton label="Billing" active={activeTab === "billing"} onClick={() => setActiveTab("billing")} />
            <SettingsTopNavButton label="Danger zone" active={activeTab === "danger"} onClick={() => setActiveTab("danger")} />
          </nav>
        </div>

        <section className="min-w-0">
          {globalError ? <p className="mb-6 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">{globalError}</p> : null}

          {activeTab === "profile" ? (
            <div className="space-y-6">
              <SectionShell
                title="Profile"
                description="Update the details your account uses for localization and valuation."
              >
                <form className="space-y-8" onSubmit={onSaveProfile}>
                  <SettingFieldRow label="Full name" hint="Used across your account and profile displays.">
                    <Input id="full-name" className="h-12 rounded-xl bg-white" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                  </SettingFieldRow>
                  <SettingsSectionDivider />
                  <SettingFieldGridRow
                    title="Timezone & preferences"
                    description="Let us know the region and defaults your account should use."
                  >
                    <div className="grid gap-4 md:grid-cols-2">
                      <FieldGroup label="Language">
                        <Input id="language" className="h-12 rounded-xl bg-white" value={language} onChange={(e) => setLanguage(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="Timezone">
                        <Input id="timezone" className="h-12 rounded-xl bg-white" value={timezone} onChange={(e) => setTimezone(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="Country code">
                        <Input id="country" className="h-12 rounded-xl bg-white" placeholder="US" value={country} onChange={(e) => setCountry(e.target.value)} />
                      </FieldGroup>
                      <FieldGroup label="Currency code">
                        <Input id="currency" className="h-12 rounded-xl bg-white" placeholder="USD" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
                      </FieldGroup>
                    </div>
                  </SettingFieldGridRow>
                  <div className="flex items-center gap-3 pt-1">
                    <Button type="submit" className="rounded-full px-5" disabled={profileSubmitting}>{profileSubmitting ? "Saving..." : "Save changes"}</Button>
                    {profileMessage ? <span className="text-sm text-primary">{profileMessage}</span> : null}
                  </div>
                </form>
              </SectionShell>
            </div>
          ) : null}

          {activeTab === "security" ? (
            <div className="space-y-6">
              <SectionShell
                title="Login & security"
                description="Manage the credentials and email address attached to your account."
              >
                <form className="space-y-8" onSubmit={onUpdateEmail}>
                  <SettingFieldGridRow
                    title="Email"
                    description="Change the email you use to sign in. A verification code will be sent to the new address."
                  >
                    <div className="grid gap-4 md:grid-cols-2">
                      <FieldGroup label="Email">
                        <Input id="settings-email" className="h-12 rounded-xl bg-white" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="Current password">
                        <Input id="settings-email-password" className="h-12 rounded-xl bg-white" type="password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} required />
                      </FieldGroup>
                    </div>
                    <div className="mt-4 flex items-center gap-3">
                      <Button type="submit" className="rounded-full px-5" disabled={emailSubmitting}>{emailSubmitting ? "Saving..." : "Update email"}</Button>
                      {emailMessage ? <span className="text-sm text-primary">{emailMessage}</span> : null}
                    </div>
                  </SettingFieldGridRow>
                </form>
                {pendingEmailChange ? (
                  <>
                    <SettingsSectionDivider />
                    <form className="space-y-4 rounded-2xl border border-border bg-secondary/20 p-5" onSubmit={onVerifyEmailChange}>
                      <div className="text-sm text-muted-foreground">
                        Verification code sent to <span className="font-semibold text-foreground">{pendingEmailChange}</span>. Your login email will stay as{" "}
                        <span className="font-semibold text-foreground">{me.user.email}</span> until verified.
                      </div>
                      <FieldGroup label="6-digit verification code">
                        <Input
                          id="email-change-code"
                          className="h-12 rounded-xl bg-white"
                          inputMode="numeric"
                          pattern="[0-9]{6}"
                          maxLength={6}
                          value={emailCode}
                          onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                          required
                        />
                      </FieldGroup>
                      <div className="flex items-center gap-3">
                        <Button type="submit" className="rounded-full px-5" disabled={verifySubmitting || emailCode.length !== 6}>
                          {verifySubmitting ? "Verifying..." : "Verify new email"}
                        </Button>
                        {verifyMessage ? <p className="text-sm text-primary">{verifyMessage}</p> : null}
                      </div>
                    </form>
                  </>
                ) : null}
                <SettingsSectionDivider />
                <form className="space-y-8" onSubmit={onChangePassword}>
                  <SettingFieldGridRow
                    title="Password"
                    description="Use a strong password and rotate it whenever you think your account may be exposed."
                  >
                    <div className="grid gap-4 md:grid-cols-3">
                      <FieldGroup label="Current password">
                        <Input id="current-password" className="h-12 rounded-xl bg-white" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
                      </FieldGroup>
                      <FieldGroup label="New password">
                        <Input id="new-password" className="h-12 rounded-xl bg-white" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
                      </FieldGroup>
                      <FieldGroup label="Confirm new password">
                        <Input id="confirm-password" className="h-12 rounded-xl bg-white" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
                      </FieldGroup>
                    </div>
                    <div className="mt-4 flex items-center gap-3">
                      <Button type="submit" className="rounded-full px-5" disabled={passwordSubmitting}>{passwordSubmitting ? "Saving..." : "Change password"}</Button>
                      {passwordMessage ? <span className="text-sm text-primary">{passwordMessage}</span> : null}
                    </div>
                  </SettingFieldGridRow>
                </form>
              </SectionShell>
            </div>
          ) : null}

          {activeTab === "billing" ? (
            <div className="space-y-6">
              <SectionShell
                title="Billing"
                description="Subscription and billing controls for your account."
              >
                <SettingFieldGridRow
                  title="Manage subscription"
                  description="This will connect to your billing portal once subscriptions are wired."
                  action={(
                    <button
                      type="button"
                      className="rounded-full border border-border px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-secondary"
                      disabled
                    >
                      Coming soon
                    </button>
                  )}
                >
                  <div className="rounded-2xl border border-border bg-secondary/20 p-5 text-sm text-muted-foreground">
                    Subscription management is not connected yet. This section is reserved for your future billing portal flow.
                  </div>
                </SettingFieldGridRow>
              </SectionShell>
            </div>
          ) : null}

          {activeTab === "danger" ? (
            <div className="space-y-6">
              <SectionShell
                title="Danger zone"
                description="Destructive account-level actions."
              >
                <form className="space-y-8" onSubmit={onDeleteAccount}>
                  <SettingFieldGridRow
                    title="Delete account"
                    description="Account deletion is permanent in the current build. We can soften this later with deactivation or delayed deletion."
                  >
                    <div className="grid gap-4 md:grid-cols-2">
                      <FieldGroup label="Current password">
                        <Input
                          id="delete-account-password"
                          className="h-12 rounded-xl bg-white"
                          type="password"
                          value={deletePassword}
                          onChange={(e) => setDeletePassword(e.target.value)}
                          required
                        />
                      </FieldGroup>
                      <FieldGroup label='Type "DELETE" to confirm'>
                        <Input
                          id="delete-account-confirmation"
                          className="h-12 rounded-xl bg-white"
                          value={deleteConfirmation}
                          onChange={(e) => setDeleteConfirmation(e.target.value.toUpperCase())}
                          required
                        />
                      </FieldGroup>
                    </div>
                    <div className="mt-4 flex items-center gap-3">
                      <Button
                        type="submit"
                        variant="outline"
                        className="rounded-full border-destructive/40 px-5 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        disabled={deleteSubmitting}
                      >
                        {deleteSubmitting ? "Deleting..." : "Delete account"}
                      </Button>
                      {deleteMessage ? <span className="text-sm text-primary">{deleteMessage}</span> : null}
                    </div>
                  </SettingFieldGridRow>
                </form>
              </SectionShell>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );

  if (embedded) {
    return <div className="px-5 pb-5 pt-0">{content}</div>;
  }

  return content;
}

function SettingsTopNavButton({
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
      className={`inline-flex items-center rounded-full px-4 py-2 text-sm transition-colors ${
        active
          ? "bg-primary text-primary-foreground shadow-[0_4px_14px_rgba(28,24,20,0.12)]"
          : "bg-white/70 font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

function SectionShell({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white">
      <div className="flex flex-wrap items-start justify-between gap-4 px-6 py-5">
        <div>
          <h2 className="font-display text-[1.9rem] font-semibold tracking-tight text-foreground">{title}</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
        </div>
        {action ? <div className="pt-1">{action}</div> : null}
      </div>
      <div className="px-6 py-5">{children}</div>
    </div>
  );
}

function SettingFieldRow({
  label,
  hint,
  children,
}: {
  label: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-3 border-b border-border pb-6 last:border-b-0 last:pb-0 md:grid-cols-[180px_minmax(0,1fr)] md:items-start">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{hint}</p>
      </div>
      <div>{children}</div>
    </div>
  );
}

function SettingFieldGridRow({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)] lg:items-start">
      <div>
        <p className="text-lg font-semibold text-foreground">{title}</p>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
        {action ? <div className="mt-4">{action}</div> : null}
      </div>
      <div>{children}</div>
    </div>
  );
}

function SettingsSectionDivider() {
  return <div className="border-t border-border" aria-hidden="true" />;
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
