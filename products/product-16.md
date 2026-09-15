<div align="center">
<img src="../assets/icons/ic-16.svg" width="88">

# 16 · Correlation & Overexposure Monitor

**💱 Forex** &nbsp;·&nbsp; Demand `●●●●○` &nbsp;·&nbsp; Supply gap `●●○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/exposure`, `/exposure warn` |
| 🌐 Dashboard | `/p/exposure-monitor` |

**Primary — 🤖 bot-led.** Overexposure is a warning you need immediately; the heat-map explains it afterwards.

## Free tier

**On-demand snapshots, unlimited.**

---

## Problem

- 'Five open trades' is frequently one leveraged bet.
- XAUUSD, silver, DXY, USDJPY, and gold miners move together, and the account discovers this during the drawdown rather than before it.
- Swap and session-spread costs compound the same concentration quietly.

## Solution

1. Cluster open positions by rolling correlation and collapse them into a single true-risk figure — effective exposure, not nominal lot count.
2. Warn when effective risk exceeds the stated per-trade risk because positions are stacked on one factor.
3. Surface swap-rollover cost and session-spread cost on the same view, since both scale with the same concentration.

**Live.** No free feed gives rolling correlations across every pair a retail book holds, so the clustering is structural: each position is decomposed into its currency legs (EURUSD buy = long EUR, short USD; XAUUSD buy = long gold, short USD; silver shares the metals factor), the legs are netted per factor, and the book collapses to a true-risk figure. Flags: one factor carrying 60% or more of gross, three or more positions leaning the same way on one factor, effective leverage above 20× balance. The heat-map is +1 where two positions share a leg the same way, −1 where they oppose. Spread and swap are estimated per position from typical published values. Snapshots are archived per account; `/exposure warn` pushes every overexposed snapshot to Telegram.

## Commands

| Command | Does |
|:--|:--|
| `/exposure [POSITIONS]` | analyse `XAUUSD buy 1, EURUSD buy 1, …`, or show the last snapshot |
| `/exposure warn` | enable overexposure push alerts |

---

## Dashboard views

- Paste the open book (one position per line), optional balance, one-click sample
- True-risk tile, biggest factor and share, leverage; the flags in plain words
- Cluster decomposition per factor and the structural correlation heat-map
- Spread and swap cost projection per position, weekly total
- Last snapshot remembered per account; push-warning toggle

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | on-demand snapshots, unlimited |
| **PRO** | live monitoring, prop-rule-aware exposure caps, historical concentration report |

## Data sources

- Open position list (broker export or account link)
- Price history for rolling correlation
- Broker swap tables

---

## Demand vs supply

- **Demand** — ●●●●○ — especially for gold traders, who are usually more concentrated than they think.
- **Supply gap** — ●●○○○ — some platforms show correlation, few translate it into a single risk figure.
- **Build effort** — ●●○ — roughly 2 weeks. Correlation windows need care; too short is noise, too long misses regime change.

## Build notes

- Pair naturally with #14: an exposure cap is a rule a prop trader can breach.
- Show the correlation window length. A concentration warning without its lookback is unfalsifiable.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
