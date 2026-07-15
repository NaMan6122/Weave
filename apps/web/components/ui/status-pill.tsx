const statusColors: Record<string, string> = {
  live: "bg-green-900/50 text-green-300",
  pending: "bg-yellow-900/50 text-yellow-300",
  placed: "bg-yellow-900/50 text-yellow-300",
  removed: "bg-red-900/50 text-red-300",
  broken: "bg-neutral-700 text-neutral-400",
  modified: "bg-blue-900/50 text-blue-300",
};

export function StatusPill({ status }: { status: string }) {
  const color = statusColors[status] || "bg-neutral-700 text-neutral-400";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}
