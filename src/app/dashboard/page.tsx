"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { ArrowDownUp, Info, TriangleAlert, CircleCheck } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Radio } from "lucide-react";
import { Card, Chip, CountUp, Disclaimer, ErrorBox, PageSkeleton } from "@/components/ui";
import { Portfolio, useApi, Holding } from "@/lib/api";
import { inr, inrCompact, pct, pctPlain, TYPE_COLOR, TYPE_LABEL } from "@/lib/format";
import { useSettings } from "@/lib/settings";

type View = "app" | "after" | "real";

function DataBadge({ d }: { d: Portfolio["data_source"] }) {
  const when = d.as_of ? new Date(d.as_of).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) : null;
  return (
    <p className="mt-3 inline-flex flex-wrap items-center gap-x-2 gap-y-1 rounded-full bg-surface-2 px-3 py-1.5 text-xs text-muted">
      <span className={"flex items-center gap-1.5 font-medium " + (d.live ? "text-pos" : "text-amber")}>
        <Radio size={13} aria-hidden /> {d.live ? `Live prices · ${d.provider}` : "Demo prices"}
      </span>
      {when && <span>as of {when}</span>}
      <span>· {d.live_symbols.length} of {d.live_symbols.length + d.demo_symbols.length} holdings live</span>
      {d.live && <span>· cost basis = {d.cost_basis}</span>}
    </p>
  );
}

function Hero({ p }: { p: Portfolio }) {
  const [view, setView] = useState<View>("real");
  const t = p.totals;
  const value = view === "app" ? t.app_value : view === "after" ? t.after_tax : t.real_value;
  const gain = value - t.invested;
  const tabs: { id: View; label: string }[] = [
    { id: "app", label: "What apps show" },
    { id: "after", label: "After tax & costs" },
    { id: "real", label: "Real value" },
  ];
  return (
    <section className="overflow-hidden rounded-3xl bg-hero p-6 text-hero-ink md:p-8" aria-label="Portfolio value">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-hero-ink/70">Your total portfolio, {p.stats.holdings} holdings across {p.stats.brokers} brokers</p>
          <p className="mt-2 text-4xl font-semibold md:text-6xl">
            <CountUp value={value} format={inr} />
          </p>
          <p className="mt-2 text-sm">
            <span className={clsx("num font-medium", gain >= 0 ? "text-[#6ee7c4]" : "text-[#fdba74]")}>
              {gain >= 0 ? "+" : "−"}
              {inr(Math.abs(gain))}
            </span>{" "}
            <span className="text-hero-ink/70">{gain >= 0 ? "gain" : "loss"} on {inr(t.invested)} invested</span>
          </p>
        </div>
        <div role="tablist" aria-label="Value view" className="flex rounded-xl bg-white/10 p-1">
          {tabs.map((tb) => (
            <button
              key={tb.id}
              role="tab"
              aria-selected={view === tb.id}
              onClick={() => setView(tb.id)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors md:text-sm",
                view === tb.id ? "bg-white text-[#07251f]" : "text-hero-ink/80 hover:text-white",
              )}
            >
              {tb.label}
            </button>
          ))}
        </div>
      </div>
      <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-white/15 pt-5 md:grid-cols-4">
        {[
          ["Apps overstate by", `${t.overstatement_pct.toFixed(1)}%`],
          ["Tax if sold today", inr(t.tax)],
          ["Inflation erosion", inr(t.inflation_erosion)],
          ["Yearly income, after tax", inr(t.annual_income_net)],
        ].map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-hero-ink/65">{k}</dt>
            <dd className="num mt-1 text-lg font-semibold">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Breakdown({ p }: { p: Portfolio }) {
  const t = p.totals;
  const parts = [
    { label: "Real value", v: t.real_value, color: "var(--brand)" },
    { label: "Inflation", v: t.inflation_erosion, color: "var(--indigo)" },
    { label: "Capital gains tax", v: t.tax, color: "var(--amber)" },
    { label: "STT & charges", v: t.costs, color: "#94a3b8" },
  ];
  return (
    <Card title="Where your money goes" subtitle={`Of the ${inrCompact(t.app_value)} apps show, only ${((t.real_value / t.app_value) * 100).toFixed(0)}% is yours in real terms`}>
      <div className="flex h-5 w-full overflow-hidden rounded-full bg-surface-2" role="img" aria-label="Breakdown of app value into real value, inflation, tax and charges">
        {parts.map((x) => (
          <div key={x.label} style={{ width: `${(x.v / t.app_value) * 100}%`, background: x.color }} className="transition-all duration-700" />
        ))}
      </div>
      <ul className="mt-5 space-y-3">
        {parts.map((x) => (
          <li key={x.label} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: x.color }} aria-hidden />
              {x.label}
            </span>
            <span className="num font-medium">
              {x.label === "Real value" ? "" : "−"}
              {inr(x.v)} <span className="ml-1 text-xs text-muted">{((x.v / t.app_value) * 100).toFixed(1)}%</span>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function Allocation({ p }: { p: Portfolio }) {
  const [by, setBy] = useState<"type" | "broker">("type");
  const rows =
    by === "type"
      ? p.allocation.map((a) => ({ ...a, label: TYPE_LABEL[a.name], color: TYPE_COLOR[a.name] }))
      : p.brokers.map((b, i) => ({ ...b, label: b.name, color: ["#0b7a66", "#4f46e5", "#d97706"][i % 3] }));
  return (
    <Card
      title="Allocation"
      action={
        <div className="flex rounded-lg bg-surface-2 p-0.5 text-xs" role="tablist">
          {(["type", "broker"] as const).map((k) => (
            <button key={k} role="tab" aria-selected={by === k} onClick={() => setBy(k)} className={clsx("rounded-md px-2.5 py-1 font-medium capitalize", by === k ? "bg-surface shadow-sm" : "text-muted")}>
              By {k}
            </button>
          ))}
        </div>
      }
    >
      <div className="flex items-center gap-4">
        <div className="h-40 w-40 shrink-0">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={rows} dataKey="value" nameKey="label" innerRadius={48} outerRadius={72} paddingAngle={2} stroke="none">
                {rows.map((r) => (
                  <Cell key={r.label} fill={r.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => inr(Number(v))} contentStyle={{ borderRadius: 10, border: "1px solid var(--line)", background: "var(--surface)" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <ul className="flex-1 space-y-2.5 text-sm">
          {rows.map((r) => (
            <li key={r.label} className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: r.color }} aria-hidden />
                {r.label}
              </span>
              <span className="num font-medium">{r.pct.toFixed(1)}%</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

function Insights({ p }: { p: Portfolio }) {
  const icon = { warn: TriangleAlert, info: Info, good: CircleCheck } as const;
  const tone = { warn: "text-amber bg-amber-soft", info: "text-indigo bg-surface-2", good: "text-brand-strong bg-brand-soft" } as const;
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {p.insights.slice(0, 3).map((i) => {
        const Icon = icon[i.tone];
        return (
          <div key={i.title} className="card flex gap-3 p-4">
            <span className={clsx("mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full", tone[i.tone])}>
              <Icon size={16} aria-hidden />
            </span>
            <div>
              <p className="text-sm font-semibold">{i.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">{i.text}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

type SortKey = "market_value" | "real_value" | "real_return_cagr_pct" | "vs_benchmark_pct";

function HoldingsTable({ p }: { p: Portfolio }) {
  const [type, setType] = useState("ALL");
  const [broker, setBroker] = useState("ALL");
  const [sort, setSort] = useState<SortKey>("market_value");
  const [open, setOpen] = useState<string | null>(null);

  const rows = useMemo(() => {
    return p.holdings
      .filter((h) => (type === "ALL" || h.type === type) && (broker === "ALL" || h.brokers.includes(broker)))
      .sort((a, b) => b[sort] - a[sort]);
  }, [p, type, broker, sort]);

  const th = (k: SortKey, label: string, hide = "") => (
    <th scope="col" className={clsx("px-3 py-2 text-right font-medium", hide)}>
      <button onClick={() => setSort(k)} className={clsx("inline-flex items-center gap-1", sort === k ? "text-ink" : "text-muted")} aria-label={`Sort by ${label}`}>
        {label}
        <ArrowDownUp size={12} aria-hidden />
      </button>
    </th>
  );

  return (
    <Card title="All holdings, merged by ISIN" subtitle={`${p.stats.lots} lots from ${p.stats.brokers} brokers become ${p.stats.holdings} holdings (${p.stats.duplicates_merged} duplicates merged)`}>
      <div className="mb-4 flex flex-wrap gap-2">
        {["ALL", "EQUITY", "REIT", "INVIT", "BOND"].map((t) => (
          <button key={t} onClick={() => setType(t)} aria-pressed={type === t} className={clsx("rounded-full border px-3 py-1 text-xs font-medium", type === t ? "border-brand bg-brand-soft text-brand-strong" : "border-line text-muted hover:text-ink")}>
            {t === "ALL" ? "All types" : TYPE_LABEL[t]}
          </button>
        ))}
        <span className="mx-1 hidden h-6 w-px bg-line md:block" aria-hidden />
        {["ALL", ...p.brokers.map((b) => b.name)].map((b) => (
          <button key={b} onClick={() => setBroker(b)} aria-pressed={broker === b} className={clsx("rounded-full border px-3 py-1 text-xs font-medium", broker === b ? "border-indigo bg-surface-2 text-ink" : "border-line text-muted hover:text-ink")}>
            {b === "ALL" ? "All brokers" : b}
          </button>
        ))}
      </div>
      <div className="-mx-2 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-xs text-muted">
            <tr className="border-b border-line">
              <th scope="col" className="px-3 py-2 text-left font-medium">Holding</th>
              {th("market_value", "Apps show", "hidden sm:table-cell")}
              {th("real_value", "Real value")}
              {th("real_return_cagr_pct", "Real return/yr", "hidden sm:table-cell")}
              {th("vs_benchmark_pct", "vs index", "hidden md:table-cell")}
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <Row key={h.symbol} h={h} open={open === h.symbol} onToggle={() => setOpen(open === h.symbol ? null : h.symbol)} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function Row({ h, open, onToggle }: { h: Holding; open: boolean; onToggle: () => void }) {
  return (
    <>
      <tr onClick={onToggle} className="cursor-pointer border-b border-line/60 transition-colors hover:bg-surface-2/60">
        <td className="px-3 py-3">
          <button className="text-left" aria-expanded={open} onClick={(e) => { e.stopPropagation(); onToggle(); }}>
            <span className="block font-medium">{h.name}</span>
            <span className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: TYPE_COLOR[h.type] }} aria-hidden />
              {TYPE_LABEL[h.type]} · {h.brokers.join(", ")}
              {h.short_lots > 0 && <Chip tone="warn">short-term lot</Chip>}
            </span>
          </button>
        </td>
        <td className="num hidden px-3 py-3 text-right sm:table-cell">{inr(h.market_value)}</td>
        <td className="num px-3 py-3 text-right font-medium">{inr(h.real_value)}</td>
        <td className={clsx("num hidden px-3 py-3 text-right sm:table-cell", h.real_return_cagr_pct < 2 ? "text-neg" : "text-pos")}>{pct(h.real_return_cagr_pct)}</td>
        <td className={clsx("num hidden px-3 py-3 text-right md:table-cell", h.vs_benchmark_pct < 0 ? "text-neg" : "text-pos")}>{pct(h.vs_benchmark_pct)}</td>
      </tr>
      {open && (
        <tr className="border-b border-line/60 bg-surface-2/50">
          <td colSpan={5} className="px-3 py-4">
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm md:grid-cols-4">
              {[
                ["Price now", `${inr(h.price)} ${h.live ? "(live)" : "(demo)"}`],
                ["Average buy price", inr(h.avg_price)],
                ["Invested", inr(h.invested)],
                ["Gain apps show", `${inr(h.gain)} (${pct(h.app_return_pct)})`],
                ["Tax if sold", inr(h.tax)],
                ["STT & charges", inr(h.costs)],
                ["Held for", `${h.years.toFixed(1)} years`],
                ["Income/yr after tax", inr(h.annual_income_net)],
                ["Index real return/yr", pctPlain(h.benchmark_real_cagr_pct)],
                ["ISIN", h.isin],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-muted">{k}</dt>
                  <dd className="num mt-0.5 font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </td>
        </tr>
      )}
    </>
  );
}

export default function Overview() {
  const { slab, inflation } = useSettings();
  const { data, error } = useApi<Portfolio>("/portfolio", { slab, inflation });
  if (error && !data) return <ErrorBox message={error} />;
  if (!data) return <PageSkeleton />;
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Welcome back, Priya</h1>
        <p className="mt-1 text-sm text-muted">
          Tax rules: {data.rules_version}. Showing what you would really keep at the {slab}% slab and {inflation}% inflation.
        </p>
        <DataBadge d={data.data_source} />
      </div>
      <Hero p={data} />
      <Insights p={data} />
      <div className="grid gap-5 lg:grid-cols-2">
        <Breakdown p={data} />
        <Allocation p={data} />
      </div>
      <HoldingsTable p={data} />
      <Disclaimer />
    </div>
  );
}
