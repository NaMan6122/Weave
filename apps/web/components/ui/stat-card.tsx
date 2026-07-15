interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendPositive?: boolean;
}

export function StatCard({ label, value, trend, trendPositive }: StatCardProps) {
  return (
    <div className="rounded-xl border border-neutral-800 p-6">
      <p className="text-sm text-neutral-400 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {trend && (
        <p className={`text-xs mt-1 ${trendPositive ? "text-green-400" : "text-neutral-500"}`}>
          {trend}
        </p>
      )}
    </div>
  );
}
