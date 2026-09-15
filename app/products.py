"""The product registry — single source of truth for all eighteen products.

Every product ships two surfaces: a Telegram half and a dashboard half.
Routes, the bot command dispatch table, the index page and the tests all read
from this module, so a product cannot quietly exist on one surface only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    number: int
    slug: str
    name: str
    vertical: str
    emoji: str
    status: str                      # "shipped" | "proposed"
    primary: str                     # "bot" | "dashboard"
    primary_why: str
    free_tier: str
    problem: str
    solution: str
    bot_commands: tuple = ()         # ((command, what it does), ...)
    dashboard_views: tuple = ()      # (view description, ...)
    upsell: str = ""

    @property
    def icon(self) -> str:
        return "assets/icons/ic-%02d.svg" % self.number

    @property
    def spec(self) -> str:
        return "products/product-%02d.md" % self.number

    @property
    def primary_label(self) -> str:
        return "🤖 bot-led" if self.primary == "bot" else "🌐 dashboard-led"


PRODUCTS = (
    Product(
        number=1, slug="gold-watch", name="Gold Watch Alert",
        vertical="Gold", emoji="🥇", status="shipped", primary="bot",
        primary_why="One command in, one alert out — the dashboard keeps the history a chat log cannot.",
        free_tier="Unlimited /watch on gold. No account.",
        problem="Traders miss gold entries to spread and slippage, and most Telegram gold channels are scams.",
        solution="Spread-aware entry and stop levels from Binance PAXGUSDT, with Yahoo GC=F as fallback.",
        bot_commands=(
            ("/watch XAUUSD", "arm a spread-aware alert on gold"),
            ("/watch list", "show every alert you have armed"),
        ),
        dashboard_views=(
            "Alert history — every trigger with the price and spread at fire time",
            "Threshold editor for each armed pair",
            "CSV export of triggers for journalling",
        ),
        upsell="/autopilot plus DCF and COT fundamentals.",
    ),
    Product(
        number=2, slug="signal-verifier", name="XAUUSD Signal Verifier",
        vertical="Gold", emoji="🥇", status="shipped", primary="bot",
        primary_why="Verification belongs in the group where the fake was posted.",
        free_tier="One verify per request, unlimited requests.",
        problem="Gold signal sellers post fabricated MT4 screenshots with cherry-picked entries.",
        solution="Pull Binance PAXGUSDT tick history and test whether the claimed fill was reachable.",
        bot_commands=(
            ("/verify GOLD PRICE", "test a claimed fill — REAL or IMPOSSIBLE"),
        ),
        dashboard_views=(
            "Verdict archive with the tick window that produced each call",
            "Batch verify — paste or upload a list of claimed fills",
            "Shareable public verdict link for posting back into a group",
        ),
        upsell="PRO batch CSV upload and weekly audit reports.",
    ),
    Product(
        number=3, slug="prop-calculator", name="Prop Firm Challenge Calculator",
        vertical="Prop firm", emoji="🏛", status="shipped", primary="dashboard",
        primary_why="The long T&C paste needs a page; the bot answers the quick yes-or-no.",
        free_tier="Full calculator and bot command, no limit.",
        problem="Traders pay $500–$5,000 in challenge fees with no expected-value estimate, and hidden rules sit buried in the T&Cs.",
        solution="Expected value on the fee, plus a red/yellow scan of pasted terms for the rules that actually fail people.",
        bot_commands=(
            ("/propcalc FEE SIZE PASS%", "expected value for one challenge"),
        ),
        dashboard_views=(
            "Full calculator with the long T&C paste box",
            "Rule-scan report, red and yellow flags itemised",
            "Saved comparisons across firms",
        ),
        upsell="Premium PDF audit and automated forecast.",
    ),
    Product(
        number=4, slug="bot-scam-detector", name="Telegram Bot Scam Detector",
        vertical="Security", emoji="🔒", status="shipped", primary="bot",
        primary_why="It audits Telegram bots, so it lives where its targets live.",
        free_tier="Unlimited /audit scans.",
        problem="Fake verification bots, malware links and fake airdrops rose sharply through 2025.",
        solution="Score a bot on private-key requests, unregulated broker pushes and missing audit links.",
        bot_commands=(
            ("/audit @bot_username", "scam score plus a checklist"),
        ),
        dashboard_views=(
            "Scan history with the score breakdown per signal",
            "Watchlist of bots to re-scan",
            "Public scam-score page per audited bot",
        ),
        upsell="PRO daily auto-scan of subscribed channels plus a malware database.",
    ),
    Product(
        number=5, slug="gold-calendar", name="Gold Seasonality Calendar",
        vertical="Gold", emoji="🥇", status="shipped", primary="dashboard",
        primary_why="The calendar is a page you scan; the bot is the push you cannot miss.",
        free_tier="Full calendar and PDF, no login.",
        problem="Traders ignore gold seasonality — Fed windows, CME holidays, jewelry cycles — and the spread widening around them.",
        solution="A monthly volatility and event calendar with the spread-risk windows marked.",
        bot_commands=(
            ("/calendar", "the next event and its historical spread behaviour"),
            ("/calendar_alert", "push 30 minutes before each window"),
        ),
        dashboard_views=(
            "Month grid of volatility patterns and Fed release windows",
            "PDF download of the current quarter",
            "Per-event history — what the spread did last time",
        ),
        upsell="PRO real-time alert bot.",
    ),
    Product(
        number=6, slug="copy-trade-audit", name="Copy-Trade Safety Audit",
        vertical="Fintech", emoji="🔒", status="shipped", primary="bot",
        primary_why="It has to run at the moment someone is being pitched.",
        free_tier="5 audits free.",
        problem="Influencers push unregulated copy-trading; users lose capital to hidden spreads and blowouts.",
        solution="Check regulation and negative-balance protection, then price the hidden spread cost.",
        bot_commands=(
            ("/copyaudit BROKER", "SAFE or HIGH RISK, with the checklist"),
        ),
        dashboard_views=(
            "Audit history with the regulator links that were checked",
            "Side-by-side broker comparison",
            "Hidden-cost model — spread cost projected over a year",
        ),
        upsell="PRO unlimited plus a weekly portfolio risk report.",
    ),
    Product(
        number=7, slug="red-flag-scanner", name="Forex Signal Red-Flag Scanner",
        vertical="Forex", emoji="💱", status="shipped", primary="bot",
        primary_why="Pitches arrive in chat, so the scan starts there.",
        free_tier="Unlimited text scans.",
        problem="Signal sellers claim 100% accuracy, delete losing trades and charge $30–$300 a month.",
        solution="Flag the language that always accompanies a fake, and check for a verified audit link.",
        bot_commands=(
            ("/scan TEXT", "red-flag report on a pitch"),
        ),
        dashboard_views=(
            "Scanner with the full pitch pasted in, flags highlighted inline",
            "Scan history per seller or channel",
            "Weekly scorecard for a channel you follow",
        ),
        upsell="PRO full group auto-scan and a weekly scorecard.",
    ),
    Product(
        number=8, slug="ib-revenue-calculator", name="IB Affiliate Revenue Calculator",
        vertical="Gold IB", emoji="🥇", status="shipped", primary="dashboard",
        primary_why="A multi-field model and a document download; the bot gives the quick estimate.",
        free_tier="Full calculator and compliance checklist.",
        problem="IB affiliates face opaque payout rules and compliance overhead they cannot price.",
        solution="Model net revenue after compliance cost, with the payout timeline made explicit.",
        bot_commands=(
            ("/ibcalc LOTS RATE", "quick net-revenue estimate"),
        ),
        dashboard_views=(
            "Multi-field revenue model with the payout timeline",
            "Downloadable compliance checklist",
            "Saved scenarios across brokers",
        ),
        upsell="PRO automated monthly forecast and audit template.",
    ),
    Product(
        number=9, slug="influencer-audit", name="Influencer Trading Scam Audit",
        vertical="Social", emoji="🔒", status="shipped", primary="bot",
        primary_why="Viral by construction — the audit gets forwarded into the group that shared the influencer.",
        free_tier="Unlimited audits plus the loss-report template.",
        problem="Billions are lost to social-media investment scams each year.",
        solution="Demand audited history rather than screenshots, and flag unregulated broker promotion.",
        bot_commands=(
            ("/influencer @handle", "audit an influencer's trading claims"),
        ),
        dashboard_views=(
            "Audit archive, shareable per handle",
            "Loss-report template generator for FTC / CFTC / IC3",
            "Broker-promotion trail for the accounts you have audited",
        ),
        upsell="PRO batch audit and an automated scam-alert channel.",
    ),
    Product(
        number=10, slug="rebate-auditor", name="Rebate Reconciliation Auditor",
        vertical="Gold IB", emoji="🥇", status="proposed", primary="dashboard",
        primary_why="CSV upload, a sortable diff, a dispute PDF; the bot pings when a run finishes.",
        free_tier="One broker, one month, full shortfall report. No card.",
        problem="Brokers underpay IB rebates through dropped accounts, silent rate changes and excluded symbols, and almost nobody checks.",
        solution="Recompute lots x rate per symbol and tier, diff against what was paid, and produce dispute-ready evidence.",
        bot_commands=(
            ("/rebateaudit", "run the last uploaded reconciliation and return the summary"),
            ("/rebatestatus", "shortfall total for the current period"),
        ),
        dashboard_views=(
            "CSV upload for the broker statement and the client trade log",
            "Sortable diff table — shortfall, missing account, silent rate change",
            "Dispute PDF with the per-account arithmetic shown",
        ),
        upsell="Multi-broker auto-reconciliation and a dispute-letter generator.",
    ),
    Product(
        number=11, slug="churn-radar", name="IB Client Churn & Blow-Up Radar",
        vertical="Gold IB", emoji="🥇", status="proposed", primary="dashboard",
        primary_why="The book is a table you study; the bot warns the moment a client crosses a line.",
        free_tier="10 tracked clients, unlimited alerts.",
        problem="IB revenue dies when the client book dies, and the warning signs are visible weeks before the payout drops.",
        solution="Score each referred client on volume decay, margin utilisation, martingale patterns and dormancy drift.",
        bot_commands=(
            ("/ibchurn", "top clients at risk right now"),
            ("/ibchurn @client", "single client detail and signal breakdown"),
        ),
        dashboard_views=(
            "Book overview ranked by 30-day blow-up probability",
            "Per-client signal breakdown and history",
            "Intervention log — what was tried and what it did",
        ),
        upsell="Unlimited clients plus auto-drafted nurture messages.",
    ),
    Product(
        number=12, slug="broker-comparator", name="Live Gold Broker Comparator",
        vertical="Gold IB", emoji="🥇", status="proposed", primary="dashboard",
        primary_why="The public table is the SEO asset; the bot drops the card straight into a group.",
        free_tier="Public comparison table and bot command, fully open.",
        problem="Nobody can see live XAUUSD trading cost across brokers side by side, so IBs cannot prove their routing is the cheap one.",
        solution="Live spread, swap, commission and slippage, ranked, rendered as a shareable card that carries the IB's own link.",
        bot_commands=(
            ("/goldspread", "current ranked comparison card"),
            ("/goldspread 1.0 overnight", "cost ranking for a lot size and holding period"),
        ),
        dashboard_views=(
            "Public indexable comparison table — the SEO asset",
            "Cost calculator for a given lot size and holding period",
            "Referral-branded card generator",
        ),
        upsell="White-label branded embeddable widget.",
    ),
    Product(
        number=13, slug="link-attribution", name="IB Link Attribution & Funnel Tracker",
        vertical="Gold IB", emoji="🥇", status="proposed", primary="dashboard",
        primary_why="Link management and a funnel need a page; the bot mints links and reports daily.",
        free_tier="3 tracked links, full funnel view.",
        problem="Broker portals report signups but never where they came from, so the IB cannot tell which channel pays.",
        solution="Per-channel short links tracking post, click, signup, first deposit and first lot.",
        bot_commands=(
            ("/newlink CHANNEL", "mint a tracked short link"),
            ("/funnel", "today's clicks, signups, deposits, first lots"),
        ),
        dashboard_views=(
            "Link manager with per-channel tags",
            "Funnel dashboard from click through to first lot",
            "Channel comparison over a date range",
        ),
        upsell="Unlimited links plus cohort LTV and payback.",
    ),
    Product(
        number=14, slug="drawdown-sentinel", name="Drawdown Sentinel",
        vertical="Prop firm", emoji="🏛", status="proposed", primary="bot",
        primary_why="The entire value is a push arriving seconds before the line is crossed.",
        free_tier="1 account on 1 firm, unlimited breach alerts.",
        problem="Most challenge failures are rule breaches, not bad strategy — the line is crossed before the trader notices it.",
        solution="Watch daily loss, trailing drawdown, news blackouts, max lot and consistency against per-firm rule packs, and warn before the breach.",
        bot_commands=(
            ("/sentinel link", "link a trading account"),
            ("/sentinel status", "distance to every active rule line"),
            ("/sentinel firm NAME", "load a firm's rule pack"),
        ),
        dashboard_views=(
            "Account linking and rule-pack selection",
            "Live distance-to-breach gauges per rule",
            "Breach history and near-miss log",
        ),
        upsell="Multi-account plus an auto-flatten webhook.",
    ),
    Product(
        number=15, slug="monte-carlo-sim", name="Monte Carlo Challenge Simulator",
        vertical="Prop firm", emoji="🏛", status="proposed", primary="dashboard",
        primary_why="The fan chart and the PDF need a page; the bot returns the summary card.",
        free_tier="1,000 simulations per run, unlimited runs.",
        problem="A single expected-value number hides the fact that the rule set, not the edge, is what fails people.",
        solution="Simulate equity paths against the actual rule set to get a realistic pass probability and cost-to-funded.",
        bot_commands=(
            ("/simulate WINRATE RR RISK%", "summary card with pass probability and expected cost"),
        ),
        dashboard_views=(
            "Equity-path fan chart across the simulated runs",
            "Rule-pack picker — daily DD, trailing DD, min days, consistency",
            "PDF export of the run",
        ),
        upsell="100k sims, the full rule-pack library and PDF export.",
    ),
    Product(
        number=16, slug="exposure-monitor", name="Correlation & Overexposure Monitor",
        vertical="Forex", emoji="💱", status="proposed", primary="bot",
        primary_why="Overexposure is a warning you need immediately; the heat-map explains it afterwards.",
        free_tier="On-demand snapshot, unlimited.",
        problem="Five open trades are often one leveraged bet, and the account finds out at the same moment the cluster moves.",
        solution="Cluster open positions into a single true-risk figure, with rollover and session-spread cost included.",
        bot_commands=(
            ("/exposure", "current cluster and true-risk figure"),
            ("/exposure warn", "enable overexposure push alerts"),
        ),
        dashboard_views=(
            "Correlation heat-map of the open book",
            "True-risk figure with the cluster decomposition",
            "Rollover and session-spread cost projection",
        ),
        upsell="Live monitoring with prop-rule-aware exposure caps.",
    ),
    Product(
        number=17, slug="tokenized-gold", name="Tokenized-Gold Premium & Payout Health",
        vertical="Crypto", emoji="🪙", status="proposed", primary="bot",
        primary_why="Depeg and poisoning checks are alerts; the premium chart is a page.",
        free_tier="Live premium readout and wallet safety check, unlimited.",
        problem="PAXG and XAUT drift from spot, and traders taking payouts in USDT get hit by chain fees, depegs and address poisoning.",
        solution="Track premium and discount against spot XAU alongside redemption fees, attestation freshness and payout-wallet health.",
        bot_commands=(
            ("/paxg", "current premium or discount vs spot XAU"),
            ("/walletcheck ADDRESS", "chain fee, depeg status, poisoning check"),
        ),
        dashboard_views=(
            "Public premium/discount chart over time",
            "Reserve attestation freshness per token",
            "Payout wallet health report",
        ),
        upsell="Arbitrage alerts and continuous wallet monitoring.",
    ),
    Product(
        number=18, slug="miner-divergence", name="Miner–Bullion Divergence Screener",
        vertical="Stocks", emoji="📈", status="proposed", primary="dashboard",
        primary_why="A sortable screener is a table; the bot carries the weekly digest.",
        free_tier="Weekly screen, full table, no login.",
        problem="Gold traders who want equity exposure have nothing that screens miners against the metal itself.",
        solution="Screen GDX, GDXJ and royalty names for beta divergence, AISC margin compression and event risk.",
        bot_commands=(
            ("/miners", "this week's divergence screen"),
            ("/miners TICKER", "single-name beta, AISC margin, next earnings"),
        ),
        dashboard_views=(
            "Sortable screener table across the miner universe",
            "Per-name divergence chart against spot gold",
            "AISC margin and earnings/halt risk panel",
        ),
        upsell="Daily alerts and backtesting.",
    ),
)

BY_SLUG = {p.slug: p for p in PRODUCTS}
BY_NUMBER = {p.number: p for p in PRODUCTS}


def command_index():
    """Map every bare command word (no arguments) to its product."""
    index = {}
    for product in PRODUCTS:
        for command, _ in product.bot_commands:
            word = command.split()[0].lstrip("/")
            index.setdefault(word, product)
    return index
