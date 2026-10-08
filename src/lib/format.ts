const inr0 = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export const inr = (v: number) => `${v < 0 ? "−" : ""}₹${inr0.format(Math.abs(Math.round(v)))}`;

/** ₹8.81 L, ₹1.2 Cr, ₹33.3 K */
export function inrCompact(v: number) {
  const a = Math.abs(v);
  const s = v < 0 ? "−" : "";
  if (a >= 1e7) return `${s}₹${(a / 1e7).toFixed(2)} Cr`;
  if (a >= 1e5) return `${s}₹${(a / 1e5).toFixed(2)} L`;
  if (a >= 1e3) return `${s}₹${(a / 1e3).toFixed(1)}K`;
  return `${s}₹${Math.round(a)}`;
}

export const pct = (v: number, d = 1) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(d)}%`;
export const pctPlain = (v: number, d = 1) => `${v.toFixed(d)}%`;

export const TYPE_LABEL: Record<string, string> = {
  EQUITY: "Stocks",
  REIT: "REITs",
  INVIT: "InvITs",
  BOND: "Bonds",
};

export const TYPE_COLOR: Record<string, string> = {
  EQUITY: "#4f46e5",
  REIT: "#0b9f84",
  INVIT: "#d97706",
  BOND: "#64748b",
};
