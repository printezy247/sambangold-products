<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-banner-light.svg">
  <img src="assets/hero-banner-dark.svg" alt="SAMBANGGOLD — 18 gold tools, a Telegram bot and a dashboard for every one" width="100%">
</picture>

<br><br>

<img src="assets/badges-strip.svg" alt="3 live · 9 shipped · 9 proposed · Telegram + dashboard · free tier on all 18 · Python 3.12 / Flask · MIT">

<br><br>

<a href="#-the-vault--9-shipped"><img src="assets/nav/vault.svg" alt="The Vault — 9 shipped" height="38"></a>
<a href="#-vault-ii--9-proposed"><img src="assets/nav/vault2.svg" alt="Vault II — 9 proposed" height="38"></a>
<a href="#-platforms--free-tiers"><img src="assets/nav/platforms.svg" alt="Platforms" height="38"></a>
<a href="#-roadmap"><img src="assets/nav/roadmap.svg" alt="Roadmap" height="38"></a>
<a href="#-quickstart"><img src="assets/nav/quickstart.svg" alt="Quickstart" height="38"></a>

<br><br>

<img src="assets/stack-ticker.svg" alt="Python 3.12 · Flask · Telegram Bot API · Binance · Yahoo Finance · SQLite · Fly.io · GitHub Actions" width="100%">

</div>

<br>

> [!IMPORTANT]
> **Educational research only. Not financial advice.** Every price, spread, and payout figure is indicative — verify with your broker before acting. Nothing here is a solicitation to trade, and no product guarantees a result.

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## ⚡ What This Is

Eighteen small, sharp tools for people who make money **around** trading, not only from it — introducing brokers, prop-challenge traders, signal buyers, and gold watchers.

Every product follows the same shape: **one job, a Telegram command *and* a dashboard page, a free tier that needs no card, and a paid tier that only sells time and scale.** One Telegram account signs you in to both halves. Nine are shipped. Nine are proposed, weighted hard toward the gold-IB business, which is where the demand is loudest and the supply is thinnest.

```mermaid
flowchart LR
    U([👤 Trader / IB]) -->|slash command| TG[🤖 Telegram Bot]
    U -->|browser| WEB[🌐 Flask Dashboard]
    TG --> AUTH{{🔑 One Telegram identity}}
    WEB --> AUTH
    AUTH --> REG[[📇 Product Registry<br/>18 products · bot half + dashboard half]]
    REG --> CORE{{⚙️ Core Engine}}
    CORE --> MD[(📈 Market Data<br/>Binance · Yahoo · Broker feeds)]
    CORE --> RULES[(📋 Rule Packs<br/>Prop firms · Brokers)]
    CORE --> LEDGER[(🧾 Rebate + Trade Ledger)]
    CORE --> OUT[📤 Verdict · Alert · PDF · Card]
    OUT --> TG
    OUT --> WEB
    REG -.free tier.-> FREE[✅ No card required]
    REG -.pro tier.-> PAY[💳 Stripe / USDT]
```

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 🏆 The Vault — 9 Shipped

<div align="center">

| | | |
|:--:|:--:|:--:|
| <img src="assets/icons/ic-01.svg" width="72"><br>**Gold Watch Alert**<br>🤖🌐 Both | <img src="assets/icons/ic-02.svg" width="72"><br>**XAUUSD Verifier**<br>🤖🌐 Both | <img src="assets/icons/ic-03.svg" width="72"><br>**Prop Calculator**<br>🤖🌐 Both |
| <img src="assets/icons/ic-04.svg" width="72"><br>**Scam Detector**<br>🤖🌐 Both | <img src="assets/icons/ic-05.svg" width="72"><br>**Gold Calendar**<br>🤖🌐 Both | <img src="assets/icons/ic-06.svg" width="72"><br>**Copy-Trade Audit**<br>🤖🌐 Both |
| <img src="assets/icons/ic-07.svg" width="72"><br>**Red-Flag Scanner**<br>🤖🌐 Both | <img src="assets/icons/ic-08.svg" width="72"><br>**IB Revenue Calc**<br>🤖🌐 Both | <img src="assets/icons/ic-09.svg" width="72"><br>**Influencer Audit**<br>🤖🌐 Both |

</div>

<br>

<details>
<summary><b>🥇 #1 · Gold Watch Alert Bot</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free, unlimited</i></summary>

<br>

**Problem** — Traders miss gold entries to spread and slippage. Most Telegram gold channels are scams.

**Solution** — `/watch XAUUSD` returns live bid, ask and spread with spread-widened entry and stop levels; `/watch XAUUSD above 2450` arms an alert that fires on the **ask** (below fires on the **bid**), so it never triggers on a price the market did not offer. Binance `PAXGUSDT` primary, Yahoo `GC=F` fallback, checked every five minutes by a free GitHub Actions cron. **Free, unlimited.**

**Platform** — 🤖🌐 **Both.** 🤖 `/watch XAUUSD`, `/watch XAUUSD above 2450`, `/watch list` &nbsp;·&nbsp; 🌐 `/p/gold-watch` — Live bid/ask/spread · Alert history · Threshold editor for each armed alert · CSV export of triggers for journalling. **Live.**

**Primary** — 🤖 bot-led. One command in, one alert out — the dashboard keeps the history a chat log cannot.

**Free tier** — `/watch` on gold, unlimited, no account.

**Upsell** — `/autopilot` plus DCF/COT fundamentals as PRO.

</details>

<details>
<summary><b>🥇 #2 · XAUUSD Signal Verifier</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free single verify</i></summary>

<br>

**Problem** — Gold signal sellers post fabricated MT4 screenshots with cherry-picked entries.

**Solution** — `/verify GOLD PRICE [DATE] [TIME]` pulls Binance `PAXGUSDT` tick history and tests the claimed fill. Returns **REAL / BORDERLINE / IMPOSSIBLE / UNVERIFIED** with the window range, the nearest candle and the gap percentage; the dashboard adds batch verify, the verdict archive and a public verdict page per check. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/verify GOLD PRICE` &nbsp;·&nbsp; 🌐 `/p/signal-verifier` — Verdict archive with the tick window that produced each call · Batch verify · Shareable public verdict link for posting back into a group.

**Primary** — 🤖 bot-led. Verification belongs in the group where the fake was posted.

**Free tier** — one verify per request, unlimited requests.

**Upsell** — PRO batch CSV upload and weekly audit reports.

</details>

<details>
<summary><b>🏛 #3 · Prop Firm Challenge Calculator</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>full calculator free</i></summary>

<br>

**Problem** — Traders pay $500–$5,000 in challenge fees with no expected-value estimate, and roughly 90% fail. Hidden rules sit buried in the T&Cs.

**Solution** — `/propcalc FEE SIZE PASS%` returns EV, ROI and the breakeven pass rate; the dashboard adds the full model, an eleven-rule red/yellow scan of pasted T&Cs, and saved firm comparisons. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/propcalc FEE SIZE PASS%` &nbsp;·&nbsp; 🌐 `/p/prop-calculator` — Full calculator with the long T&C paste box · Rule-scan report, red and yellow flags itemised · Saved comparisons across firms.

**Primary** — 🌐 dashboard-led. The long T&C paste needs a page; the bot answers the quick yes-or-no.

**Free tier** — full calculator and bot command, no limit.

**Upsell** — premium PDF audit and automated forecast.

</details>

<details>
<summary><b>🔒 #4 · Telegram Bot Scam Detector</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free scans</i></summary>

<br>

**Problem** — Fake verification bots, malware links, and fake airdrops rose sharply through 2025.

**Solution** — `/audit @bot_username` checks for private-key requests, unregulated broker pushes, and missing audit links. Returns a **SCAM SCORE** and a checklist; the dashboard archives every scan, keeps a watchlist and gives each scan a public share page. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/audit @bot_username` &nbsp;·&nbsp; 🌐 `/p/bot-scam-detector` — Scan history with the score breakdown per signal · Watchlist of bots to re-scan · Public scam-score page per audited bot.

**Primary** — 🤖 bot-led. It audits Telegram bots, so it lives where its targets live.

**Free tier** — unlimited `/audit` scans.

**Upsell** — PRO daily auto-scan of subscribed channels plus a malware database.

</details>

<details>
<summary><b>🥇 #5 · Gold Seasonality Calendar</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>calendar + PDF free</i></summary>

<br>

**Problem** — Traders ignore gold seasonality — Fed windows, CME holidays, jewelry cycles — and the spread-widening events around them.

**Solution** — `/calendar` returns the next red USD events, the next FOMC and CME holiday, and this month's seasonality; `/calendar_alert` pushes 30 minutes before each. The dashboard adds the month grid, a quarter PDF, the 12-month seasonality strip, and a measured per-event spread history. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/calendar`, `/calendar_alert` &nbsp;·&nbsp; 🌐 `/p/gold-calendar` — Month grid of volatility patterns and Fed release windows · PDF download of the current quarter · Per-event history.

**Primary** — 🌐 dashboard-led. The calendar is a page you scan; the bot is the push you cannot miss.

**Free tier** — full calendar and PDF, no login.

**Upsell** — PRO real-time alert bot.

</details>

<details>
<summary><b>🔒 #6 · Copy-Trade Safety Audit</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>5 free audits</i></summary>

<br>

**Problem** — Influencers push unregulated copy-trading; users lose capital to hidden spreads and blowouts.

**Solution** — `/copyaudit BROKER` checks regulation (SEC/FCA/ASIC links) and negative-balance protection, and prices the hidden spread cost. Returns **HIGH RISK / CAUTION / LOW RISK** with the regulator registers to check and the spread cost per year. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/copyaudit BROKER` &nbsp;·&nbsp; 🌐 `/p/copy-trade-audit` — Audit history with the regulator links that were checked · Side-by-side broker comparison · Hidden-cost model.

**Primary** — 🤖 bot-led. It has to run at the moment someone is being pitched.

**Free tier** — 5 audits.

**Upsell** — PRO unlimited plus a weekly portfolio risk report.

</details>

<details>
<summary><b>💱 #7 · Forex Signal Red-Flag Scanner</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free text scan</i></summary>

<br>

**Problem** — Signal sellers claim "100% accuracy", delete losing trades, flood fake reviews, and charge $30–$300 a month.

**Solution** — Web scanner plus `/scan TEXT`. NLP flags "guaranteed", "no risk", "VIP spots left", and checks for verified audit links (MyFXBook / FX Blue). Every flag carries its reason; the dashboard keeps history per seller. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/scan TEXT` &nbsp;·&nbsp; 🌐 `/p/red-flag-scanner` — Scanner with the full pitch pasted in, flags highlighted inline · Scan history per seller or channel · Weekly scorecard for a channel you follow.

**Primary** — 🤖 bot-led. Pitches arrive in chat, so the scan starts there.

**Free tier** — unlimited text scans.

**Upsell** — PRO full group auto-scan and a weekly scorecard.

</details>

<details>
<summary><b>🥇 #8 · IB Affiliate Revenue Calculator</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free calculator</i></summary>

<br>

**Problem** — IB affiliates face opaque payout rules and compliance overhead, and referred clients complain about buggy platforms and slow withdrawals.

**Solution** — `/ibcalc LOTS RATE [CLIENTS] [CLAWBACK%]` returns net monthly and annual rebate revenue; the dashboard adds compliance cost, payout threshold and hold period, a 12-month payout timeline showing when the first cash lands, a downloadable compliance checklist and saved broker scenarios. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/ibcalc LOTS RATE [CLIENTS] [CLAWBACK%]` &nbsp;·&nbsp; 🌐 `/p/ib-revenue-calculator` — Multi-field revenue model with the payout timeline · Downloadable compliance checklist · Saved scenarios across brokers.

**Primary** — 🌐 dashboard-led. A multi-field model and a document download; the bot gives the quick estimate.

**Free tier** — full calculator and checklist.

**Upsell** — PRO automated monthly forecast and audit template.

</details>

<details>
<summary><b>🔒 #9 · Influencer Trading Scam Audit</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>free audit + template</i></summary>

<br>

**Problem** — Billions are lost to social-media investment scams each year, and a large share of short-form "financial advice" is misleading.

**Solution** — `/influencer @handle` demands audited trading history rather than screenshots, flags rented luxury props, and checks unregulated broker promotions. Ships a free **loss report template** for FTC / CFTC / IC3 / SC Malaysia / BNM, generated on the dashboard. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/influencer @handle` &nbsp;·&nbsp; 🌐 `/p/influencer-audit` — Audit archive, shareable per handle · Loss-report template generator for FTC / CFTC / IC3 · Broker-promotion trail for the accounts you have audited.

**Primary** — 🤖 bot-led. Viral by construction — the audit gets forwarded into the group that shared the influencer.

**Free tier** — unlimited audits plus the loss-report template.

**Upsell** — PRO batch audit and an automated scam-alert channel.

</details>

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 🔮 Vault II — 9 Proposed

The shipped nine are almost all **defensive** — auditors, verifiers, red-flag scanners — plus two static calculators. Nothing yet serves an introducing broker's *actual daily operations*. Vault II fixes that, weighted **4 gold IB / 2 prop / 1 forex / 1 crypto / 1 stocks**.

Scored on what matters: how badly people want it, versus how little exists today.

<div align="center">

| | # | Product | Vertical | Platform | Free tier | Demand | Supply gap | Effort |
|:--:|:--|:--|:--|:--|:--|:--|:--|:--|
| <img src="assets/icons/ic-10.svg" width="52"> | **10** | Rebate Reconciliation Auditor | 🥇 Gold IB | 🤖🌐 Both | 1 broker · 1 month | `●●●●●` | `○○○○○` | ●●○ |
| <img src="assets/icons/ic-11.svg" width="52"> | **11** | IB Client Churn & Blow-Up Radar | 🥇 Gold IB | 🤖🌐 Both | 10 clients | `●●●●○` | `○○○○○` | ●●● |
| <img src="assets/icons/ic-12.svg" width="52"> | **12** | Live Gold Broker Comparator | 🥇 Gold IB | 🤖🌐 Both | fully open | `●●●●○` | `●●○○○` | ●●○ |
| <img src="assets/icons/ic-13.svg" width="52"> | **13** | IB Link Attribution Tracker | 🥇 Gold IB | 🤖🌐 Both | 3 links | `●●●○○` | `●○○○○` | ●●○ |
| <img src="assets/icons/ic-14.svg" width="52"> | **14** | Drawdown Sentinel | 🏛 Prop | 🤖🌐 Both | 1 account · 1 firm | `●●●●●` | `●○○○○` | ●●● |
| <img src="assets/icons/ic-15.svg" width="52"> | **15** | Monte Carlo Challenge Sim | 🏛 Prop | 🤖🌐 Both | 1,000 sims | `●●●●○` | `●●○○○` | ●○○ |
| <img src="assets/icons/ic-16.svg" width="52"> | **16** | Correlation & Overexposure | 💱 Forex | 🤖🌐 Both | snapshots | `●●●●○` | `●●○○○` | ●●○ |
| <img src="assets/icons/ic-17.svg" width="52"> | **17** | Tokenized-Gold Premium Monitor | 🪙 Crypto | 🤖🌐 Both | unlimited | `●●●○○` | `○○○○○` | ●○○ |
| <img src="assets/icons/ic-18.svg" width="52"> | **18** | Miner–Bullion Divergence Screener | 📈 Stocks | 🤖🌐 Both | weekly screen | `●●●○○` | `●○○○○` | ●●○ |

<sub>`●` demand = how loudly it is asked for &nbsp;·&nbsp; `○` supply gap = how little exists (more `○` = emptier market) &nbsp;·&nbsp; effort = build weeks</sub>

</div>

<br>

<details>
<summary><b>🥇 #10 · Rebate Reconciliation Auditor</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <b>the biggest gap in the set</b></summary>

<br>

**Problem** — Brokers underpay IB rebates and quietly change per-lot rates. Almost no IB reconciles, because doing it by hand across a few hundred accounts is miserable.

**Solution** — Upload the broker rebate statement CSV and the client trade log. Recompute `lots × rate` per symbol and account tier, diff it against what was actually paid, and flag shortfalls, missing accounts, silent rate changes and excluded symbols; download the dispute PDF. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/rebateaudit`, `/rebatestatus` &nbsp;·&nbsp; 🌐 `/p/rebate-auditor` — CSV upload for the broker statement and the client trade log · Sortable diff table · Dispute PDF with the per-account arithmetic shown.

**Primary** — 🌐 dashboard-led. CSV upload, a sortable diff, a dispute PDF; the bot pings when a run finishes.

**Free tier** — one broker, one month, full shortfall report. No card.

**Upsell** — multi-broker monthly auto-reconciliation and a dispute-letter generator.

**Data** — broker rebate statement, trade log export, IB tier schedule.

📄 [Full spec →](products/product-10.md)

</details>

<details>
<summary><b>🥇 #11 · IB Client Churn & Blow-Up Radar</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — IB revenue dies when the client book dies, and it dies quietly. By the time volume shows up flat in the monthly statement, the client is already gone.

**Solution** — Score every referred client on declining lot volume, rising margin utilisation, martingale and revenge-trade patterns, and dormancy drift. Output a 30-day churn or blow-up probability with a suggested intervention, ranked by revenue at risk; the dashboard keeps the intervention log. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/ibchurn`, `/ibchurn ACCOUNT` &nbsp;·&nbsp; 🌐 `/p/churn-radar` — Book overview ranked by 30-day blow-up probability · Per-client signal breakdown and history · Intervention log.

**Primary** — 🌐 dashboard-led. The book is a table you study; the bot warns the moment a client crosses a line.

**Free tier** — 10 tracked clients, unlimited alerts.

**Upsell** — unlimited clients and auto-drafted nurture messages.

📄 [Full spec →](products/product-11.md)

</details>

<details>
<summary><b>🥇 #12 · Live Gold Broker Comparator</b> &nbsp;—&nbsp; 🤖🌐 Both &nbsp;·&nbsp; <i>doubles as the IB's lead magnet</i></summary>

<br>

**Problem** — An IB has to justify which broker they route clients to, and clients have no way to compare the numbers that actually cost them money.

**Solution** — Live XAUUSD spread, swap long and short, commission, and observed slippage across a broker set, rendered as a ranked shareable card carrying the IB's referral link. Published values seed the table; community-measured spreads replace them once three reports are in. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/goldspread`, `/goldspread 1.0 overnight` &nbsp;·&nbsp; 🌐 `/p/broker-comparator` — Public indexable comparison table · Cost calculator for a given lot size and holding period · Referral-branded card generator.

**Primary** — 🌐 dashboard-led. The public table is the SEO asset; the bot drops the card straight into a group.

**Free tier** — public comparison table and bot command, fully open.

**Upsell** — white-label branded embeddable widget.

📄 [Full spec →](products/product-12.md)

</details>

<details>
<summary><b>🥇 #13 · IB Link Attribution & Funnel Tracker</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — Broker portals report signups but never say where they came from, so an IB cannot tell which content earned the client.

**Solution** — Per-channel short links tracking post → click → signup → first deposit → first lot, closing the attribution hole the broker leaves open. Short links redirect and count; later stages are logged from the portal report. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/newlink CHANNEL`, `/funnel` &nbsp;·&nbsp; 🌐 `/p/link-attribution` — Link manager with per-channel tags · Funnel dashboard from click through to first lot · Channel comparison over a date range.

**Primary** — 🌐 dashboard-led. Link management and a funnel need a page; the bot mints links and reports daily.

**Free tier** — 3 tracked links, full funnel view.

**Upsell** — unlimited links, cohort LTV, and payback period.

📄 [Full spec →](products/product-13.md)

</details>

<details>
<summary><b>🏛 #14 · Drawdown Sentinel (Rule Guardian)</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — Most challenge failures are **rule breaches, not bad strategy** — a daily-loss line crossed by one trade, a news-window entry, a lot size over cap.

**Solution** — Real-time monitor of daily loss, trailing drawdown, news blackout windows, max lot, and consistency rules, driven by per-firm rule packs. It alerts *before* the breach, with an optional flatten webhook. The account reports equity by bot, form or a per-account ping URL; warnings push to Telegram once per transition. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/sentinel link`, `/sentinel status`, `/sentinel firm NAME` &nbsp;·&nbsp; 🌐 `/p/drawdown-sentinel` — Account linking and rule-pack selection · Live distance-to-breach gauges per rule · Breach history and near-miss log.

**Primary** — 🤖 bot-led. The entire value is a push arriving seconds before the line is crossed.

**Free tier** — 1 account on 1 firm, unlimited breach alerts.

**Upsell** — multi-account monitoring and auto-flatten.

📄 [Full spec →](products/product-14.md)

</details>

<details>
<summary><b>🏛 #15 · Monte Carlo Challenge Simulator</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — Product #3 gives a static EV number, which hides the thing that actually kills accounts: path risk. A profitable edge still breaches a trailing drawdown on a bad sequence.

**Solution** — Simulate N equity paths against the *real* rule set — daily DD, trailing DD, minimum trading days, consistency rule — from the trader's own win rate, RR, and variance. Return a realistic pass probability and the expected total cost-to-funded across retries. Fan chart, failure share per rule, PDF per run. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/simulate WINRATE RR RISK%` &nbsp;·&nbsp; 🌐 `/p/monte-carlo-sim` — Equity-path fan chart across the simulated runs · Rule-pack picker · PDF export of the run.

**Primary** — 🌐 dashboard-led. The fan chart and the PDF need a page; the bot returns the summary card.

**Free tier** — 1,000 simulations per run, unlimited runs.

**Upsell** — 100k sims, full rule-pack library, PDF export.

📄 [Full spec →](products/product-15.md)

</details>

<details>
<summary><b>💱 #16 · Correlation & Overexposure Monitor</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — "Five open trades" is often one leveraged bet. XAUUSD, silver, DXY, USDJPY, and miners move together, and the account finds out during the drawdown.

**Solution** — Cluster open positions into a single true-risk figure, and surface swap-rollover and session-spread cost alongside it. Structural currency-leg clustering, a heat-map, and push warnings. **Live.**

**Platform** — 🤖🌐 **Both.** 🤖 `/exposure`, `/exposure warn` &nbsp;·&nbsp; 🌐 `/p/exposure-monitor` — Correlation heat-map of the open book · True-risk figure with the cluster decomposition · Rollover and session-spread cost projection.

**Primary** — 🤖 bot-led. Overexposure is a warning you need immediately; the heat-map explains it afterwards.

**Free tier** — on-demand snapshots, unlimited.

**Upsell** — live monitoring with prop-rule-aware exposure caps.

📄 [Full spec →](products/product-16.md)

</details>

<details>
<summary><b>🪙 #17 · Tokenized-Gold Premium & Payout Health Monitor</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — PAXG and XAUT drift from spot XAU, and nobody watches the premium. Separately, traders taking IB and prop payouts in USDT get hit by chain fees, depeg moments, and address-poisoning attacks.

**Solution** — **Live.** PAXG (Binance) and XAUT (Bitfinex) premium against Yahoo GC=F, the PAXG−XAUT spread, and the USDT peg from Kraken, sampled every five minutes into a seven-day chart. A dated facts table per token for attestation and redemption. An offline wallet check: chain, EIP-55 checksum, address poisoning against the address you expected, typical chain fees.

**Platform** — 🤖🌐 **Both.** 🤖 `/paxg`, `/walletcheck ADDRESS [EXPECTED]` &nbsp;·&nbsp; 🌐 `/p/tokenized-gold` — Live readout and seven-day premium chart · Dated attestation and redemption table per token · Wallet health form.

**Primary** — 🤖 bot-led. Depeg and poisoning checks are alerts; the premium chart is a page.

**Free tier** — live premium readout and wallet safety check, unlimited.

**Upsell** — arbitrage alerts and continuous wallet monitoring.

📄 [Full spec →](products/product-17.md)

</details>

<details>
<summary><b>📈 #18 · Miner–Bullion Divergence Screener</b> &nbsp;—&nbsp; 🤖🌐 Both</summary>

<br>

**Problem** — Gold traders who want equity exposure are badly served. Generic stock screeners know nothing about AISC, and gold sites know nothing about equities.

**Solution** — **Live.** Six months of Yahoo closes for GDX, GDXJ, majors, mid-tiers and royalty names, each regressed on GC=F. The screen sorts on the residual: the 20-session move β and gold do not explain. Flags for decoupling, lagging, leading, thin AISC margin (dated, hand-maintained) and earnings within 14 days. Monday digest on the bot.

**Platform** — 🤖🌐 **Both.** 🤖 `/miners`, `/miners TICKER`, `/miners weekly` &nbsp;·&nbsp; 🌐 `/p/miner-divergence` — Sortable screener table, no login · Per-name chart against gold rebased to 100 · AISC margin and earnings panel.

**Primary** — 🌐 dashboard-led. A sortable screener is a table; the bot carries the weekly digest.

**Free tier** — weekly screen, full table, no login.

**Upsell** — daily alerts and backtesting.

📄 [Full spec →](products/product-18.md)

</details>

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 📊 Platforms & Free Tiers

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/metrics-3d-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/metrics-3d-light.svg">
  <img src="assets/metrics-3d-dark.svg" alt="18 products by vertical: Gold IB 5, Gold market 3, Prop firm 3, Forex 2, Crypto 2, Stocks 1, Fintech 2" width="100%">
</picture>

</div>

<br>

**Every product ships both surfaces.** One Telegram account signs you in to the
dashboard, so the bot and the page always agree on who you are and what you are
entitled to.

| Half | Always gives you | Never |
|:--|:--|:--|
| 🤖 **Telegram** | At least one slash command that returns the product's core answer, plus push alerts wherever the product has a trigger | A paywall at the door |
| 🌐 **Dashboard** | A page at `/p/<slug>`: run history, configuration, export, a shareable link | A second login |

Shape no longer decides *whether* a surface exists — only which one is **primary**,
meaning where the value actually lands. That marker is kept on every product below,
because it is real information: a breach alert is worthless on a page you are not
looking at, and a sortable diff table is unreadable in a chat window.

<br>

### 🎖️ Ranks — Awam → General → A-Team → Rambo

The ladder, the labels and the broker doors come from Sam's site
(`printezy247/website_sam`), so one person carries one rank across both
properties. `app/tiers.py` is the copy that this app reads.

| Rank | Own broker | Broker under Sam | What it adds |
|:--|--:|:--|:--|
| 🪪 **Awam** / Public | Free | Free | All 18 tools, full free tier, no sign-in |
| 🎫 **General** | $19 / mo | Free — any account | Saved run history, CSV export, armed alerts |
| ⚙️ **A-Team** | $49 / mo | Free — deposit $100+ | Continuous monitoring, daily alerts, bulk CSV, scheduled reports, your own universe |
| 🎖️ **Rambo** | $129 / mo | Free — deposit $500+ | Multiple seats, unlimited clients and client reports, white-label widget, outbound webhooks, priority support |

Annual is twelve months for the price of ten, **derived from the monthly price
rather than typed twice**, so the two can never drift: $190, $490 and $1,290,
saving $38, $98 and $258.

> [!NOTE]
> A rank is never a side effect of signing in. Signing in is free and grants
> nothing; a rank is paid for, earned at the broker door, given by an admin, or
> carried as a team seat. What the price buys is the **memory** around the tools
> — the saved run, the armed alert, the export — not the answer itself, which
> stays open to Awam with no account at all.

**Where the line sits.** Convenience is charged for; safety is not.

| Behaviour | Rank | Why |
|:--|:--|:--|
| Arming a price alert | General | A remembered level is the memory the rank sells |
| The 30-minute calendar reminder | General | Same thing: reading `/calendar` is free, being reminded is not |
| Run history, CSV export | General | The chat log cannot be scrolled for last month |
| **Drawdown breach warning** | **Free** | The difference between noticing and losing a funded account |
| **Over-exposure warning** | **Free** | A risk line, not a convenience |

The two risk warnings are deliberately ungated and the reasoning is written into
`sentineltool.py` so it does not get tidied away later. Scale on those products
is sold honestly by the account cap instead: one linked account free, ten on
A-Team, fifty on Rambo.

**The card on a product page is computed, not written.** `app/perks.py` derives
what a rank gives on one tool from the three places a rank is actually wired —
the autopilot registry, the `LIMITS` map and the feature matrix — so a page can
only ever claim something that exists. `broker-comparator` is the one tool where
no rank changes anything, and its page says exactly that rather than inventing an
upgrade.

> [!IMPORTANT]
> This replaces the registry's `upsell` sentence, which used to be rendered on
> every product page as if it were a live capability. Ten of eighteen products
> advertised features nobody had built, and the card read "UPGRADE · A-TEAM" even
> to a Rambo holder. The guard is a test: every line a page can show must resolve
> from the wiring, and a rank is never offered when it would add nothing.

#### 🧭 Written for someone who has never used it

Two changes aimed at the same thing: nobody should ever face a blank box.

**On the bot**, the tools menu asks *who you are* first — four rooms instead of
eighteen buttons — and every question in a guided flow offers something to press.
Where a number is wanted, the buttons are built from the price **right now**:
asking `/watch` for a level offers the live mid and four steps either side, so
the commonest answer is a tap rather than a figure you have to know. Where a
sentence is wanted, a **Use an example** button fills in real text. A step can
never be empty: `test_howto` asserts that every free-text step still offers an
example even with the price feed dead.

**On the dashboard**, every tool page opens with three short steps in plain
language and a concrete example. Where the form reads its values from the URL,
the example is a link that fills the page in. Where it cannot be, the example is
printed to copy.

The map lives in `app/howto.py` and a test requires an entry for all eighteen, so
a new product cannot ship as an unexplained form.

#### 👁️ Group auto-scan

The last promise on those scanner pages, now built. The scanners answer one
pasted pitch well, but the scam arrives in a group at 2am while the owner is
asleep, and by morning three members have sent USDT to a wallet.

Add the bot to the group, **make it an administrator** (a bot only sees ordinary
messages in a group when it is an admin), and send `/watchgroup` inside that
room. Every message long enough to be a pitch runs through the same rule engine
the red-flag scanner uses, and anything carrying a red flag is sent privately to
the watcher with the verdict and the reasons.

| Guard | Why |
|:--|:--|
| 90-character floor | Chat is not a pitch. Short messages are never scanned. |
| One alert per author per group per day | A spammer posting twenty times costs one message |
| 12 alerts per group per day | A room that goes bad cannot flood the watcher |
| Red flags only | A yellow alone is not worth waking someone for |

> [!NOTE]
> The bot posts the confirmation **in the group** when watching starts, and never
> posts anything else there. People in a room deserve to know a bot is reading
> what they write, even though it tips off a scammer who is paying attention.
> Ordinary conversation is scanned in memory and discarded; only a flagged
> message is stored, as a scan the watcher can review.

`/groups` lists the watched rooms, `/unwatchgroup` stops one, and the dashboard
has the same list. A lapsed rank stops the scanning and keeps the row, so it
resumes when the rank comes back.

> [!IMPORTANT]
> A rank never unlocks a *product*. It unlocks the **memory, automation and
> scale** around products whose free tier is already open to everybody. The gate
> in `app/gate.py` enforces that: a blocked call answers with the free result
> plus one line naming the rank, never an error page. Ask `/watch` for the gold
> price without an account and it answers; ask it to *remember* a level and it
> names the rank.

A rank is an **entitlement row**, not a column on the user: source (`ib`,
`stripe`, `crypto`, `manual`), an optional expiry, and a unique external id that
makes every grant idempotent. Your effective rank is the highest grant still
active, which is why the broker door and a card subscription can coexist without
either one clobbering the other.

#### 📊 The premium band — is this the moment, or just Tuesday?

"PAXG is 1.4% over spot" is useless on its own, because nobody knows whether
1.4% is the usual toll or a bad day to buy. A fixed warning threshold does not
fix it either: it fires on every coin at the same number, when each keeps its
own habitual range.

The checker has logged PAXG and XAUT against spot every five minutes since #17
shipped. `/paxg` now reads that back as **each coin's own 10th–90th percentile
band over thirty days**, so the question becomes cheap, normal or dear *for this
coin* — plus the follow-up nobody else answers: **which of the two is the
cheaper way into gold right now, and by how much.**

The autopilot speaks when a premium *leaves* its band. A break is a crossing,
not a state: a coin already outside stays quiet, because a daily push repeating
yesterday's news trains people to ignore it.

#### ☀️ The Morning Brief — one message instead of eighteen

Eighteen tools is eighteen things to remember to check, and nobody checks
eighteen. The autopilot solved half of that by making each tool speak for
itself; five separate pushes is still five. This is the other half: **one
message, once a day, at an hour you pick, covering everything that decides
whether today is a day to trade.**

| In it | From |
|:--|:--|
| Is today safe to trade at all | #5 the calendar's verdict |
| Cheap hour or dear one, and the wait | #1 the hours map |
| Has the tokenised-gold premium left its band | #17 |
| What moved *yours* overnight | armed alerts that fired · accounts no longer safe against their rule pack |

`/brief` reads it now, for anyone. `/brief 8` has it arrive every morning at 8
**KL time** — someone choosing when to be woken is not going to convert time
zones. `/brief off` stops it. The dashboard carries the same picker and a live
preview.

Reading it is free; being *sent* it is the rank, which puts it on `alerts`
beside the calendar reminder — the same free door General already opens.

> [!NOTE]
> A quiet morning still marks the day done, so a silent 8am cannot pile up into
> a second message at noon. And one dead feed never eats the brief — a section
> that raises is simply left out, and the rest of the morning still arrives.

#### 📋 The event record — what the spread actually did

Every calendar tells you NFP is at 20:30. None of them tell you the thing that
decides whether you keep your money: **the spread blows out around the release,
and how long it takes to come back.** A stop that was fine at 20:29 is inside
the spread at 20:30.

The checker has been tagging every spread sample that falls inside a red-event
window since the calendar shipped. `/calendar spread` reads it back as a curve
per event — calm before, the peak, and the minute it came home — and the
calendar's head now opens with one word for **is today safe to trade**, plus a
safe re-entry clock while a release is still settling.

| | |
|:--|:--|
| 🤖 | `/calendar` leads with today's verdict; `/calendar spread` is the full record |
| 🌐 | `/p/gold-calendar` — the verdict card, then a curve per event with the peak in red and the recovered side in green |

Two refusals matter more than the feature. **One release is an anecdote**, so
nothing is claimed under `MIN_OCCURRENCES`. And **a recovery we never observed is
never promised** — a spread still wide at the edge of the measured span reports
no all-clear, because someone would re-enter on it.

#### 🕘 The hours map — what the spread log was for

The checker has sampled the gold bid, ask and spread every five minutes since
the day it shipped, and until now nothing read it back. `/watch hours` turns that
log into the question a trader actually has at 9am: **is now a sensible time to
enter, or should I wait?**

| | |
|:--|:--|
| 🤖 | `/watch hours`, or `/watch hours 5` for five lots — the verdict, the wait, and what entering now costs |
| 🌐 | `/p/gold-watch` — a 24-hour bar of median spread, this hour outlined, cheapest and dearest named |
| 🛰️ | The A-Team daily push carries the verdict, so the price comes with what to do about it |

Three rules keep it honest. **KL time, not UTC** — an hour label the audience has
to convert is an hour label they will misread. **An hour with too few samples
says so** rather than guessing; a confident wrong answer about when to trade is
worse than no answer. And **the verdict is free at every rank**, because paying
the wrong spread is a loss and warning about a loss is never what we charge for.
A rank buys the length of the window behind it — 7 days at Awam and General,
30 at A-Team and Rambo.

#### 🧰 My Setup — the answers a tool never asks twice

Eighteen tools, and nearly every one of them opens by asking the same four
things: which broker, how big the account, which prop firm, how many lots a
month. Answer them once and every surface remembers.

`/setup` on the bot walks you through it with buttons, or reads it back and
takes `/setup size=100000` for a single change. `/setup` on the dashboard is the
same seven answers as a form, and the nav carries it.

| Saved once | Fills in |
|:--|:--|
| Broker · lots a month · rebate per lot · clients | 🤝 #8 IB Revenue · #10 Rebate Auditor · #11 Churn Radar · #12 Broker Comparator |
| Account size · prop firm | 🏦 #3 Prop Calculator · #14 Drawdown Sentinel · #15 Monte Carlo |
| Main channel | #13 Link Attribution |

> [!NOTE]
> Two rules make this safe. A saved value only ever fills a **GET**, and every
> dashboard handler that writes gates on `POST` — so a prefilled field can never
> create, delete or charge anything. And a value you typed always wins: the
> setup can fill a gap, never overwrite an answer.

#### 🛰️ Autopilot — what A-Team actually buys

`/autopilot` on the bot, or the panel on your dashboard, turns five of the tools
into standing questions. Once a day the checker asks them for you and pushes the
answer to Telegram.

| Tool | Speaks when |
|:--|:--|
| 🥇 Gold Watch | Every day — the bid, the ask, the spread and how many alerts you have armed |
| ⛏️ Miner Divergence | A miner is actually moving against bullion |
| 🪙 Tokenized Gold | A premium or the USDT peg leaves its band |
| 🛡️ Drawdown Sentinel | A linked account is no longer safe against its rule pack |
| 🌐 Exposure Monitor | Every day, on your last snapshot |

> [!NOTE]
> Silence is the feature. Four of the five say nothing on a quiet day, because a
> digest nobody reads trains you to ignore the one that matters. A day that
> produced nothing still counts as sent, so you get at most one message per tool
> per day.

The switch survives a lapsed rank. Pushes stop the day the rank lapses and
resume the day it comes back, with nothing to set up again.

#### 📄 Scheduled reports

Four more switches on the same registry, on a slower clock. A report reads what
you already ran; it never invents a run, so an untouched tool stays silent
rather than reporting on nothing.

| Report | Every | Built from |
|:--|:--|:--|
| 🌐 Weekly risk report | week | Your last exposure snapshot (#16) |
| 🤝 Weekly book scorecard | week | Your last churn scan — only the clients at risk (#11) |
| 💰 Weekly rebate audit | week | Your last reconciliation run (#10) |
| 📈 Monthly forecast | month | Your last IB revenue model (#8) |

Periods are ISO weeks and calendar months, so a year boundary cannot fire a
report twice, and a period that produced nothing still counts as done. A quiet
month cannot pile up into a burst on the day something finally happens.

#### 📏 The caps a rank raises

The other half of "paid ranks sell scale". Every number below was already a hard
free cap before the ladder existed. A rank raises it; nothing new was closed to
get here, and the Public column is unchanged.

| Cap | Awam | General | A-Team | Rambo |
|:--|--:|--:|--:|--:|
| Linked prop accounts (#14) | 1 | 1 | 10 | 50 |
| Clients per run (#11) | 10 | 10 | 200 | ∞ |
| Tracked links (#13) | 3 | 3 | 50 | ∞ |
| Monte Carlo paths (#15) | 1,000 | 1,000 | 100,000 | 100,000 |
| Rows per batch (#2) | 20 | 20 | 200 | 1,000 |
| Saved comparisons | 8 | 8 | 50 | 200 |

The table is published on `/pricing`, read from the same `LIMITS` map the code
enforces, so the page cannot promise a number the gate does not honour.

#### 🎟️ Three ways up, two of them free

Money is the door most members never use. Both free doors are ported from Sam's
site, where they are how people actually reach a paid rank.

| Door | Costs | What you get |
|:--|:--|:--|
| 🏦 **Broker account** | Nothing | An HFM account under Sam. Any account opens General, deposit $100 opens A-Team, $500 opens Rambo. Thirty days, renewed while the account stays active. This is why General is $19 only for a trader on their own broker. |
| 🤝 **Referral** | Nothing | Bring one person in. When they reach a paid rank or the broker door, you move up one rank for seven days. Once per person; never reaches Rambo. |
| 💳 **Subscription** | $49 or $129 a month | The same ranks, month to month or annually. |

Annual billing is twelve months for the price of ten, so A-Team saves $98 a year
and Rambo saves $258. The saving is printed on the card rather than hidden in a
footnote.

`/broker <account>` queues an account for verification and `/invite` hands back
your own deep link. Both also live on `/pricing`. Sam verifies a deposit from
the admin page, which grants the rank and pays any referral credit owed in the
same step.

#### 👥 Seats — Rambo carrying a team

A group lead or an IB does not want ten subscriptions. `/seats add <telegram id>`
hands a team member your own rank, up to ten of them, and `/seats remove` takes it
back the day they leave.

A seat is not a new kind of record. It is an ordinary entitlement with
`source="seat"` and a `granted_by` naming the holder who pays for it, so every
question the rest of the app already asks — "what rank is this owner?" — answers
correctly without knowing seats exist. Two things fall out for free: a seat
carries the holder's own expiry, so it cannot outlive the rank behind it, and a
seat is granted at the holder's tier, so it can never outrank them.

#### 🏷️ White-label and 🔗 webhooks

The last two Rambo capabilities answer one request: *let my people see this under
my name, and let my own systems see it at all.*

`/widget gold-watch Sam Flip Seribu` mints a card at `/w/<token>` carrying one
tool's live answer under the holder's name. It is public and embeddable, because
the people looking at it are the holder's audience, not ours. Editing the card
keeps its token, so a live embed never breaks on a rename, and the card goes dark
the day the rank paying for it lapses.

> [!IMPORTANT]
> White-label renames the wrapper, never the disclaimer. The risk strip and the
> data sources stay on every card.

`/webhook https://...` registers an endpoint. Every autopilot push and scheduled
report the holder receives is also POSTed there, signed
`HMAC-SHA256(body, secret)` in `X-Sambanggold-Signature` so the receiver can
prove where it came from. The endpoint must be https, the secret survives a URL
change so the receiver keeps verifying, and delivery is best-effort: a dead
endpoint never delays or swallows the Telegram message, which is the one a human
actually reads.

<div align="center">

| # | Product | 🤖 Telegram | 🌐 Dashboard | Primary | Free tier |
|:--|:--|:--|:--|:--:|:--|
| 🥇 **1** | Gold Watch Alert | `/watch XAUUSD` | `/p/gold-watch` | 🤖 | Unlimited /watch on gold. No account |
| 🥇 **2** | XAUUSD Signal Verifier | `/verify GOLD PRICE` | `/p/signal-verifier` | 🤖 | One verify per request, unlimited requests |
| 🏛 **3** | Prop Firm Challenge Calculator | `/propcalc FEE SIZE PASS%` | `/p/prop-calculator` | 🌐 | Full calculator and bot command, no limit |
| 🔒 **4** | Telegram Bot Scam Detector | `/audit @bot_username` | `/p/bot-scam-detector` | 🤖 | Unlimited /audit scans |
| 🥇 **5** | Gold Seasonality Calendar | `/calendar` · `/calendar_alert` | `/p/gold-calendar` | 🌐 | Full calendar and PDF, no login |
| 🔒 **6** | Copy-Trade Safety Audit | `/copyaudit BROKER` | `/p/copy-trade-audit` | 🤖 | 5 audits free |
| 💱 **7** | Forex Signal Red-Flag Scanner | `/scan TEXT` | `/p/red-flag-scanner` | 🤖 | Unlimited text scans |
| 🥇 **8** | IB Affiliate Revenue Calculator | `/ibcalc LOTS RATE [CLIENTS] [CLAWBACK%]` | `/p/ib-revenue-calculator` | 🌐 | Full calculator and compliance checklist |
| 🔒 **9** | Influencer Trading Scam Audit | `/influencer @handle` | `/p/influencer-audit` | 🤖 | Unlimited audits plus the loss-report template |
| 🥇 **10** | Rebate Reconciliation Auditor | `/rebateaudit` | `/p/rebate-auditor` | 🌐 | One broker, one month, full shortfall report. No card |
| 🥇 **11** | IB Client Churn & Blow-Up Radar | `/ibchurn` | `/p/churn-radar` | 🌐 | 10 tracked clients, unlimited alerts |
| 🥇 **12** | Live Gold Broker Comparator | `/goldspread` | `/p/broker-comparator` | 🌐 | Public comparison table and bot command, fully open |
| 🥇 **13** | IB Link Attribution & Funnel Tracker | `/newlink CHANNEL` | `/p/link-attribution` | 🌐 | 3 tracked links, full funnel view |
| 🏛 **14** | Drawdown Sentinel | `/sentinel link` | `/p/drawdown-sentinel` | 🤖 | 1 account on 1 firm, unlimited breach alerts |
| 🏛 **15** | Monte Carlo Challenge Simulator | `/simulate WINRATE RR RISK%` | `/p/monte-carlo-sim` | 🌐 | 1,000 simulations per run, unlimited runs |
| 💱 **16** | Correlation & Overexposure Monitor | `/exposure` | `/p/exposure-monitor` | 🤖 | On-demand snapshot, unlimited |
| 🪙 **17** | Tokenized-Gold Premium & Payout Health | `/paxg` | `/p/tokenized-gold` | 🤖 | Live premium readout and wallet safety check, unlimited |
| 📈 **18** | Miner–Bullion Divergence Screener | `/miners` | `/p/miner-divergence` | 🌐 | Weekly screen, full table, no login |

</div>

<div align="center">

| | Count |
|:--|:--:|
| 🤖🌐 Both surfaces | **18 / 18** |
| 🤖 Bot-led | **9** |
| 🌐 Dashboard-led | **9** |
| ✅ Free tier, no card | **18 / 18** |

</div>

> [!NOTE]
> **No product is paywalled at the door.** Every one of the eighteen does its core job for free, without a card. Paid tiers sell only *scale* (more clients, more sims, more brokers) and *automation* (continuous monitoring instead of on-demand).

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 🗺️ Roadmap

<div align="center">

<img src="assets/roadmap-orbit.svg" alt="Roadmap: now Vault I live, next IB ops suite 10-13, then prop and forex 14-16, later crypto and stocks 17-18" width="420">

</div>

- [x] **Phase 0 — the spine** — one Flask app, a page per product, one Telegram identity across bot and dashboard
- [x] **Vault I** — 9 products shipped
- [x] **Gold IB ops suite** — #10 Rebate Auditor ✅, #11 Churn Radar ✅, #12 Broker Comparator ✅, #13 Attribution ✅
- [x] **Prop + forex** — #14 Drawdown Sentinel ✅, #15 Monte Carlo Sim ✅, #16 Overexposure Monitor ✅
- [x] **Crypto + stocks** — #17 Tokenized-Gold Monitor ✅, #18 Miner Divergence Screener ✅
- [x] **Rank spine** — entitlements, the gate on both surfaces, `/pricing`, admin grants
- [x] **A-Team autopilot** — daily standing questions on five tools, on both surfaces
- [x] **A-Team scale** — every free cap is now rank-aware, published on the ranks page
- [x] **A-Team reports** — weekly scorecards and a monthly forecast, on the same registry
- [x] **Free doors** — the broker account and referral credit, both surfaces
- [x] **Rambo seats** — ten team members on one rank, with the expiry that pays for them
- [x] **Rambo extras** — the white-label widget and signed outbound webhooks
- [x] **My Setup** — the recurring answers saved once, pre-filling forms on both surfaces
- [x] **#1 hours map** — best and worst hours to trade gold, from our own spread log
- [x] **#5 event record** — what the spread did at the last releases, plus the safe re-entry clock
- [x] **Morning Brief** — one daily message at your KL hour, across the calendar, the hours map and your own positions
- [x] **#17 premium band** — each coin's own 30-day range, and the cheaper way into gold today
- [x] **One language per page** — every surface rendered in both and checked that neither bleeds into the other
- [ ] One billing spine (Stripe + USDT) writing into the same entitlements table

```mermaid
timeline
    title Build order — gold IB first, because the gap is widest there
    Now : Vault I live (9 products)
    Next : #10 Rebate Auditor : #11 Churn Radar : #12 Broker Comparator : #13 Attribution
    Then : #14 Drawdown Sentinel : #15 Monte Carlo Sim : #16 Overexposure Monitor
    Later : #17 Tokenized-Gold Monitor : #18 Miner Divergence Screener
```

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 🚀 Quickstart

```bash
git clone https://github.com/printezy247/sambangold-products.git
cd sambangold-products
cp .env.example .env               # fill in your keys — never commit this file
pip install -r requirements.txt

flask --app wsgi run               # 🌐 dashboard on http://localhost:5000
pytest -q                          # the surface contract: both halves, all 18
```

The landing page at `/` wears the **SAMBANGGOLD** brand (Bahasa Melayu first,
`EN` toggle top right); every product has its own page at `/p/<slug>`, and
`/dashboard` is the member home. Sign in at `/signin` three ways, no password:
**Telegram** (Login Widget — same account the bot uses), **email** (an 8-digit
code, ten minutes, five tries) or **Google** (placeholder until OAuth exists).
Signing in through a second door links it to the same account. The Telegram id
in `ADMIN_TELEGRAM_ID` is the admin: every feature open, plus `/admin` with the
account list and a CSV export. The 🤖 half is the same process — point Telegram
at `POST /webhook/telegram` once `PUBLIC_BASE_URL` is reachable over HTTPS.

Every surface is **Bahasa Melayu first**: the registry copy, the tool panels,
the scanner findings and the bot replies all switch with the `EN` toggle or
`/language`, and the trading vocabulary Malaysians already use in English
(spread, lot, drawdown, prop firm, rebate, payout) stays as it is. In the bot,
**▶️ Mula** on any tool card starts a guided flow — one question at a time with
tap-to-answer buttons — so nobody has to remember `/propcalc 500 100000 15`;
typing a bare command such as `/scan` does the same. If
`TELEGRAM_BOT_USERNAME` is not set, the app asks the Bot API for it once and
caches it, so the Telegram login button appears either way.

| Variable | Required | Purpose |
|:--|:--:|:--|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot identity, and the key that signs dashboard logins |
| `FLASK_SECRET_KEY` | ✅ | Session signing for the 🌐 dashboard |
| `PUBLIC_BASE_URL` | ✅ | Where Telegram sends the webhook, and the base for shareable links |
| `STRIPE_API_KEY` | — | PRO tier checkout |
| `STRIPE_WEBHOOK_SECRET` | — | Subscription state sync |
| `USDT_ADDRESS` | — | Crypto payment path |
| `ADMIN_TELEGRAM_ID` | ✅ | The admin account: every feature open, `/admin` user list and CSV export |
| `DATABASE_PATH` | — | SQLite file for armed alerts and trigger history (default `data/sambangold.db`) |
| `TASK_TOKEN` | — | Shared secret the scheduler sends to `POST /tasks/check-alerts` |
| `TELEGRAM_BOT_USERNAME` | ✅ | The bot's `@username` (no `@`) — the Telegram Login Widget and every "open bot" link need it |
| `PUBLIC_CHANNEL_URL` | — | Adds a 📢 channel button to the bot's main menu |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASS` `MAIL_FROM` | — | Email sign-in codes over any free SMTP relay (a Gmail app password works); unset → Telegram sign-in only |
| `EZYAI_SITE_URL` | — | Web base URL for shareable links |
| `SENTRY_DSN` | — | Error tracking |
| `EZYAI_DEMO_DATA` | — | Seed demo data (`true` / `false`) |

<details>
<summary><b>🛠 Deploy</b></summary>

<br>

CI runs on every push and pull request against `master` — the README/asset check, then `py_compile`, then pytest, then deploy to Fly.io on `master` pushes only. See [`.github/workflows/build-deploy.yml`](.github/workflows/build-deploy.yml).

```bash
fly deploy --remote-only
```

`FLY_API_TOKEN` must be set as a repository secret. Never commit `.env`.

Or let Fly deploy straight from GitHub (Dashboard → Launch an App from GitHub): the repo carries a `Dockerfile` and `fly.toml` (app `sambangold-products`, port 8080, a 1 GB volume at `/data` for SQLite). After the first deploy, set the secrets with `fly secrets set` and run `fly ssh console -C "flask --app wsgi set-webhook"` once so Telegram knows where to send updates.

</details>

<img src="assets/divider-flow.svg" alt="" width="100%">

<br>

## 🧱 Repo Map

```
sambangold-products/
├── assets/
│   ├── hero-banner-{dark,light}.svg    animated hero
│   ├── metrics-3d-{dark,light}.svg     isometric vertical breakdown
│   ├── divider-flow.svg                animated section rule
│   ├── stack-ticker.svg                scrolling stack marquee
│   ├── roadmap-orbit.svg               orbital roadmap
│   ├── badges-strip.svg                self-hosted badges
│   ├── nav/                            clickable section chips
│   └── icons/ic-01..18.svg             3D product icons
├── Dockerfile                          Fly.io build — python:3.12-slim + gunicorn on 8080
├── fly.toml                            app sambangold-products, 1 GB volume at /data
├── app/
│   ├── products.py                     the registry — 18 products, both halves
│   ├── tiers.py                        the rank ladder — ported from website_sam
│   ├── gate.py                         one gate, both surfaces — scale only, never the door
│   ├── autopilot.py                    the daily standing questions behind A-Team
│   ├── doors.py                        the two free ways up — broker account, referral
│   ├── seats.py                        Rambo carrying a team on one rank
│   ├── whitelabel.py                   the branded card and the signed webhook out
│   ├── groups.py                       group auto-scan — the bot watches a room
│   ├── howto.py                        three plain steps and an example, per tool
│   ├── setup.py                        My Setup — the answers a tool never asks twice
│   ├── hours.py                        #1 best and worst hours, read back from the spread log
│   ├── eventspread.py                  #5 what the spread did at the release, and when it came home
│   ├── brief.py                        the Morning Brief — one message a day, at your KL hour
│   ├── premium.py                      #17 each coin's own premium band, and the cheaper route
│   ├── auth.py                         Telegram Login Widget → web session
│   ├── telegram.py                     webhook + command dispatch
│   ├── views.py                        /, /pricing and /p/<slug>
│   └── templates/                      dashboard pages
├── tests/                              surface contract + auth verification
├── products/product-01..18.md          per-product specs
├── scripts/                            check, commit and deploy helpers
├── wsgi.py                             gunicorn entry point
└── .github/workflows/build-deploy.yml  CI/CD
```

<img src="assets/divider-flow.svg" alt="" width="100%">

<div align="center">

<br>

<img src="assets/hero-animated.svg" alt="" width="110">

### printezy · sambangold

<sub>Python · Flask · Telegram Bot API · Binance · Yahoo Finance · Stripe · Fly.io</sub>

<sub>**Educational research only. Not financial advice.** Verify every price with your broker.</sub>

<sub>MIT</sub>

<br>

<img src="assets/divider-flow.svg" alt="" width="100%">

</div>
