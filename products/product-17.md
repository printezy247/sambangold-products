<div align="center">
<img src="../assets/icons/ic-17.svg" width="88">

# 17 · Tokenized-Gold Premium & Payout Health Monitor

**🪙 Crypto** &nbsp;·&nbsp; Demand `●●●○○` &nbsp;·&nbsp; Supply gap `○○○○○` &nbsp;·&nbsp; Effort `●○○`

</div>

---

## Platform

🤖 **Telegram-first** — `/paxg`, `/walletcheck`, depeg push. Public web premium chart alongside.

## Free tier

**Live premium readout and wallet safety check, unlimited.**

---

## Problem

- PAXG and XAUT drift from spot XAU, and nobody watches the premium. The drift is the arbitrage and also the risk.
- Separately, traders taking IB and prop payouts in USDT get hit by chain fees, depeg moments, and address-poisoning attacks — losses that have nothing to do with trading.

## Solution

1. Track tokenized-gold premium and discount against spot XAU, alongside redemption fees and reserve-attestation freshness (a stale attestation is the real tail risk).
2. Payout-wallet health check: current chain fee, stablecoin depeg watch, and address-poisoning detection on the paste target.
3. Push when premium crosses a threshold or a peg slips.

## Commands

| Command | Does |
|:--|:--|
| `/paxg` | current premium/discount vs spot XAU |
| `/walletcheck ADDRESS` | chain fee, depeg status, poisoning check |

---

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | live premium and wallet check, unlimited |
| **PRO** | arbitrage alerts, continuous wallet monitoring, multi-chain fee routing |

## Data sources

- PAXG/XAUT market prices
- Spot XAU reference
- Issuer attestation pages
- Chain fee oracles

---

## Demand vs supply

- **Demand** — ●●●○○ — small audience, but it is exactly the audience already using the other products.
- **Supply gap** — ○○○○○ — nothing connects tokenized gold to the payout workflow.
- **Build effort** — ●○○ — roughly 1 week. Data is public and cheap; the value is the framing.

## Build notes

- Keep it anchored to gold. This is not a general crypto product, and it should not drift into one.
- Address-poisoning check must be conservative — a false 'safe' here costs the user their payout.

---

<div align="center">
<sub>Status: <b>PROPOSED</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
