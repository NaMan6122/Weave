"use client";

import { useState, useEffect } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { WeaveClient } from "@/lib/api-client";

interface MetricsPoint {
  recorded_at: string;
  dr: number | null;
  da: number | null;
  wts: number | null;
  organic_traffic: number | null;
}

interface LinkPoint {
  date: string;
  new_that_week: number;
  cumulative: number;
}

interface CreditPoint {
  week: string;
  earned: number;
  spent: number;
}

export function AnalyticsContent({ token }: { token: string }) {
  const [domains, setDomains] = useState<Array<{ id: string; domain: string }>>([]);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricsPoint[]>([]);
  const [linkSeries, setLinkSeries] = useState<LinkPoint[]>([]);
  const [creditSeries, setCreditSeries] = useState<CreditPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const client = WeaveClient.authenticated(token);

  useEffect(() => {
    client.listDomains().then((res) => {
      setDomains(res.domains);
      if (res.domains.length > 0) {
        setSelectedDomainId(res.domains[0].id);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedDomainId) return;
    Promise.all([
      client.getMetrics(selectedDomainId),
      client.getLinkSeries(selectedDomainId),
      client.getCreditSeries(selectedDomainId),
    ]).then(([m, l, c]) => {
      setMetrics(m.history);
      setLinkSeries(l.series);
      setCreditSeries(c.series);
    }).catch(() => {});
  }, [selectedDomainId]);

  const latestMetrics = metrics.length > 0 ? metrics[metrics.length - 1] : null;
  const firstMetrics = metrics.length > 1 ? metrics[0] : null;

  function trend(current: number | null, first: number | null): string {
    if (current == null || first == null) return "—";
    const diff = current - first;
    return diff > 0 ? `+${diff}` : `${diff}`;
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Analytics</h1>
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl border border-neutral-800 animate-pulse bg-neutral-900" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Domain Rating</p>
          <p className="text-3xl font-bold">{latestMetrics?.dr ?? "—"}</p>
          <p className="text-xs text-neutral-500 mt-1">{trend(latestMetrics?.dr ?? null, firstMetrics?.dr ?? null)} since tracking</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Total Links</p>
          <p className="text-3xl font-bold">{linkSeries.length > 0 ? linkSeries[linkSeries.length - 1].cumulative : 0}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 p-6">
          <p className="text-sm text-neutral-400 mb-1">Organic Traffic</p>
          <p className="text-3xl font-bold">
            {latestMetrics?.organic_traffic
              ? latestMetrics.organic_traffic >= 1000
                ? `${(latestMetrics.organic_traffic / 1000).toFixed(1)}k`
                : latestMetrics.organic_traffic
              : "—"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-neutral-800 p-6">
          <h3 className="text-sm font-medium text-neutral-400 mb-4">DR / DA Trend</h3>
          {metrics.length < 2 ? (
            <div className="flex items-center justify-center h-48 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
              Not enough data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="recorded_at" tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })} stroke="#525252" fontSize={11} />
                <YAxis stroke="#525252" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #262626", borderRadius: "8px" }} />
                <Legend />
                <Line type="monotone" dataKey="dr" name="DR" stroke="#ffffff" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="da" name="DA" stroke="#a3a3a3" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="wts" name="WTS" stroke="#60a5fa" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-neutral-800 p-6">
          <h3 className="text-sm font-medium text-neutral-400 mb-4">Links Over Time</h3>
          {linkSeries.length < 1 ? (
            <div className="flex items-center justify-center h-48 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
              Not enough data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={linkSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="date" tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })} stroke="#525252" fontSize={11} />
                <YAxis stroke="#525252" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #262626", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="cumulative" name="Cumulative" stroke="#4ade80" fill="#4ade80" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-neutral-800 p-6">
          <h3 className="text-sm font-medium text-neutral-400 mb-4">Credit Flow</h3>
          {creditSeries.length < 1 ? (
            <div className="flex items-center justify-center h-48 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
              Not enough data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={creditSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="week" tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })} stroke="#525252" fontSize={11} />
                <YAxis stroke="#525252" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #262626", borderRadius: "8px" }} />
                <Legend />
                <Bar dataKey="earned" name="Earned" fill="#4ade80" radius={[2, 2, 0, 0]} />
                <Bar dataKey="spent" name="Spent" fill="#f87171" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-neutral-800 p-6">
          <h3 className="text-sm font-medium text-neutral-400 mb-4">Organic Traffic</h3>
          {metrics.length < 2 ? (
            <div className="flex items-center justify-center h-48 rounded-lg bg-neutral-900 text-neutral-500 text-sm">
              Not enough data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="recorded_at" tickFormatter={(v) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })} stroke="#525252" fontSize={11} />
                <YAxis stroke="#525252" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#171717", border: "1px solid #262626", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="organic_traffic" name="Traffic" stroke="#60a5fa" fill="#60a5fa" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
