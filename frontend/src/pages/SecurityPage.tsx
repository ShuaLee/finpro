import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, Lock, Server, ShieldCheck, UserCheck } from "lucide-react";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

const principles = [
  {
    icon: ShieldCheck,
    title: "Account protection",
    copy: "Layered sign-in checks help keep unauthorized users out of your account.",
  },
  {
    icon: Lock,
    title: "Sensitive data handling",
    copy: "Security-sensitive updates require strict validation before account changes are accepted.",
  },
  {
    icon: Server,
    title: "Risk controls",
    copy: "Repeated failed logins trigger temporary lockouts to reduce brute-force attack risk.",
  },
  {
    icon: UserCheck,
    title: "User controls",
    copy: "You can manage your email, password, and important account preferences in Settings.",
  },
];

const faqs = [
  {
    question: "How does FinPro protect my account sign-in?",
    answer:
      "FinPro uses verification codes, trusted-session checks, and temporary lockouts after repeated failed login attempts.",
  },
  {
    question: "How is my personal account information protected?",
    answer:
      "Account actions are validated on the backend, and security-sensitive updates require credential checks before changes are applied.",
  },
  {
    question: "What happens when I change my email?",
    answer:
      "Your email does not change right away. A code is sent to the new email, and your login email updates only after successful verification.",
  },
  {
    question: "Can I change my password from inside the app?",
    answer:
      "Yes. You can change your password in Settings using your current password, and password rules are enforced before updates are saved.",
  },
  {
    question: "Can I cancel or resend an email change verification code?",
    answer:
      "Yes. If you start an email change and decide not to continue, you can cancel it from Settings. You can also resend a verification code.",
  },
];

export function SecurityPage() {
  const [openFaq, setOpenFaq] = useState<number>(0);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="mb-10 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="space-y-4">
          <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Security focused on protecting your account and sensitive information.
          </h1>
          <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
            FinPro is designed to keep your account secure while giving you clear control over key security settings.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/signup">
              <Button>Get started</Button>
            </Link>
            <Link to="/pricing">
              <Button variant="outline">View pricing</Button>
            </Link>
          </div>
        </div>

        <Card className="bg-white/90">
          <CardHeader>
            <CardTitle className="font-display text-2xl">At a glance</CardTitle>
            <CardDescription>Core protections currently available in FinPro.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>- Verification-based sign-in flow</p>
            <p>- Lockouts after repeated failed login attempts</p>
            <p>- Verified email change before account email replacement</p>
            <p>- In-app controls for password and account preferences</p>
          </CardContent>
        </Card>
      </section>

      <section className="mb-10 grid gap-4 sm:grid-cols-2">
        {principles.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title} className="bg-white/90">
              <CardContent className="space-y-3 p-6">
                <Icon className="h-5 w-5 text-primary" />
                <h2 className="font-display text-2xl font-semibold tracking-tight">{item.title}</h2>
                <p className="text-sm text-muted-foreground">{item.copy}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <section>
        <h2 className="mb-4 font-display text-3xl font-bold tracking-tight">Security FAQ</h2>
        <div className="space-y-3">
          {faqs.map((faq, index) => {
            const open = openFaq === index;
            return (
              <Card key={faq.question} className="bg-white/90">
                <button
                  type="button"
                  onClick={() => setOpenFaq(open ? -1 : index)}
                  className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
                >
                  <span className="text-base font-semibold">{faq.question}</span>
                  <ChevronDown className={`h-4 w-4 text-muted-foreground transition ${open ? "rotate-180" : ""}`} />
                </button>
                {open ? (
                  <CardContent className="pt-0">
                    <p className="text-sm text-muted-foreground">{faq.answer}</p>
                  </CardContent>
                ) : null}
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}
