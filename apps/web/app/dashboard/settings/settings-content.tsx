"use client";

import { useState } from "react";
import { signOut } from "next-auth/react";
import { WeaveClient } from "@/lib/api-client";

interface SettingsContentProps {
  email: string;
  name: string;
  plan: string;
  token: string;
}

export function SettingsContent({ email, name, plan, token }: SettingsContentProps) {
  const [editName, setEditName] = useState(name || "");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const [deleteEmail, setDeleteEmail] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  const client = WeaveClient.authenticated(token);

  async function handleSave() {
    if (!editName.trim()) return;
    setSaving(true);
    setSaveMsg("");
    try {
      await client.updateProfile(editName.trim());
      setSaveMsg("Profile updated");
      setTimeout(() => setSaveMsg(""), 3000);
    } catch {
      setSaveMsg("Failed to update");
    }
    setSaving(false);
  }

  async function handleDelete() {
    if (deleteEmail !== email) {
      setDeleteError("Email does not match");
      return;
    }
    setDeleting(true);
    setDeleteError("");
    try {
      await client.deleteAccount(deleteEmail);
      await signOut({ callbackUrl: "/login" });
    } catch {
      setDeleteError("Failed to delete account");
      setDeleting(false);
    }
  }

  const planLabels: Record<string, string> = {
    free: "Free",
    starter: "Starter",
    pro: "Pro",
    agency: "Agency",
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

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
            <div className="flex gap-2">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Your name"
                className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
              />
              <button
                onClick={handleSave}
                disabled={saving || !editName.trim()}
                className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
            {saveMsg && (
              <p className={`text-xs mt-1 ${saveMsg === "Profile updated" ? "text-green-400" : "text-red-400"}`}>
                {saveMsg}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-400 mb-1">
              Plan
            </label>
            <div className="flex items-center gap-3">
              <span className="inline-block rounded-full bg-neutral-800 px-3 py-1 text-xs font-medium">
                {planLabels[plan] || plan}
              </span>
              {plan === "free" && (
                <a
                  href="/pricing"
                  className="text-sm text-neutral-400 hover:text-white underline"
                >
                  Upgrade
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-red-900/50 p-6">
        <h2 className="text-lg font-semibold text-red-400 mb-2">
          Danger Zone
        </h2>
        <p className="text-sm text-neutral-400 mb-4">
          Once you delete your account, there is no going back.
        </p>
        {!showDelete ? (
          <button
            onClick={() => setShowDelete(true)}
            className="rounded-lg bg-red-900/30 border border-red-800 text-red-400 px-4 py-2 text-sm font-medium hover:bg-red-900/50"
          >
            Delete Account
          </button>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-neutral-300">
              Type your email (<span className="font-mono text-neutral-400">{email}</span>) to confirm:
            </p>
            <input
              type="email"
              value={deleteEmail}
              onChange={(e) => { setDeleteEmail(e.target.value); setDeleteError(""); }}
              placeholder={email}
              className="w-full rounded-lg border border-red-800 bg-neutral-900 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-red-600"
            />
            {deleteError && (
              <p className="text-xs text-red-400">{deleteError}</p>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleDelete}
                disabled={deleting || !deleteEmail}
                className="rounded-lg bg-red-600 text-white px-4 py-2 text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? "Deleting..." : "Confirm Delete"}
              </button>
              <button
                onClick={() => { setShowDelete(false); setDeleteEmail(""); setDeleteError(""); }}
                className="rounded-lg border border-neutral-700 px-4 py-2 text-sm font-medium hover:bg-neutral-800"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
