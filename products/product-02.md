<div align="center">
<img src="../assets/icons/ic-02.svg" width="88">

# 2 · XAUUSD Signal Verifier

**🥇 Gold** &nbsp;·&nbsp; Status `SHIPPED` &nbsp;·&nbsp; Primary 🤖 bot-led

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/verify GOLD PRICE` |
| 🌐 Dashboard | `/p/signal-verifier` |

**Primary — 🤖 bot-led.** Verification belongs in the group where the fake was posted.

## Free tier

**One verify per request, unlimited requests.**

---

## Problem

- Signal sellers post MT4 screenshots showing fills that the market never printed.
- Buyers have no way to check, because tick history is not something you can eyeball.

## Solution

Pull Binance PAXGUSDT tick history and test whether the claimed fill was reachable.

`/verify GOLD 2431.5 2026-09-14 14:30` (MYT) fetches the one-minute PAXGUSDT candles around that time — ±60 minutes with a time, the whole day with a date only, the last 24 hours with neither — and tests the price against every candle's low and high. Verdicts: **REAL** (inside a candle), **BORDERLINE** (outside every candle but within the source tolerance: 0.4% for the PAXG premium, 1.2% for the Yahoo GC=F futures basis fallback), **IMPOSSIBLE** (further than that), **UNVERIFIED** (no candles). Every verdict is archived with its window and gets a public share link for posting back into the group. **Live.**

## Commands

| Command | Does |
|:--|:--|
| `/verify GOLD PRICE [DATE] [TIME]` | REAL / BORDERLINE / IMPOSSIBLE / UNVERIFIED with the window range, nearest candle and gap |

## Dashboard views

- Single-claim form (price, date, time, side) with the window range, gap and nearest candle
- Batch verify — one claim per line, up to 20 per run
- Verdict archive per account with the window that produced each call
- Public verdict page per check at `/p/signal-verifier/s/<id>`

## Monetization

- **Free** — one verify per request, unlimited requests, verdict archive.
- **PRO** — batch CSV upload and weekly audit reports.

No product is paywalled at the door. Paid tiers sell scale and automation only.

## Data sources

- Binance `PAXGUSDT` one-minute klines (free, public, 24/7)
- Yahoo Finance `GC=F` one-minute bars as fallback for the last seven days

---

<div align="center">
<sub>Educational research only. Not financial advice. Verify every price with your broker.</sub>
</div>
