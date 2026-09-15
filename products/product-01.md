<div align="center">
<img src="../assets/icons/ic-01.svg" width="88">

# 1 · Gold Watch Alert

**🥇 Gold** &nbsp;·&nbsp; Status `SHIPPED` &nbsp;·&nbsp; Primary 🤖 bot-led

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/watch XAUUSD`, `/watch list` |
| 🌐 Dashboard | `/p/gold-watch` |

**Primary — 🤖 bot-led.** One command in, one alert out — the dashboard keeps the history a chat log cannot.

## Free tier

**Unlimited /watch on gold. No account.**

---

## Problem

- Gold moves fast and the entry a trader sees is not the entry they get — spread and slippage eat the difference.
- The Telegram channels that promise gold calls are overwhelmingly scams, so the alternative is worse than nothing.

## Solution

Spread-aware entry and stop levels from Binance PAXGUSDT, with Yahoo GC=F as fallback.

## Commands

| Command | Does |
|:--|:--|
| `/watch XAUUSD` | live bid, ask, spread in bps, and spread-widened long/short entry and stop levels |
| `/watch XAUUSD above 2450` | arm an alert that fires when the **ask** reaches the level |
| `/watch XAUUSD below 2380` | arm an alert that fires when the **bid** falls to the level |
| `/watch list` | show every alert you have armed |
| `/watch clear` | disarm them all |

## Dashboard views

- Live price panel — bid, ask, spread and the entry/stop levels, no login needed
- Alert history — every trigger with the price and spread at fire time, keyed to the same Telegram account the bot uses
- Threshold editor for each armed alert — arm, edit the level, disarm; the bot's `/watch list` shows the same rows
- CSV export of triggers for journalling

## Monetization

- **Free** — unlimited `/watch` on gold, alert history on the dashboard.
- **PRO** — `/autopilot`, DCF and COT fundamentals, multi-pair watching.

No product is paywalled at the door. Paid tiers sell scale and automation only.

## Data sources

- Binance `PAXGUSDT` book ticker — primary, free public endpoint, gives a real bid and ask
- Yahoo Finance `GC=F` — fallback when Binance is unreachable; no order book, so spread reads n/a
- Alerts are checked every five minutes by a GitHub Actions cron calling `POST /tasks/check-alerts`, or by `flask --app wsgi check-alerts` from any cron

---

<div align="center">
<sub>Educational research only. Not financial advice. Verify every price with your broker.</sub>
</div>
