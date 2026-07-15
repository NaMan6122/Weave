import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";
import { SettingsContent } from "./settings-content";

export const metadata: Metadata = {
  title: "Settings",
  description: "Manage your account profile and preferences.",
  robots: { index: false, follow: false },
};

export default async function SettingsPage() {
  const token = await getBackendToken();
  if (!token) return <div>Not authenticated</div>;
  const client = WeaveClient.authenticated(token);

  let email = "";
  let name = "";
  let plan = "free";

  try {
    const me = await client.getMe();
    email = me.email;
    name = me.name || "";
    plan = me.plan || "free";
  } catch {
    // API not available
  }

  return <SettingsContent email={email} name={name} plan={plan} token={token} />;
}
