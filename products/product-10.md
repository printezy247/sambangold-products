<div align="center">
<img src="../assets/icons/ic-10.svg" width="88">

# 10 · Rebate Reconciliation Auditor

**🥇 Gold IB** &nbsp;·&nbsp; Demand `●●●●●` &nbsp;·&nbsp; Supply gap `○○○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/rebateaudit`, `/rebatestatus` |
| 🌐 Dashboard | `/p/rebate-auditor` |

**Primary — 🌐 dashboard-led.** CSV upload, a sortable diff, a dispute PDF; the bot pings when a run finishes.

## Free tier

**One broker, one month, full shortfall report. No card, no account required.**

---

## Problem

- Brokers underpay IB rebates. Sometimes it is a dropped account, sometimes a silent per-lot rate change, sometimes a symbol excluded from the schedule without notice.
- Almost no IB checks, because reconciling a few hundred accounts by hand against a monthly statement is miserable work.
- The result is a revenue leak nobody can size, and no evidence to dispute with.

## Solution

1. Upload two files: the broker's rebate statement CSV and the client trade log.
2. Recompute expected rebate as `lots x rate` per symbol and per account tier, using the IB's own tier schedule.
3. Diff expected against paid. Surface three failure classes: **shortfall** (paid less than owed), **missing account** (traded but absent from the statement), **silent rate change** (effective rate differs from the schedule).
4. Export a dispute-ready PDF with the per-account arithmetic shown.

## Commands

| Command | Does |
|:--|:--|
| `/rebateaudit` | run the last uploaded reconciliation and return the summary |
| `/rebatestatus` | show shortfall total for the current period |

---

## Dashboard views

- CSV upload for the broker statement and the client trade log
- Sortable diff table — shortfall, missing account, silent rate change
- Dispute PDF with the per-account arithmetic shown

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | 1 broker, 1 month, full report |
| **PRO** | multi-broker, monthly auto-reconciliation, dispute-letter generator, history and trend |

## Data sources

- Broker rebate statement (CSV export)
- Client trade log (MT4/MT5 or broker portal export)
- IB tier schedule (entered once)

---

## Demand vs supply

- **Demand** — ●●●●● — every IB suspects underpayment and none can prove it.
- **Supply gap** — ○○○○○ — no retail-facing tool exists.
- **Build effort** — ●●○ — roughly 2 weeks. Mostly CSV normalisation across broker formats; the arithmetic is simple.

## Build notes

- Broker CSV formats vary wildly. Ship with adapters for the two or three brokers the user actually routes to, plus a column-mapping UI for the rest.
- Never store client PII beyond the account identifier needed to reconcile.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
