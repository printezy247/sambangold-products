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
| 🤖 Telegram | `/miners`, `/miners TICKER`, `/miners weekly` |
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

**Live.** Six months of daily closes from Yahoo Finance for a fixed universe — GDX, GDXJ, seven majors and mid-tiers, three royalty names — with GC=F as the bullion reference. Each name is regressed on gold over the window (β and ρ) and again over the last 20 sessions; the residual is the 20-session move that β and gold's move do not explain, and the screen sorts on its size. Flags: decoupled (20-session ρ below 0.3), lagging or leading (residual beyond ±5 %), thin AISC margin (below 20 % of spot), earnings within 14 days. AISC is quarterly and hand-maintained, so every row carries the disclosure period; ETFs and royalty names have none and say why. Earnings dates are estimates from each company's usual cadence, labelled as such. `/miners weekly` switches on a Monday digest, pushed once per ISO week by the five-minute checker. The residual is presented as a question to investigate, never a signal.

## Commands

| Command | Does |
|:--|:--|
| `/miners` | this week's screen: the six largest residuals with β and flags |
| `/miners TICKER` | one name: β and ρ over 6 months and 20 sessions, the explained and residual move, AISC margin, next earnings, flags |
| `/miners weekly` | Monday digest on or off |

---

## Dashboard views

- Screener table across the universe, sortable by residual, 20-session return, β, ρ, AISC margin, earnings, name; no login
- Per-name panel: residual, β/ρ, AISC margin, earnings estimate, and a chart of the name against gold rebased to 100
- Monday digest toggle for signed-in users

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | weekly screen, full table, no login |
| **PRO** | daily alerts, backtesting, custom universe |

## Data sources

- Yahoo Finance daily closes, six months, per ticker and GC=F
- AISC per company from the last quarterly report, hand-maintained in the code with its period
- Earnings dates estimated from each company's cadence, labelled as estimates; no paid calendar

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
<sub>Status: <b>LIVE</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
