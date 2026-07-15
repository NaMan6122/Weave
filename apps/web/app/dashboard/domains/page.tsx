import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient, Domain } from "@/lib/api-client";
import { ExportButton } from "@/components/dashboard/export-button";

export const metadata: Metadata = {
  title: "Domains",
  description: "Manage your registered domains and view vetting status.",
  robots: { index: false, follow: false },
};

const statusColors: Record<string, string> = {
  active: "bg-green-900 text-green-300",
  pending: "bg-yellow-900 text-yellow-300",
  rejected: "bg-red-900 text-red-300",
  suspended: "bg-red-900 text-red-300",
};

export default async function DomainsPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let domains: Domain[] = [];
  let plan = "free";
  try {
    const [res, me] = await Promise.all([
      client.listDomains(),
      client.getMe(),
    ]);
    domains = res.domains;
    plan = me.plan || "free";
  } catch {
    // API not available
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Domains</h1>
        <div className="flex items-center gap-2">
          <ExportButton endpoint="/api/v1/domains/export" label="Export CSV" token={token} plan={plan} />
          <a
          href="/dashboard/domains/add"
          className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200"
        >
          Add Domain
        </a>
        </div>
      </div>

      <div className="rounded-xl border border-neutral-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-400 text-left">
              <th className="px-4 py-3 font-medium">Domain</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">WTS</th>
              <th className="px-4 py-3 font-medium">DR</th>
              <th className="px-4 py-3 font-medium">Niche</th>
              <th className="px-4 py-3 font-medium">Verified</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {domains.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No domains yet. Add your first domain to get started.
                </td>
              </tr>
            ) : (
              domains.map((d) => (
                <tr
                  key={d.id}
                  className="border-b border-neutral-800 hover:bg-neutral-900"
                >
                  <td className="px-4 py-3 font-medium">{d.domain}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[d.status]}`}
                    >
                      {d.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{d.wts}</td>
                  <td className="px-4 py-3">{d.dr}</td>
                  <td className="px-4 py-3 text-neutral-400">{d.niche}</td>
                  <td className="px-4 py-3">
                    {d.verified ? (
                      <span className="text-green-400">&#10003;</span>
                    ) : (
                      <span className="text-red-400">&#10007;</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <a
                        href={`/dashboard/domains/${d.id}`}
                        className="text-xs border border-neutral-700 rounded px-2 py-1 hover:bg-neutral-800"
                      >
                        View
                      </a>
                    </div>
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
