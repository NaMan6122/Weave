import type { Metadata } from "next";
import { getBackendToken } from "@/lib/auth";
import { WeaveClient } from "@/lib/api-client";

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

  try {
    const me = await client.getMe();
    email = me.email;
    name = me.name;
  } catch {
    // API not available
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Profile */}
      <div className="rounded-xl border border-neutral-800 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-400 mb-1">
              Email
            </label>
            <input
              type="email"
              readOnly
              value={email}
              className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-400 mb-1">
              Name
            </label>
            <input
              type="text"
              readOnly
              defaultValue={name}
              placeholder="Your name"
              className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-400 mb-1">
              Plan
            </label>
            <span className="inline-block rounded-full bg-neutral-800 px-3 py-1 text-xs font-medium">
              Free
            </span>
          </div>
        </div>
      </div>

      {/* Danger zone */}
      <div className="rounded-xl border border-red-900/50 p-6">
        <h2 className="text-lg font-semibold text-red-400 mb-2">
          Danger Zone
        </h2>
        <p className="text-sm text-neutral-400 mb-4">
          Once you delete your account, there is no going back.
        </p>
        <button
          disabled
          className="rounded-lg bg-red-900/30 border border-red-800 text-red-400 px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
        >
          Delete Account
        </button>
        <p className="text-xs text-neutral-500 mt-2">
          Contact support to delete your account.
        </p>
      </div>
    </div>
  );
}
