import { Link } from "react-router-dom";

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-14 border-t border-zinc-800 bg-[#0a0b0d] text-zinc-100">
      <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        <div className="space-y-2">
          <p className="font-display text-xl font-bold tracking-tight">FinPro</p>
          <p className="text-sm text-zinc-400">
            Wealth visibility platform for individuals and advisory workflows.
          </p>
        </div>

        <FooterColumn
          title="Company"
          links={[
            { label: "About us", to: "/about" },
            { label: "Contact", to: "/contact" },
            { label: "Pricing", to: "/pricing" },
            { label: "Security", to: "/security" },
          ]}
        />

        <FooterColumn
          title="Legal"
          links={[
            { label: "Privacy Policy", to: "/privacy" },
            { label: "Terms of Service", to: "/terms" },
          ]}
        />

        <FooterColumn
          title="Support"
          links={[
            { label: "Login", to: "/login" },
            { label: "Sign up", to: "/signup" },
          ]}
        />
      </div>

      <div className="border-t border-zinc-800">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-3 px-4 py-4 text-xs text-zinc-500 sm:px-6 lg:px-8">
          <p>© {year} FinPro. All rights reserved.</p>
          <p>For informational purposes only. Not investment advice.</p>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { label: string; to: string }[];
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-zinc-100">{title}</p>
      <ul className="space-y-1.5">
        {links.map((link) => (
          <li key={link.to}>
            <Link to={link.to} className="text-sm text-zinc-400 transition hover:text-zinc-100">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
