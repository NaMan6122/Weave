export function DrBadge({ dr }: { dr: number | null | undefined }) {
  if (dr == null) return null;
  const rounded = Math.round(dr);
  let color = "bg-red-900/50 text-red-300";
  if (rounded >= 50) color = "bg-green-900/50 text-green-300";
  else if (rounded >= 20) color = "bg-yellow-900/50 text-yellow-300";

  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold ${color}`}>
      DR {rounded}
    </span>
  );
}
