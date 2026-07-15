"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { WeaveClient, Link } from "@/lib/api-client";
import { DrBadge } from "@/components/ui/dr-badge";
import { StatusPill } from "@/components/ui/status-pill";
import { StatCard } from "@/components/ui/stat-card";

interface DashboardContentProps {
  token: string;
  initialDomainCount: number;
  initialLinkCount: number;
  initialCreditBalance: number;
}

export function DashboardContent({
  token,
  initialDomainCount,
  initialLinkCount,
  initialCreditBalance,
}: DashboardContentProps) {
  const [domains, setDomains] = useState<Array<{ id: string; domain: string; dr: number }>>([]);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const [recentLinks, setRecentLinks] = useState<Link[]>([]);
  const [drHistory, setDrHistory] = useState<Array<{ recorded_at: string; dr: number | null }>>([]);
  const [linkCount, setLinkCount] = useState(initialLinkCount);
  const [creditBalance, setCreditBalance] = useState(initialCreditBalance);

  const client = WeaveClient.authenticated(token);

  useEffect(() => {
    client.listDomains().then((res) => {
      setDomains(res.domains);
      if (res.domains.length > 0) {
        setSelectedDomainId(res.domains[0].id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedDomainId) return;
    Promise.all([
      client.listLinks(),
      client.getMetrics(selectedDomainId),
      client.getBalance(selectedDomainId),
    ]).then(([links, metrics, balance]) => {
      setRecentLinks(links.slice(0, 5));
      setLinkCount(links.length);
      setDrHistory(metrics.history.map((h) => ({ recorded_at: h.recorded_at, dr: h.dr })));
      setCreditBalance(balance.balance);
    }).catch(() => {});
  }, [selectedDomainId]);

  const firstDr = drHistory.length > 0 ? drHistory[0].dr : null;
  const latestDr = drHistory.length > 0 ? drHistory[drHistory.length - 1].dr : null;
  const drTrend = firstDr != null && latestDr != null ? latestDr - firstDr : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        {domains.length > 1 && (
          <select
            value={selectedDomainId || ""}
            onChange={(e) => setSelectedDomainId(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-sm text-white"
          >
            {domains.map((d) => (
              <option key={d.id} value={d.id}>{d.domain}</option>
            ))}
          </select>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          label="Domain Rating"
          value={latestDr ?? "—"}
          trend={drTrend !== 0 ? `${drTrend > 0 ? "+" : ""}${drTrend} since tracking` : undefined}
          trendPositive={drTrend > 0}
        />
        <StatCard label="Backlinks" value={linkCount} />
        <StatCard label="Credits" value={creditBalance.toFixed(0)} />
      </div>

      <div className="rounded-xl border border-neutral-800 p-6 mb-8">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">DR History</h3>
        {drHistory.length < 2 ? (
          <div className="flex items-center justify-center h-40 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
            Not enough data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={drHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis
                dataKey="recorded_at"
                tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                stroke="#525252"
                fontSize={11}
              />
              <YAxis stroke="#525252" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #262626", borderRadius: "8px" }} />
              <Line type="monotone" dataKey="dr" name="DR" stroke="#ffffff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Recent Backlinks</h2>
        <div className="rounded-xl border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-400 text-left">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Target</th>
                <th className="px-4 py-3 font-medium">Anchor</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentLinks.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-neutral-500">
                    No links yet. Add a domain and start discovering link opportunities.
                  </td>
                </tr>
              ) : (
                recentLinks.map((link) => (
                  <tr key={link.id} className="border-b border-neutral-800 hover:bg-neutral-900">
                    <td className="px-4 py-3 text-neutral-400">
                      {new Date(link.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 truncate max-w-[200px]">{link.source_url}</td>
                    <td className="px-4 py-3 truncate max-w-[200px]">{link.target_url}</td>
                    <td className="px-4 py-3">{link.anchor_text}</td>
                    <td className="px-4 py-3"><StatusPill status={link.status} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-3">
          <a
            href="/dashboard/domains/add"
            className="rounded-lg bg-white text-black px-4 py-2 text-sm font-medium hover:bg-neutral-200"
          >
            Add Domain
          </a>
          <a
            href="/dashboard/links"
            className="rounded-lg border border-neutral-700 px-4 py-2 text-sm font-medium hover:bg-neutral-800"
          >
            Discover Links
          </a>
        </div>
      </div>
    </div>
  );
}
