"""#17 Tokenized Gold — the bot readouts, the wallet check, the premium log, the dashboard."""

import time

from . import premium, store, tokengold
from .brand import DEFAULT_LANG, t

SLUG = "tokenized-gold"


def _fmt(x):
    return format(x, ",.2f") if x is not None else "—"


def _pct(x):
    return ("%+.2f%%" % x) if x is not None else "—"


def readout_lines(a, lang):
    lines = [t("tk.head", lang, paxg=_fmt(a.get("paxg")), xaut=_fmt(a.get("xaut")), spot=_fmt(a.get("spot")))]
    lines.append(t("tk.premium", lang, paxg=_pct(a["paxg_premium"]), xaut=_pct(a["xaut_premium"]), spread=_pct(a["paxg_xaut"])))
    if a.get("usdt") is not None:
        lines.append(t("tk.peg_" + a["peg"], lang, usdt=format(a["usdt"], ".4f"), off=_pct(a["usdt_off"])))
    for f in a["flags"]:
        lines.append(t("tk.f_" + f, lang, pct=tokengold.PREMIUM_WARN))
    if a.get("errors"):
        lines.append(t("tk.partial", lang, n=len(a["errors"])))
    lines.append(t("tk.basis", lang))
    return lines


def _analysed(max_age=tokengold.CACHE_SECONDS):
    return tokengold.analyse(tokengold.snapshot(max_age))


def bot_paxg(args, chat_id=None, lang=DEFAULT_LANG, **_):
    try:
        a = _analysed()
    except tokengold.FeedError:
        return t("tk.down", lang)
    # The number alone is not the answer. Where it sits in its own range is.
    return "\n".join(readout_lines(a, lang) + [""] + premium.lines(a, lang=lang) + [t("scan.disclaimer", lang)])


def wallet_lines(w, lang):
    if not w["chain"]:
        return [t("tk.w_unknown", lang)]
    lines = [t("tk.w_chain", lang, chain=t("tk.chain_" + w["chain"], lang), addr=w["address"][:8] + "…" + w["address"][-6:])]
    if w["chain"] == "evm":
        lines.append(t("tk.w_checksum_" + ("ok" if w["checksum"] else ("bad" if w["checksum"] is False else "none")), lang))
    if w["poisoning"]:
        lines.append(t("tk.w_poison_" + w["poisoning"], lang))
    lines.append(t("tk.w_fees", lang, fees=" · ".join("%s $%g" % (k, v) for k, v in tokengold.FEES.items())))
    return lines


def bot_walletcheck(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if not args:
        return t("tk.w_usage", lang)
    w = tokengold.check_wallet(args[0], args[1] if len(args) > 1 else None)
    lines = wallet_lines(w, lang)
    try:
        a = _analysed()
        if a.get("usdt") is not None:
            lines.append(t("tk.peg_" + a["peg"], lang, usdt=format(a["usdt"], ".4f"), off=_pct(a["usdt_off"])))
    except tokengold.FeedError:
        pass
    return "\n".join(lines + ["", t("tk.w_rules", lang)])


def log_premium():
    """Called by the five-minute checker; never raises."""
    try:
        a = tokengold.analyse(tokengold.snapshot(max_age=0))
    except Exception:  # noqa: BLE001 — a dead feed must not break the checker
        return False
    store.log_premium(a.get("paxg"), a.get("xaut"), a.get("spot"), a.get("usdt"))
    return True


def svg_history(rows, width=720, height=200):
    """PAXG and XAUT premium (%) over time, inline SVG."""
    pts = [(r["at"], tokengold.premium(r["paxg"], r["spot"]), tokengold.premium(r["xaut"], r["spot"])) for r in rows if r["spot"]]
    pts = [p for p in pts if p[1] is not None or p[2] is not None]
    if len(pts) < 2:
        return ""
    vals = [v for p in pts for v in p[1:] if v is not None]
    lo, hi = min(vals + [0]) - 0.2, max(vals + [0]) + 0.2
    t0, t1 = pts[0][0], pts[-1][0]
    pad = 40

    def x(ts):
        return pad + (ts - t0) / max(1, t1 - t0) * (width - pad - 10)

    def y(v):
        return height - 20 - (v - lo) / (hi - lo) * (height - 30)

    def line(idx, colour):
        seq = " ".join("%.1f,%.1f" % (x(p[0]), y(p[idx])) for p in pts if p[idx] is not None)
        return '<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (seq, colour)

    return ('<svg viewBox="0 0 %d %d" width="100%%" role="img" style="max-width:100%%;height:auto">' % (width, height)
            + '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#9aa3b2" stroke-dasharray="4 4"/>' % (x(t0), y(0), x(t1), y(0))
            + line(1, "#f5d76e") + line(2, "#b7c0ce")
            + ''.join('<text x="2" y="%.1f" font-size="10" fill="#9aa3b2" font-family="monospace">%+.1f%%</text>' % (y(v) + 3, v) for v in (lo + 0.2, 0, hi - 0.2))
            + '</svg>')


def dashboard_tokengold(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    form = request.values
    ctx = {"form": form, "a": None, "error": None, "tokens": tokengold.tokens(lang), "facts_date": tokengold.FACTS_DATE,
           "fees": tokengold.FEES, "wallet": None, "lines": readout_lines, "wallet_lines": wallet_lines, "pct": _pct, "fmt": _fmt,
           "history": store.premium_history(days=7), "svg": None}
    try:
        ctx["a"] = _analysed()
    except tokengold.FeedError:
        ctx["error"] = t("tk.down", lang)
    # The band needs the live premium to say where *now* sits, so it comes after.
    ctx["bands"] = premium.bands(ctx["a"] or {})
    ctx["cheapest"] = premium.cheapest(ctx["a"]) if ctx["a"] else None
    ctx["band_days"] = premium.DAYS
    ctx["band_line"] = lambda b: premium.line(b, lang)     # bound, never defaulting to MS
    if form.get("address"):
        ctx["wallet"] = tokengold.check_wallet(form["address"], form.get("expected") or None)
    ctx["svg"] = svg_history(ctx["history"])
    return ctx
