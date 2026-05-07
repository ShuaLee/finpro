import type { ReactNode } from "react";

type FloatingPillProps = {
  children: ReactNode;
};

export function FloatingPill({ children }: FloatingPillProps) {
  return <span className="floating-pill">{children}</span>;
}
