import type { ButtonHTMLAttributes, ReactNode } from "react";

import { FloatingPill } from "./FloatingPill";

type NavButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon: ReactNode;
  label: string;
  tooltip?: string | null;
};

export function NavButton({ icon, label, tooltip, className = "", ...buttonProps }: NavButtonProps) {
  return (
    <button type="button" className={`nav-button ${className}`.trim()} aria-label={label} {...buttonProps}>
      <span className="nav-button-icon" aria-hidden="true">
        {icon}
      </span>
      {tooltip ? (
        <span className="nav-button-tooltip">
          <FloatingPill>{tooltip}</FloatingPill>
        </span>
      ) : null}
    </button>
  );
}
