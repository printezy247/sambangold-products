<div align="center">
<img src="../assets/icons/ic-05.svg" width="88">

# 5 · Gold Seasonality Calendar

**🥇 Gold** &nbsp;·&nbsp; Status `SHIPPED` &nbsp;·&nbsp; Primary 🌐 dashboard-led

</div>

---

## Platform

🤖🌐 **Both.** Every product in this repo ships a Telegram half and a dashboard
half, on one Telegram account, with the same free tier on each.

| Half | This product |
|:--|:--|
| 🤖 Telegram | `/calendar`, `/calendar_alert` |
| 🌐 Dashboard | `/p/gold-calendar` |

**Primary — 🌐 dashboard-led.** The calendar is a page you scan; the bot is the push you cannot miss.

## Free tier

**Full calendar and PDF, no login.**

---

## Problem

- Gold has strong seasonal structure — Fed windows, CME holidays, jewelry demand cycles — and most traders trade straight through it.
- Spreads widen predictably around these windows, and that cost is avoidable.

## Solution

A monthly volatility and event calendar with the spread-risk windows marked.

## Commands

| Command | Does |
|:--|:--|
| `/calendar` | next three red USD events (MYT), next FOMC statement, next CME holiday, this month's seasonality, and your alert state — with a one-tap on/off button |
| `/calendar_alert` | toggle a push 30 minutes before every red USD event and FOMC statement |

## Dashboard views

- Month grid (MYT) with red USD events, FOMC statement days, CME closures and thin sessions; today outlined in gold; prev/next month
- PDF download of the current quarter — one page per month, events and seasonality, generated in-app
- Seasonality strip — average return and range per calendar month from ten years of `GC=F`, static long-run table as fallback
- Per-event history — the five-minute checker samples the spread and tags samples inside ±30 min of a red event; worst and mean per event vs the baseline median

## Monetization

- **Free** — full calendar, PDF download, and the event history.
- **PRO** — real-time alert bot with per-event lead time.

No product is paywalled at the door. Paid tiers sell scale and automation only.

## Data sources

- Forex Factory weekly JSON (`ff_calendar_thisweek` + `nextweek`) — red USD events, free, no key; last good copy kept when unreachable
- Federal Reserve FOMC schedule and CME Globex holidays — embedded for the year, so the grid reaches past the feed's two-week horizon
- Yahoo Finance `GC=F` monthly history — seasonality, cached a day
- The app's own spread log — what the spread did around each event

---

<div align="center">
<sub>Educational research only. Not financial advice. Verify every price with your broker.</sub>
</div>
