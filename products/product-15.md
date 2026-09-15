<div align="center">
<img src="../assets/icons/ic-15.svg" width="88">

# 15 · Monte Carlo Challenge Simulator

**🏛 Prop firm** &nbsp;·&nbsp; Demand `●●●●○` &nbsp;·&nbsp; Supply gap `●●○○○` &nbsp;·&nbsp; Effort `●○○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/simulate WINRATE RR RISK%` |
| 🌐 Dashboard | `/p/monte-carlo-sim` |

**Primary — 🌐 dashboard-led.** The fan chart and the PDF need a page; the bot returns the summary card.

## Free tier

**1,000 simulations per run, unlimited runs.**

---

## Problem

- Product #3 returns a static expected value, which hides the thing that actually kills accounts: **path risk**.
- A genuinely profitable edge still breaches a trailing drawdown on an unlucky sequence.
- Traders therefore underestimate both failure probability and the total cost of retrying until they pass.

## Solution

1. Simulate N equity paths from the trader's own win rate, reward-to-risk, and variance.
2. Evaluate each path against the *real* rule set: daily drawdown, trailing drawdown, minimum trading days, consistency rule.
3. Return realistic pass probability, the distribution of outcomes, and the **expected total cost-to-funded** across retries — the number that actually matters.
4. Fan chart shows where the breaches cluster, which is usually earlier than traders expect.

## Commands

| Command | Does |
|:--|:--|
| `/simulate WINRATE RR RISK%` | summary card with pass probability and expected cost |

---

## Dashboard views

- Equity-path fan chart across the simulated runs
- Rule-pack picker — daily DD, trailing DD, min days, consistency
- PDF export of the run

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | 1,000 sims per run, unlimited runs |
| **PRO** | 100,000 sims, full rule-pack library, PDF export, side-by-side firm comparison |

## Data sources

- User-supplied edge parameters
- Per-firm rule packs (shared with #14)

---

## Demand vs supply

- **Demand** — ●●●●○ — directly answers 'should I pay this fee'.
- **Supply gap** — ●●○○○ — generic Monte Carlo tools exist; none encode prop rule sets.
- **Build effort** — ●○○ — roughly 1 week. Pure computation, no live feeds, no auth complexity.

## Build notes

- Reuse the rule packs from #14. One curated source, two products.
- Show the assumption set on the output. A simulator that hides its inputs is a marketing tool, not an analysis tool.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
