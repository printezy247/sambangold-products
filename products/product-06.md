<div align="center">
<img src="../assets/icons/ic-06.svg" width="88">

# 6 · Copy-Trade Safety Audit

**🔒 Fintech** &nbsp;·&nbsp; Status `SHIPPED` &nbsp;·&nbsp; Primary 🤖 bot-led

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/copyaudit BROKER` |
| 🌐 Dashboard | `/p/copy-trade-audit` |

**Primary — 🤖 bot-led.** It has to run at the moment someone is being pitched.

## Free tier

**5 audits free.**

---

## Problem

- Copy-trading is pushed hard by influencers and is frequently routed through unregulated brokers.
- The cost is hidden in the spread, and the risk is hidden in the absence of negative-balance protection.

## Solution

Check regulation and negative-balance protection, then price the hidden spread cost.

`/copyaudit exness 2 10` looks the broker up in the built-in table (18 brokers with their regulators and NBP status), flags offshore-only licensing, prices the spread at 2 pips × 10 lots a month, and scans any pasted pitch against the shared red-flag rules. Unknown brokers are not condemned — they start at CAUTION with the tier-1 registers linked so you can verify the licence yourself. **Live.**

## Commands

| Command | Does |
|:--|:--|
| `/copyaudit BROKER [SPREAD_PIPS] [LOTS_PER_MONTH]` | regulators in our table, tier-1 or offshore, NBP, spread cost per month and year |

## Dashboard views

- Audit form with spread and monthly lots; regulator table with a link to each official register
- Audit history and a watchlist of brokers to re-check (signed in)
- Hidden-cost model — spread cost per month and per year
- Public share page per audit at `/p/copy-trade-audit/s/<id>`

## Monetization

- **Free** — 5 audits, with the regulator links shown.
- **PRO** — unlimited audits and a weekly portfolio risk report.

No product is paywalled at the door. Paid tiers sell scale and automation only.

## Data sources

- SEC, FCA and ASIC public registers
- Broker-published spread schedules

---

<div align="center">
<sub>Educational research only. Not financial advice. Verify every price with your broker.</sub>
</div>
