"use client";

import { Building2, Route, Zap } from "lucide-react";
import { Card, Disclaimer, ErrorBox, PageSkeleton } from "@/components/ui";
import { useApi } from "@/lib/api";
import { inr } from "@/lib/format";
import { useSettings } from "@/lib/settings";

type Own = {
  items: { symbol: string; name: string; kind: string; units: number; physical: number; physical_unit: string; income_year: number; income_year_net: number; value: number }[];
  note: string;
};

const ICON = { office: Building2, road: Route, power: Zap } as const;
const VERB = { office: "rent", road: "toll", power: "transmission" } as const;

export default function OwnPage() {
  const { slab, inflation } = useSettings();
  const { data, error } = useApi<Own>("/ownership", { slab, inflation });
  if (error && !data) return <ErrorBox message={error} />;
  if (!data) return <PageSkeleton />;
  const totalIncome = data.items.reduce((a, i) => a + i.income_year_net, 0);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">What you actually own</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          A REIT or InvIT unit is a small share of real buildings, roads and power lines. Here is your share, and the rent or toll it paid you.
        </p>
      </div>

      <section className="rounded-3xl bg-hero p-6 text-hero-ink md:p-8">
        <p className="text-sm text-hero-ink/70">Real-asset income after tax at your {slab}% slab</p>
        <p className="num mt-1 text-4xl font-semibold md:text-5xl">{inr(totalIncome)} <span className="text-lg font-normal text-hero-ink/70">a year</span></p>
        <p className="mt-2 text-sm text-hero-ink/80">That is about {inr(totalIncome / 12)} every month from property and infrastructure you part-own.</p>
      </section>

      <div className="grid gap-5 md:grid-cols-2">
        {data.items.map((i) => {
          const Icon = ICON[i.kind as keyof typeof ICON] ?? Building2;
          return (
            <Card key={i.symbol}>
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-soft text-brand-strong">
                  <Icon size={24} aria-hidden />
                </span>
                <div className="min-w-0">
                  <h2 className="font-semibold">{i.name}</h2>
                  <p className="num text-sm text-muted">{i.units.toLocaleString("en-IN")} units · worth {inr(i.value)}</p>
                </div>
              </div>
              <p className="mt-5 text-sm text-muted">You own about</p>
              <p className="num text-3xl font-semibold">
                {i.physical >= 100 ? Math.round(i.physical).toLocaleString("en-IN") : i.physical.toFixed(1)}
                <span className="ml-2 text-base font-normal text-muted">{i.physical_unit}</span>
              </p>
              <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-line pt-4 text-sm">
                <div>
                  <dt className="text-xs text-muted">Paid to you each year ({VERB[i.kind as keyof typeof VERB]})</dt>
                  <dd className="num mt-0.5 font-semibold">{inr(i.income_year)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">After tax at {slab}%</dt>
                  <dd className="num mt-0.5 font-semibold text-pos">{inr(i.income_year_net)}</dd>
                </div>
              </dl>
            </Card>
          );
        })}
      </div>
      <p className="text-xs text-muted">{data.note}</p>
      <Disclaimer />
    </div>
  );
}
