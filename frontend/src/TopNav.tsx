import { Dropdown } from "./Dropdown";
import { NavButton } from "./NavButton";
import { useAuth } from "./context/AuthContext";

type TopNavProps = {
  title?: string;
  onOpenSettings: () => void;
  hideBorder?: boolean;
};

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" className="nav-button-svg" focusable="false">
      <path
        d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 8a7 7 0 0 0-14 0"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export function TopNav({ title, onOpenSettings, hideBorder = false }: TopNavProps) {
  const { logout } = useAuth();

  return (
    <header className={`top-nav ${hideBorder ? "top-nav-borderless" : ""}`.trim()}>
      <div className="top-nav-title">{title}</div>
      <div className="top-nav-actions">
        <Dropdown
          label="Profile menu"
          items={[{ label: "Settings", onSelect: onOpenSettings }, { label: "Logout", onSelect: logout }]}
          trigger={({ menuId, open, toggle }) => (
            <NavButton
              icon={<ProfileIcon />}
              label="Profile"
              aria-controls={open ? menuId : undefined}
              aria-expanded={open}
              aria-haspopup="menu"
              onClick={toggle}
            />
          )}
        />
      </div>
    </header>
  );
}
