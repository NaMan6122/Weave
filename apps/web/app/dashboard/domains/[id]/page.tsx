import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";
import { VerifyButtons } from "./verify-buttons";

export const metadata: Metadata = {
  title: "Domain Details",
  description: "View domain verification status, WTS score, and metrics.",
  robots: { index: false, follow: false },
};

const statusColors: Record<string, string> = {
  active: "bg-green-900 text-green-300",
  pending: "bg-yellow-900 text-yellow-300",
  rejected: "bg-red-900 text-red-300",
  suspended: "bg-red-900 text-red-300",
};

export default async function DomainDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let domain;
  let balance = 0;
  try {
    domain = await client.getDomain(id);
  } catch {
    return (
      <div className="text-center py-12 text-neutral-500">
        Domain not found or failed to load.
      </div>
    );
  }

  try {
    const bal = await client.getBalance(id);
    balance = bal.balance;
  } catch {
    // no balance data
  }

  const verificationToken = domain.verification_token;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold">{domain.domain}</h1>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[domain.status]}`}
        >
          {domain.status}
        </span>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {[
          { label: "WTS", value: domain.wts },
          { label: "DR", value: domain.dr },
          { label: "DA", value: domain.da },
          { label: "Spam Score", value: domain.spam_score },
          { label: "Domain Age", value: `${domain.domain_age} yrs` },
          {
            label: "Organic Traffic",
            value: domain.organic_traffic.toLocaleString(),
          },
        ].map((m) => (
          <div
            key={m.label}
            className="rounded-xl border border-neutral-800 p-4"
          >
            <p className="text-sm text-neutral-400 mb-1">{m.label}</p>
            <p className="text-2xl font-bold">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Verification section */}
      {!domain.verified && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Verify Ownership</h2>
          <div className="space-y-4">
            <div className="rounded-xl border border-neutral-800 p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">DNS Verification</h3>
                <VerifyButtons domainId={id} method="dns" />
              </div>
              <p className="text-sm text-neutral-400">
                Add TXT record{" "}
                <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-xs">
                  weave-verify={verificationToken}
                </code>{" "}
                to{" "}
                <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-xs">
                  _weave.{domain.domain}
                </code>
              </p>
            </div>

            <div className="rounded-xl border border-neutral-800 p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">Meta Tag Verification</h3>
                <VerifyButtons domainId={id} method="meta" />
              </div>
              <p className="text-sm text-neutral-400">
                Add{" "}
                <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-xs">
                  {`<meta name="weave-verify" content="${verificationToken}">`}
                </code>{" "}
                to your homepage
              </p>
            </div>

            <div className="rounded-xl border border-neutral-800 p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">File Verification</h3>
                <VerifyButtons domainId={id} method="file" />
              </div>
              <p className="text-sm text-neutral-400">
                Create{" "}
                <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-xs">
                  /.well-known/weave-verify.txt
                </code>{" "}
                with content{" "}
                <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-xs">
                  {verificationToken}
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Credit balance */}
      <div className="mb-8">
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Credit Balance</p>
          <p className="text-3xl font-bold">{balance.toFixed(2)}</p>
        </div>
      </div>

      {/* Recent links */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Recent Links</h2>
        <div className="rounded-xl border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-400 text-left">
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Target</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No links yet for this domain.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
