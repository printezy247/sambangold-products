"""#2 Signal Verifier — the bot command, the dashboard context, the public verdict page."""

import datetime as dt

from . import store, verify
from . import gate
from .brand import DEFAULT_LANG, t

ICON = {"REAL": "✅", "BORDERLINE": "🟡", "IMPOSSIBLE": "❌", "UNVERIFIED": "❔"}
BATCH_LIMIT = 20


def verdict_text(verdict, lang):
    return t("ver.v_" + verdict.lower(), lang)


def _fmt(x):
    return format(x, ",.2f")


def _nearest_line(r, lang):
    n = r.get("nearest")
    if not n:
        return None
    at = dt.datetime.fromisoformat(n["at"]).astimezone(verify.MYT).strftime("%d %b %H:%M")
    return t("ver.line_nearest", lang, at=at, low=_fmt(n["low"]), high=_fmt(n["high"]))


def lines(r, lang):
    out = ["%s <b>%s</b> · %s" % (ICON[r["verdict"]], verdict_text(r["verdict"], lang), r["subject"])]
    if r["verdict"] == "UNVERIFIED":
        out.append(t("ver.line_nodata", lang, err=(r.get("error") or "")[:80]))
        return out
    out.append(t("ver.line_range", lang, low=_fmt(r["low"]), high=_fmt(r["high"]), src=r["source"], n=r["candles"]))
    near = _nearest_line(r, lang)
    if near:
        out.append(near)
    if r["verdict"] != "REAL":
        out.append(t("ver.line_gap", lang, gap=_fmt(r["gap"]), pct=r["gap_pct"] * 100))
    return out


# --- bot -------------------------------------------------------------------- #

def _split_args(args):
    """/verify [GOLD|XAUUSD] PRICE [DATE] [TIME] [buy|sell]"""
    rest = [a for a in args if a.upper() not in ("GOLD", "XAUUSD", "XAU")]
    if not rest:
        return None
    return verify.parse_claim_line(" ".join(rest))


def bot_verify(args, chat_id=None, lang=DEFAULT_LANG, **_):
    claim = _split_args(args)
    if not claim:
        return t("ver.usage", lang)
    price, date_text, time_text, side = claim
    try:
        r = verify.verify(price, date_text, time_text, side)
    except ValueError:
        return t("ver.bad_input", lang) + "\n\n" + t("ver.usage", lang)
    out = lines(r, lang) + ["", t("ver.note", lang)]
    if chat_id:
        out.append(t("scan.saved", lang, n=store.save_scan(r, owner=chat_id)))
    out.append(t("scan.disclaimer", lang))
    return "\n".join(out)


# --- dashboard -------------------------------------------------------------- #

def dashboard_verify(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.form if request.method == "POST" else {}
    ctx = {"form": form, "results": [], "error": None, "owner": owner, "history": [],
           "icon": ICON, "verdict_text": verdict_text, "lines": lines, "fmt": _fmt, "batch_limit": gate.limit("batch_rows", user=user)}
    claims = []
    if request.method == "POST" and form.get("action") == "batch":
        for raw in form.get("claims", "").splitlines()[:ctx["batch_limit"]]:
            c = verify.parse_claim_line(raw)
            if c:
                claims.append(c)
        if not claims:
            ctx["error"] = t("ui.v_need_lines", lang)
    elif request.method == "POST" and form.get("price"):
        claims.append((form["price"], form.get("date") or None, form.get("time") or None, form.get("side", "")))
    for price, date_text, time_text, side in claims:
        try:
            r = verify.verify(price, date_text, time_text, side)
        except ValueError:
            ctx["error"] = t("ver.bad_input", lang)
            continue
        r["id"] = store.save_scan(r, owner=owner)
        ctx["results"].append(r)
    if owner:
        from .gate import allows, user_tier
        if allows(user_tier(user), "history"):    # keeping a run is what General buys
            ctx["history"] = store.scans_for(owner, "signal-verifier")
    return ctx


def public_page(scan_id):
    row = store.get_scan(scan_id)
    if not row or row["product"] != "signal-verifier":
        return None
    return {"row": row, "report": row["report"], "icon": ICON, "verdict_text": verdict_text, "lines": lines,
            "others": store.public_scans("signal-verifier", row["subject"])}
