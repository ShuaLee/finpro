type BrandLogoProps = {
  compact?: boolean;
};

function BrandIcon() {
  return (
    <span className="brand-logo-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" className="brand-logo-svg" focusable="false">
        <path
          d="M5 19V5m0 14h14M8.5 15.5l3.25-4 2.5 2.5L18.5 8"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
        />
      </svg>
    </span>
  );
}

export function BrandLogo({ compact = false }: BrandLogoProps) {
  return (
    <span className={`brand-logo ${compact ? "brand-logo-compact" : ""}`.trim()}>
      <span className="brand-logo-icon-slot">
        <BrandIcon />
      </span>
      {!compact ? <span className="brand-logo-wordmark">FinPro</span> : null}
    </span>
  );
}
