import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient, Link } from "@/lib/api-client";
import { StatusPill } from "@/components/ui/status-pill";
import { ExportButton } from "@/components/dashboard/export-button";

export const metadata: Metadata = {
  title: "Links",
  description: "Track all your placed and received backlinks with live status monitoring.",
  robots: { index: false, follow: false },
};

const tabs = ["all", "live", "pending", "removed", "broken"] as const;
const tabLabels: Record<string, string> = {
  all: "All",
  live: "Live",
  pending: "Pending",
  removed: "Removed",
  broken: "Broken",
};

const statusColors: Record<string, string> = {
  live: "bg-green-900 text-green-300",
  pending: "bg-yellow-900 text-yellow-300",
  removed: "bg-neutral-700 text-neutral-300",
  broken: "bg-red-900 text-red-300",
};

function scoreColor(score: number): string {
  if (score > 70) return "bg-green-900 text-green-300";
  if (score > 40) return "bg-yellow-900 text-yellow-300";
  return "bg-red-900 text-red-300";
}

export default async function LinksPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status: filterStatus } = await searchParams;
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  const activeTab = filterStatus || "all";
  let links: Link[] = [];
  let plan = "free";

  try {
    const [linksData, me] = await Promise.all([
      client.listLinks(activeTab === "all" ? undefined : activeTab),
      client.getMe(),
    ]);
    links = linksData;
    plan = me.plan || "free";
  } catch {
    // API not available
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Links</h1>
        <ExportButton endpoint="/api/v1/links/export" label="Export CSV" token={token} plan={plan} />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-6 border-b border-neutral-800">
        {tabs.map((tab) => (
          <a
            key={tab}
            href={tab === "all" ? "/dashboard/links" : `/dashboard/links?status=${tab}`}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              tab === activeTab
                ? "border-white text-white"
                : "border-transparent text-neutral-400 hover:text-white"
            }`}
          >
            {tabLabels[tab]}
          </a>
        ))}
      </div>

      <div className="rounded-xl border border-neutral-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-400 text-left">
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Source URL</th>
              <th className="px-4 py-3 font-medium">Target URL</th>
              <th className="px-4 py-3 font-medium">Anchor Text</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Credits</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {links.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No links found.
                </td>
              </tr>
            ) : (
              links.map((link) => (
                <tr
                  key={link.id}
                  className="border-b border-neutral-800 hover:bg-neutral-900 cursor-pointer"
                >
                  <td className="px-4 py-3 text-neutral-400">
                    {new Date(link.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 truncate max-w-[200px]">
                    {link.source_url}
                  </td>
                  <td className="px-4 py-3 truncate max-w-[200px]">
                    {link.target_url}
                  </td>
                  <td className="px-4 py-3">{link.anchor_text}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${scoreColor(link.match_score)}`}
                    >
                      {link.match_score}
                    </span>
                  </td>
                  <td className="px-4 py-3">{link.credits}</td>
                  <td className="px-4 py-3">
                    <StatusPill status={link.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
