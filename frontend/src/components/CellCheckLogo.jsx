/**
 * CellCheck logo mark: a cell (ring) holding an STR barcode with a verified
 * green check. The outline/bars use `currentColor` so the mark inherits the
 * surrounding text color (dark ink in light mode, white in dark mode); the
 * green stays fixed as the "authenticated" accent.
 */
export function CellCheckLogo({ className = "h-6 w-6", ...props }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      role="img"
      aria-label="CellCheck logo"
      {...props}
    >
      <circle cx="29" cy="30" r="24" fill="none" stroke="currentColor" strokeWidth="3.2" />
      <path d="M11 43 H49" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <rect x="12" y="35" width="4" height="8" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="17.5" y="27" width="4" height="16" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="23" y="31" width="4" height="12" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="34" y="25" width="4" height="18" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="39.5" y="33" width="4" height="10" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="28.5" y="17" width="4.5" height="26" fill="#1f9d57" />
      <path
        d="M20 39 L28 48 L52 15"
        fill="none"
        stroke="#1f9d57"
        strokeWidth="5.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
