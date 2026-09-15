"""Rule engine behind the four scanners: #4 bot scam, #6 copy-trade, #7 signal pitch, #9 influencer.

One shape for all of them: text in → findings out → a 0–100 risk score and a
verdict. Every rule is a regex with a flag, a label and a plain-language "why",
so the bot, the dashboard and the tests all read the same table. Positive
signals (a verified track-record link, a regulator number) *lower* the score,
which is what separates "salesy but honest" from "scam".

Nothing here calls the network. Regulator checks are pointers to the official
registers — there is no free JSON API for them, and a table that pretended to
be one would be worse than none.
"""

import re

RED, YELLOW, GOOD = "red", "yellow", "good"
WEIGHT = {RED: 25, YELLOW: 10, GOOD: -15}

# --- shared rule fragments ------------------------------------------------- #

PITCH_RULES = (
    (RED, "Guaranteed returns", r"guarantee[ds]?|no[- ]loss|risk[- ]free|100 ?% (win|accura|profit|safe)|(never|zero) los(e|s)",
     "Nobody can guarantee a market outcome. This phrase is the single most reliable scam marker."),
    (RED, "Fee to withdraw", r"(withdraw|release|unlock)[^.]{0,40}(fee|tax|deposit)|pay[^.]{0,30}to (withdraw|release)",
     "A legitimate broker never charges you to receive your own money."),
    (RED, "Wallet / key request", r"(seed|recovery) phrase|private key|connect (your )?wallet|send (usdt|btc|eth|crypto) to",
     "No service needs your keys or a transfer to an address to 'verify' anything."),
    (YELLOW, "Urgency", r"(limited|last|only \d+) (slots?|seats?|spots?|places?)|hurry|act now|today only|closing (soon|tonight)|countdown",
     "Manufactured deadlines exist to stop you checking."),
    (YELLOW, "Screenshot as proof", r"screenshot|screen ?shot|proof of (profit|payout)|see my results",
     "Screenshots are edited in seconds. Ask for a verified, live track record."),
    (YELLOW, "Lifestyle bait", r"lambo|lamborghini|passive income|financial freedom|quit (your|my) job|flip(ped)? \$?\d",
     "Lifestyle imagery sells the dream, not the method."),
    (YELLOW, "Move to private chat", r"\bdm\b|direct message|inbox me|pm me|whats ?app me|telegram me",
     "Private channels remove the audience that could warn you."),
    (YELLOW, "Paid VIP tier", r"vip|premium (group|signals?)|\$\s?\d{2,4}\s?(/|per)\s?(month|mo|week)",
     "Not a scam by itself, but it is where the money is asked for."),
    (YELLOW, "Double / multiply", r"(double|triple|10x|100x)[^.]{0,20}(account|capital|money|investment)",
     "Compounding claims without drawdown are not real."),
    (YELLOW, "Referral / IB link", r"(refid|ref=|/ref/|invitecode|affid|partner ?id)",
     "The pitch is paid by the broker per deposit. Not wrong — but it is the business model."),
    (GOOD, "Verified track record link", r"myfxbook\.com|fxblue\.com|fxstat\.com|psyquation|darwinex",
     "A third-party verified account is the one form of proof that cannot be edited."),
    (GOOD, "Risk disclosure present", r"past performance|not financial advice|capital (is )?at risk|you (can|may) lose",
     "Honest sellers say it. Scammers never do."),
)

# Regulators worth trusting, with where to check. Order matters: first is tier 1.
REGULATORS = {
    "FCA": ("UK Financial Conduct Authority", "https://register.fca.org.uk/"),
    "ASIC": ("Australian Securities & Investments Commission", "https://connectonline.asic.gov.au/"),
    "CFTC/NFA": ("US CFTC / NFA BASIC", "https://www.nfa.futures.org/basicnet/"),
    "CySEC": ("Cyprus Securities and Exchange Commission", "https://www.cysec.gov.cy/en-GB/entities/investment-firms/cypriot/"),
    "MAS": ("Monetary Authority of Singapore", "https://eservices.mas.gov.sg/fid"),
    "SC Malaysia": ("Securities Commission Malaysia", "https://www.sc.com.my/regulation/enforcement/investor-alerts/sc-investor-alerts/investor-alert-list"),
    "BaFin": ("German Federal Financial Supervisory Authority", "https://portal.mvp.bafin.de/database/InstInfo/"),
    "FSCA": ("South African Financial Sector Conduct Authority", "https://www.fsca.co.za/Regulated%20Entities/Pages/default.aspx"),
    "CBI": ("Central Bank of Ireland", "https://registers.centralbank.ie/"),
    "FSA Seychelles": ("Seychelles FSA (offshore)", "https://fsaseychelles.sc/regulated-entities/capital-markets"),
    "CIMA": ("Cayman Islands Monetary Authority (offshore)", "https://www.cima.ky/search-entities-cima"),
    "FSC Mauritius": ("Mauritius FSC (offshore)", "https://www.fscmauritius.org/en/supervision/register-of-licensees"),
    "VFSC": ("Vanuatu FSC (offshore)", "https://www.vfsc.vu/"),
}
TIER1 = ("FCA", "ASIC", "CFTC/NFA", "CySEC", "MAS", "BaFin", "CBI")
OFFSHORE = ("FSA Seychelles", "CIMA", "FSC Mauritius", "VFSC")

# Brokers a Malaysian gold trader will actually meet. Entities and licences change:
# this is a starting point that always ends in "verify on the register", never a verdict.
BROKERS = {
    "hfm": {"name": "HFM (HF Markets)", "regulators": ("FCA", "CySEC", "FSCA", "FSA Seychelles"), "nbp": True},
    "exness": {"name": "Exness", "regulators": ("FCA", "CySEC", "FSCA", "FSA Seychelles"), "nbp": True},
    "ic markets": {"name": "IC Markets", "regulators": ("ASIC", "CySEC", "FSA Seychelles"), "nbp": True},
    "pepperstone": {"name": "Pepperstone", "regulators": ("ASIC", "FCA", "CySEC", "BaFin", "SC Malaysia"), "nbp": True},
    "xm": {"name": "XM", "regulators": ("CySEC", "ASIC", "FSC Mauritius"), "nbp": True},
    "fxtm": {"name": "FXTM", "regulators": ("FCA", "CySEC", "FSCA", "FSC Mauritius"), "nbp": True},
    "vantage": {"name": "Vantage Markets", "regulators": ("ASIC", "FCA", "CIMA", "VFSC"), "nbp": True},
    "oanda": {"name": "OANDA", "regulators": ("CFTC/NFA", "FCA", "ASIC", "MAS"), "nbp": True},
    "fbs": {"name": "FBS", "regulators": ("CySEC", "ASIC", "FSC Mauritius"), "nbp": True},
    "octafx": {"name": "OctaFX", "regulators": ("CySEC", "FSCA"), "nbp": True},
    "tickmill": {"name": "Tickmill", "regulators": ("FCA", "CySEC", "FSCA", "FSA Seychelles"), "nbp": True},
    "fp markets": {"name": "FP Markets", "regulators": ("ASIC", "CySEC", "FSCA"), "nbp": True},
    "avatrade": {"name": "AvaTrade", "regulators": ("CBI", "ASIC", "FSCA"), "nbp": True},
    "admirals": {"name": "Admirals", "regulators": ("FCA", "ASIC", "CySEC"), "nbp": True},
    "ig": {"name": "IG", "regulators": ("FCA", "ASIC", "CFTC/NFA", "MAS"), "nbp": True},
    "saxo": {"name": "Saxo", "regulators": ("FCA", "ASIC", "MAS"), "nbp": True},
    "cmc": {"name": "CMC Markets", "regulators": ("FCA", "ASIC", "MAS"), "nbp": True},
    "etoro": {"name": "eToro", "regulators": ("FCA", "ASIC", "CySEC"), "nbp": True},
}

BOT_RULES = PITCH_RULES + (
    (RED, "Airdrop / claim", r"airdrop|claim (your|free) (tokens?|reward|bonus)|free (btc|usdt|eth)",
     "Airdrop bots exist to get a wallet connection or a 'gas fee' out of you."),
    (RED, "Verification fee", r"verif(y|ication)[^.]{0,40}(fee|deposit|pay)|pay[^.]{0,20}to (verify|activate)",
     "Verification is never paid for."),
    (YELLOW, "Shortened link", r"bit\.ly|t\.ly|tinyurl|cutt\.ly|rb\.gy|is\.gd",
     "A shortener hides the destination. Real services link to their own domain."),
    (YELLOW, "Crypto address in chat", r"\b(0x[a-fA-F0-9]{40}|T[A-Za-z0-9]{33}|bc1[a-z0-9]{25,60}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
     "A raw address in a bot message is a request to send money to a stranger."),
    (YELLOW, "Impersonation", r"official|support|admin|helpdesk|customer ?care|verify[ _]?b[o0]t|wallet[ _]?b[o0]t",
     "Real support never opens a chat with you first, and never through a lookalike username."),
    (YELLOW, "Lookalike username", r"(?i)(0fficial|0fficia1|offical|suport|supp0rt|bin[a4]nce|c0inbase|te1egram|metamask|trustwa11et|b0t\b|_bot_)",
     "Character swaps that read right at a glance are how lookalikes are made."),
)

COPY_RULES = PITCH_RULES + (
    (RED, "Unregulated / offshore only", r"unregulated|no (license|licence|regulation)|st\.? vincent|svg|marshall islands|comoros|mwali",
     "Unregulated means no one to complain to. SVG and Comoros are the addresses that mean 'none'."),
    (RED, "No negative balance protection", r"no negative balance|nbp (not|un)available|liable for (negative|debit) balance",
     "Without NBP a gap can leave you owing the broker money."),
    (YELLOW, "Hidden spread / markup", r"mark[- ]?up|wider spread|spread (is )?(marked|added)|commission per copy|performance fee",
     "Copy trading is often free because the spread is where they earn. Price it."),
    (YELLOW, "Bonus deposit", r"deposit bonus|\d+ ?% bonus|welcome bonus",
     "Bonuses come with trading-volume conditions that lock the withdrawal."),
    (GOOD, "Negative balance protection stated", r"negative balance protection|\bnbp\b",
     "You cannot lose more than your deposit."),
    (GOOD, "Regulator number stated", r"(fca|asic|cysec|mas|bafin|cbi|nfa)[^.]{0,30}(\d{5,8}|no\.?|number|licen[cs]e)",
     "A number you can look up on the register. Do look it up."),
)

INFLUENCER_RULES = PITCH_RULES + (
    (RED, "Cash-out via 'course' + broker", r"(course|mentorship|masterclass)[^.]{0,60}(deposit|open (an )?account|my link)",
     "The pattern: sell a course, then earn again when you deposit through their link."),
    (YELLOW, "Unverifiable P&L", r"(made|profit(ed)?|earned|banked)\s?\$?\d{1,3}(,\d{3})*(k)?[^.]{0,30}(today|this week|in a day|overnight)",
     "Round numbers, short windows, no account statement."),
    (YELLOW, "Giveaway hook", r"giveaway|free (mentorship|course|signals?) for (the first|first \d+)",
     "The giveaway is the lead magnet for the deposit link."),
    (YELLOW, "Deleted-losses pattern", r"(only|all) (winning|profitable) trades|no losing trades shown",
     "A feed with no losses is a feed with deletions."),
    (GOOD, "Losses shown", r"(losing|lost|drawdown|red day|took a loss)",
     "Showing losses is the cheapest honesty signal there is."),
)

SIGNAL_RULES = PITCH_RULES + (
    (RED, "Accuracy claim", r"\d{2,3} ?% (accura|win ?rate|success)",
     "Win rate without R and drawdown is a marketing number, not a performance number."),
    (YELLOW, "Pips-per-week promise", r"\d{2,4}\+? ?pips (a|per|every) (day|week|month)",
     "Pips are not money. Without lot size and risk it means nothing."),
    (YELLOW, "Free then paid", r"free (for|trial)[^.]{0,30}(then|after)|upgrade to",
     "The free channel exists to convert you to the paid one."),
    (YELLOW, "Copy blindly", r"copy (my|our|the) (trades|signals) (exactly|blindly)|just copy",
     "'Just copy' removes the one thing that protects you: your own sizing."),
)

TABLES = {
    "bot-scam-detector": BOT_RULES,
    "copy-trade-audit": COPY_RULES,
    "red-flag-scanner": SIGNAL_RULES,
    "influencer-audit": INFLUENCER_RULES,
}


def run_rules(text, rules):
    text = text or ""
    found = []
    for flag, label, pattern, why in rules:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 50)
            found.append({"flag": flag, "label": label, "why": why,
                          "snippet": " ".join(text[start:m.end() + 50].split())})
    order = {RED: 0, YELLOW: 1, GOOD: 2}
    found.sort(key=lambda f: order[f["flag"]])
    return found


def score_of(findings, base=0):
    raw = base + sum(WEIGHT[f["flag"]] for f in findings)
    return max(0, min(100, raw))


def verdict_of(score):
    if score >= 60:
        return "HIGH RISK"
    if score >= 30:
        return "CAUTION"
    return "LOW RISK"


def _report(slug, subject, text, findings, base=0, extra=None):
    score = score_of(findings, base)
    return {"product": slug, "subject": subject, "text": text or "", "findings": findings,
            "score": score, "verdict": verdict_of(score),
            "reds": sum(1 for f in findings if f["flag"] == RED),
            "yellows": sum(1 for f in findings if f["flag"] == YELLOW),
            "goods": sum(1 for f in findings if f["flag"] == GOOD),
            **(extra or {})}


CHECKLIST_EN = (
    "Username ends in 'bot' and matches the project's own site exactly",
    "The bot is linked from the project's official website or channel",
    "It never asks for a seed phrase, private key or wallet connection",
    "It never asks for a fee, 'gas' or deposit to verify, claim or unlock",
    "Every link goes to the project's own domain, not a shortener",
)
DEMANDS_EN = (
    "A third-party verified account (Myfxbook / FX Blue), not screenshots",
    "Twelve months of history including the losing months",
    "Maximum drawdown and average R, not win rate",
    "Which broker entity and regulator number the referral link goes to",
)


# --- #4 bot scam ------------------------------------------------------------- #

def audit_bot(handle, text=""):
    handle = (handle or "").strip().lstrip("@")
    findings = run_rules(text, BOT_RULES)
    name_findings = run_rules("@" + handle, BOT_RULES[-2:])   # impersonation + lookalike on the username itself
    for f in name_findings:
        f["label"] += " (username)"
    findings = name_findings + findings
    base = 10 if not handle.lower().endswith("bot") and handle else 0   # Telegram bots must end in "bot"
    if not text.strip():
        base += 0
    return _report("bot-scam-detector", "@" + handle if handle else "(no handle)", text, findings, base,
                   {"checklist": list(CHECKLIST_EN)})


# --- #6 copy-trade ------------------------------------------------------------- #

def _pip_value(lots):
    return lots * 10.0   # standard lot, USD-quoted pair or XAUUSD in $0.01 steps → $10 per pip per lot


def audit_copy(broker, text="", spread_pips=None, lots_per_month=None):
    key = (broker or "").strip().lower()
    known = next((v for k, v in BROKERS.items() if k in key or key in k), None) if key else None
    findings = run_rules(text, COPY_RULES)
    base = 0
    extra = {"broker": known["name"] if known else (broker or "(unnamed)"), "known": bool(known),
             "regulators": [], "tier1": False, "nbp": known["nbp"] if known else None}
    if known:
        extra["regulators"] = [(r,) + REGULATORS[r] for r in known["regulators"]]
        extra["tier1"] = any(r in TIER1 for r in known["regulators"])
        if not extra["tier1"]:
            base += 20
            findings.insert(0, {"flag": YELLOW, "label": "Offshore-only licences", "why": "No tier-1 regulator in our table for this broker. Check the registers before depositing.", "snippet": ", ".join(known["regulators"])})
        if known["nbp"]:
            findings.append({"flag": GOOD, "label": "Negative balance protection (known)", "why": "Listed as offering NBP on retail accounts. Confirm for your entity.", "snippet": known["name"]})
    else:
        base += 30
        findings.insert(0, {"flag": YELLOW, "label": "Broker not in our table", "why": "Unknown is not bad — but you must verify the licence number on the official register yourself.", "snippet": broker or ""})
    cost = None
    if spread_pips is not None and lots_per_month is not None:
        try:
            sp, lots = float(spread_pips), float(lots_per_month)
            monthly = sp * _pip_value(lots)
            cost = {"spread_pips": sp, "lots": lots, "monthly": monthly, "yearly": monthly * 12}
        except ValueError:
            cost = None
    extra["cost"] = cost
    extra["registers"] = [(r,) + REGULATORS[r] for r in TIER1]
    return _report("copy-trade-audit", extra["broker"], text, findings, base, extra)


# --- #7 signal pitch ----------------------------------------------------------- #

def scan_pitch(text):
    findings = run_rules(text, SIGNAL_RULES)
    return _report("red-flag-scanner", (text or "").strip()[:60] or "(empty)", text, findings)


# --- #9 influencer ------------------------------------------------------------- #

def audit_influencer(handle, text=""):
    handle = (handle or "").strip().lstrip("@")
    findings = run_rules(text, INFLUENCER_RULES)
    ibs = re.findall(r"https?://\S*(?:refid|ref=|/ref/|invitecode|affid)[^\s]*", text or "", re.IGNORECASE)
    return _report("influencer-audit", "@" + handle if handle else "(no handle)", text, findings, 0,
                   {"broker_links": ibs, "demands": list(DEMANDS_EN)})


def loss_report(handle, platform, amount, currency, date, story, broker=""):
    """Plain-text report in the shape FTC (reportfraud.ftc.gov), CFTC and IC3 forms ask for."""
    lines = [
        "SCAM LOSS REPORT — prepared with SAMBANGGOLD #9",
        "",
        "Subject: %s" % (handle or "(unknown)"),
        "Platform: %s" % (platform or "(unknown)"),
        "Broker / venue promoted: %s" % (broker or "(none named)"),
        "Amount lost: %s %s" % (amount or "?", currency or ""),
        "Date(s): %s" % (date or "?"),
        "",
        "What happened (chronological):",
        story.strip() or "(describe: first contact, what was promised, what you paid, what happened after)",
        "",
        "Evidence attached: screenshots of the promotion, payment receipts, chat export, referral link.",
        "",
        "Where to file:",
        "  US FTC     https://reportfraud.ftc.gov/",
        "  US CFTC    https://www.cftc.gov/complaint",
        "  FBI IC3    https://www.ic3.gov/",
        "  Malaysia   https://www.sc.com.my/  (Securities Commission) · https://portal.bnm.gov.my/ (BNM)",
        "  Singapore  https://www.police.gov.sg/i-witness",
        "",
        "Educational research only. Not legal advice.",
    ]
    return "\n".join(lines)


# --- Bahasa Melayu ------------------------------------------------------------- #
# Findings are stored in English (the canonical report); the surfaces localise
# them at render time. Keyed by the English label.

MS = {
    "Guaranteed returns": ("Untung dijamin", "Tiada siapa boleh jamin hasil pasaran. Ini penanda scam paling boleh dipercayai."),
    "Fee to withdraw": ("Yuran untuk keluarkan duit", "Broker sah tak pernah caj anda untuk terima duit anda sendiri."),
    "Wallet / key request": ("Minta wallet / private key", "Tiada servis perlukan key anda atau transfer ke alamat untuk 'sahkan' apa-apa."),
    "Urgency": ("Desakan masa", "Tarikh akhir rekaan wujud untuk halang anda daripada menyemak."),
    "Screenshot as proof": ("Screenshot sebagai bukti", "Screenshot boleh diedit dalam beberapa saat. Minta rekod langsung yang disahkan."),
    "Lifestyle bait": ("Umpan gaya hidup", "Imej mewah jual impian, bukan kaedah."),
    "Move to private chat": ("Ajak ke chat peribadi", "Chat peribadi buang orang ramai yang boleh beri amaran kepada anda."),
    "Paid VIP tier": ("Tier VIP berbayar", "Bukan scam dengan sendirinya, tetapi di sinilah duit diminta."),
    "Double / multiply": ("Gandakan modal", "Dakwaan kompaun tanpa drawdown tak wujud."),
    "Referral / IB link": ("Pautan rujukan / IB", "Pitch ini dibayar broker setiap deposit. Tak salah — tetapi itulah model bisnesnya."),
    "Verified track record link": ("Pautan rekod disahkan", "Akaun yang disahkan pihak ketiga ialah satu-satunya bukti yang tak boleh diedit."),
    "Risk disclosure present": ("Ada pendedahan risiko", "Penjual jujur sebut. Scammer tak pernah."),
    "Airdrop / claim": ("Airdrop / claim", "Bot airdrop wujud untuk dapatkan sambungan wallet atau 'yuran gas' daripada anda."),
    "Verification fee": ("Yuran verifikasi", "Verifikasi tak pernah berbayar."),
    "Shortened link": ("Pautan dipendekkan", "Pemendek pautan sembunyikan destinasi. Servis sebenar paut ke domain sendiri."),
    "Crypto address in chat": ("Alamat crypto dalam chat", "Alamat mentah dalam mesej bot ialah permintaan hantar duit kepada orang asing."),
    "Impersonation": ("Menyamar", "Support sebenar tak pernah mulakan chat dengan anda, dan tak pernah guna username tiruan."),
    "Lookalike username": ("Username tiruan", "Tukar huruf yang nampak betul sekali pandang — begitulah tiruan dibuat."),
    "Impersonation (username)": ("Menyamar (username)", "Support sebenar tak pernah mulakan chat dengan anda, dan tak pernah guna username tiruan."),
    "Lookalike username (username)": ("Username tiruan (username)", "Tukar huruf yang nampak betul sekali pandang — begitulah tiruan dibuat."),
    "Unregulated / offshore only": ("Tanpa lesen / offshore sahaja", "Tanpa lesen bermakna tiada tempat mengadu. SVG dan Comoros ialah alamat yang bermaksud 'tiada'."),
    "No negative balance protection": ("Tiada negative balance protection", "Tanpa NBP, gap boleh buat anda berhutang dengan broker."),
    "Hidden spread / markup": ("Spread / markup tersembunyi", "Copy trading selalunya percuma sebab spread ialah tempat mereka untung. Kira kosnya."),
    "Bonus deposit": ("Bonus deposit", "Bonus datang dengan syarat volum yang kunci pengeluaran."),
    "Negative balance protection stated": ("NBP dinyatakan", "Anda tak boleh rugi lebih daripada deposit."),
    "Regulator number stated": ("Nombor lesen dinyatakan", "Nombor yang boleh disemak di daftar. Semaklah."),
    "Offshore-only licences": ("Lesen offshore sahaja", "Tiada regulator tier-1 dalam jadual kami untuk broker ini. Semak daftar sebelum deposit."),
    "Broker not in our table": ("Broker tiada dalam jadual kami", "Tak dikenali bukan bermakna buruk — tetapi anda mesti sahkan nombor lesen di daftar rasmi sendiri."),
    "Negative balance protection (known)": ("Negative balance protection (diketahui)", "Disenaraikan menawarkan NBP pada akaun runcit. Sahkan untuk entiti anda."),
    "Cash-out via 'course' + broker": ("Untung melalui 'kursus' + broker", "Coraknya: jual kursus, kemudian untung lagi bila anda deposit melalui pautan mereka."),
    "Unverifiable P&L": ("P&L tak boleh disahkan", "Nombor bulat, tempoh singkat, tiada penyata akaun."),
    "Giveaway hook": ("Umpan giveaway", "Giveaway ialah umpan untuk pautan deposit."),
    "Deleted-losses pattern": ("Corak rugi dipadam", "Feed tanpa kerugian ialah feed yang ada pemadaman."),
    "Losses shown": ("Kerugian ditunjukkan", "Tunjuk kerugian ialah isyarat kejujuran paling murah."),
    "Accuracy claim": ("Dakwaan ketepatan", "Win rate tanpa R dan drawdown ialah nombor marketing, bukan prestasi."),
    "Pips-per-week promise": ("Janji pip seminggu", "Pip bukan duit. Tanpa saiz lot dan risiko ia tak bermakna."),
    "Free then paid": ("Percuma kemudian berbayar", "Channel percuma wujud untuk tukar anda ke yang berbayar."),
    "Copy blindly": ("Copy membuta tuli", "'Copy je' buang satu-satunya perlindungan anda: saiz posisi anda sendiri."),
}

CHECKLIST_MS = (
    "Username berakhir dengan 'bot' dan sama tepat dengan laman rasmi projek",
    "Bot dipaut dari laman web atau channel rasmi projek",
    "Ia tak pernah minta seed phrase, private key atau sambungan wallet",
    "Ia tak pernah minta yuran, 'gas' atau deposit untuk sahkan, claim atau buka",
    "Setiap pautan ke domain projek sendiri, bukan pemendek pautan",
)
DEMANDS_MS = (
    "Akaun yang disahkan pihak ketiga (Myfxbook / FX Blue), bukan screenshot",
    "Dua belas bulan sejarah termasuk bulan yang rugi",
    "Drawdown maksimum dan purata R, bukan win rate",
    "Entiti broker dan nombor regulator mana yang pautan rujukan itu tuju",
)


def localise(findings, lang="ms"):
    """Copies of the findings with label and reason in `lang`."""
    if lang != "ms":
        return findings
    out = []
    for f in findings:
        label, why = MS.get(f["label"], (f["label"], f["why"]))
        out.append({**f, "label": label, "why": why})
    return out


def checklist(lang="ms"):
    return list(CHECKLIST_MS) if lang == "ms" else list(CHECKLIST_EN)


def demands(lang="ms"):
    return list(DEMANDS_MS) if lang == "ms" else list(DEMANDS_EN)
