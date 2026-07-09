// Standard shadcn/Tailwind skeleton: a pulsing muted block. Pass className for sizing.
export default function Skeleton({ className = "" }) {
  return <div className={`animate-pulse rounded-md bg-muted ${className}`} />;
}
