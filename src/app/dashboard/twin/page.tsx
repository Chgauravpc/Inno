"use client";

import { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, Chip, Disclaimer, ErrorBox, PageSkeleton } from "@/components/ui";
import { useApi } from "@/lib/api";
import { inr, inrCompact, pct, TYPE_COLOR } from "@/lib/format";
import { useSettings } from "@/lib/settings";

type Band = { year: number; p10: number; p50: number; p90: number };
type Twin = {
  shift: number;
  weights: { labels: string[]; you: number[]; twin: number[] };
  metrics: Record<"you" | "twin", { real_return: number; vol: number; income: number; top_pct: number }>;
  holdings: { symbol: string; name: string; type: string; you: number; twin: number }[];
  fan: { you: Band[]; twin: Band[]; prob_twin_better: number; start: number };
  tracker: { m: number; you: number; twin: number }[];
  tracker_live: boolean;
  disclaimer: string;
};

function WeightBar({ label, w }: { label: string; w: number[] }) {
  const colors = ["#4f46e5", "#0b9f84", "#64748b"];
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium text-muted">{label}</p>
      <div className="flex h-7 overflow-hidden rounded-lg" role="img" aria-label={`${label} allocation`}>
        {w.map((x, i) => (
          <div key={i} style={{ width: `${x}%`, background: colors[i] }} className="num flex items-center justify-center text-[11px] font-medium text-white transition-all duration-700">
            {x >= 8 ? `${x.toFixed(0)}%` : ""}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TwinPage() {
  const { slab, inflation } = useSettings();
  const [shift, setShift] = useState(15);
  const { data, error } = useApi<Twin>("/twin", { slab, inflation, shift });
  if (error && !data) return <ErrorBox message={error} />;
  if (!data) return <PageSkeleton />;

  const y = data.metrics.you;
  const t = data.metrics.twin;
  const fan = data.fan.you.map((b, i) => ({
    year: b.year,
    youBand: [b.p10, b.p90],
    twinBand: [data.fan.twin[i].p10, data.fan.twin[i].p90],
    you: b.p50,
    twin: data.fan.twin[i].p50,
  }));

  const rows: [string, string, string, string][] = [
    ["Expected real return/yr", pct(y.real_return), pct(t.real_return), "after tax and inflation"],
    ["Volatility (yearly)", `${y.vol.toFixed(1)}%`, `${t.vol.toFixed(1)}%`, t.vol < y.vol ? "lower is steadier" : "higher"],
    ["Income after tax/yr", inr(y.income), inr(t.income), "rent, toll and interest"],
    ["Largest holding", `${y.top_pct.toFixed(1)}%`, `${t.top_pct.toFixed(1)}%`, "concentration"],
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Portfolio Twin</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            A risk-free copy of your portfolio with part of your stocks moved into REITs, InvITs and bonds, picked for your {slab}% slab. It tracks beside you so you can see the difference without touching real money.
          </p>
        </div>
        <label className="card flex items-center gap-3 px-4 py-2.5 text-sm">
          <span className="text-muted">Move</span>
          <input type="range" min={10} max={20} step={1} value={shift} onChange={(e) => setShift(Number(e.target.value))} className="w-28 accent-[var(--brand)]" aria-label="Share of portfolio to move into income assets" />
          <span className="num w-10 font-semibold">{shift}%</span>
        </label>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_1fr]">
        <Card title="You vs your Twin" subtitle={`Moves ${data.shift.toFixed(0)}% of the portfolio out of stocks`}>
          <div className="space-y-4">
            <WeightBar label="You today" w={data.weights.you} />
            <WeightBar label="Twin" w={data.weights.twin} />
            <div className="flex flex-wrap gap-3 text-xs text-muted">
              {data.weights.labels.map((l, i) => (
                <span key={l} className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: ["#4f46e5", "#0b9f84", "#64748b"][i] }} aria-hidden />
                  {l}
                </span>
              ))}
            </div>
          </div>
          <table className="mt-5 w-full text-sm">
            <thead className="text-xs text-muted">
              <tr className="border-b border-line">
                <th scope="col" className="py-2 text-left font-medium">Measure</th>
                <th scope="col" className="py-2 text-right font-medium">You</th>
                <th scope="col" className="py-2 text-right font-medium">Twin</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([k, a, b, note]) => (
                <tr key={k} className="border-b border-line/60">
                  <th scope="row" className="py-2.5 text-left font-medium">
                    {k}
                    <span className="block text-xs font-normal text-muted">{note}</span>
                  </th>
                  <td className="num py-2.5 text-right">{a}</td>
                  <td className="num py-2.5 text-right font-semibold">{b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="What the Twin changes" subtitle="Holdings you keep are scaled, income baskets are added">
          <ul className="space-y-2.5 text-sm">
            {data.holdings.map((h) => {
              const d = h.twin - h.you;
              return (
                <li key={h.symbol} className="flex items-center justify-between gap-3">
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: TYPE_COLOR[h.type] }} aria-hidden />
                    <span className="truncate">{h.name}</span>
                  </span>
                  <span className="num shrink-0 text-right">
                    {inrCompact(h.twin)}{" "}
                    {Math.abs(d) > 500 && <span className={d > 0 ? "text-pos" : "text-neg"}>({d > 0 ? "+" : "−"}{inrCompact(Math.abs(d))})</span>}
                  </span>
                </li>
              );
            })}
          </ul>
        </Card>
      </div>

      <Card
        title="Next 5 years, in a range of outcomes"
        subtitle="Monte Carlo on past return and risk. Shaded = 10th to 90th percentile, line = median, after tax"
        action={<Chip tone="brand">Twin ends higher in {data.fan.prob_twin_better.toFixed(0)}% of 600 runs</Chip>}
      >
        <div className="h-72 md:h-80" role="img" aria-label="Range of 5-year outcomes for you and your twin">
          <ResponsiveContainer>
            <ComposedChart data={fan} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="year" tickFormatter={(v) => (v === 0 ? "Now" : `Y${v}`)} stroke="var(--line)" />
              <YAxis tickFormatter={(v) => inrCompact(v)} width={72} domain={["auto", "auto"]} stroke="var(--line)" />
              <Tooltip
                formatter={(v, n) => (Array.isArray(v) ? [`${inrCompact(Number(v[0]))} to ${inrCompact(Number(v[1]))}`, String(n)] : [inrCompact(Number(v)), String(n)])}
                labelFormatter={(v) => (v === 0 ? "Today" : `Year ${v}`)}
                contentStyle={{ borderRadius: 10, border: "1px solid var(--line)", background: "var(--surface)" }}
              />
              <Legend verticalAlign="bottom" height={28} />
              <Area isAnimationActive={false} dataKey="youBand" name="You (range)" stroke="none" fill="#4f46e5" fillOpacity={0.14} />
              <Area isAnimationActive={false} dataKey="twinBand" name="Twin (range)" stroke="none" fill="#0b9f84" fillOpacity={0.16} />
              <Line isAnimationActive={false} dataKey="you" name="You (median)" stroke="#4f46e5" strokeWidth={2.4} dot={false} />
              <Line isAnimationActive={false} dataKey="twin" name="Twin (median)" stroke="#0b9f84" strokeWidth={2.4} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card title="Paper-tracked, last 12 months" subtitle={`Both portfolios at today's weights on ${data.tracker_live ? "real market history (Yahoo Finance)" : "the simulated market"}, in real terms (₹100 = 12 months ago)`}>
        <div className="h-60" role="img" aria-label="Twin tracker line chart">
          <ResponsiveContainer>
            <LineChart data={data.tracker} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="m" tickFormatter={(m) => (m === 12 ? "Now" : `${12 - m}m ago`)} interval={2} stroke="var(--line)" />
              <YAxis domain={["auto", "auto"]} tickFormatter={(v) => `${Math.round(v)}`} width={40} stroke="var(--line)" />
              <Tooltip formatter={(v) => Number(v).toFixed(1)} labelFormatter={(m) => (m === 12 ? "Now" : `${12 - Number(m)} months ago`)} contentStyle={{ borderRadius: 10, border: "1px solid var(--line)", background: "var(--surface)" }} />
              <Legend verticalAlign="bottom" height={28} />
              <Line isAnimationActive={false} dataKey="you" name="You" stroke="#4f46e5" strokeWidth={2.4} dot={false} />
              <Line isAnimationActive={false} dataKey="twin" name="Twin" stroke="#0b9f84" strokeWidth={2.4} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <p className="text-xs text-muted">{data.disclaimer}</p>
      <Disclaimer />
    </div>
  );
}
