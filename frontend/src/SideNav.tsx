import { NavButton } from "./NavButton";

type SideNavProps = {
  collapsed: boolean;
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

export function SideNav({ collapsed }: SideNavProps) {
  return (
    <nav className={`side-nav ${collapsed ? "side-nav-collapsed" : ""}`} aria-label="Primary navigation">
      <div className="side-nav-top">
        <NavButton icon={<PortfolioIcon />} label="Portfolio" tooltip={collapsed ? "Portfolio" : null} />
      </div>
    </nav>
  );
}
