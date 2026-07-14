import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Overview of your domains, credits, and recent backlinks.",
  robots: { index: false, follow: false },
};

export default async function DashboardPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let domainCount = 0;
  let linkCount = 0;
  let creditBalance = 0;
  let recentLinks: Awaited<ReturnType<typeof client.listLinks>> = [];

  try {
    const [domainsRes, links] = await Promise.all([
      client.listDomains(),
      client.listLinks(),
    ]);
    domainCount = domainsRes.total;
    recentLinks = links.slice(0, 5);
    linkCount = links.length;

    // Sum credit balances across all domains
    const balances = await Promise.all(
      domainsRes.domains.map((d) => client.getBalance(d.id).catch(() => null)),
    );
    creditBalance = balances.reduce(
      (sum, b) => sum + (b?.balance ?? 0),
      0,
    );
  } catch {
    // API not available — show zeros
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Credit Balance</p>
          <p className="text-3xl font-bold">{creditBalance.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Active Links</p>
          <p className="text-3xl font-bold">{linkCount}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Domains</p>
          <p className="text-3xl font-bold">{domainCount}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-3">
          <a
            href="/dashboard/domains/add"
            className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200"
          >
            Add Domain
          </a>
          <a
            href="/dashboard/links"
            className="rounded-lg border border-neutral-700 px-4 py-2 text-sm font-medium hover:bg-neutral-800"
          >
            Discover Links
          </a>
        </div>
      </div>

      {/* Recent Links */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Recent Links</h2>
        <div className="rounded-xl border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-400 text-left">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Target</th>
                <th className="px-4 py-3 font-medium">Anchor Text</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentLinks.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-neutral-500"
                  >
                    No links yet. Add a domain and start discovering link
                    opportunities.
                  </td>
                </tr>
              ) : (
                recentLinks.map((link) => (
                  <tr
                    key={link.id}
                    className="border-b border-neutral-800 hover:bg-neutral-900"
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
                    <td className="px-4 py-3">{link.match_score}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block rounded-full px-2 py-0.5 text-xs font-medium bg-neutral-700 text-neutral-300">
                        {link.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
