import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { AnalyticsContent } from "./analytics-content";

export const metadata: Metadata = {
  title: "Analytics",
  description: "Track domain authority trends, link growth, and WTS scores over time.",
  robots: { index: false, follow: false },
};

export default async function AnalyticsPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;

  return <AnalyticsContent token={token} />;
}
