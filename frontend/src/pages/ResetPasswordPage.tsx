import { useMemo, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ChartNoAxesCombined } from "lucide-react";

import { resetPassword } from "../api/auth";
import { ApiError } from "../api/http";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { FloatingInput } from "../components/ui/floating-input";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get("token") ?? "", [searchParams]);

  const [newPassword, setNewPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await resetPassword(token, newPassword);
      setSuccessMessage(response.detail);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to reset password.");
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
        <Card className="mx-auto max-w-lg bg-white/95">
          <CardHeader>
            <CardTitle className="font-display text-3xl">Reset password</CardTitle>
          </CardHeader>
          <CardContent>
            {token ? (
              <form className="space-y-4" onSubmit={onSubmit}>
                <FloatingInput
                  id="reset-password"
                  label="New password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />

                {error ? <p className="text-sm text-destructive">{error}</p> : null}
                {successMessage ? <p className="text-sm text-primary">{successMessage}</p> : null}

                <Button className="w-full" type="submit" disabled={submitting}>
                  {submitting ? "Resetting..." : "Reset password"}
                </Button>
              </form>
            ) : (
              <p className="text-sm text-destructive">Missing reset token. Open the full link from your email.</p>
            )}

            <p className="mt-6 text-sm text-muted-foreground">
              Back to <Link className="font-semibold text-primary" to="/login">login</Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
