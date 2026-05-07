import { NavButton } from "./NavButton";

function HamburgerIcon() {
  return (
    <svg viewBox="0 0 24 24" className="nav-button-svg" focusable="false">
      <path d="M5 7h14M5 12h14M5 17h14" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
    </svg>
  );
}

type TopNavProps = {
  sideNavCollapsed: boolean;
  onToggleSideNav: () => void;
};

export function TopNav({ sideNavCollapsed, onToggleSideNav }: TopNavProps) {
  return (
    <header className="top-nav">
      <div className="top-nav-side-slot">
        <NavButton
          icon={<HamburgerIcon />}
          label={sideNavCollapsed ? "Expand side navigation" : "Collapse side navigation"}
          onClick={onToggleSideNav}
        />
      </div>
    </header>
  );
}
