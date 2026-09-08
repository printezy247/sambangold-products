<div align="center">
<img src="../assets/icons/ic-16.svg" width="88">

# 16 · Correlation & Overexposure Monitor

**💱 Forex** &nbsp;·&nbsp; Demand `●●●●○` &nbsp;·&nbsp; Supply gap `●●○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both** — web heat-map of the position cluster, `/exposure` snapshot and overexposure warning in Telegram.

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

## Commands

| Command | Does |
|:--|:--|
| `/exposure` | current cluster and true-risk figure |
| `/exposure warn` | enable overexposure push alerts |

---

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
