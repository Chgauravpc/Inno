"use client";

import clsx from "clsx";
import { Card, Disclaimer, ErrorBox, PageSkeleton } from "@/components/ui";
import { useApi } from "@/lib/api";
import { pct } from "@/lib/format";
import { useSettings } from "@/lib/settings";

type Slab = {
  slabs: number[];
  rows: { key: string; label: string; pre_tax: number; vol: number; values: number[] }[];
  best: { slab: number; key: string; label: string; real: number; risk_adj: number }[];
};

function heat(v: number) {
  // real return -> background tint: low = amber, high = brand
  if (v < 1) return "color-mix(in srgb, var(--amber) 28%, var(--surface))";
  const t = Math.min(v / 6.5, 1);
  return `color-mix(in srgb, var(--brand) ${Math.round(12 + t * 38)}%, var(--surface))`;
}

export default function SlabPage() {
  const { slab, inflation } = useSettings();
  const { data, error } = useApi<Slab>("/slab", { inflation });
  if (error && !data) return <ErrorBox message={error} />;
  if (!data) return <PageSkeleton />;
  const idx = data.slabs.indexOf(slab);
  const best = data.best[idx];
  const bond = data.rows.find((r) => r.key === "gsec")!;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Your slab, your answer</h1>
        <p className="mt-1 text-sm text-muted">
          Real yearly return after tax and {inflation}% inflation, on ₹5 lakh over 5 years with income reinvested.
        </p>
      </div>

      <section className="rounded-3xl bg-hero p-6 text-hero-ink md:p-8">
        <p className="text-sm text-hero-ink/70">At the {slab}% slab, the best risk-adjusted fit is</p>
        <p className="mt-1 text-3xl font-semibold md:text-4xl">{best.label}</p>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-hero-ink/80">
          The same 7.5% bond earns about <span className="num font-semibold text-white">{pct(bond.values[idx], 1)}</span> a year in real terms at your slab, against{" "}
          <span className="num font-semibold text-white">{pct(bond.values[0], 1)}</span> at zero tax. Taxes change which asset is worth owning.
        </p>
      </section>

      <Card title="Real return per year, by slab" subtitle="Your slab is highlighted. Darker green means more money kept after tax and inflation.">
        <div className="-mx-2 overflow-x-auto">
          <table className="w-full min-w-[560px] border-separate border-spacing-1 text-sm">
            <thead>
              <tr className="text-xs text-muted">
                <th scope="col" className="px-2 py-1 text-left font-medium">Asset</th>
                <th scope="col" className="px-2 py-1 text-right font-medium">Pre-tax</th>
                {data.slabs.map((s) => (
                  <th key={s} scope="col" className={clsx("num px-2 py-1 text-right font-medium", s === slab && "text-brand-strong")}>
                    {s}%
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.key}>
                  <th scope="row" className="px-2 py-2 text-left font-medium">{r.label}</th>
                  <td className="num px-2 py-2 text-right text-muted">{r.pre_tax.toFixed(1)}%</td>
                  {r.values.map((v, i) => (
                    <td
                      key={i}
                      style={{ background: heat(v) }}
                      className={clsx("num rounded-md px-2 py-2 text-right font-medium", data.slabs[i] === slab && "ring-2 ring-brand")}
                    >
                      {v.toFixed(1)}%
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">Pre-tax = price growth plus income. Real = after tax, selling costs and inflation.</p>
      </Card>

      <Card title="Best fit by slab" subtitle="Highest real return per unit of risk among market-linked assets">
        <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.best.map((b) => (
            <li key={b.slab} className={clsx("rounded-xl border p-4", b.slab === slab ? "border-brand bg-brand-soft" : "border-line")}>
              <p className="text-xs text-muted">{b.slab}% slab</p>
              <p className="mt-1 font-semibold">{b.label}</p>
              <p className="num mt-1 text-sm text-muted">{pct(b.real)} real a year</p>
            </li>
          ))}
        </ol>
      </Card>
      <Disclaimer />
    </div>
  );
}
