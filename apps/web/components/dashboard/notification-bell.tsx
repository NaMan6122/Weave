"use client";

import { useState, useEffect, useRef } from "react";
import { WeaveClient, Notification } from "@/lib/api-client";

const typeIcons: Record<string, string> = {
  link_removed: "⚠",
  link_placed: "🔗",
  credits_low: "💰",
  domain_vetted: "✓",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function NotificationBell({ token }: { token: string }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const client = WeaveClient.authenticated(token);

  async function fetchNotifications() {
    if (document.visibilityState === "hidden") return;
    try {
      const res = await client.getNotifications();
      setNotifications(res.notifications);
      setUnreadCount(res.unread_count);
    } catch {
      // silent
    }
  }

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleMarkRead(id: string) {
    try {
      await client.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // silent
    }
  }

  async function handleMarkAllRead() {
    try {
      await client.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {
      // silent
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-md hover:bg-neutral-800 transition"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-neutral-800 bg-neutral-950 shadow-xl z-50">
          <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-neutral-400 hover:text-white"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-neutral-500">
                No notifications
              </p>
            ) : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  onClick={() => !n.read && handleMarkRead(n.id)}
                  className={`w-full text-left px-4 py-3 border-b border-neutral-800/50 hover:bg-neutral-900 transition ${
                    !n.read ? "bg-neutral-900/50" : ""
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 text-sm">
                      {typeIcons[n.type] || "•"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${!n.read ? "text-white font-medium" : "text-neutral-400"}`}>
                        {n.title}
                      </p>
                      <p className="text-xs text-neutral-500 truncate">
                        {n.message}
                      </p>
                      <p className="text-xs text-neutral-600 mt-1">
                        {timeAgo(n.created_at)}
                      </p>
                    </div>
                    {!n.read && (
                      <span className="mt-1.5 h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
