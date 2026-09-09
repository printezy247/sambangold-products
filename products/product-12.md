<div align="center">
<img src="../assets/icons/ic-12.svg" width="88">

# 12 · Live Gold Broker Comparator

**🥇 Gold IB** &nbsp;·&nbsp; Demand `●●●●○` &nbsp;·&nbsp; Supply gap `●●○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/goldspread`, `/goldspread 1.0 overnight` |
| 🌐 Dashboard | `/p/broker-comparator` |

**Primary — 🌐 dashboard-led.** The public table is the SEO asset; the bot drops the card straight into a group.

## Free tier

**Fully open. Public comparison table and bot command, no login.**

---

## Problem

- An IB has to justify which broker they route clients to, and 'trust me' is not a justification.
- Clients have no way to compare the numbers that actually cost them money: spread on XAUUSD, swap long and short, commission per lot, and real slippage.
- Broker marketing pages quote best-case spreads that do not survive a London open.

## Solution

1. Track live XAUUSD spread, swap long and short, commission, and observed slippage across a configured broker set.
2. Rank brokers on total round-trip cost for a stated lot size and holding period — overnight holds change the ranking entirely once swap is counted.
3. Render the ranking as a shareable card carrying the IB's own referral link.
4. The public web table is the top-of-funnel asset; the bot card is the distribution mechanism.

## Commands

| Command | Does |
|:--|:--|
| `/goldspread` | current ranked comparison card |
| `/goldspread 1.0 overnight` | cost ranking for a specific lot size and holding period |

---

## Dashboard views

- Public indexable comparison table — the SEO asset
- Cost calculator for a given lot size and holding period
- Referral-branded card generator

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | public table and bot command, fully open |
| **PRO** | white-label branded embeddable widget, custom broker set, historical spread charts |

## Data sources

- Broker price feeds or public spread pages
- Swap tables (broker published)
- Observed fill data where available

---

## Demand vs supply

- **Demand** — ●●●●○ — serves the IB and the client at the same time.
- **Supply gap** — ●●○○○ — comparison sites exist but are affiliate-farmed, stale, and not gold-specific.
- **Build effort** — ●●○ — roughly 2 weeks. Feed reliability is the whole problem; the presentation is easy.

## Build notes

- Label the data source and timestamp on every row. A comparison tool that cannot be audited becomes exactly the thing products #6 and #7 flag.
- Do not rank by referral payout. If the ranking is bought, the asset is worthless within a month.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
