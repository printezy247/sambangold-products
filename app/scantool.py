"""#4 #6 #7 #9 — the four scanners: bot commands and dashboard contexts.

Every scan is archived in `scans` (owner = chat id or `u:<id>`), so the bot and
the dashboard share one history, one watchlist and one public share page.
"""

from . import scan, store
from .brand import DEFAULT_LANG, t

FLAG_ICON = {scan.RED: "🔴", scan.YELLOW: "🟡", scan.GOOD: "🟢"}
VERDICT_ICON = {"HIGH RISK": "🚨", "CAUTION": "⚠️", "LOW RISK": "✅"}
TOP = 5


def verdict_text(verdict, lang):
    return t("scan.verdict_" + verdict.split()[0].lower(), lang)


def _lines(report, lang):
    head = "%s <b>%s</b> · %s %d/100" % (VERDICT_ICON[report["verdict"]], verdict_text(report["verdict"], lang),
                                         t("scan.score", lang), report["score"])
    lines = [head, "%s: <b>%s</b>" % (t("scan.subject", lang), report["subject"]), ""]
    if report["findings"]:
        for f in scan.localise(report["findings"], lang)[:TOP]:
            lines.append("%s <b>%s</b> — %s" % (FLAG_ICON[f["flag"]], f["label"], f["why"]))
        more = len(report["findings"]) - TOP
        if more > 0:
            lines.append(t("scan.more", lang, n=more))
    else:
        lines.append(t("scan.clean", lang))
    return lines


def _finish(report, chat_id, lang, tail):
    lines = _lines(report, lang) + ["", tail, ""]
    if chat_id:   # archived per chat; the surface-contract test calls handlers without a chat
        lines.append(t("scan.saved", lang, n=store.save_scan(report, owner=chat_id)))
    lines.append(t("scan.disclaimer", lang))
    return "\n".join(lines)


# --- bot -------------------------------------------------------------------- #

def bot_audit(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if not args:
        return t("scan.usage_audit", lang)
    report = scan.audit_bot(args[0], " ".join(args[1:]))
    return _finish(report, chat_id, lang, t("scan.tail_audit", lang))


def bot_copyaudit(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if not args:
        return t("scan.usage_copy", lang)
    nums = [a for a in args[1:] if a.replace(".", "", 1).isdigit()]
    words = [a for a in args[1:] if a not in nums]
    report = scan.audit_copy(args[0], " ".join(words),
                             spread_pips=nums[0] if len(nums) > 0 else None,
                             lots_per_month=nums[1] if len(nums) > 1 else None)
    tail = []
    if report["known"]:
        tail.append(t("scan.regs", lang, regs=", ".join(r[0] for r in report["regulators"]) or "—"))
    if report["cost"]:
        c = report["cost"]
        tail.append(t("scan.cost", lang, pips=c["spread_pips"], lots=c["lots"], monthly=c["monthly"], yearly=c["yearly"]))
    tail.append(t("scan.tail_copy", lang))
    return _finish(report, chat_id, lang, "\n".join(tail))


def bot_scan(args, chat_id=None, lang=DEFAULT_LANG, **_):
    text = " ".join(args).strip()
    if len(text) < 8:
        return t("scan.usage_scan", lang)
    return _finish(scan.scan_pitch(text), chat_id, lang, t("scan.tail_scan", lang))


def bot_influencer(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if not args:
        return t("scan.usage_influencer", lang)
    report = scan.audit_influencer(args[0], " ".join(args[1:]))
    tail = [t("scan.demand", lang)] + ["• " + d for d in scan.demands(lang)]
    if report["broker_links"]:
        tail.append(t("scan.ib_links", lang, n=len(report["broker_links"])))
    return _finish(report, chat_id, lang, "\n".join(tail))


# --- dashboard -------------------------------------------------------------- #

FORMS = {   # labels are brand string keys; the template runs them through t()
    "bot-scam-detector": {"subject_label": "ui.s_sub_bot", "subject_placeholder": "@some_verify_bot",
                          "text_label": "ui.s_txt_bot", "needs_subject": True},
    "copy-trade-audit": {"subject_label": "ui.s_sub_copy", "subject_placeholder": "Exness, HFM, IC Markets…",
                         "text_label": "ui.s_txt_copy", "needs_subject": True},
    "red-flag-scanner": {"subject_label": "ui.s_sub_scan", "subject_placeholder": "@vip_gold_signals",
                         "text_label": "ui.s_txt_scan", "needs_subject": False},
    "influencer-audit": {"subject_label": "ui.s_sub_inf", "subject_placeholder": "@rich_gold_guru",
                         "text_label": "ui.s_txt_inf", "needs_subject": True},
}


def _run(slug, form):
    subject, text = form.get("subject", "").strip(), form.get("text", "").strip()
    if slug == "bot-scam-detector":
        return scan.audit_bot(subject, text)
    if slug == "copy-trade-audit":
        return scan.audit_copy(subject, text, form.get("spread_pips") or None, form.get("lots") or None)
    if slug == "influencer-audit":
        return scan.audit_influencer(subject, text)
    report = scan.scan_pitch(text)
    if subject:
        report["subject"] = "@" + subject.lstrip("@")
    return report


def _dashboard(slug):
    def build(request, user=None):
        from .auth import lang as ui_lang
        lang = ui_lang()
        owner = user["owner"] if user else None
        form = request.form if request.method == "POST" else {}
        ctx = {"slug": slug, "form": form, "spec": FORMS[slug], "report": None, "error": None, "scan_id": None,
               "owner": owner, "history": [], "watch": [], "public": [], "loss": None,
               "flag_icon": FLAG_ICON, "verdict_icon": VERDICT_ICON, "verdict_text": verdict_text,
               "localise": scan.localise, "checklist": scan.checklist, "demands": scan.demands}
        if request.method == "POST" and request.form.get("action") == "loss":
            f = request.form
            ctx["loss"] = scan.loss_report(f.get("handle", ""), f.get("platform", ""), f.get("amount", ""),
                                           f.get("currency", ""), f.get("date", ""), f.get("story", ""), f.get("broker", ""))
        elif request.method == "POST":
            spec = FORMS[slug]
            if spec["needs_subject"] and not form.get("subject", "").strip():
                ctx["error"] = t("ui.s_need_sub", lang, label=t(spec["subject_label"], lang))
            elif not spec["needs_subject"] and len(form.get("text", "").strip()) < 8:
                ctx["error"] = t("ui.s_need_text", lang)
            else:
                ctx["report"] = _run(slug, form)
                ctx["scan_id"] = store.save_scan(ctx["report"], owner=owner)
                ctx["public"] = store.public_scans(slug, ctx["report"]["subject"])
        if owner:
            from .gate import allows, user_tier
            if allows(user_tier(user), "history"):    # keeping a run is what General buys
                ctx["history"] = store.scans_for(owner, slug)
            ctx["watch"] = store.watchlist(owner, slug)
        return ctx
    return build


dashboard_botscam = _dashboard("bot-scam-detector")
dashboard_copyaudit = _dashboard("copy-trade-audit")
dashboard_redflag = _dashboard("red-flag-scanner")
dashboard_influencer = _dashboard("influencer-audit")


def public_page(scan_id):
    row = store.get_scan(scan_id)
    if not row or row["product"] not in FORMS:
        return None
    return {"row": row, "report": row["report"], "flag_icon": FLAG_ICON, "verdict_icon": VERDICT_ICON,
            "verdict_text": verdict_text, "localise": scan.localise,
            "others": store.public_scans(row["product"], row["subject"])}
