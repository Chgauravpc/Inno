"use client";

import { useState } from "react";
import clsx from "clsx";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, Disclaimer, ErrorBox, PageSkeleton } from "@/components/ui";
import { useApi } from "@/lib/api";
import { pct, TYPE_LABEL } from "@/lib/format";
import { useSettings } from "@/lib/settings";

type Bench = {
  months: number;
  live: boolean;
  sources: Record<string, string>;
  labels: Record<string, string>;
  series: Record<string, number>[];
  summary: { key: string; label: string; pre_tax: number; real: number; real_5y_cagr: number }[];
  holdings: { symbol: string; name: string; type: string; app_return: number; real_cagr: number; benchmark: number; delta: number }[];
};

const COLORS: Record<string, string> = { nifty50: "#4f46e5", reit_invit_index: "#0b9f84", gsec_index: "#d97706" };

export default function Benchmarks() {
  const { slab, inflation } = useSettings();
  const [months, setMonths] = useState(36);
  const [mode, setMode] = useState<"pre" | "real">("real");
  const { data, error } = useApi<Bench>("/benchmarks", { slab, inflation, months });
  if (error && !data) return <ErrorBox message={error} />;
  if (!data) return <PageSkeleton />;

  const keys = Object.keys(data.labels);
  const maxAbs = Math.max(...data.holdings.map((h) => Math.abs(h.delta)), 1);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Benchmark check</h1>
        <p className="mt-1 text-sm text-muted">
          See which market index actually rewarded a {slab}% taxpayer. Switch to real value to include tax and inflation.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {data.summary.map((s) => (
          <div key={s.key} className="card p-4">
            <p className="flex items-center gap-2 text-sm text-muted">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[s.key] }} aria-hidden />
              {s.label}, {data.months} months
            </p>
            <p className="num mt-2 text-2xl font-semibold">{pct(mode === "pre" ? s.pre_tax : s.real)}</p>
            <p className="mt-1 text-xs text-muted">
              {mode === "pre" ? `After tax and inflation: ${pct(s.real)}` : `Before tax and inflation: ${pct(s.pre_tax)}`}
            </p>
          </div>
        ))}
      </div>

      <Card
        title={mode === "real" ? "Growth of ₹100, after tax and inflation" : "Growth of ₹100, before tax"}
        subtitle={data.live ? "Real market history from Yahoo Finance, with dividends and rent added back" : "Simulated index paths calibrated to long-run returns (demo)"}
        action={
          <div className="flex flex-wrap gap-2">
            <div className="flex rounded-lg bg-surface-2 p-0.5 text-xs" role="tablist" aria-label="Basis">
              {(["real", "pre"] as const).map((m) => (
                <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)} className={clsx("rounded-md px-2.5 py-1 font-medium", mode === m ? "bg-surface shadow-sm" : "text-muted")}>
                  {m === "real" ? "Real value" : "Pre-tax"}
                </button>
              ))}
            </div>
            <div className="flex rounded-lg bg-surface-2 p-0.5 text-xs" role="tablist" aria-label="Period">
              {[12, 24, 36, 60].map((m) => (
                <button key={m} role="tab" aria-selected={months === m} onClick={() => setMonths(m)} className={clsx("num rounded-md px-2.5 py-1 font-medium", months === m ? "bg-surface shadow-sm" : "text-muted")}>
                  {m / 12}Y
                </button>
              ))}
            </div>
          </div>
        }
      >
        <div className="h-72 md:h-96" role="img" aria-label="Line chart comparing index growth">
          <ResponsiveContainer>
            <LineChart data={data.series} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="m" tickFormatter={(m) => (m === 0 ? "Now" : `${-m}m ago`)} interval="preserveStartEnd" minTickGap={40} stroke="var(--line)" />
              <YAxis domain={["auto", "auto"]} tickFormatter={(v) => `${Math.round(v)}`} width={44} stroke="var(--line)" />
              <Tooltip
                labelFormatter={(m) => (Number(m) === 0 ? "Now" : `${-Number(m)} months ago`)}
                formatter={(v, n) => [Number(v).toFixed(1), String(n)]}
                contentStyle={{ borderRadius: 10, border: "1px solid var(--line)", background: "var(--surface)" }}
              />
              <Legend verticalAlign="bottom" height={28} />
              {keys.map((k) => (
                <Line isAnimationActive={false} key={k} type="monotone" dataKey={`${k}_${mode}`} name={data.labels[k]} stroke={COLORS[k]} strokeWidth={2.2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <ul className="space-y-1 text-xs text-muted" aria-label="Data sources">
        {keys.map((k) => (
          <li key={k} className="flex items-start gap-2">
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full" style={{ background: COLORS[k] }} aria-hidden />
            <span><span className="font-medium text-ink">{data.labels[k]}:</span> {data.sources[k]}</span>
          </li>
        ))}
      </ul>

      <Card title="Each holding vs its index" subtitle="Real, after-tax return per year including income, against the matching index over the same holding period">
        <ul className="divide-y divide-line/70">
          {data.holdings.map((h) => (
            <li key={h.symbol} className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-2 py-3 md:grid-cols-[220px_1fr_auto]">
              <div>
                <p className="text-sm font-medium">{h.name}</p>
                <p className="text-xs text-muted">{TYPE_LABEL[h.type]}</p>
              </div>
              <div className="order-3 col-span-2 md:order-none md:col-span-1">
                <div className="relative h-2.5 rounded-full bg-surface-2" aria-hidden>
                  <div className="absolute inset-y-0 left-1/2 w-px bg-line" />
                  <div
                    className={clsx("absolute inset-y-0 rounded-full", h.delta >= 0 ? "bg-brand" : "bg-amber")}
                    style={{ width: `${(Math.abs(h.delta) / maxAbs) * 50}%`, [h.delta >= 0 ? "left" : "right"]: "50%" } as React.CSSProperties}
                  />
                </div>
              </div>
              <div className="text-right">
                <p className={clsx("num text-sm font-semibold", h.delta >= 0 ? "text-pos" : "text-neg")}>{pct(h.delta)} vs index</p>
                <p className="num text-xs text-muted">
                  you {pct(h.real_cagr)} · index {pct(h.benchmark)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Card>
      <Disclaimer />
    </div>
  );
}
