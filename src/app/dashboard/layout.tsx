"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { BarChart3, Building2, GitCompare, LayoutDashboard, MessageCircle, Percent, Sparkles } from "lucide-react";
import { Logo } from "@/components/ui";
import { useSettings } from "@/lib/settings";

const NAV = [
  { href: "/dashboard", label: "Overview", short: "Home", icon: LayoutDashboard },
  { href: "/dashboard/benchmarks", label: "Benchmarks", short: "Bench", icon: BarChart3 },
  { href: "/dashboard/slab", label: "Your slab", short: "Slab", icon: Percent },
  { href: "/dashboard/twin", label: "Twin", short: "Twin", icon: GitCompare },
  { href: "/dashboard/own", label: "What you own", short: "Own", icon: Building2 },
  { href: "/dashboard/ask", label: "Ask", short: "Ask", icon: MessageCircle },
];

const SLABS = [0, 5, 10, 15, 20, 30];

function Controls() {
  const { slab, setSlab, inflation, setInflation } = useSettings();
  return (
    <div className="flex w-full flex-wrap items-center gap-x-5 gap-y-2 md:w-auto">
      <div className="flex w-full items-center gap-2 md:w-auto">
        <span id="slab-label" className="text-xs font-medium text-muted">Tax slab</span>
        <div role="radiogroup" aria-labelledby="slab-label" className="flex flex-1 rounded-lg bg-surface-2 p-0.5 md:flex-none">
          {SLABS.map((s) => (
            <button
              key={s}
              role="radio"
              aria-checked={slab === s}
              onClick={() => setSlab(s)}
              className={clsx(
                "num flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors md:flex-none md:px-2.5",
                slab === s ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink",
              )}
            >
              {s}%
            </button>
          ))}
        </div>
      </div>
      <label className="flex items-center gap-2 text-xs font-medium text-muted">
        Inflation
        <input
          type="range"
          min={2}
          max={9}
          step={0.5}
          value={inflation}
          onChange={(e) => setInflation(Number(e.target.value))}
          className="w-28 accent-[var(--brand)]"
          aria-label="Yearly inflation"
        />
        <span className="num w-9 text-ink">{inflation}%</span>
      </label>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen md:grid md:grid-cols-[232px_1fr]">
      <aside className="hidden border-r border-line bg-surface md:block">
        <div className="sticky top-0 flex h-screen flex-col p-5">
          <Logo className="text-lg" />
          <nav className="mt-8 space-y-1" aria-label="Main">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = href === "/dashboard" ? path === href : path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={clsx(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                    active ? "bg-brand-soft text-brand-strong" : "text-muted hover:bg-surface-2 hover:text-ink",
                  )}
                >
                  <Icon size={18} aria-hidden />
                  {label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-auto rounded-xl bg-surface-2 p-4 text-xs text-muted">
            <div className="mb-1 flex items-center gap-1.5 font-medium text-ink">
              <Sparkles size={14} aria-hidden /> Demo investor
            </div>
            Priya Sharma, Pune. 3 brokers linked through a sandbox consent.
            <div className="mt-3 border-t border-line pt-3">Built by Team Innovisionaries</div>
          </div>
        </div>
      </aside>

      <div className="min-w-0 overflow-x-clip pb-24 md:pb-10">
        <div className="sticky top-0 z-20 border-b border-line bg-bg/85 px-4 py-3 backdrop-blur md:px-8">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between md:gap-4">
            <div className="md:hidden">
              <Logo />
            </div>
            <Controls />
          </div>
        </div>
        <main className="mx-auto max-w-6xl px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-6 border-t border-line bg-surface/95 backdrop-blur md:hidden"
        aria-label="Main mobile"
      >
        {NAV.map(({ href, label, short, icon: Icon }) => {
          const active = href === "/dashboard" ? path === href : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-label={label}
              aria-current={active ? "page" : undefined}
              className={clsx("flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium", active ? "text-brand" : "text-muted")}
            >
              <Icon size={20} aria-hidden />
              {short}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
