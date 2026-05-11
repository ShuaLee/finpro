import { useEffect, useId, useRef, useState, type ReactNode } from "react";

type DropdownTriggerProps = {
  menuId: string;
  open: boolean;
  toggle: () => void;
};

type DropdownItem = {
  label: string;
  onSelect?: () => void | Promise<void>;
};

type DropdownProps = {
  label: string;
  trigger: (props: DropdownTriggerProps) => ReactNode;
  items: DropdownItem[];
};

export function Dropdown({ label, trigger, items }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    const closeOnOutsidePointerDown = (event: PointerEvent) => {
      if (!dropdownRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("pointerdown", closeOnOutsidePointerDown);
    document.addEventListener("keydown", closeOnEscape);

    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointerDown);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <div className="dropdown" ref={dropdownRef}>
      {trigger({
        menuId,
        open,
        toggle: () => setOpen((current) => !current),
      })}
      {open ? (
        <div id={menuId} className="dropdown-menu" role="menu" aria-label={label}>
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              className="dropdown-menu-item text-dropdown"
              role="menuitem"
              onClick={() => {
                item.onSelect?.();
                setOpen(false);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
