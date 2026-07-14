"use client";

import { useSession, signOut } from "next-auth/react";

function UserSection() {
  const { data: session } = useSession();

  if (!session?.user) return null;

  return (
    <div className="border-t border-neutral-800 pt-4 mt-4">
      <div className="text-sm truncate text-neutral-300">
        {session.user.name || session.user.email}
      </div>
      {session.user.name && session.user.email && (
        <div className="text-xs text-neutral-500 truncate">
          {session.user.email}
        </div>
      )}
      <button
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="mt-3 w-full text-left text-sm text-neutral-400 hover:text-white transition px-3 py-2 rounded-md hover:bg-neutral-800"
      >
        Sign out
      </button>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-neutral-950 text-white">
      <aside className="w-64 border-r border-neutral-800 p-6 flex flex-col">
        <h2 className="text-lg font-bold mb-8">Weave</h2>
        <nav className="flex flex-col gap-2 text-sm flex-1">
          <a href="/dashboard" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Overview
          </a>
          <a href="/dashboard/domains" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Domains
          </a>
          <a href="/dashboard/links" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Links
          </a>
          <a href="/dashboard/network" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Network
          </a>
          <a href="/dashboard/credits" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Credits
          </a>
          <a href="/dashboard/analytics" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Analytics
          </a>
          <a href="/dashboard/settings" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            Settings
          </a>
          <a href="/dashboard/api-keys" className="px-3 py-2 rounded-md hover:bg-neutral-800">
            API Keys
          </a>
        </nav>
        <UserSection />
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
