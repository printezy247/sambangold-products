"""SAMBANGGOLD brand: one place for the name, the tokens and every user-facing string.

Mirrors ``src/config/brand.ts`` and ``messages/{ms,en}.json`` in the website repo
so the dashboard, the bot and the site read as one product. Bahasa Melayu is the
default; English is the second language. Product names, rank names and brand
names stay untranslated — only the surrounding words change.
"""

BRAND = {
    "name": "SAMBANGGOLD",
    "short": "SBG",
    "person": "Sam",
    "since": 2022,
    "tagline": {"ms": "Alat emas, telus.", "en": "Gold tools, transparent."},
    "group": "Sam Flip Seribu",
}

# Sam's palette, verbatim from the website's globals.css.
TOKENS = {
    "bg": "#050505", "surface": "#0b0e14", "surface2": "#11151d", "border": "#1e2330",
    "fg": "#f3f4f6", "muted": "#9aa3b2", "gold": "#d4af37", "gold2": "#f5d76e",
    "gold_deep": "#7a4003", "win": "#00c46a", "loss": "#ff4d4f", "chrome": "#b7c0ce",
    "graphite": "#050609",
}

# Rank vocabulary from the website: Awam (public) → General (free) → A-Team → Rambo.
RANKS = {
    "public": {"ms": "Awam", "en": "Public"},
    "free": {"ms": "General", "en": "General"},
    "pro": {"ms": "A-Team", "en": "A-Team"},
    "elite": {"ms": "Rambo", "en": "Rambo"},
}

LANGS = ("ms", "en")
DEFAULT_LANG = "ms"

STRINGS = {
    "ms": {
        # nav
        "nav.products": "Produk", "nav.dashboard": "Dashboard", "nav.account": "Akaun",
        "nav.signin": "Log masuk", "nav.signout": "Log keluar", "nav.admin": "Admin",
        "nav.cta": "Buka bot", "nav.lang": "EN",
        # landing
        "hero.badge": "Sejak {since} · SAMBANGGOLD · 18 alat emas",
        "hero.title": "Alat emas, telus.", "hero.title2": "Dua permukaan.",
        "hero.subtitle": "Setiap alat menjawab di Telegram dan mempunyai halaman sendiri di sini. Satu akaun Telegram menyambungkan kedua-duanya. Semua ada tier percuma, tiada yang dikunci di pintu.",
        "hero.cta_primary": "Buka bot Telegram", "hero.cta_secondary": "Lihat semua alat",
        "hero.note": "Pendidikan sahaja. Bukan nasihat kewangan.",
        "stats.products": "Alat", "stats.live": "Sudah hidup", "stats.free": "Tier percuma", "stats.since": "Sejak",
        "doors.title": "Dua cara guna", "doors.subtitle": "Sama alat, sama tier percuma. Pilih di mana anda mahu jawapan itu sampai.",
        "doors.a_title": "🤖 Di Telegram", "doors.a_body": "Satu arahan, satu jawapan. Alert masuk terus ke chat anda.", "doors.a_cta": "Buka bot",
        "doors.b_title": "🌐 Di dashboard", "doors.b_body": "Sejarah, tetapan, eksport CSV. Semua yang chat tak boleh simpan.", "doors.b_cta": "Log masuk",
        "grid.title": "Lapan belas alat", "grid.subtitle": "Sembilan sudah hidup. Sembilan lagi dalam giliran — spesifikasi ditulis, halaman ditempah.",
        "grid.live": "Hidup", "grid.queued": "Giliran", "grid.open": "Buka",
        "faq.title": "Soalan lazim",
        "faq.q1": "Perlu bayar ke?", "faq.a1": "Tidak. Setiap alat ada tier percuma yang berfungsi sepenuhnya. Tier berbayar jual skala dan automasi sahaja.",
        "faq.q2": "Kenapa perlu akaun Telegram?", "faq.a2": "Supaya alert dari bot dan sejarah di dashboard adalah satu senarai. Boleh juga daftar dengan emel dan pautkan Telegram kemudian.",
        "faq.q3": "Data harga dari mana?", "faq.a3": "Binance PAXGUSDT (bid dan ask sebenar) dengan Yahoo Finance GC=F sebagai sandaran. Kedua-duanya percuma dan awam.",
        "faq.q4": "Ini nasihat kewangan?", "faq.a4": "Bukan. Semua ini untuk pendidikan. Sahkan setiap harga dengan broker anda sendiri.",
        # sign-in
        "signin.title": "Log masuk", "signin.subtitle": "Telegram, emel, atau Google. Tiada kata laluan.",
        "signin.telegram": "Log masuk dengan Telegram", "signin.telegram_hint": "Butang ini ingat akaun Telegram terakhir. Untuk tukar: app Telegram → Tetapan → Privasi & Keselamatan → Laman web → putuskan sambungan.",
        "signin.email_label": "Emel anda", "signin.email_cta": "Hantar kod 8 digit",
        "signin.email_hint": "Kami hantar kod 8 digit ke emel anda. Sah selama 10 minit.",
        "signin.google": "Teruskan dengan Google", "signin.google_soon": "Akan datang",
        "signin.or": "atau",
        "verify.title": "Semak emel anda", "verify.subtitle": "Kod 8 digit dihantar ke {email}.",
        "verify.code_label": "Kod", "verify.cta": "Sahkan & masuk", "verify.resend": "Hantar semula",
        "verify.wrong": "Kod salah atau sudah tamat. Cuba lagi.", "verify.too_many": "Terlalu banyak cubaan. Minta kod baharu.",
        "verify.cooldown": "Tunggu seminit sebelum minta kod baharu.", "verify.bad_email": "Emel tidak sah.",
        "verify.mail_down": "Emel tidak dapat dihantar buat masa ini. Guna Telegram, atau cuba sebentar lagi.",
        "verify.sent": "Kod dihantar.", "verify.dev_code": "Mod dev — kod anda: {code}",
        "google.title": "Google — akan datang", "google.body": "Log masuk Google sedang disediakan. Guna Telegram atau emel buat masa ini.",
        # dashboard
        "dash.title": "Dashboard ahli", "dash.subtitle": "Alat anda, alert anda, rekod anda.",
        "dash.rank": "Pangkat semasa", "dash.member_since": "Ahli sejak", "dash.upgrade": "Naik ke A-Team untuk automasi",
        "dash.alerts": "Alert aktif", "dash.triggers": "Alert dicetus", "dash.saved": "Perbandingan disimpan", "dash.linked": "Telegram dipautkan",
        "dash.live": "Alat hidup", "dash.queued": "Dalam giliran", "dash.open": "Buka alat",
        "dash.link_tg": "Pautkan Telegram supaya alert masuk ke chat anda.", "dash.link_email": "Tambah emel supaya anda boleh log masuk tanpa Telegram.",
        "dash.not_linked": "Belum dipautkan",
        # account
        "account.title": "Akaun", "account.email": "Emel", "account.telegram": "Telegram", "account.lang": "Bahasa",
        "account.none": "Tiada", "account.signout": "Log keluar", "account.admin": "Anda admin. Semua ciri terbuka.",
        # admin
        "admin.title": "Admin", "admin.subtitle": "Setiap akaun, emel dan pautan Telegram.",
        "admin.users": "Akaun", "admin.emails": "Dengan emel", "admin.telegrams": "Dengan Telegram", "admin.starts": "Bot /start",
        "admin.export": "Eksport CSV", "admin.col_email": "Emel", "admin.col_tg": "Telegram", "admin.col_name": "Nama",
        "admin.col_lang": "Bahasa", "admin.col_created": "Daftar", "admin.col_last": "Log masuk akhir",
        # product page
        "product.bot_half": "Separuh Telegram", "product.web_half": "Separuh dashboard", "product.free": "Tier percuma",
        "product.live_note": "Hidup di bawah — nombor yang sama bot berikan.",
        "product.soon": "Panel akan hidup apabila setiap paparan disambung ke data.",
        "product.queued": "Dalam giliran — spesifikasi ditulis, permukaan ditempah.",
        "product.upsell": "Naik taraf", "product.upsell_note": "Tier berbayar jual skala dan automasi sahaja, bukan akses asas.",
        "product.back": "Semua alat", "product.signin": "Log masuk untuk simpan dan eksport.",
        # footer
        "footer.legal": "Undang-undang", "footer.risk": "Pendedahan risiko", "footer.rights": "Untuk pendidikan sahaja. Bukan nasihat kewangan.",
        "risk.strip": "Dagangan emas, forex dan CFD secara margin melibatkan risiko yang tinggi dan anda boleh kehilangan lebih daripada deposit awal. Prestasi lepas bukan petunjuk prestasi akan datang. Semua kandungan adalah untuk tujuan pendidikan sahaja dan bukan nasihat kewangan. Sahkan setiap harga dengan broker anda.",
        # email
        "mail.subject": "Kod log masuk {brand} anda: {code}",
        "mail.body": "Kod log masuk anda: {code}\n\nSah selama 10 minit. Jika anda tidak minta kod ini, abaikan emel ini.\n\n{brand} · Pendidikan sahaja. Bukan nasihat kewangan.",
        # bot
        "bot.pick_lang": "🌐 Pilih bahasa / Choose your language:",
        "bot.lang_set": "Bahasa ditukar ke Bahasa Melayu.",
        "bot.welcome": "<b>{brand}</b>. 18 alat emas, setiap satu menjawab di sini dan di dashboard.\n\nSemua ada tier percuma. Tiada yang dikunci di pintu.\n\n⚠️ Dagangan CFD berisiko tinggi. Pendidikan sahaja, bukan nasihat kewangan.",
        "bot.menu": "Apa yang anda mahu buat?",
        "bot.btn_tools": "🥇 Cuba alat percuma", "bot.btn_dash": "🌐 Buka dashboard", "bot.btn_faq": "❓ Soalan lazim",
        "bot.btn_channel": "📢 Channel awam", "bot.btn_back": "⬅️ Kembali", "bot.btn_menu": "⬅️ Menu Utama",
        "bot.btn_try": "▶️ Cuba contoh", "bot.btn_open": "🌐 Buka di dashboard", "bot.btn_share": "📤 Kongsi", "bot.btn_again": "🔁 Cuba lagi",
        "bot.btn_more": "🔮 Lihat yang dalam giliran",
        "bot.tools": "<b>Alat yang sudah hidup</b>\nPilih satu. Setiap satu percuma.",
        "bot.queued": "<b>Dalam giliran</b>\nSpesifikasi ditulis, halaman ditempah. Bot akan jawab bila hidup.",
        "bot.tool_card": "{emoji} <b>{name}</b>\n{solution}\n\n<b>Tier percuma:</b> {free}\n<b>Arahan:</b> <code>{command}</code>",
        "bot.faq": "<b>Soalan lazim</b>\n\n<b>Perlu bayar ke?</b> Tidak. Setiap alat ada tier percuma yang berfungsi sepenuhnya.\n\n<b>Kenapa Telegram?</b> Supaya alert di sini dan sejarah di dashboard adalah satu senarai.\n\n<b>Data harga?</b> Binance PAXGUSDT, sandaran Yahoo GC=F. Percuma dan awam.\n\n<b>Nasihat kewangan?</b> Bukan. Pendidikan sahaja.",
        "bot.help": "<b>Arahan</b>", "bot.help_tail": "/start — menu · /language — tukar bahasa · /dashboard — pautan dashboard\n\nPendidikan sahaja. Bukan nasihat kewangan.",
        "bot.dash": "Dashboard anda. Log masuk dengan Telegram — akaun yang sama, senarai alert yang sama.",
        "bot.unknown": "Arahan tak dikenali. Hantar /start untuk menu.",
        "bot.queued_reply": "{emoji} <b>{name}</b> — dalam giliran.\n{solution}",
        "bot.result_tail": "Simpan, eksport dan bandingkan di dashboard.",
        "bot.share_text": "Saya guna {brand} untuk emas. Cuba percuma:",
        # calendar
        "cal.title": "📅 <b>Kalendar emas</b>",
        "cal.next": "Acara USD merah seterusnya", "cal.none": "Tiada acara merah dalam suapan minggu ini.",
        "cal.fomc": "FOMC seterusnya", "cal.holiday": "Cuti CME seterusnya", "cal.season": "Bulan ini (purata {n} tahun)",
        "cal.season_line": "pulangan {ret:+.1f}% · julat {rng:.1f}%",
        "cal.on": "🔔 Alert 30 minit sebelum: <b>HIDUP</b>", "cal.off": "🔕 Alert 30 minit sebelum: <b>MATI</b>",
        "cal.btn_on": "🔔 Hidupkan alert", "cal.btn_off": "🔕 Matikan alert",
        "cal.push": "⏰ <b>{title}</b> dalam 30 minit ({when} MYT).\nSpread biasanya melebar. Pendidikan sahaja.",
        "cal.need_chat": "Alert perlukan chat Telegram. Buka bot dan hantar /calendar_alert.",
        "cal.spread_note": "Spread diukur setiap 5 minit; sejarah setiap acara terkumpul dari sini.",
        # scanners
        "scan.score": "skor", "scan.subject": "Subjek",
        "scan.verdict_high": "RISIKO TINGGI", "scan.verdict_caution": "BERHATI-HATI", "scan.verdict_low": "RISIKO RENDAH",
        "scan.more": "… {n} lagi penemuan di dashboard.", "scan.clean": "Tiada bendera dijumpai dalam teks ini. Itu bukan bukti selamat.",
        "scan.saved": "Disimpan sebagai imbasan #{n} — sejarah dan senarai pantau ada di dashboard.",
        "scan.disclaimer": "Pendidikan sahaja. Bukan nasihat kewangan.",
        "scan.usage_audit": "Guna: <code>/audit @nama_bot [apa yang bot itu kata]</code>\nContoh: <code>/audit @wallet_verify_b0t hantar seed phrase untuk claim</code>",
        "scan.usage_copy": "Guna: <code>/copyaudit BROKER [SPREAD_PIP] [LOT_SEBULAN]</code>\nContoh: <code>/copyaudit exness 2 10</code>",
        "scan.usage_scan": "Guna: <code>/scan TEKS</code> — tampal pitch signal (sekurang-kurangnya satu ayat).",
        "scan.usage_influencer": "Guna: <code>/influencer @handle [teks post atau DM]</code>",
        "scan.tail_audit": "Semak: nama berakhir 'bot', dipaut dari laman rasmi, tak pernah minta seed phrase atau yuran.",
        "scan.tail_copy": "Sahkan nombor lesen di daftar pengawal selia sebelum deposit.",
        "scan.tail_scan": "Minta akaun Myfxbook/FX Blue yang disahkan. Tangkapan skrin bukan bukti.",
        "scan.regs": "Pengawal selia dalam jadual kami: {regs}",
        "scan.cost": "Kos spread: {pips:g} pip × {lots:g} lot ≈ <b>${monthly:,.0f}/bulan</b> · ${yearly:,.0f}/tahun",
        "scan.demand": "Minta daripada mereka:",
        "scan.ib_links": "🔗 {n} pautan rujukan broker dijumpai — mereka dibayar bila anda deposit.",
    },
    "en": {
        "nav.products": "Tools", "nav.dashboard": "Dashboard", "nav.account": "Account",
        "nav.signin": "Sign in", "nav.signout": "Sign out", "nav.admin": "Admin",
        "nav.cta": "Open bot", "nav.lang": "BM",
        "hero.badge": "Since {since} · SAMBANGGOLD · 18 gold tools",
        "hero.title": "Gold tools, transparent.", "hero.title2": "Two surfaces.",
        "hero.subtitle": "Every tool answers in Telegram and has its own page here. One Telegram account links the two. All have a free tier; none is locked at the door.",
        "hero.cta_primary": "Open the Telegram bot", "hero.cta_secondary": "See every tool",
        "hero.note": "Education only. Not financial advice.",
        "stats.products": "Tools", "stats.live": "Live", "stats.free": "Free tiers", "stats.since": "Since",
        "doors.title": "Two ways to use it", "doors.subtitle": "Same tool, same free tier. Pick where you want the answer to land.",
        "doors.a_title": "🤖 In Telegram", "doors.a_body": "One command, one answer. Alerts land in your chat.", "doors.a_cta": "Open bot",
        "doors.b_title": "🌐 On the dashboard", "doors.b_body": "History, settings, CSV export. Everything a chat cannot keep.", "doors.b_cta": "Sign in",
        "grid.title": "Eighteen tools", "grid.subtitle": "Nine are live. Nine are queued — spec written, page reserved.",
        "grid.live": "Live", "grid.queued": "Queued", "grid.open": "Open",
        "faq.title": "FAQ",
        "faq.q1": "Do I have to pay?", "faq.a1": "No. Every tool has a fully working free tier. Paid tiers sell scale and automation only.",
        "faq.q2": "Why a Telegram account?", "faq.a2": "So bot alerts and dashboard history are one list. You can also sign up by email and link Telegram later.",
        "faq.q3": "Where does the price come from?", "faq.a3": "Binance PAXGUSDT (real bid and ask) with Yahoo Finance GC=F as fallback. Both free and public.",
        "faq.q4": "Is this financial advice?", "faq.a4": "No. Education only. Verify every price with your own broker.",
        "signin.title": "Sign in", "signin.subtitle": "Telegram, email, or Google. No password.",
        "signin.telegram": "Sign in with Telegram", "signin.telegram_hint": "This button remembers the last Telegram account. To switch: Telegram app → Settings → Privacy & Security → Websites → disconnect this site.",
        "signin.email_label": "Your email", "signin.email_cta": "Send 8-digit code",
        "signin.email_hint": "We email you an 8-digit code. Valid for 10 minutes.",
        "signin.google": "Continue with Google", "signin.google_soon": "Coming soon",
        "signin.or": "or",
        "verify.title": "Check your email", "verify.subtitle": "An 8-digit code was sent to {email}.",
        "verify.code_label": "Code", "verify.cta": "Verify & enter", "verify.resend": "Resend",
        "verify.wrong": "Wrong or expired code. Try again.", "verify.too_many": "Too many attempts. Request a new code.",
        "verify.cooldown": "Wait a minute before requesting another code.", "verify.bad_email": "Invalid email.",
        "verify.mail_down": "Email cannot be sent right now. Use Telegram, or try again shortly.",
        "verify.sent": "Code sent.", "verify.dev_code": "Dev mode — your code: {code}",
        "google.title": "Google — coming soon", "google.body": "Google sign-in is being set up. Use Telegram or email for now.",
        "dash.title": "Member dashboard", "dash.subtitle": "Your tools, your alerts, your record.",
        "dash.rank": "Current rank", "dash.member_since": "Member since", "dash.upgrade": "Move up to A-Team for automation",
        "dash.alerts": "Armed alerts", "dash.triggers": "Alerts fired", "dash.saved": "Saved comparisons", "dash.linked": "Telegram linked",
        "dash.live": "Live tools", "dash.queued": "Queued", "dash.open": "Open tool",
        "dash.link_tg": "Link Telegram so alerts land in your chat.", "dash.link_email": "Add an email so you can sign in without Telegram.",
        "dash.not_linked": "Not linked",
        "account.title": "Account", "account.email": "Email", "account.telegram": "Telegram", "account.lang": "Language",
        "account.none": "None", "account.signout": "Sign out", "account.admin": "You are admin. Every feature is open.",
        "admin.title": "Admin", "admin.subtitle": "Every account, email and Telegram link.",
        "admin.users": "Accounts", "admin.emails": "With email", "admin.telegrams": "With Telegram", "admin.starts": "Bot /start",
        "admin.export": "Export CSV", "admin.col_email": "Email", "admin.col_tg": "Telegram", "admin.col_name": "Name",
        "admin.col_lang": "Lang", "admin.col_created": "Joined", "admin.col_last": "Last sign-in",
        "product.bot_half": "Telegram half", "product.web_half": "Dashboard half", "product.free": "Free tier",
        "product.live_note": "Live below — the same numbers the bot returns.",
        "product.soon": "Panels come online as each view is wired to data.",
        "product.queued": "Queued — the spec is written, the surface is reserved.",
        "product.upsell": "Upgrade", "product.upsell_note": "Paid tiers sell scale and automation only, never basic access.",
        "product.back": "All tools", "product.signin": "Sign in to save and export.",
        "footer.legal": "Legal", "footer.risk": "Risk disclosure", "footer.rights": "Education only. Not financial advice.",
        "risk.strip": "Trading gold, forex and CFDs on margin carries a high level of risk and you could lose more than your initial deposit. Past performance is not indicative of future results. All content is for education only and is not financial advice. Verify every price with your broker.",
        "mail.subject": "Your {brand} sign-in code: {code}",
        "mail.body": "Your sign-in code: {code}\n\nValid for 10 minutes. If you did not request it, ignore this email.\n\n{brand} · Education only. Not financial advice.",
        "bot.pick_lang": "🌐 Choose your language / Pilih bahasa anda:",
        "bot.lang_set": "Language set to English.",
        "bot.welcome": "<b>{brand}</b>. 18 gold tools, each answering here and on the dashboard.\n\nAll have a free tier. None is locked at the door.\n\n⚠️ CFD trading carries high risk. Education only, not financial advice.",
        "bot.menu": "What do you want to do?",
        "bot.btn_tools": "🥇 Try a free tool", "bot.btn_dash": "🌐 Open dashboard", "bot.btn_faq": "❓ FAQ",
        "bot.btn_channel": "📢 Public channel", "bot.btn_back": "⬅️ Back", "bot.btn_menu": "⬅️ Main Menu",
        "bot.btn_try": "▶️ Try an example", "bot.btn_open": "🌐 Open on dashboard", "bot.btn_share": "📤 Share", "bot.btn_again": "🔁 Try again",
        "bot.btn_more": "🔮 See what is queued",
        "bot.tools": "<b>Tools that are live</b>\nPick one. Each is free.",
        "bot.queued": "<b>Queued</b>\nSpec written, page reserved. The bot answers once each is live.",
        "bot.tool_card": "{emoji} <b>{name}</b>\n{solution}\n\n<b>Free tier:</b> {free}\n<b>Command:</b> <code>{command}</code>",
        "bot.faq": "<b>FAQ</b>\n\n<b>Do I have to pay?</b> No. Every tool has a fully working free tier.\n\n<b>Why Telegram?</b> So alerts here and history on the dashboard are one list.\n\n<b>Price data?</b> Binance PAXGUSDT, Yahoo GC=F fallback. Free and public.\n\n<b>Financial advice?</b> No. Education only.",
        "bot.help": "<b>Commands</b>", "bot.help_tail": "/start — menu · /language — switch language · /dashboard — dashboard link\n\nEducation only. Not financial advice.",
        "bot.dash": "Your dashboard. Sign in with Telegram — same account, same alert list.",
        "bot.unknown": "Unknown command. Send /start for the menu.",
        "bot.queued_reply": "{emoji} <b>{name}</b> — queued.\n{solution}",
        "bot.result_tail": "Save, export and compare on the dashboard.",
        "bot.share_text": "I use {brand} for gold. Try it free:",
        "cal.title": "📅 <b>Gold calendar</b>",
        "cal.next": "Next red USD events", "cal.none": "No red events in this week's feed.",
        "cal.fomc": "Next FOMC", "cal.holiday": "Next CME holiday", "cal.season": "This month ({n}-year average)",
        "cal.season_line": "return {ret:+.1f}% · range {rng:.1f}%",
        "cal.on": "🔔 30-minute alert: <b>ON</b>", "cal.off": "🔕 30-minute alert: <b>OFF</b>",
        "cal.btn_on": "🔔 Turn alerts on", "cal.btn_off": "🔕 Turn alerts off",
        "cal.push": "⏰ <b>{title}</b> in 30 minutes ({when} MYT).\nSpreads usually widen. Education only.",
        "cal.need_chat": "Alerts need a Telegram chat. Open the bot and send /calendar_alert.",
        "cal.spread_note": "Spread is sampled every 5 minutes; per-event history builds from here.",
        "scan.score": "score", "scan.subject": "Subject",
        "scan.verdict_high": "HIGH RISK", "scan.verdict_caution": "CAUTION", "scan.verdict_low": "LOW RISK",
        "scan.more": "… {n} more findings on the dashboard.", "scan.clean": "No flags found in this text. That is not proof it is safe.",
        "scan.saved": "Saved as scan #{n} — history and watchlist are on the dashboard.",
        "scan.disclaimer": "Education only. Not financial advice.",
        "scan.usage_audit": "Usage: <code>/audit @bot_username [what the bot said]</code>\nExample: <code>/audit @wallet_verify_b0t send your seed phrase to claim</code>",
        "scan.usage_copy": "Usage: <code>/copyaudit BROKER [SPREAD_PIPS] [LOTS_PER_MONTH]</code>\nExample: <code>/copyaudit exness 2 10</code>",
        "scan.usage_scan": "Usage: <code>/scan TEXT</code> — paste the signal pitch (at least one sentence).",
        "scan.usage_influencer": "Usage: <code>/influencer @handle [their post or DM]</code>",
        "scan.tail_audit": "Check: name ends in 'bot', linked from the official site, never asks for a seed phrase or a fee.",
        "scan.tail_copy": "Verify the licence number on the regulator's register before you deposit.",
        "scan.tail_scan": "Ask for a verified Myfxbook / FX Blue account. Screenshots are not proof.",
        "scan.regs": "Regulators in our table: {regs}",
        "scan.cost": "Spread cost: {pips:g} pips × {lots:g} lots ≈ <b>${monthly:,.0f}/month</b> · ${yearly:,.0f}/year",
        "scan.demand": "Demand from them:",
        "scan.ib_links": "🔗 {n} broker referral link(s) found — they get paid when you deposit.",
    },
}


def t(key, lang=DEFAULT_LANG, **kwargs):
    """Look a string up in `lang`, falling back to Bahasa Melayu, then to the key."""
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    text = table.get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    return text.format(brand=BRAND["name"], since=BRAND["since"], **kwargs) if ("{" in text) else text


def rank_label(rank, lang=DEFAULT_LANG):
    return RANKS.get(rank, RANKS["public"]).get(lang) or RANKS["public"]["ms"]


def normalise_lang(code):
    """Telegram language codes → our two. Indonesian reads Malay comfortably."""
    code = (code or "").lower()
    if code.startswith(("ms", "id")):
        return "ms"
    if code.startswith("en"):
        return "en"
    return None
