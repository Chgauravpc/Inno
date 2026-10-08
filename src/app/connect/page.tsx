"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import clsx from "clsx";
import { Check, FileUp, Landmark, Loader2, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/ui";
import { api } from "@/lib/api";
import { inr } from "@/lib/format";

type Fetch = { brokers: { name: string; value: number }[]; lots: number; holdings: number; duplicates_merged: number; value: number };
const STEPS = ["Consent", "Fetching", "Unifying"];

export default function Connect() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Fetch | null>(null);
  const [err, setErr] = useState("");
  const [fileName, setFileName] = useState("");
  const file = useRef<HTMLInputElement>(null);

  const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

  async function run() {
    setBusy(true);
    setErr("");
    try {
      setStep(0);
      await api("/connect/consent", { method: "POST", body: JSON.stringify({ provider: "sandbox-aa" }) });
      await wait(700);
      setStep(1);
      const data = await api<Fetch>("/connect/fetch");
      await wait(900);
      setStep(2);
      await wait(900);
      setResult(data);
      setStep(3);
    } catch {
      setErr("The sandbox could not be reached. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5">
        <Logo />
        <span className="text-xs text-muted">Team Innovisionaries</span>
      </header>
      <main className="mx-auto max-w-xl px-5 pb-16 pt-6">
        <h1 className="text-3xl font-semibold tracking-tight">Connect every broker with one consent</h1>
        <p className="mt-2 text-muted">Read-only access through the Account Aggregator framework. This demo uses a sandbox with a sample investor.</p>

        <ol className="mt-8 flex items-center gap-2" aria-label="Progress">
          {STEPS.map((s, i) => (
            <li key={s} className="flex flex-1 items-center gap-2">
              <span className={clsx("flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold", step > i ? "bg-brand text-on-brand" : step === i && busy ? "bg-brand-soft text-brand-strong" : "bg-surface-2 text-muted")}>
                {step > i ? <Check size={14} aria-hidden /> : i + 1}
              </span>
              <span className={clsx("text-xs font-medium", step >= i ? "text-ink" : "text-muted")}>{s}</span>
              {i < STEPS.length - 1 && <span className="h-px flex-1 bg-line" aria-hidden />}
            </li>
          ))}
        </ol>

        <div className="card mt-6 p-6">
          {!result ? (
            <>
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-brand-strong">
                  <Landmark size={20} aria-hidden />
                </span>
                <div>
                  <p className="font-semibold">Share your holdings from NSDL and CDSL</p>
                  <p className="mt-1 text-sm text-muted">TrackFolio gets a read-only view of every demat account linked to your PAN. We never see passwords and cannot place trades.</p>
                </div>
              </div>
              <ul className="mt-5 space-y-2 text-sm">
                {["Holdings and quantities only", "Valid for 90 days, revoke any time", "Encrypted, and deleted when you ask"].map((t) => (
                  <li key={t} className="flex items-center gap-2">
                    <ShieldCheck size={16} className="text-brand" aria-hidden />
                    {t}
                  </li>
                ))}
              </ul>
              <button onClick={run} disabled={busy} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-brand px-5 py-3 font-medium text-on-brand transition-opacity disabled:opacity-80">
                {busy ? <><Loader2 size={18} className="animate-spin" aria-hidden /> {["Asking for consent…", "Fetching holdings…", "Merging duplicates by ISIN…"][step]}</> : "Approve consent and fetch"}
              </button>
              {err && <p role="alert" className="mt-3 text-sm text-neg">{err}</p>}
              <div className="my-5 flex items-center gap-3 text-xs text-muted">
                <span className="h-px flex-1 bg-line" /> or <span className="h-px flex-1 bg-line" />
              </div>
              <input ref={file} type="file" accept="application/pdf" className="sr-only" aria-label="Upload CAS PDF" onChange={(e) => { setFileName(e.target.files?.[0]?.name ?? ""); if (e.target.files?.[0]) run(); }} />
              <button onClick={() => file.current?.click()} disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl border border-line px-5 py-3 text-sm font-medium hover:bg-surface-2">
                <FileUp size={16} aria-hidden /> {fileName || "Upload a CAS PDF instead"}
              </button>
              <p className="mt-2 text-center text-xs text-muted">Demo: any PDF loads the same sample investor.</p>
            </>
          ) : (
            <div>
              <p className="flex items-center gap-2 font-semibold text-pos"><Check size={18} aria-hidden /> Connected</p>
              <p className="num mt-3 text-3xl font-semibold">{inr(result.value)}</p>
              <p className="mt-1 text-sm text-muted">{result.lots} lots from {result.brokers.length} brokers became {result.holdings} holdings ({result.duplicates_merged} duplicates merged).</p>
              <ul className="mt-4 divide-y divide-line text-sm">
                {result.brokers.map((b) => (
                  <li key={b.name} className="flex justify-between py-2"><span>{b.name}</span><span className="num font-medium">{inr(b.value)}</span></li>
                ))}
              </ul>
              <button onClick={() => router.push("/dashboard")} className="mt-6 w-full rounded-xl bg-brand px-5 py-3 font-medium text-on-brand">See what it is really worth</button>
            </div>
          )}
        </div>
        <p className="mt-6 text-center text-xs text-muted">Sandbox demo with sample data. Education only, not investment advice.</p>
      </main>
    </div>
  );
}
