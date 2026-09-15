<div align="center">
<img src="../assets/icons/ic-13.svg" width="88">

# 13 · IB Link Attribution & Funnel Tracker

**🥇 Gold IB** &nbsp;·&nbsp; Demand `●●●○○` &nbsp;·&nbsp; Supply gap `●○○○○` &nbsp;·&nbsp; Effort `●●○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/newlink CHANNEL`, `/funnel` |
| 🌐 Dashboard | `/p/link-attribution` |

**Primary — 🌐 dashboard-led.** Link management and a funnel need a page; the bot mints links and reports daily.

## Free tier

**3 tracked links, full funnel view.**

---

## Problem

- Broker portals report that a signup happened. They do not report where it came from.
- An IB posting across a channel, a group, YouTube, and a landing page cannot tell which one earned the client.
- Without attribution, spend and effort go to whatever felt busiest, not whatever converted.

## Solution

1. Per-channel short links that carry a campaign tag through to the broker signup.
2. Track the full funnel: post → click → signup → first deposit → first lot. The last two are the only ones that pay.
3. Cohort the results by channel and by content piece, so the IB learns which *kind* of post converts, not just which platform.
4. Daily digest with the deltas.

**Live.** A tracked link is a short code at `/l/<code>` that redirects to the IB's referral URL and counts the click. Broker portals do not call back, so the later stages — signup, first deposit, first lot — are logged by the IB on the dashboard, one at a time or by pasting the portal report (channel, stage, count). The funnel per channel over 7, 30 or 90 days shows clicks → signups → deposits → first lots with the conversion between each, ranked by first lots. `/newlink` defaults the destination to the IB link saved in Broker Comparator. Three links on the free tier.

## Commands

| Command | Does |
|:--|:--|
| `/newlink CHANNEL [URL]` | mint a tracked short link (URL defaults to the saved IB link) |
| `/funnel [7\|30\|90]` | clicks, signups, deposits, first lots per channel over the range |

---

## Dashboard views

- Link manager: one short link per channel, the destination, delete
- Funnel tiles and the channel comparison table over 7 / 30 / 90 days, with signup/click, deposit/signup, lot/deposit and click→lot rates
- Stage logging: a form per channel and stage, or a pasted portal report (CSV)
- Redirect endpoint `/l/<code>` that counts every click

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | 3 tracked links, full funnel view |
| **PRO** | unlimited links, cohort LTV, payback period, UTM auto-tagging |

## Data sources

- Click events (own redirector)
- Broker signup/deposit confirmations where the portal exposes them
- Manual reconciliation fallback

---

## Demand vs supply

- **Demand** — ●●●○○ — obvious once an IB has more than two channels.
- **Supply gap** — ●○○○○ — generic link shorteners exist, but none map to a broker funnel.
- **Build effort** — ●●○ — roughly 2 weeks. The redirector is trivial; matching signups back to clicks is the real work.

## Build notes

- Where the broker portal exposes no callback, fall back to a claimed-signup form plus periodic manual reconciliation. Partial attribution beats none.
- Store no more than the campaign tag and a hashed identifier. This must not become a tracking product.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
