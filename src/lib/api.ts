"use client";

import { useEffect, useState } from "react";

const BASE = "/api/py";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

/** GET with params; keeps the previous data on screen while a new request loads. */
export function useApi<T>(path: string, params: Record<string, string | number> = {}) {
  const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  const key = `${path}?${qs}`;
  const [state, setState] = useState<{ key: string; data: T | null; error: string | null }>({ key: "", data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    api<T>(`${path}${qs ? "?" + qs : ""}`)
      .then((d) => !cancelled && setState({ key, data: d, error: null }))
      .catch((e) => !cancelled && setState((s) => ({ ...s, key, error: e.message })));
    return () => {
      cancelled = true;
    };
  }, [path, qs, key]);

  return { data: state.data, error: state.error, loading: state.key !== key };
}

export type Holding = {
  symbol: string;
  name: string;
  isin: string;
  type: "EQUITY" | "REIT" | "INVIT" | "BOND";
  price: number;
  brokers: string[];
  lots: number;
  qty: number;
  invested: number;
  market_value: number;
  tax: number;
  costs: number;
  after_tax: number;
  real_value: number;
  annual_income_net: number;
  years: number;
  avg_price: number;
  gain: number;
  app_return_pct: number;
  real_gain: number;
  real_return_cagr_pct: number;
  benchmark_real_cagr_pct: number;
  vs_benchmark_pct: number;
  weight_pct: number;
  short_lots: number;
  live: boolean;
};

export type Portfolio = {
  slab: number;
  inflation: number;
  rules_version: string;
  totals: {
    invested: number;
    app_value: number;
    tax: number;
    costs: number;
    after_tax: number;
    real_value: number;
    inflation_erosion: number;
    gain_app: number;
    gain_real: number;
    overstatement_pct: number;
    annual_income_net: number;
  };
  waterfall: { label: string; value: number; kind: "total" | "delta" }[];
  allocation: { name: string; value: number; pct: number }[];
  brokers: { name: string; value: number; pct: number }[];
  holdings: Holding[];
  stats: { holdings: number; lots: number; duplicates_merged: number; brokers: number; equity_pct: number; top_symbol: string; top_pct: number };
  insights: { tone: "warn" | "info" | "good"; title: string; text: string }[];
  data_source: { live: boolean; provider: string; as_of: string | null; live_symbols: string[]; demo_symbols: string[]; cost_basis: string };
};

export type Example = {
  amount: number;
  growth: number;
  years: number;
  inflation: number;
  app_value: number;
  tax: number;
  costs: number;
  after_tax: number;
  real_value: number;
  inflation_erosion: number;
};
