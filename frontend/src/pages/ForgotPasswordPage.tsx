import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ChartNoAxesCombined } from "lucide-react";

import { forgotPassword } from "../api/auth";
import { ApiError } from "../api/http";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { FloatingInput } from "../components/ui/floating-input";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await forgotPassword(email.trim());
      setSuccessMessage(response.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to send reset email right now.");
      }
    } finally {
      setSubmitting(false);
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
        <form className="mx-auto max-w-lg" onSubmit={onSubmit}>
          <Card className="bg-white/95">
            <CardHeader>
              <CardTitle className="font-display text-3xl">Forgot password</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Enter the email address associated with your account to reset your password.
                </p>
                <FloatingInput
                  id="forgot-email"
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                />

                {error ? <p className="text-sm text-destructive">{error}</p> : null}
                {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}
              </div>

              <Button className="mt-6 w-full" type="submit" disabled={submitting}>
                {submitting ? "Sending..." : "Continue"}
              </Button>

              <p className="mt-6 text-sm text-muted-foreground">
                Back to <Link className="font-semibold text-primary" to="/login">login</Link>
              </p>
            </CardContent>
          </Card>
        </form>
      </div>
    </main>
  );
}
