import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient, CreditTransaction } from "@/lib/api-client";
import { ExportButton } from "@/components/dashboard/export-button";

export const metadata: Metadata = {
  title: "Credits",
  description: "View your credit balance, transaction history, and earnings.",
  robots: { index: false, follow: false },
};

const typeColors: Record<string, string> = {
  earned: "bg-green-900 text-green-300",
  spent: "bg-red-900 text-red-300",
  reversed: "bg-orange-900 text-orange-300",
  bonus: "bg-blue-900 text-blue-300",
  expired: "bg-neutral-700 text-neutral-300",
};

export default async function CreditsPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let balance = 0;
  let lifetimeEarned = 0;
  let lifetimeSpent = 0;
  let transactions: CreditTransaction[] = [];
  let totalTransactions = 0;
  let plan = "free";

  try {
    const [domainsRes, me] = await Promise.all([
      client.listDomains(),
      client.getMe(),
    ]);
    plan = me.plan || "free";
    if (domainsRes.domains.length > 0) {
      const firstDomain = domainsRes.domains[0];
      const [bal, history] = await Promise.all([
        client.getBalance(firstDomain.id),
        client.getCreditHistory(firstDomain.id),
      ]);
      balance = bal.balance;
      lifetimeEarned = bal.lifetime_earned;
      lifetimeSpent = bal.lifetime_spent;
      transactions = history.transactions;
      totalTransactions = history.total;
    }
  } catch {
    // API not available
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Credits</h1>
        <ExportButton endpoint="/api/v1/credits/export" label="Export CSV" token={token} plan={plan} />
      </div>

      {/* Balance card */}
      <div className="rounded-xl border border-neutral-800 p-6 mb-6">
        <p className="text-sm text-neutral-400 mb-1">Current Balance</p>
        <p className="text-4xl font-bold">
          {balance.toFixed(2)} <span className="text-lg text-neutral-400">credits</span>
        </p>
      </div>

      {/* Lifetime stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Lifetime Earned</p>
          <p className="text-xl font-bold text-green-400">{lifetimeEarned.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Lifetime Spent</p>
          <p className="text-xl font-bold text-red-400">{lifetimeSpent.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-4">
          <p className="text-sm text-neutral-400 mb-1">Net</p>
          <p className="text-xl font-bold">{(lifetimeEarned - lifetimeSpent).toFixed(2)}</p>
        </div>
      </div>

      {/* Transaction history */}
      <h2 className="text-lg font-semibold mb-4">Transaction History</h2>
      <div className="rounded-xl border border-neutral-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-400 text-left">
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Description</th>
              <th className="px-4 py-3 font-medium">Link ID</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No transactions yet.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr
                  key={tx.id}
                  className="border-b border-neutral-800 hover:bg-neutral-900"
                >
                  <td className="px-4 py-3 text-neutral-400">
                    {new Date(tx.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[tx.type]}`}
                    >
                      {tx.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium">
                    {tx.amount > 0 ? "+" : ""}
                    {tx.amount.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-neutral-400">
                    {tx.description}
                  </td>
                  <td className="px-4 py-3 text-neutral-500 font-mono text-xs">
                    {tx.link_id || "-"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 text-sm text-neutral-400">
        <p>Showing {transactions.length} of {totalTransactions} transactions</p>
        <div className="flex gap-2">
          <button
            disabled
            className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs disabled:opacity-50"
          >
            Previous
          </button>
          <button
            disabled
            className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
