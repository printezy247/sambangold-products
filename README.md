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

| Rank | Price | HFM door | What it adds |
|:--|--:|:--|:--|
| 🪪 **Awam** / Public | Free | — | All 18 tools, full free tier, no sign-in |
| 🎫 **General** | Free | Account, any deposit | Saved run history, CSV export, armed alerts |
| ⚙️ **A-Team** | $49 / mo | Deposit $100+ | Continuous monitoring, daily alerts, bulk CSV, scheduled PDF reports, your own universe |
| 🎖️ **Rambo** | $129 / mo | Deposit $500+ | Multiple seats, unlimited clients and client reports, white-label widget, outbound webhooks, priority support |

> [!IMPORTANT]
> A rank never unlocks a *product*. It unlocks **scale and automation** on
> products whose free tier is already open to everybody. The gate in `app/gate.py`
> enforces that: a blocked call answers with the free result plus one line naming
> the rank, never an error page.

A rank is an **entitlement row**, not a column on the user: source (`ib`,
`stripe`, `crypto`, `manual`), an optional expiry, and a unique external id that
makes every grant idempotent. Your effective rank is the highest grant still
active, which is why the broker door and a card subscription can coexist without
either one clobbering the other.

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
- [ ] **A-Team batch + reports** — bulk CSV upload and scheduled PDF reports
- [ ] **Rambo scale** — seats, client reports, white-label widget, outbound webhooks
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
