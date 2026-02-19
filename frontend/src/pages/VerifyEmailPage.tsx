import { useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { verifyEmail } from "../api/auth";
import { ApiError } from "../api/http";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useAuth } from "../context/AuthContext";

export function VerifyEmailPage() {
  const { refreshAuth } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const defaultEmail = useMemo(() => searchParams.get("email") ?? "", [searchParams]);

  const [email, setEmail] = useState(defaultEmail);
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await verifyEmail(email.trim(), code.trim());
      setSuccess(response.detail);
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

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Card className="mx-auto max-w-lg bg-white/95">
        <CardHeader>
          <Badge className="w-fit">Email Passcode</Badge>
          <CardTitle className="font-display text-3xl">Confirm your account</CardTitle>
          <CardDescription>Enter the 6-digit passcode sent to your email.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <label htmlFor="verification-email" className="text-sm font-medium">Email</label>
              <Input
                id="verification-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="verification-code" className="text-sm font-medium">6-digit code</label>
              <Input
                id="verification-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={code}
                onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                required
              />
            </div>

            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            {success ? <p className="text-sm text-primary">{success}</p> : null}

            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? "Verifying..." : "Verify email"}
            </Button>
          </form>

          <p className="mt-5 text-sm text-muted-foreground">
            Continue to <Link className="font-semibold text-primary" to="/login">login</Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
