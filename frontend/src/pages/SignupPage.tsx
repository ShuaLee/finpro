import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ChartNoAxesCombined } from "lucide-react";

import { register, resendVerification, verifyEmail } from "../api/auth";
import { ApiError } from "../api/http";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { FloatingInput } from "../components/ui/floating-input";
import { useAuth } from "../context/AuthContext";

const FALLBACK_CURRENCY_BY_COUNTRY: Record<string, string> = {
  AU: "AUD",
  CA: "CAD",
  CH: "CHF",
  DE: "EUR",
  ES: "EUR",
  FR: "EUR",
  GB: "GBP",
  IE: "EUR",
  IT: "EUR",
  JP: "JPY",
  MX: "MXN",
  NL: "EUR",
  NZ: "NZD",
  SE: "SEK",
  SG: "SGD",
  US: "USD",
};

function getBrowserDefaults() {
  const locale = navigator.language || "en-US";
  const language = locale.split("-")[0]?.trim().toLowerCase() || "en";
  const country = locale.split("-")[1]?.trim().toUpperCase() || "";
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  const currency = FALLBACK_CURRENCY_BY_COUNTRY[country] ?? "USD";

  return { language, country, timezone, currency };
}

export function SignupPage() {
  const { user, refreshAuth } = useAuth();
  const navigate = useNavigate();
  const browserDefaults = getBrowserDefaults();

  const [stage, setStage] = useState<"signup" | "verify">("signup");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await register({
        fullName: fullName.trim(),
        email: email.trim(),
        password,
        acceptTerms: true,
        language: browserDefaults.language,
        timezone: browserDefaults.timezone,
        country: browserDefaults.country,
        currency: browserDefaults.currency,
      });
      setSuccessMessage(response.detail);
      setStage("verify");
      setCode("");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Signup failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const onVerify = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await verifyEmail(email.trim(), code.trim());
      setSuccessMessage(response.detail);
      await refreshAuth();
      navigate("/", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Verification failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const onResend = async () => {
    setResending(true);
    setError(null);

    try {
      const response = await resendVerification(email.trim());
      setSuccessMessage(response.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to resend verification email right now.");
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <main className="w-full">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        <Link to="/" className="inline-flex items-center gap-2">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ChartNoAxesCombined className="h-5 w-5" />
          </span>
          <span className="font-display text-[1.45rem] font-bold tracking-tight">FinPro</span>
        </Link>
      </div>

      <div className="mx-auto w-full max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <Card className="mx-auto max-w-lg bg-white/95">
          <CardHeader>
            <CardTitle className="font-display text-3xl">
              {stage === "signup" ? "Create your account" : "Verify your email"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stage === "signup" ? (
              <form className="space-y-4" onSubmit={onSubmit}>
                <FloatingInput
                  id="signup-name"
                  label="Name"
                  type="text"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  required
                  autoComplete="name"
                />

                <FloatingInput
                  id="signup-email"
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                />

                <FloatingInput
                  id="signup-password"
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />

                <p className="text-sm text-muted-foreground">
                  By continuing to sign up you accept our{" "}
                  <Link to="/terms" className="font-semibold text-primary">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link to="/privacy" className="font-semibold text-primary">
                    Privacy Policy
                  </Link>
                  .
                </p>

                {error ? <p className="text-sm text-destructive">{error}</p> : null}
                {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}

                <Button className="w-full" type="submit" disabled={submitting}>
                  {submitting ? "Creating account..." : "Create account"}
                </Button>
              </form>
            ) : (
              <form className="space-y-4" onSubmit={onVerify}>
                <FloatingInput id="verify-email" label="Email" type="email" value={email} disabled readOnly />

                <FloatingInput
                  id="verification-code"
                  label="6-digit code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={code}
                  onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  required
                />

                {error ? <p className="text-sm text-destructive">{error}</p> : null}
                {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}

                <Button className="w-full" type="submit" disabled={submitting}>
                  {submitting ? "Verifying..." : "Verify email"}
                </Button>

                <Button
                  className="w-full"
                  variant="secondary"
                  type="button"
                  onClick={onResend}
                  disabled={resending}
                >
                  {resending ? "Sending..." : "Resend verification code"}
                </Button>
              </form>
            )}

            <p className="mt-6 text-sm text-muted-foreground">
              Already have an account? <Link className="font-semibold text-primary" to="/login">Log in</Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
