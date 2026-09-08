<div align="center">
<img src="../assets/icons/ic-14.svg" width="88">

# 14 · Drawdown Sentinel (Rule Guardian)

**🏛 Prop firm** &nbsp;·&nbsp; Demand `●●●●●` &nbsp;·&nbsp; Supply gap `●○○○○` &nbsp;·&nbsp; Effort `●●●`

</div>

---

## Platform

🤖 **Telegram-first** — the entire value is a push arriving seconds before the line is crossed. The web side only links accounts and selects rule packs.

## Free tier

**1 account on 1 firm, unlimited breach alerts.**

---

## Problem

- Most challenge failures are **rule breaches, not bad strategy**.
- A daily-loss line crossed by one trade. An entry inside a news blackout. A lot size over cap. A trailing drawdown that moved while the trader was not looking.
- The trader usually had the edge. They lost the account to a rule they could have avoided with thirty seconds of warning.

## Solution

1. Real-time monitor of daily loss, trailing drawdown, news blackout windows, maximum lot, and consistency rules.
2. Driven by **per-firm rule packs**, because every firm defines trailing drawdown differently — some on balance, some on equity, some on high-water mark.
3. Alert at a configurable distance *before* the line, not at it. A breach alert is a post-mortem; a proximity alert is a save.
4. Optional flatten webhook for traders who want the guard automated.

## Commands

| Command | Does |
|:--|:--|
| `/sentinel link` | link a trading account |
| `/sentinel status` | distance to every active rule line |
| `/sentinel firm NAME` | load a firm's rule pack |

---

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | 1 account, 1 firm, unlimited breach alerts |
| **PRO** | multi-account, auto-flatten webhook, custom rule packs, breach post-mortems |

## Data sources

- Account equity and balance feed (broker or firm dashboard)
- Economic calendar for news windows
- Per-firm rule packs (curated)

---

## Demand vs supply

- **Demand** — ●●●●● — the failure mode this prevents is the single most common way challenges die.
- **Supply gap** — ●○○○○ — a few MT4/MT5 EAs exist, platform-locked and opaque.
- **Build effort** — ●●● — roughly 3-4 weeks. Latency and correctness are both hard requirements; a late alert is worse than none.

## Build notes

- Rule packs must be versioned and dated. Firms change rules without notice, and a stale pack gives false confidence — which is worse than no tool.
- State plainly that the sentinel is a monitor, not a guarantee. Feed lag exists and must be disclosed.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
