import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { MailCheck } from "lucide-react";

import { register, resendVerification } from "../api/auth";
import { ApiError } from "../api/http";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../context/AuthContext";

export function SignupPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
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
      const response = await register(email.trim(), password, acceptTerms);
      setSuccessMessage(response.detail);
      navigate(`/verify-email?email=${encodeURIComponent(email.trim())}`);
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
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Card className="mx-auto max-w-lg bg-white/95">
        <CardHeader>
          <Badge className="w-fit">Get Started</Badge>
          <CardTitle className="font-display text-3xl">Create your account</CardTitle>
          <CardDescription>Sign up now and verify your email to unlock login.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <label htmlFor="signup-email" className="text-sm font-medium">Email</label>
              <Input
                id="signup-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="signup-password" className="text-sm font-medium">Password</label>
              <Input
                id="signup-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            <label className="flex items-start gap-2 rounded-lg border border-border bg-secondary/40 p-3 text-sm" htmlFor="accept-terms">
              <input
                id="accept-terms"
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-border"
                checked={acceptTerms}
                onChange={(event) => setAcceptTerms(event.target.checked)}
                required
              />
              <span>I accept the terms of use and understand authentication requires email verification.</span>
            </label>

            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}

            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? "Creating account..." : "Create account"}
            </Button>

            <Button
              className="w-full"
              variant="secondary"
              type="button"
              onClick={onResend}
              disabled={resending || !email.trim()}
            >
              {resending ? "Sending..." : "Resend verification email"}
            </Button>
          </form>

          <div className="mt-6 rounded-lg border border-border bg-secondary/40 p-3 text-sm text-muted-foreground">
            <div className="mb-1 flex items-center gap-2 text-foreground">
              <MailCheck className="h-4 w-4 text-primary" />
              Verification-first auth flow
            </div>
            Already have an account? <Link className="font-semibold text-primary" to="/login">Log in</Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
