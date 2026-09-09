<div align="center">
<img src="../assets/icons/ic-18.svg" width="88">

# 18 · Miner-Bullion Divergence Screener

**📈 Stocks** &nbsp;·&nbsp; Demand `●●●○○` &nbsp;·&nbsp; Supply gap `●○○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/miners`, `/miners TICKER` |
| 🌐 Dashboard | `/p/miner-divergence` |

**Primary — 🌐 dashboard-led.** A sortable screener is a table; the bot carries the weekly digest.

## Free tier

**Weekly screen, full table, no login.**

---

## Problem

- Gold traders who want equity exposure are badly served.
- Generic stock screeners know nothing about all-in sustaining cost. Gold sites know nothing about equities.
- The result is that miner positions get sized off a gold view, with no reference to the margin structure that actually drives the equity.

## Solution

1. Screen GDX, GDXJ, and royalty names for beta divergence against spot gold — miners that stopped tracking bullion are either broken or mispriced.
2. Add AISC-versus-price margin compression, which is the mechanism behind most of that divergence.
3. Flag earnings dates and halt risk, since both break the correlation temporarily and trap positions.

## Commands

| Command | Does |
|:--|:--|
| `/miners` | this week's divergence screen |
| `/miners TICKER` | single-name beta, AISC margin, next earnings |

---

## Dashboard views

- Sortable screener table across the miner universe
- Per-name divergence chart against spot gold
- AISC margin and earnings/halt risk panel

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | weekly screen, full table, no login |
| **PRO** | daily alerts, backtesting, custom universe |

## Data sources

- Equity price history (Yahoo Finance)
- Spot gold reference
- Company AISC disclosures (quarterly)
- Earnings calendar

---

## Demand vs supply

- **Demand** — ●●●○○ — a natural extension for existing gold users.
- **Supply gap** — ●○○○○ — mining-specific screeners are institutional and expensive.
- **Build effort** — ●●○ — roughly 2 weeks. AISC data is quarterly and manual to maintain; everything else is automatable.

## Build notes

- AISC is reported quarterly and inconsistently. Show the disclosure date on every row.
- Divergence is a question, not a signal. Present it as something to investigate.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
