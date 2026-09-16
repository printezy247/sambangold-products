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

**Live.** Headers are matched loosely (account/login/client, symbol/instrument, lots/volume, rebate/paid), delimiters are sniffed, and the rate card takes a default rate, per-symbol overrides (`XAUUSD=8`) and volume tiers (`100:7.5, 500:8`) applied on the account's month total. Each line is classified as shortfall, missing account, silent rate change (same lots, lower implied rate), excluded symbol (traded, paid nothing), overpaid, or exact. A sample dataset loads with one click. Runs are archived per account; the bot reads the last one back.

## Commands

| Command | Does |
|:--|:--|
| `/rebateaudit` | summary of your last reconciliation, or `/rebateaudit LOTS RATE PAID` for a one-line check |
| `/rebatestatus` | show shortfall total for the current period |

---

## Dashboard views

- CSV paste or upload for the broker statement and the client trade log; rate card with per-symbol rates and volume tiers; sample data loader
- Sortable diff table — shortfall, missing account, silent rate change, excluded symbol, overpaid, exact — with the implied rate per line
- Dispute PDF with the per-account arithmetic shown, downloadable per run
- Run history per account (signed in)

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
<sub>Status: <b>SHIPPED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
