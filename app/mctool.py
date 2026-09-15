"""#15 Monte Carlo Challenge Simulator — the bot card, the dashboard run, the PDF."""

import random

from flask import current_app

from . import mc, store
from . import gate
from .brand import DEFAULT_LANG, t
from .goldcal import simple_pdf
from .sentinel import PACKS

SLUG = "monte-carlo-sim"
ICON = {"good": "✅", "fair": "🟡", "poor": "❌"}


def _pct(x):
    return "%.0f%%" % (x * 100)


def summary_lines(res, lang):
    i = res["inputs"]
    v = mc.verdict(res["p_pass"])
    lines = [t("mc.head", lang, icon=ICON[v], p=_pct(res["p_pass"]), firm=i["pack_name"], wr=i["winrate"] * 100, rr=i["rr"], risk=i["risk_pct"], target=i["target_pct"]),
             t("mc.cost", lang, attempts=res["expected_attempts"] if res["expected_attempts"] else "∞",
               cost=("$%s" % format(res["cost_to_funded"], ",.0f")) if res["cost_to_funded"] else "∞", fee=i["fee"])]
    if res["reasons"]:
        lines.append(t("mc.fails", lang, reasons=" · ".join("%s %s" % (t("mc.r_" + k, lang), _pct(p)) for k, p in sorted(res["reasons"].items(), key=lambda kv: -kv[1]))))
    if res["median_trades_to_pass"]:
        lines.append(t("mc.median", lang, trades=res["median_trades_to_pass"], days=res["median_days_to_pass"]))
    lines.append(t("mc.expectancy", lang, r=res["expectancy_r"], sims=i["sims"]))
    return lines


def bot_simulate(args, chat_id=None, lang=DEFAULT_LANG, **_):
    if len(args) < 3:
        return t("mc.usage", lang)
    firm = args[3] if len(args) > 3 else "ftmo"
    from .sentinel import find_pack
    key = find_pack(firm) or "ftmo"
    try:
        target = float(args[4]) if len(args) > 4 else (8.0 if PACKS[key]["max_pct"] <= 8 else 10.0)
        cap = gate.limit("sims", chat_id=chat_id)
        res = mc.run(args[0].rstrip("%"), args[1], args[2].rstrip("%"), key, target, 500, 3, cap, cap=cap)
    except (ValueError, IndexError):
        return t("mc.bad", lang) + "\n\n" + t("mc.usage", lang)
    out = summary_lines(res, lang)
    if chat_id:
        rid = store.save_run(SLUG, {k: v for k, v in res.items() if k not in ("bands", "samples")}, owner=chat_id,
                             label="%s %g/%g/%g" % (res["inputs"]["pack_name"], res["inputs"]["winrate"] * 100, res["inputs"]["rr"], res["inputs"]["risk_pct"]),
                             metric=res["p_pass"])
        out.append(t("scan.saved", lang, n=rid))
    out.append(t("scan.disclaimer", lang))
    return "\n".join(out)


def dashboard_mc(request, user=None):
    from .auth import lang as ui_lang
    lang = ui_lang()
    owner = user["owner"] if user else None
    form = request.values
    ctx = {"form": form, "owner": owner, "res": None, "svg": None, "error": None, "packs": PACKS, "free": gate.limit("sims", user=user),
           "icon": ICON, "verdict": mc.verdict, "lines": summary_lines, "runs": [], "run_id": None, "pct": _pct}
    if form.get("winrate"):
        try:
            seed = int(form.get("seed") or random.randrange(1, 10 ** 6))
            res = mc.run(form["winrate"], form.get("rr", 2), form.get("risk", 1), form.get("firm", "ftmo"), form.get("target", 10),
                         form.get("fee", 500), form.get("tpd", 3), form.get("sims", ctx["free"]), seed=seed, cap=ctx["free"])
            res["seed"] = seed
            ctx["res"], ctx["svg"] = res, mc.svg_fan(res)
            if owner:
                ctx["run_id"] = store.save_run(SLUG, {k: v for k, v in res.items() if k not in ("bands", "samples")}, owner=owner,
                                               label="%s %g/%g/%g" % (res["inputs"]["pack_name"], res["inputs"]["winrate"] * 100, res["inputs"]["rr"], res["inputs"]["risk_pct"]),
                                               metric=res["p_pass"])
        except ValueError:
            ctx["error"] = t("mc.bad", lang)
    if owner:
        ctx["runs"] = store.runs_for(SLUG, owner)
    return ctx


def pdf_for(run_id, owner=None, lang=DEFAULT_LANG, brand="SAMBANGGOLD"):
    row = store.get_run(run_id)
    if not row or row["product"] != SLUG or (row["owner"] and row["owner"] != (str(owner) if owner else None)):
        return None, None
    res = row["run"]
    i = res["inputs"]
    lines = ["%s — Monte Carlo challenge simulation #%d" % (brand, row["id"]), "",
             "Inputs: win rate %g%%, R:R %g, risk %g%% per trade, %d trades/day, %d paths" % (i["winrate"] * 100, i["rr"], i["risk_pct"], i["trades_per_day"], i["sims"]),
             "Rule pack: %s — daily %g%%, max DD %g%%%s, min days %s, target %g%%" % (
                 i["pack_name"], PACKS[i["pack"]]["daily_pct"], PACKS[i["pack"]]["max_pct"], " trailing" if PACKS[i["pack"]]["trailing"] else "", PACKS[i["pack"]]["min_days"], i["target_pct"]),
             ""]
    import re
    lines += [re.sub(r"<[^>]+>", "", l) for l in summary_lines(res, "en")]
    lines += ["", "Path risk, not edge, is what fails most challenges. Educational research only. Not financial advice."]
    return "mc-run-%d.pdf" % row["id"], simple_pdf([lines])
