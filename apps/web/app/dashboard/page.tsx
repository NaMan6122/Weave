import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";
import { DashboardContent } from "./dashboard-content";

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

  try {
    const [domainsRes, links] = await Promise.all([
      client.listDomains(),
      client.listLinks(),
    ]);
    domainCount = domainsRes.total;
    linkCount = links.length;

    const balances = await Promise.all(
      domainsRes.domains.map((d) => client.getBalance(d.id).catch(() => null)),
    );
    creditBalance = balances.reduce((sum, b) => sum + (b?.balance ?? 0), 0);
  } catch {
    // API not available
  }

  return (
    <DashboardContent
      token={token}
      initialDomainCount={domainCount}
      initialLinkCount={linkCount}
      initialCreditBalance={creditBalance}
    />
  );
}
