<div align="center">
<img src="../assets/icons/ic-11.svg" width="88">

# 11 · IB Client Churn & Blow-Up Radar

**🥇 Gold IB** &nbsp;·&nbsp; Demand `●●●●○` &nbsp;·&nbsp; Supply gap `○○○○○` &nbsp;·&nbsp; Effort `●●●`

</div>

---

## Platform

🤖🌐 **Both** — web dashboard for the whole book, Telegram push the moment a client crosses a risk threshold.

## Free tier

**10 tracked clients, unlimited alerts.**

---

## Problem

- IB revenue dies when the client book dies, and it dies quietly.
- By the time flat volume shows up in a monthly statement, the client has already stopped trading or already blown the account.
- There is a window — usually two to four weeks — where an intervention still works, and no tool surfaces it.

## Solution

1. Score every referred client on four signals: declining lot volume against their own baseline, rising margin utilisation, martingale or revenge-trade patterns (position size escalating after losses), and dormancy drift (widening gaps between sessions).
2. Combine into a 30-day churn or blow-up probability per client.
3. Rank the book by revenue at risk, not by probability alone — a high-volume client at 40% matters more than a dormant one at 90%.
4. Attach a suggested intervention to each flag.

## Commands

| Command | Does |
|:--|:--|
| `/ibchurn` | top clients at risk right now |
| `/ibchurn @client` | single client detail and signal breakdown |

---

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | 10 tracked clients, unlimited alerts |
| **PRO** | unlimited clients, auto-drafted nurture messages, revenue-at-risk forecasting |

## Data sources

- Client trade log / volume feed
- Account equity and margin snapshots
- Session timestamps

---

## Demand vs supply

- **Demand** — ●●●●○ — direct, measurable revenue impact for the IB.
- **Supply gap** — ○○○○○ — CRMs do generic churn; none understand lots, margin, or martingale.
- **Build effort** — ●●● — roughly 3-4 weeks. The scoring model needs tuning against real book data before it is trustworthy.

## Build notes

- Start with rule-based thresholds, not ML. An IB will not trust a black box scoring their income.
- Interventions must be suggestions the IB sends, never automated messages to clients — that is a compliance line.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
