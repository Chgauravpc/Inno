# TrackFolio — by Team Innovisionaries

See what your investments are *really* worth: every stock, REIT, InvIT and bond from every broker, after tax, costs and inflation.

- **Frontend:** Next.js (App Router), Tailwind, Recharts, Framer Motion
- **Backend:** FastAPI (`api/index.py`, engines in `backend/`), deployed as a Vercel Python function
- **Data:** demo investor from a sandbox Account Aggregator fetch (`backend/data.py`); tax rules in `backend/tax_rules.py`

## Run locally
```bash
python -m venv .venv && .venv/Scripts/pip install fastapi uvicorn   # macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m uvicorn api.index:app --port 8000          # API + docs at /api/py/docs
npm install && npm run dev                                         # http://localhost:3000 (proxies /api/py to :8000)
```

## Deploy
`npx vercel login` then `npx vercel --prod`. No env vars needed. `/api/py/*` is rewritten to the Python function.

## Live data and AI (optional, both degrade gracefully)
- **Yahoo Finance** (on by default, no key): live prices for the 9 listed holdings, real cost basis from the close on each purchase date, and real Nifty 50 / REIT-InvIT basket / G-Sec ETF history for Benchmarks and the Twin tracker. Set `LIVE_DATA=0` for deterministic demo prices. Bonds stay on demo values.
- **OpenRouter LLM** for the Ask tab: copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (and optionally `OPENROUTER_MODEL`). On Vercel add the same variables in Project Settings. Without a key, or if the call fails, Ask uses the built-in rule-based answers. The key is only read server-side.
- `GET /api/py/status` shows what is enabled.

Tests: `python -m pytest tests` (mocks Yahoo and OpenRouter).

Education only, not investment advice.
