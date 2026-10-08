"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";

type Settings = {
  slab: number;
  inflation: number;
  setSlab: (v: number) => void;
  setInflation: (v: number) => void;
};

const Ctx = createContext<Settings | null>(null);
const KEY = "trackfolio.settings.v1";
const DEFAULT = JSON.stringify({ slab: 30, inflation: 5 });

const listeners = new Set<() => void>();
function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}
function snapshot(): string {
  try {
    return localStorage.getItem(KEY) ?? DEFAULT;
  } catch {
    return DEFAULT;
  }
}
function write(v: { slab: number; inflation: number }) {
  try {
    localStorage.setItem(KEY, JSON.stringify(v));
  } catch {
    /* storage unavailable: setting lasts only until reload */
  }
  listeners.forEach((l) => l());
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  // server snapshot = defaults, so hydration always matches; the stored value applies right after
  const raw = useSyncExternalStore(subscribe, snapshot, () => DEFAULT);
  const parsed = useMemo(() => {
    try {
      const s = JSON.parse(raw);
      return { slab: Number(s.slab) || 0, inflation: Number(s.inflation) || 5 };
    } catch {
      return { slab: 30, inflation: 5 };
    }
  }, [raw]);

  const setSlab = useCallback((v: number) => write({ ...parsed, slab: v }), [parsed]);
  const setInflation = useCallback((v: number) => write({ ...parsed, inflation: v }), [parsed]);
  const value = useMemo<Settings>(() => ({ ...parsed, setSlab, setInflation }), [parsed, setSlab, setInflation]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSettings() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useSettings outside SettingsProvider");
  return c;
}
