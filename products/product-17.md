<div align="center">
<img src="../assets/icons/ic-17.svg" width="88">

# 17 · Tokenized-Gold Premium & Payout Health Monitor

**🪙 Crypto** &nbsp;·&nbsp; Demand `●●●○○` &nbsp;·&nbsp; Supply gap `○○○○○` &nbsp;·&nbsp; Effort `●○○`

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/paxg`, `/walletcheck ADDRESS [EXPECTED]` |
| 🌐 Dashboard | `/p/tokenized-gold` |

**Primary — 🤖 bot-led.** Depeg and poisoning checks are alerts; the premium chart is a page.

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

**Live.** PAXG comes from Binance (PAXGUSDT) and XAUT from Bitfinex (tXAUT:USD), both public. There is no free real-time LBMA spot, so the reference is Yahoo GC=F — the front futures contract, which carries a small basis over spot — and every readout says so; the PAXG−XAUT spread needs no reference and is the cleanest number on the page. The USDT peg is Kraken's public USDT/USD ticker, flagged beyond 0.3 %. A premium beyond 1 % is flagged. The five-minute checker samples all four numbers into a premium log, and the dashboard charts seven days of it. Reserve attestation and redemption terms are a dated facts table linking to each issuer's page, not a live feed. The wallet check is offline: chain detection (EVM, Tron, Bitcoin, Solana), the EIP-55 checksum on a mixed-case Ethereum address, and address poisoning — the address about to be paid shares its first and last four characters with the one from your history but is not the same address. Chain fees are typical published values, dated, to verify with the wallet.

## Commands

| Command | Does |
|:--|:--|
| `/paxg` | PAXG and XAUT premium vs GC=F, PAXG−XAUT spread, USDT peg, flags — plus each coin's own 30-day band, so the premium reads as cheap, normal or dear, and which coin is the cheaper way into gold right now |
| `/walletcheck ADDRESS [EXPECTED]` | chain, EIP-55 checksum, poisoning against the expected address, typical fees, peg status |

---

## Dashboard views

- Live readout: PAXG, XAUT, spot reference, USDT peg, with flags
- Premium band per coin — the 10th to 90th percentile of its own premium over thirty days, with a marker for where the premium sits right now, and the cheaper route named. Nothing is drawn under 100 samples
- Seven-day premium chart from the checker's log
- Dated facts table per token, in both languages: issuer, chain, attestation cadence, redemption terms, fees, issuer link
- Wallet health form: chain, checksum, poisoning verdict, typical transfer fees, payout rules

## Monetization

| Tier | Includes |
|:--|:--|
| **Free** | live premium and wallet check, unlimited |
| **PRO** | arbitrage alerts, continuous wallet monitoring, multi-chain fee routing |

## Data sources

- Binance public ticker (PAXGUSDT), Bitfinex public ticker (tXAUT:USD)
- Yahoo Finance GC=F as the spot reference (front futures; small basis)
- Kraken public ticker (USDTUSD) for the peg
- Issuer pages (Paxos, Tether) for attestation and redemption terms, dated in the table
- Typical chain fees, dated; no oracle

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
<sub>Status: <b>LIVE</b> &nbsp;·&nbsp; <a href="../README.md">← back to all 18 products</a></sub>

<sub>Educational research only. Not financial advice.</sub>
</div>
