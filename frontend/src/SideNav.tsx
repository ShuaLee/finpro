import { BrandLogo } from "./BrandLogo";
import { SideNavButton } from "./SideNavButton";
import { NavButton } from "./NavButton";

type SideNavProps = {
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

function PortfolioIcon() {
  return (
    <svg viewBox="0 0 24 24" className="nav-button-svg" focusable="false">
      <path
        d="M5 19V5m0 14h14M8.5 15.5l3.25-4 2.5 2.5L18.5 8"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function CollapseIcon() {
  return (
    <svg viewBox="0 0 24 24" className="nav-button-svg" focusable="false">
      <path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

function ExpandIcon() {
  return (
    <svg viewBox="0 0 24 24" className="nav-button-svg" focusable="false">
      <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

export function SideNav({ collapsed, onToggleCollapsed }: SideNavProps) {
  return (
    <nav className={`side-nav ${collapsed ? "side-nav-collapsed" : ""}`} aria-label="Primary navigation">
      <div className="side-nav-header">
        <BrandLogo compact={collapsed} />
      </div>
      <div className="side-nav-top">
        <SideNavButton
          collapsed={collapsed}
          icon={<PortfolioIcon />}
          label="Portfolio"
          tooltip={collapsed ? "Portfolio" : null}
        />
      </div>
      <div className="side-nav-bottom">
        <NavButton
          icon={collapsed ? <ExpandIcon /> : <CollapseIcon />}
          label={collapsed ? "Expand side navigation" : "Collapse side navigation"}
          tooltip={collapsed ? "Expand side navigation" : null}
          onClick={onToggleCollapsed}
        />
      </div>
    </nav>
  );
}
