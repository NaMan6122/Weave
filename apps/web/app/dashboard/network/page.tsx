import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient, NetworkSite } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Network",
  description: "Browse the Weave network of verified domains and discover potential link partners.",
  robots: { index: false, follow: false },
};

export default async function NetworkPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let sites: NetworkSite[] = [];
  let total = 0;

  try {
    const res = await client.browseNetwork({ page_size: 50 });
    sites = res.sites;
    total = res.total;
  } catch {
    // API not available
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Network</h1>
      <p className="text-neutral-400 mb-6">
        {total} verified sites in the network
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sites.length === 0 ? (
          <p className="text-neutral-500 col-span-full text-center py-12">
            No sites in the network yet.
          </p>
        ) : (
          sites.map((site, i) => (
            <div
              key={i}
              className="rounded-xl border border-neutral-800 p-5 hover:border-neutral-600 transition"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-sm text-neutral-300">
                  {site.domain}
                </span>
                <span className="text-xs bg-neutral-800 rounded-full px-2 py-0.5 text-neutral-400">
                  {site.language}
                </span>
              </div>

              {site.niche && (
                <span className="inline-block text-xs bg-blue-900/50 text-blue-300 rounded-full px-2 py-0.5 mb-3">
                  {site.niche}
                </span>
              )}

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <p className="text-neutral-500">DR</p>
                  <p className="font-semibold">{site.dr}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Traffic</p>
                  <p className="font-semibold">
                    {site.monthly_traffic >= 1000
                      ? `${(site.monthly_traffic / 1000).toFixed(1)}k`
                      : site.monthly_traffic}
                  </p>
                </div>
                <div>
                  <p className="text-neutral-500">Age</p>
                  <p className="font-semibold">{site.domain_age_months}mo</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
