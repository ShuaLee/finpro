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

export type SettingsTab = "profile";

type SettingsPageProps = {
  embedded?: boolean;
  activeSection?: SettingsTab | null;
  onSectionChange?: (section: SettingsTab | null) => void;
};

export function SettingsPage({ embedded = false }: SettingsPageProps) {
  const { refreshAuth, logoutAllSessions, loading: authLoading } = useAuth();
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
  const [deletePasswordConfirm, setDeletePasswordConfirm] = useState("");
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);
  const [logoutAllSubmitting, setLogoutAllSubmitting] = useState(false);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

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
      setEmailModalOpen(false);
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
      setPasswordModalOpen(false);
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

    if (deletePassword !== deletePasswordConfirm) {
      setGlobalError("Password and confirmation password do not match.");
      setDeleteSubmitting(false);
      return;
    }

    try {
      const response = await deleteAccount(deletePassword, deleteConfirmation);
      setDeleteMessage(response.detail);
      setDeletePassword("");
      setDeletePasswordConfirm("");
      setDeleteConfirmation("");
      setDeleteModalOpen(false);
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

  const onLogoutAllSessions = async () => {
    setLogoutAllSubmitting(true);
    setGlobalError(null);
    try {
      await logoutAllSessions();
      navigate("/signup", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not log out of all sessions.");
      }
    } finally {
      setLogoutAllSubmitting(false);
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
    <main className={`mx-auto w-full ${embedded ? "max-w-[980px] px-0 py-0" : "max-w-[980px] px-4 py-8 sm:px-6 lg:px-8"}`}>
      <header className={`pb-2 ${embedded ? "pt-5" : ""}`}>
        <h1 className="text-[2rem] font-semibold tracking-tight text-foreground">Settings</h1>
      </header>
      <nav className="mb-7 flex min-h-[48px] items-end justify-between gap-4 border-b border-[#d8d2c7] text-sm" aria-label="Settings sections">
        <div className="flex items-end gap-8">
          <button
            type="button"
            className="-mb-px shrink-0 border-b-2 border-[#2d2925] px-0 pb-3 text-sm font-medium leading-none text-[#47423b]"
          >
            Account
          </button>
        </div>
        <div className="pb-2">
          <Button
            type="submit"
            form="settings-profile-form"
            className="h-[34px] rounded-full bg-[#2d2925] px-4 text-sm font-medium text-[#f8f6f1] shadow-[0_4px_10px_rgba(28,24,20,0.03)] hover:bg-[#2d2925] hover:text-[#f8f6f1]"
            disabled={profileSubmitting}
          >
            {profileSubmitting ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </nav>
      <div className="min-w-0">
        <section className="min-w-0">
          {globalError ? <p className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">{globalError}</p> : null}

          <div className="space-y-12">
              <SettingsPanel title={null} description={null}>
                <form id="settings-profile-form" className="divide-y divide-[#e4ded3]" onSubmit={onSaveProfile}>
                  <SettingsSectionBlock title="Profile" description="Your personal information and account security settings.">
                    <div className="space-y-4">
                      <FieldGroup label="Full name">
                        <Input id="full-name" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                      </FieldGroup>
                      <FieldGroup label="Email">
                        <div className="flex gap-3">
                          <Input className="h-11 rounded-[18px] border-[#d8d2c7] bg-white text-muted-foreground" value={me.user.email} disabled readOnly />
                          <Button
                            type="button"
                            variant="outline"
                            className="h-[38px] shrink-0 rounded-full border-[#d8d2c7] bg-white px-[15px] text-sm font-medium text-[#47423b] shadow-[0_4px_10px_rgba(28,24,20,0.03)] hover:bg-white hover:text-[#47423b]"
                            onClick={() => {
                              setEmail(me.user.email);
                              setEmailPassword("");
                              setEmailCode("");
                              setEmailMessage(null);
                              setVerifyMessage(null);
                              setEmailModalOpen(true);
                            }}
                          >
                            Edit
                          </Button>
                        </div>
                      </FieldGroup>
                      <FieldGroup label="Password">
                        <div className="flex gap-3">
                          <Input className="h-11 rounded-[18px] border-[#d8d2c7] bg-white text-muted-foreground" value="**********" disabled readOnly />
                          <Button
                            type="button"
                            variant="outline"
                            className="h-[38px] shrink-0 rounded-full border-[#d8d2c7] bg-white px-[15px] text-sm font-medium text-[#47423b] shadow-[0_4px_10px_rgba(28,24,20,0.03)] hover:bg-white hover:text-[#47423b]"
                            onClick={() => {
                              setCurrentPassword("");
                              setNewPassword("");
                              setConfirmPassword("");
                              setPasswordMessage(null);
                              setPasswordModalOpen(true);
                            }}
                          >
                            Edit
                          </Button>
                        </div>
                      </FieldGroup>
                      <div className="flex flex-wrap items-center gap-3 pt-2">
                        {profileMessage ? <p className="text-sm text-primary">{profileMessage}</p> : null}
                        {passwordMessage ? <p className="text-sm text-primary">{passwordMessage}</p> : null}
                        {verifyMessage ? <p className="text-sm text-primary">{verifyMessage}</p> : null}
                      </div>
                    </div>
                  </SettingsSectionBlock>

                  <SettingsSectionBlock title="Preferences" description="Finance defaults used for valuation and reporting.">
                    <div className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-2">
                        <FieldGroup label="Country code">
                          <Input id="country" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" placeholder="US" value={country} onChange={(e) => setCountry(e.target.value)} />
                        </FieldGroup>
                        <FieldGroup label="Currency code">
                          <Input id="currency" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" placeholder="USD" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
                        </FieldGroup>
                      </div>
                    </div>
                  </SettingsSectionBlock>
                </form>
              </SettingsPanel>

            <SettingsPanel title={null} description={null}>
              <SettingsSectionBlock title="Danger Zone" description="Permanent account-level actions.">
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="h-[38px] rounded-full border-[#d8d2c7] bg-white px-[15px] text-sm font-medium text-[#47423b] shadow-[0_4px_10px_rgba(28,24,20,0.03)] hover:bg-white hover:text-[#47423b]"
                    onClick={onLogoutAllSessions}
                    disabled={logoutAllSubmitting}
                  >
                    {logoutAllSubmitting ? "Logging out..." : "Logout of all sessions"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-full border-destructive/40 px-5 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => {
                      setDeletePassword("");
                      setDeletePasswordConfirm("");
                      setDeleteConfirmation("");
                      setDeleteMessage(null);
                      setDeleteModalOpen(true);
                    }}
                  >
                    Delete Account
                  </Button>
                  {deleteMessage ? <p className="text-sm text-primary">{deleteMessage}</p> : null}
                </div>
              </SettingsSectionBlock>
            </SettingsPanel>
          </div>
        </section>
      </div>
      <SettingsModal
        open={emailModalOpen}
        title={pendingEmailChange ? "Verify new email" : "Update email"}
        description={
          pendingEmailChange
            ? `Enter the 6-digit code sent to ${pendingEmailChange}.`
            : "Enter your new email and current password. A verification code will be sent to the new address."
        }
        onClose={() => setEmailModalOpen(false)}
      >
        {pendingEmailChange ? (
          <form className="space-y-4" onSubmit={onVerifyEmailChange}>
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
            <div className="flex items-center justify-end gap-3">
              <Button type="button" variant="outline" className="rounded-full" onClick={() => setEmailModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="rounded-full px-5" disabled={verifySubmitting || emailCode.length !== 6}>
                {verifySubmitting ? "Verifying..." : "Verify"}
              </Button>
            </div>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={onUpdateEmail}>
            <FieldGroup label="New email">
              <Input id="settings-email" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </FieldGroup>
            <FieldGroup label="Current password">
              <Input id="settings-email-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} required />
            </FieldGroup>
            {emailMessage ? <p className="text-sm text-primary">{emailMessage}</p> : null}
            <div className="flex items-center justify-end gap-3">
              <Button type="button" variant="outline" className="rounded-full" onClick={() => setEmailModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="rounded-full px-5" disabled={emailSubmitting}>
                {emailSubmitting ? "Saving..." : "Update email"}
              </Button>
            </div>
          </form>
        )}
      </SettingsModal>
      <SettingsModal
        open={passwordModalOpen}
        title="Change password"
        description="Use a strong password and rotate it whenever needed."
        onClose={() => setPasswordModalOpen(false)}
      >
        <form className="space-y-4" onSubmit={onChangePassword}>
          <FieldGroup label="Current password">
            <Input id="current-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          </FieldGroup>
          <FieldGroup label="New password">
            <Input id="new-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
          </FieldGroup>
          <FieldGroup label="Confirm password">
            <Input id="confirm-password" className="h-11 rounded-[18px] border-[#d8d2c7] bg-white" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
          </FieldGroup>
          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="outline" className="rounded-full" onClick={() => setPasswordModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" className="rounded-full px-5" disabled={passwordSubmitting}>
              {passwordSubmitting ? "Saving..." : "Change password"}
            </Button>
          </div>
        </form>
      </SettingsModal>
      <SettingsModal
        open={deleteModalOpen}
        title="Delete account"
        description='This is permanent. Confirm your password and type "DELETE" to continue.'
        onClose={() => setDeleteModalOpen(false)}
      >
        <form className="space-y-4" onSubmit={onDeleteAccount}>
          <FieldGroup label="Current password">
            <Input
              id="delete-account-password"
              className="h-11 rounded-[18px] border-[#d8d2c7] bg-white"
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              required
            />
          </FieldGroup>
          <FieldGroup label="Confirm password">
            <Input
              id="delete-account-password-confirm"
              className="h-11 rounded-[18px] border-[#d8d2c7] bg-white"
              type="password"
              value={deletePasswordConfirm}
              onChange={(e) => setDeletePasswordConfirm(e.target.value)}
              required
            />
          </FieldGroup>
          <FieldGroup label='Type "DELETE" to confirm'>
            <Input
              id="delete-account-confirmation"
              className="h-11 rounded-[18px] border-[#d8d2c7] bg-white"
              value={deleteConfirmation}
              onChange={(e) => setDeleteConfirmation(e.target.value.toUpperCase())}
              required
            />
          </FieldGroup>
          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="outline" className="rounded-full" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="outline"
              className="rounded-full border-destructive/40 px-5 text-destructive hover:bg-destructive/10 hover:text-destructive"
              disabled={deleteSubmitting || deleteConfirmation !== "DELETE"}
            >
              {deleteSubmitting ? "Deleting..." : "Delete account"}
            </Button>
          </div>
        </form>
      </SettingsModal>
    </main>
  );
  if (embedded) {
    return <div className="px-5 pt-0">{content}</div>;
  }

  return content;
}

function SettingsModal({
  open,
  title,
  description,
  children,
  onClose,
}: {
  open: boolean;
  title: string;
  description: string;
  children: ReactNode;
  onClose: () => void;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#1f1b17]/30 px-4 py-6" role="dialog" aria-modal="true" aria-labelledby="settings-modal-title">
      <button type="button" className="absolute inset-0 cursor-default" aria-label="Close modal" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg rounded-[28px] border border-[#d8d2c7] bg-white p-6 shadow-[0_24px_70px_rgba(31,27,23,0.18)]">
        <div className="mb-6">
          <h2 id="settings-modal-title" className="text-xl font-semibold tracking-tight text-foreground">
            {title}
          </h2>
          <p className="mt-2 text-sm leading-6 text-foreground/60">{description}</p>
        </div>
        {children}
      </div>
    </div>
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




