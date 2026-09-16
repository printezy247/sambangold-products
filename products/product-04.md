<div align="center">
<img src="../assets/icons/ic-04.svg" width="88">

# 4 · Telegram Bot Scam Detector

**🔒 Security** &nbsp;·&nbsp; Status `SHIPPED` &nbsp;·&nbsp; Primary 🤖 bot-led

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/audit @bot_username` |
| 🌐 Dashboard | `/p/bot-scam-detector` |

**Primary — 🤖 bot-led.** It audits Telegram bots, so it lives where its targets live.

## Free tier

**Unlimited /audit scans.**

---

## Problem

- Fake verification bots, malware links and fake airdrops rose sharply through 2025.
- A user has seconds to judge a bot, and the signals that matter are not visible in the bot's profile.

## Solution

Score a bot on private-key requests, unregulated broker pushes and missing audit links.

`/audit @bot_username [what the bot said]` checks the username itself (must end in `bot`, no lookalike character swaps, no fake-support words) and the pasted text against the shared red-flag rules — seed-phrase and wallet requests, claim/airdrop bait, fees to unlock. Every rule carries its own *why*, the score is 0–100 and the verdict is **HIGH RISK / CAUTION / LOW RISK**. Every scan is archived, so the dashboard shows history, a watchlist to re-scan and a public share page per scan. **Live.**

## Commands

| Command | Does |
|:--|:--|
| `/audit @bot_username [text]` | scam score, top findings, the 5-point checklist |

## Dashboard views

- Public register cross-reference — after a scan, whether this subject has been flagged before, and a link to its record at `/register`

- Paste form: username plus what the bot said; findings table with the flag, the reason and the matching snippet
- Scan history with the score breakdown per signal (signed in)
- Watchlist of bots to re-scan in one tap
- Public scam-score page per scan at `/p/bot-scam-detector/s/<id>`, forwardable

## Monetization

- **Free** — unlimited `/audit` scans and the scan history.
- **PRO** — daily auto-scan of subscribed channels plus a malware database.

No product is paywalled at the door. Paid tiers sell scale and automation only.

## Data sources

- The pasted text and the username — nothing is fetched from Telegram
- Shared rule table in `app/scan.py` (no paid API, no ML)

---

<div align="center">
<sub>Educational research only. Not financial advice. Verify every price with your broker.</sub>
</div>
