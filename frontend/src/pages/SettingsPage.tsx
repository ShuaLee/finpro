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

export type SettingsTab = "profile" | "danger";

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
  const [editingProfileSection, setEditingProfileSection] = useState<"name" | "preferences" | null>(null);
  const [editingSecuritySection, setEditingSecuritySection] = useState<"email" | "password" | null>(null);
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
      <header className={`pb-2 ${embedded ? "pt-5" : ""}`}>
        <h1 className="text-[2rem] font-semibold tracking-tight text-foreground">Settings</h1>
      </header>
      <nav className="mb-7 flex gap-8 overflow-x-auto border-b border-[#d8d2c7] text-sm" aria-label="Settings sections">
        <SettingsTabButton label="Account" active={activeTab === "profile"} onClick={() => setActiveTab("profile")} />
        <SettingsTabButton label="Danger zone" active={activeTab === "danger"} onClick={() => setActiveTab("danger")} />
      </nav>
      <div className="min-w-0">
        <section className="min-w-0">
          {globalError ? <p className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">{globalError}</p> : null}

          {activeTab === "profile" ? (
            <div className="space-y-12">
              <SettingsPanel title={null} description={null}>
                <form id="settings-profile-form" className="divide-y divide-[#e4ded3]" onSubmit={onSaveProfile}>
                  <SettingsSectionBlock title="Profile" description="Your personal information and account profile settings.">
                    <div className="space-y-5">
                      <div>
                        <p className="text-xs font-medium text-foreground/70">Avatar</p>
                        <div className="mt-3 flex items-center gap-4">
                          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#2d2925] text-xl font-semibold text-[#f8f6f1]">
                            {getInitials(fullName || me.user.email)}
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-foreground">{fullName || "Not set"}</p>
                            <p className="mt-1 text-sm text-foreground/60">{me.user.email}</p>
                          </div>
                        </div>
                      </div>

                      <SettingsReadRow
                        title="Full name"
                        value={fullName || "Not set"}
                        onEdit={() => setEditingProfileSection(editingProfileSection === "name" ? null : "name")}
                      >
                        {editingProfileSection === "name" ? (
                          <div className="space-y-4 pt-4">
                            <Input id="full-name" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                            <Button type="submit" className="h-9 rounded-full bg-[#2d2925] px-4 text-xs text-[#f8f6f1] hover:bg-[#2d2925]" disabled={profileSubmitting}>
                              {profileSubmitting ? "Saving..." : "Save changes"}
                            </Button>
                          </div>
                        ) : null}
                      </SettingsReadRow>
                    </div>
                  </SettingsSectionBlock>

                  <SettingsSectionBlock title="Account" description="Your login identity and current account state.">
                    <div className="space-y-1">
                      <SettingsReadRow title="Email" value={me.user.email} />
                      <SettingsReadRow title="Email status" value={me.user.is_email_verified ? "Verified" : "Not verified"} />
                      <SettingsReadRow title="Account status" value={me.user.is_active ? "Active" : "Inactive"} />
                      <SettingsReadRow title="Date joined" value={formatSettingsDate(me.user.date_joined)} />
                    </div>
                  </SettingsSectionBlock>

                  <SettingsSectionBlock title="Preferences" description="Your localization, reporting, and valuation defaults.">
                    <div className="space-y-1">
                      <SettingsReadRow
                        title="Language"
                        value={language || "Not set"}
                        onEdit={() => setEditingProfileSection(editingProfileSection === "preferences" ? null : "preferences")}
                      >
                        {editingProfileSection === "preferences" ? (
                          <div className="space-y-4 pt-4">
                            <div className="grid gap-4 md:grid-cols-2">
                              <FieldGroup label="Language">
                                <Input id="language" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" value={language} onChange={(e) => setLanguage(e.target.value)} required />
                              </FieldGroup>
                              <FieldGroup label="Timezone">
                                <Input id="timezone" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" value={timezone} onChange={(e) => setTimezone(e.target.value)} required />
                              </FieldGroup>
                              <FieldGroup label="Country code">
                                <Input id="country" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" placeholder="US" value={country} onChange={(e) => setCountry(e.target.value)} />
                              </FieldGroup>
                              <FieldGroup label="Currency code">
                                <Input id="currency" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" placeholder="USD" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
                              </FieldGroup>
                            </div>
                            <Button type="submit" className="h-9 rounded-full bg-[#2d2925] px-4 text-xs text-[#f8f6f1] hover:bg-[#2d2925]" disabled={profileSubmitting}>
                              {profileSubmitting ? "Saving..." : "Save changes"}
                            </Button>
                          </div>
                        ) : null}
                      </SettingsReadRow>
                      <SettingsReadRow title="Timezone" value={timezone || "Not set"} onEdit={() => setEditingProfileSection(editingProfileSection === "preferences" ? null : "preferences")} />
                      <SettingsReadRow title="Country" value={country || "Not set"} onEdit={() => setEditingProfileSection(editingProfileSection === "preferences" ? null : "preferences")} />
                      <SettingsReadRow title="Currency" value={currency || "Not set"} onEdit={() => setEditingProfileSection(editingProfileSection === "preferences" ? null : "preferences")} />
                    </div>
                  </SettingsSectionBlock>
                  {profileMessage ? <p className="pt-4 text-sm text-primary">{profileMessage}</p> : null}
                </form>
              </SettingsPanel>

              <SettingsPanel title={null} description={null}>
                <SettingsSectionBlock title="Login and security" description="Change the credentials used to access your account.">
                  <div className="space-y-8">
                    <form className="divide-y divide-[#e4ded3]" onSubmit={onUpdateEmail}>
                      <SettingsReadRow
                        title="Email"
                        value="Change the email address used to sign in."
                        onEdit={() => setEditingSecuritySection(editingSecuritySection === "email" ? null : "email")}
                      >
                        {editingSecuritySection === "email" ? (
                          <div className="space-y-4 pt-4">
                            <div className="grid gap-4 md:grid-cols-2">
                              <FieldGroup label="Email">
                                <Input id="settings-email" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                              </FieldGroup>
                              <FieldGroup label="Current password">
                                <Input id="settings-email-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} required />
                              </FieldGroup>
                            </div>
                            <div className="flex items-center gap-3">
                              <Button type="submit" className="rounded-full px-5" disabled={emailSubmitting}>{emailSubmitting ? "Saving..." : "Update email"}</Button>
                              {emailMessage ? <span className="text-sm text-primary">{emailMessage}</span> : null}
                            </div>
                          </div>
                        ) : null}
                      </SettingsReadRow>
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
                              className="h-11 rounded-[18px] border-[#d8d2c7] bg-white"
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

                    <form className="divide-y divide-[#e4ded3]" onSubmit={onChangePassword}>
                      <SettingsReadRow
                        title="Password"
                        value="Use a strong password and rotate it whenever needed."
                        onEdit={() => setEditingSecuritySection(editingSecuritySection === "password" ? null : "password")}
                      >
                        {editingSecuritySection === "password" ? (
                          <div className="space-y-4 pt-4">
                            <div className="grid gap-4 md:grid-cols-3">
                              <FieldGroup label="Current password">
                                <Input id="current-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
                              </FieldGroup>
                              <FieldGroup label="New password">
                                <Input id="new-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
                              </FieldGroup>
                              <FieldGroup label="Confirm password">
                                <Input id="confirm-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
                              </FieldGroup>
                            </div>
                            <div className="flex items-center gap-3">
                              <Button type="submit" className="rounded-full px-5" disabled={passwordSubmitting}>{passwordSubmitting ? "Saving..." : "Change password"}</Button>
                              {passwordMessage ? <span className="text-sm text-primary">{passwordMessage}</span> : null}
                            </div>
                          </div>
                        ) : null}
                      </SettingsReadRow>
                    </form>
                  </div>
                </SettingsSectionBlock>
              </SettingsPanel>
            </div>
          ) : null}

          {activeTab === "danger" ? (
            <SettingsPanel title="Terms and account actions" description="Destructive account-level actions.">
              <form className="divide-y divide-[#e4ded3]" onSubmit={onDeleteAccount}>
                <SettingsFormRow title="Delete account" description="Account deletion is permanent in the current build.">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FieldGroup label="Current password">
                      <Input id="delete-account-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={deletePassword} onChange={(e) => setDeletePassword(e.target.value)} required />
                    </FieldGroup>
                    <FieldGroup label='Type "DELETE" to confirm'>
                      <Input id="delete-account-confirmation" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" value={deleteConfirmation} onChange={(e) => setDeleteConfirmation(e.target.value.toUpperCase())} required />
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

function SettingsTabButton({
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
      className={`relative shrink-0 border-b-2 px-0 pb-3 pt-1 text-sm transition-colors ${
        active
          ? "border-[#2d2925] text-[#1f1b17]"
          : "border-transparent text-[#47423b]/68 hover:text-[#47423b]"
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
  title: string | null;
  description: string | null;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="min-w-0">
      {title || description || actions ? (
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            {title ? <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2> : null}
            {description ? <p className="mt-1 text-sm text-foreground/62">{description}</p> : null}
          </div>
          {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
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
    <div className="grid gap-5 py-7 first:pt-0 md:grid-cols-[260px_minmax(0,1fr)] md:items-start xl:grid-cols-[300px_minmax(0,1fr)]">
      <div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        {description ? <p className="mt-1 max-w-[16rem] text-xs leading-5 text-foreground/60">{description}</p> : null}
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

function SettingsSectionBlock({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-6 py-8 first:pt-0 md:grid-cols-[260px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)]">
      <div>
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        <p className="mt-2 max-w-[16rem] text-sm leading-6 text-foreground/58">{description}</p>
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

function SettingsReadRow({
  title,
  value,
  onEdit,
  children,
}: {
  title: string;
  value: string;
  onEdit?: () => void;
  children?: ReactNode;
}) {
  return (
    <div className="py-6">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
        <div>
          <p className="text-sm font-semibold text-foreground">{title}</p>
          <p className="mt-2 text-sm leading-6 text-foreground/62">{value}</p>
        </div>
        {onEdit ? (
          <button
            type="button"
            onClick={onEdit}
            className="justify-self-start text-sm font-medium text-[#00756f] transition-colors hover:text-[#005f5a] md:justify-self-end"
          >
            Edit
          </button>
        ) : null}
      </div>
      {children ? <div className="mt-1">{children}</div> : null}
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
      <span className="text-xs font-medium text-foreground/78">{label}</span>
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

function getInitials(value: string) {
  const parts = value
    .trim()
    .split(/\s+|@/)
    .filter(Boolean)
    .slice(0, 2);
  return (parts.map((part) => part[0]).join("") || "U").toUpperCase();
}


