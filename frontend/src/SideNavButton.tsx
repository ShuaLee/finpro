import type { ButtonHTMLAttributes, ReactNode } from "react";

import { FloatingPill } from "./FloatingPill";

type SideNavButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  icon: ReactNode;
  label: string;
  collapsed: boolean;
  tooltip?: string | null;
};

export function SideNavButton({ icon, label, collapsed, tooltip, className = "", ...buttonProps }: SideNavButtonProps) {
  return (
    <button
      type="button"
      className={`side-nav-button ${collapsed ? "side-nav-button-collapsed" : ""} ${className}`.trim()}
      aria-label={label}
      {...buttonProps}
    >
      <span className="side-nav-button-icon" aria-hidden="true">
        {icon}
      </span>
      {!collapsed ? <span className="side-nav-button-label">{label}</span> : null}
      {collapsed && tooltip ? (
        <span className="nav-button-tooltip">
          <FloatingPill>{tooltip}</FloatingPill>
        </span>
      ) : null}
    </button>
  );
}
