"use client";

import { useState } from "react";
import { Example, useApi } from "@/lib/api";
import { CountUp, Skeleton } from "@/components/ui";
import { inr, inrCompact } from "@/lib/format";

function Slider({ label, value, min, max, step, onChange, fmt }: { label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void; fmt: (v: number) => string }) {
  return (
    <label className="block text-sm">
      <span className="flex justify-between text-muted">
        {label}
        <span className="num font-medium text-ink">{fmt(value)}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="mt-2 w-full accent-[var(--brand)]" />
    </label>
  );
}

export function ExampleCard() {
  const [amount, setAmount] = useState(500000);
  const [growth, setGrowth] = useState(12);
  const [years, setYears] = useState(5);
  const { data } = useApi<Example>("/example", { amount, growth, years, inflation: 5 });

  return (
    <div className="card p-5 md:p-6" aria-label="Live example from the TrackFolio engine">
      <p className="text-xs font-medium uppercase tracking-wider text-muted">Try it: one stock, sold after {years} years</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <Slider label="Invested" value={amount} min={100000} max={2000000} step={50000} onChange={setAmount} fmt={inrCompact} />
        <Slider label="Growth a year" value={growth} min={4} max={25} step={1} onChange={setGrowth} fmt={(v) => `${v}%`} />
        <Slider label="Years held" value={years} min={1} max={15} step={1} onChange={setYears} fmt={(v) => `${v}y`} />
      </div>
      {data ? (
        <div className="mt-6 grid items-end gap-4 sm:grid-cols-2">
          <div className="rounded-2xl bg-surface-2 p-4">
            <p className="text-xs text-muted">What your app shows</p>
            <p className="mt-1 text-3xl font-semibold"><CountUp value={data.app_value} format={inr} /></p>
          </div>
          <div className="rounded-2xl bg-brand p-4 text-on-brand">
            <p className="text-xs text-on-brand/75">What it is really worth to you</p>
            <p className="mt-1 text-3xl font-semibold"><CountUp value={data.real_value} format={inr} /></p>
          </div>
          <ul className="num space-y-1 text-sm text-muted sm:col-span-2">
            <li className="flex justify-between"><span>− Long-term capital gains tax (12.5% + cess)</span><span>{inr(data.tax)}</span></li>
            <li className="flex justify-between"><span>− STT and charges</span><span>{inr(data.costs)}</span></li>
            <li className="flex justify-between"><span>÷ 5% yearly inflation, in today&apos;s rupees</span><span>−{inr(data.inflation_erosion)}</span></li>
          </ul>
        </div>
      ) : (
        <Skeleton className="mt-6 h-40" />
      )}
      <p className="mt-4 text-xs text-muted">Computed live by the FastAPI engine. Illustrative, education only.</p>
    </div>
  );
}
