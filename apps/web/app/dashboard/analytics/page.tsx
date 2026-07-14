import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Analytics",
  description: "Track domain authority trends, link growth, and WTS scores over time.",
  robots: { index: false, follow: false },
};

export default async function AnalyticsPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let domainCount = 0;
  let linkCount = 0;

  try {
    const [domainsRes, links] = await Promise.all([
      client.listDomains(),
      client.listLinks(),
    ]);
    domainCount = domainsRes.total;
    linkCount = links.length;
  } catch {
    // API not available
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>

      {/* Key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Total Domains</p>
          <p className="text-2xl font-bold">{domainCount}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Total Links</p>
          <p className="text-2xl font-bold">{linkCount}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Link Survival Rate</p>
          <p className="text-2xl font-bold">-</p>
        </div>
      </div>

      {/* Chart placeholders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          "DR Trend",
          "Links Over Time",
          "Credit Flow",
          "Match Quality Distribution",
        ].map((title) => (
          <div
            key={title}
            className="rounded-xl border border-neutral-800 p-6"
          >
            <h3 className="text-sm font-medium text-neutral-400 mb-4">
              {title}
            </h3>
            <div className="flex items-center justify-center h-40 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
              Chart coming soon
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
