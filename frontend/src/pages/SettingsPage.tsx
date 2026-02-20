import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  changePassword,
  cancelPendingEmailChange,
  getMe,
  getProfile,
  resendPendingEmailChangeCode,
  type MeResponse,
  type ProfileResponse,
  updateEmail,
  updateProfile,
  verifyPendingEmailChange,
} from "../api/settings";
import { ApiError } from "../api/http";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../context/AuthContext";

export function SettingsPage() {
  const { refreshAuth } = useAuth();

  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<MeResponse | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [emailSubmitting, setEmailSubmitting] = useState(false);
  const [emailMessage, setEmailMessage] = useState<string | null>(null);
  const [emailCode, setEmailCode] = useState("");
  const [verifySubmitting, setVerifySubmitting] = useState(false);
  const [verifyMessage, setVerifyMessage] = useState<string | null>(null);
  const [resendSubmitting, setResendSubmitting] = useState(false);
  const [cancelSubmitting, setCancelSubmitting] = useState(false);

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
  const [receiveEmailUpdates, setReceiveEmailUpdates] = useState(true);
  const [receiveMarketingEmails, setReceiveMarketingEmails] = useState(false);
  const [profileSubmitting, setProfileSubmitting] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setGlobalError(null);
      try {
        const [meData, profileData] = await Promise.all([getMe(), getProfile()]);
        setMe(meData);
        setProfile(profileData);

        setEmail(meData.email);
        setFullName(profileData.full_name ?? "");
        setLanguage(profileData.language ?? "en");
        setTimezone(profileData.timezone ?? "UTC");
        setCountry(profileData.country ?? "");
        setCurrency(profileData.currency ?? "USD");
        setReceiveEmailUpdates(profileData.receive_email_updates);
        setReceiveMarketingEmails(profileData.receive_marketing_emails);
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
      setMe(res);
      setEmailPassword("");
      setEmailCode("");
      setEmailMessage(res.detail);
      await refreshAuth();
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
    if (!me?.pending_email_change) {
      return;
    }
    setVerifySubmitting(true);
    setVerifyMessage(null);
    setGlobalError(null);

    try {
      const res = await verifyPendingEmailChange(me.pending_email_change, emailCode.trim());
      setMe(res);
      setEmail(res.email);
      setEmailCode("");
      setVerifyMessage(res.detail);
      setEmailMessage(null);
      await refreshAuth();
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

  const onResendEmailChangeCode = async () => {
    setResendSubmitting(true);
    setGlobalError(null);
    setVerifyMessage(null);
    try {
      const res = await resendPendingEmailChangeCode();
      setMe(res);
      setVerifyMessage(res.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not resend verification code.");
      }
    } finally {
      setResendSubmitting(false);
    }
  };

  const onCancelEmailChange = async () => {
    setCancelSubmitting(true);
    setGlobalError(null);
    setVerifyMessage(null);
    try {
      const res = await cancelPendingEmailChange();
      setMe(res);
      setEmailCode("");
      setEmailMessage(res.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not cancel pending email change.");
      }
    } finally {
      setCancelSubmitting(false);
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
        full_name: fullName.trim() || null,
        language: language.trim().toLowerCase(),
        timezone: timezone.trim(),
        country: country.trim().toUpperCase() || null,
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

  const onSavePreferences = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProfileSubmitting(true);
    setProfileMessage(null);
    setGlobalError(null);

    try {
      const updated = await updateProfile({
        receive_email_updates: receiveEmailUpdates,
        receive_marketing_emails: receiveMarketingEmails,
      });
      setProfile(updated);
      setProfileMessage("Preferences updated successfully.");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setGlobalError(caught.message);
      } else {
        setGlobalError("Could not save preferences.");
      }
    } finally {
      setProfileSubmitting(false);
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

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">User settings</p>
          <h1 className="font-display text-3xl font-bold tracking-tight">Settings</h1>
        </div>
        <Link to="/" className="text-sm font-semibold text-primary">Back to dashboard</Link>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        <a href="#accounts" className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary">Accounts</a>
        <a href="#security" className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary">Login and security</a>
        <a href="#profile" className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary">Personal information</a>
        <a href="#notifications" className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary">Notifications</a>
        <a href="#investments" className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary">Investments</a>
      </div>

      {globalError ? <p className="mb-4 text-sm text-destructive">{globalError}</p> : null}

      <div className="space-y-6">
        <Card id="accounts" className="scroll-mt-24">
          <CardHeader>
            <Badge className="w-fit">Accounts</Badge>
            <CardTitle className="font-display text-2xl">Email</CardTitle>
            <CardDescription>Update your login email. You will need to verify the new address.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={onUpdateEmail}>
              <Field label="Email" htmlFor="settings-email">
                <Input id="settings-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </Field>
              <Field label="Current password" htmlFor="settings-email-password">
                <Input id="settings-email-password" type="password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} required />
              </Field>
              <div className="sm:col-span-2 flex items-center gap-3">
                <Button type="submit" disabled={emailSubmitting}>{emailSubmitting ? "Saving..." : "Update email"}</Button>
                {emailMessage ? <span className="text-sm text-primary">{emailMessage}</span> : null}
              </div>
            </form>
            {me.pending_email_change ? (
              <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={onVerifyEmailChange}>
                <div className="sm:col-span-2 rounded-md border border-border bg-secondary/40 px-3 py-2 text-sm text-muted-foreground">
                  Verification code sent to <span className="font-semibold text-foreground">{me.pending_email_change}</span>. Your login email will stay as{" "}
                  <span className="font-semibold text-foreground">{me.email}</span> until verified.
                </div>
                <Field label="6-digit verification code" htmlFor="email-change-code">
                  <Input
                    id="email-change-code"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={emailCode}
                    onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    required
                  />
                </Field>
                <div className="flex items-end">
                  <Button type="submit" disabled={verifySubmitting || emailCode.length !== 6}>
                    {verifySubmitting ? "Verifying..." : "Verify new email"}
                  </Button>
                </div>
                <div className="sm:col-span-2 flex flex-wrap items-center gap-3">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={onResendEmailChangeCode}
                    disabled={resendSubmitting || cancelSubmitting}
                  >
                    {resendSubmitting ? "Resending..." : "Resend code"}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onCancelEmailChange}
                    disabled={cancelSubmitting || resendSubmitting}
                  >
                    {cancelSubmitting ? "Canceling..." : "Cancel request"}
                  </Button>
                </div>
                {verifyMessage ? <p className="sm:col-span-2 text-sm text-primary">{verifyMessage}</p> : null}
              </form>
            ) : null}
          </CardContent>
        </Card>

        <Card id="security" className="scroll-mt-24">
          <CardHeader>
            <Badge className="w-fit">Login and security</Badge>
            <CardTitle className="font-display text-2xl">Password</CardTitle>
            <CardDescription>Change your password for better account security.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-3" onSubmit={onChangePassword}>
              <Field label="Current password" htmlFor="current-password">
                <Input id="current-password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
              </Field>
              <Field label="New password" htmlFor="new-password">
                <Input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
              </Field>
              <Field label="Confirm new password" htmlFor="confirm-password">
                <Input id="confirm-password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
              </Field>
              <div className="sm:col-span-3 flex items-center gap-3">
                <Button type="submit" disabled={passwordSubmitting}>{passwordSubmitting ? "Saving..." : "Change password"}</Button>
                {passwordMessage ? <span className="text-sm text-primary">{passwordMessage}</span> : null}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card id="profile" className="scroll-mt-24">
          <CardHeader>
            <Badge className="w-fit">Personal information</Badge>
            <CardTitle className="font-display text-2xl">Profile settings</CardTitle>
            <CardDescription>Personal details and valuation defaults.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={onSaveProfile}>
              <Field label="Full name" htmlFor="full-name">
                <Input id="full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </Field>
              <Field label="Language" htmlFor="language">
                <Input id="language" value={language} onChange={(e) => setLanguage(e.target.value)} required />
              </Field>
              <Field label="Timezone" htmlFor="timezone">
                <Input id="timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} required />
              </Field>
              <Field label="Country code" htmlFor="country">
                <Input id="country" placeholder="US" value={country} onChange={(e) => setCountry(e.target.value)} />
              </Field>
              <Field label="Currency code" htmlFor="currency">
                <Input id="currency" placeholder="USD" value={currency} onChange={(e) => setCurrency(e.target.value)} required />
              </Field>
              <div className="sm:col-span-2 flex items-center gap-3">
                <Button type="submit" disabled={profileSubmitting}>{profileSubmitting ? "Saving..." : "Save profile"}</Button>
                {profileMessage ? <span className="text-sm text-primary">{profileMessage}</span> : null}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card id="notifications" className="scroll-mt-24">
          <CardHeader>
            <Badge className="w-fit">Notifications</Badge>
            <CardTitle className="font-display text-2xl">Email preferences</CardTitle>
            <CardDescription>Communication and update preferences.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onSavePreferences}>
              <label className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-sm">
                <input type="checkbox" checked={receiveEmailUpdates} onChange={(e) => setReceiveEmailUpdates(e.target.checked)} className="h-4 w-4" />
                Receive account and platform updates
              </label>
              <label className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-sm">
                <input type="checkbox" checked={receiveMarketingEmails} onChange={(e) => setReceiveMarketingEmails(e.target.checked)} className="h-4 w-4" />
                Receive product and marketing emails
              </label>
              <div className="flex items-center gap-3">
                <Button type="submit" disabled={profileSubmitting}>{profileSubmitting ? "Saving..." : "Save notifications"}</Button>
                {profileMessage ? <span className="text-sm text-primary">{profileMessage}</span> : null}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card id="investments" className="scroll-mt-24">
          <CardHeader>
            <Badge className="w-fit">Investments</Badge>
            <CardTitle className="font-display text-2xl">Investment preferences</CardTitle>
            <CardDescription>Portfolio preferences and rules.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Investment-specific controls will be added here as portfolio settings are expanded.</p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={htmlFor} className="text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}
