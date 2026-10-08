"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Send } from "lucide-react";
import { api } from "@/lib/api";
import { useSettings } from "@/lib/settings";
import { Disclaimer } from "@/components/ui";

type Msg = { role: "user" | "bot"; text: string; sources?: string[]; engine?: "llm" | "rules"; model?: string; note?: string };
type Lang = "en" | "hi" | "mr";

const SUGGEST: Record<Lang, string[]> = {
  en: ["Why is my real value lower?", "How is my capital gains tax calculated?", "What are REITs and InvITs?", "Is my portfolio too risky?", "Which asset suits my slab?"],
  hi: ["मेरा असली मूल्य कम क्यों है?", "मेरा LTCG टैक्स कैसे बनता है?", "REIT और InvIT क्या हैं?", "महंगाई का असर क्या है?"],
  mr: ["माझे खरे मूल्य कमी का आहे?", "माझा LTCG कर कसा ठरतो?", "REIT आणि InvIT म्हणजे काय?", "महागाईचा परिणाम काय?"],
};

const GREET: Record<Lang, string> = {
  en: "Hi Priya. Ask me anything about your numbers. I only use your own portfolio and the tax rules shown here.",
  hi: "नमस्ते प्रिया। अपने आँकड़ों के बारे में कुछ भी पूछें। मैं सिर्फ आपका पोर्टफोलियो और टैक्स नियम इस्तेमाल करता हूँ।",
  mr: "नमस्कार प्रिया. तुमच्या आकड्यांबद्दल काहीही विचारा. मी फक्त तुमचा पोर्टफोलिओ आणि कर नियम वापरतो.",
};

export default function Ask() {
  const { slab, inflation } = useSettings();
  const [lang, setLang] = useState<Lang>("en");
  const [msgs, setMsgs] = useState<Msg[]>([{ role: "bot", text: GREET.en }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [msgs, busy]);

  function switchLang(l: Lang) {
    setLang(l);
    setMsgs([{ role: "bot", text: GREET[l] }]);
  }

  async function send(q: string) {
    if (!q.trim() || busy) return;
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const history = msgs.slice(1).map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.text }));
      const r = await api<{ answer: string; sources: string[]; engine: "llm" | "rules"; model?: string; note?: string }>("/explain", { method: "POST", body: JSON.stringify({ question: q, lang, slab, inflation, history }) });
      setMsgs((m) => [...m, { role: "bot", text: r.answer, sources: r.sources, engine: r.engine, model: r.model, note: r.note }]);
    } catch {
      setMsgs((m) => [...m, { role: "bot", text: "I could not reach the server. Please try again." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-11rem)] max-w-3xl flex-col md:h-[calc(100vh-9rem)]">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Ask TrackFolio</h1>
          <p className="mt-1 text-sm text-muted">Plain-language answers about your own money, in your language.</p>
        </div>
        <div className="flex rounded-lg bg-surface-2 p-0.5 text-xs" role="radiogroup" aria-label="Language">
          {([["en", "English"], ["hi", "हिन्दी"], ["mr", "मराठी"]] as [Lang, string][]).map(([k, label]) => (
            <button key={k} role="radio" aria-checked={lang === k} onClick={() => switchLang(k)} className={clsx("rounded-md px-3 py-1.5 font-medium", lang === k ? "bg-surface shadow-sm" : "text-muted")}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="card flex-1 space-y-4 overflow-y-auto p-4 md:p-5" aria-live="polite">
        {msgs.map((m, i) => (
          <div key={i} className={clsx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div className={clsx("max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed", m.role === "user" ? "bg-brand text-on-brand" : "bg-surface-2")}>
              {m.text}
              {m.sources && (
                <p className="mt-2 border-t border-line pt-2 text-xs text-muted">
                  <span className={clsx("mr-2 rounded-full px-2 py-0.5 font-medium", m.engine === "llm" ? "bg-brand-soft text-brand-strong" : "bg-surface text-muted")}>
                    {m.engine === "llm" ? `AI · ${m.model}` : "Built-in answer"}
                  </span>
                  Based on: {m.sources.join(" · ")}
                  {m.note && <span className="mt-1 block">{m.note}</span>}
                </p>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex">
            <div className="rounded-2xl bg-surface-2 px-4 py-3 text-sm text-muted">Thinking…</div>
          </div>
        )}
        <div ref={end} />
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGGEST[lang].map((s) => (
          <button key={s} onClick={() => send(s)} className="rounded-full border border-line bg-surface px-3 py-1.5 text-xs text-muted transition-colors hover:border-brand hover:text-ink">
            {s}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="mt-3 flex gap-2"
      >
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about tax, REITs, risk, your slab…" aria-label="Your question" className="min-w-0 flex-1 rounded-xl border border-line bg-surface px-4 py-3 text-sm outline-none focus:border-brand" />
        <button type="submit" disabled={busy || !input.trim()} className="flex items-center gap-2 rounded-xl bg-brand px-4 py-3 text-sm font-medium text-on-brand disabled:opacity-50" aria-label="Send">
          <Send size={16} aria-hidden />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
      <Disclaimer />
    </div>
  );
}
