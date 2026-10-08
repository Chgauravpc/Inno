"use client";

import { animate } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import Link from "next/link";

export function Logo({ className, dark }: { className?: string; dark?: boolean }) {
  return (
    <Link href="/" className={clsx("inline-flex items-center gap-2 font-semibold tracking-tight", className)} aria-label="TrackFolio home">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden>
        <rect width="32" height="32" rx="9" fill="#0b7a66" />
        <path d="M7 21l6-6 4 4 8-9" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="25" cy="10" r="2.4" fill="#f6b04c" />
      </svg>
      <span className={dark ? "text-white" : "text-ink"}>TrackFolio</span>
    </Link>
  );
}

export function CountUp({ value, format, duration = 0.9 }: { value: number; format: (v: number) => string; duration?: number }) {
  const [shown, setShown] = useState(value);
  const prev = useRef(value);
  useEffect(() => {
    const c = animate(prev.current, value, { duration, ease: "easeOut", onUpdate: (v) => setShown(v) });
    prev.current = value;
    return () => c.stop();
  }, [value, duration]);
  return <span className="num">{format(shown)}</span>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton", className)} aria-hidden />;
}

export function PageSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading">
      <Skeleton className="h-40" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="card p-6 text-sm" role="alert">
      <p className="font-medium">Could not reach the TrackFolio API.</p>
      <p className="mt-1 text-muted">{message}. Start the backend (uvicorn api.index:app --port 8000) and refresh.</p>
    </div>
  );
}

export function Disclaimer() {
  return (
    <p className="mt-8 text-xs leading-relaxed text-muted">
      Demo data from a sandbox Account Aggregator fetch. Estimates use stated tax rules and assumptions and are for education only, not investment advice.
    </p>
  );
}

export function Card({ title, subtitle, action, children, className }: { title?: string; subtitle?: string; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={clsx("card p-5 md:p-6", className)}>
      {(title || action) && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-base font-semibold">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function Chip({ tone = "neutral", children }: { tone?: "neutral" | "good" | "warn" | "brand"; children: React.ReactNode }) {
  const tones = {
    neutral: "bg-surface-2 text-muted",
    good: "bg-brand-soft text-brand-strong",
    warn: "bg-amber-soft text-amber",
    brand: "bg-brand text-on-brand",
  };
  return <span className={clsx("inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}
