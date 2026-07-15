"use client";

import { Suspense } from "react";
import { useSession, signOut } from "next-auth/react";
import { NotificationBell } from "@/components/dashboard/notification-bell";
import { DomainProvider } from "@/lib/domain-context";
import { DomainSwitcher } from "@/components/dashboard/domain-switcher";

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

function SidebarContent({ token }: { token: string }) {
  return (
    <DomainProvider token={token}>
      <DomainSwitcher />
      <div className="border-t border-neutral-800 my-2" />
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
    </DomainProvider>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session } = useSession();

  return (
    <div className="flex min-h-screen bg-neutral-950 text-white">
      <aside className="w-64 border-r border-neutral-800 p-6 flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Weave</h2>
          {session?.backendToken && (
            <NotificationBell token={session.backendToken} />
          )}
        </div>
        {session?.backendToken ? (
          <Suspense fallback={<div className="h-8 rounded-lg bg-neutral-900 animate-pulse mb-4" />}>
            <SidebarContent token={session.backendToken} />
          </Suspense>
        ) : (
          <nav className="flex flex-col gap-2 text-sm flex-1">
            <a href="/dashboard" className="px-3 py-2 rounded-md hover:bg-neutral-800">Overview</a>
            <a href="/dashboard/domains" className="px-3 py-2 rounded-md hover:bg-neutral-800">Domains</a>
            <a href="/dashboard/links" className="px-3 py-2 rounded-md hover:bg-neutral-800">Links</a>
            <a href="/dashboard/network" className="px-3 py-2 rounded-md hover:bg-neutral-800">Network</a>
            <a href="/dashboard/credits" className="px-3 py-2 rounded-md hover:bg-neutral-800">Credits</a>
            <a href="/dashboard/analytics" className="px-3 py-2 rounded-md hover:bg-neutral-800">Analytics</a>
            <a href="/dashboard/settings" className="px-3 py-2 rounded-md hover:bg-neutral-800">Settings</a>
            <a href="/dashboard/api-keys" className="px-3 py-2 rounded-md hover:bg-neutral-800">API Keys</a>
          </nav>
        )}
        <UserSection />
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
