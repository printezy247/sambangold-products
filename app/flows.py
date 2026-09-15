"""Guided flows: the bot asks one thing at a time, with buttons, and builds the
command itself. Nobody has to remember `/propcalc 500 100000 15`.

A flow is a list of steps. Each step has a prompt (brand string key), optional
quick-answer buttons, and flags: `number` (validate), `optional` (Skip button),
`text` (typed answers accepted — default yes), `when` (skip the step when the
answers so far say so). State lives in `tg_users.state` so it survives restarts
and the machine going to sleep.
"""

from . import store
from .brand import DEFAULT_LANG, t


def S(key, prompt, options=(), number=False, optional=False, text=True, when=None):
    return {"key": key, "prompt": prompt, "options": tuple(options), "number": number,
            "optional": optional, "text": text, "when": when}


FLOWS = {
    "gold-watch": [
        S("mode", "flow.watch_mode", text=False,
          options=(("flow.watch_price", "price"), ("flow.watch_above", "above"), ("flow.watch_below", "below"))),
        S("level", "flow.watch_level", number=True, when=lambda a: a.get("mode") != "price"),
    ],
    "prop-calculator": [
        S("fee", "flow.prop_fee", number=True, options=(("$100", "100"), ("$250", "250"), ("$500", "500"), ("$1,000", "1000"))),
        S("size", "flow.prop_size", number=True,
          options=(("$10k", "10000"), ("$25k", "25000"), ("$50k", "50000"), ("$100k", "100000"), ("$200k", "200000"))),
        S("pass", "flow.prop_pass", number=True, options=(("10%", "10"), ("15%", "15"), ("25%", "25"), ("40%", "40"))),
    ],
    "ib-revenue-calculator": [
        S("lots", "flow.ib_lots", number=True, options=(("10", "10"), ("40", "40"), ("100", "100"))),
        S("rate", "flow.ib_rate", number=True, options=(("$3", "3"), ("$5", "5"), ("$7", "7"), ("$10", "10"))),
        S("clients", "flow.ib_clients", number=True, options=(("1", "1"), ("10", "10"), ("25", "25"), ("50", "50"))),
        S("claw", "flow.ib_claw", number=True, options=(("0%", "0"), ("5%", "5"), ("10%", "10"))),
    ],
    "gold-calendar": [],
    "rebate-auditor": [],      # dashboard-led: the bot reads back the last run
    "churn-radar": [],
    "exposure-monitor": [S("positions", "flow.ex_positions")],
    "tokenized-gold": [],
    "miner-divergence": [],
    "monte-carlo-sim": [
        S("wr", "flow.mc_wr", number=True, options=(("35%", "35"), ("45%", "45"), ("55%", "55"), ("65%", "65"))),
        S("rr", "flow.mc_rr", number=True, options=(("1", "1"), ("1.5", "1.5"), ("2", "2"), ("3", "3"))),
        S("risk", "flow.mc_risk", number=True, options=(("0.5%", "0.5"), ("1%", "1"), ("2%", "2"))),
        S("firm", "flow.mc_firm", text=False, options=(("FTMO", "ftmo"), ("FundedNext", "fundednext"), ("The5ers", "the5ers"), ("MyFundedFX", "myfundedfx"), ("E8", "e8"))),
    ],
    "drawdown-sentinel": [
        S("name", "flow.sn_name"),
        S("firm", "flow.sn_firm", options=(("FTMO", "ftmo"), ("FundedNext", "fundednext"), ("The5ers", "the5ers"), ("FundingPips", "fundingpips"), ("MyFundedFX", "myfundedfx"), ("E8", "e8"))),
        S("balance", "flow.sn_balance", number=True, options=(("$10k", "10000"), ("$25k", "25000"), ("$50k", "50000"), ("$100k", "100000"))),
    ],
    "link-attribution": [
        S("channel", "flow.lk_channel"),
        S("url", "flow.lk_url", optional=True),
    ],
    "broker-comparator": [
        S("lots", "flow.bc_lots", number=True, options=(("0.1", "0.1"), ("0.5", "0.5"), ("1", "1"), ("5", "5"))),
        S("nights", "flow.bc_nights", number=True, options=(("0", "0"), ("1", "1"), ("5", "5"), ("20", "20"))),
    ],
    "bot-scam-detector": [
        S("handle", "flow.audit_handle"),
        S("text", "flow.audit_text", optional=True),
    ],
    "copy-trade-audit": [
        S("broker", "flow.copy_broker",
          options=(("Exness", "exness"), ("HFM", "hfm"), ("XM", "xm"), ("OctaFX", "octafx"), ("FBS", "fbs"), ("Vantage", "vantage"))),
        S("spread", "flow.copy_spread", number=True, optional=True, options=(("1 pip", "1"), ("2 pip", "2"), ("3 pip", "3"))),
        S("lots", "flow.copy_lots", number=True, optional=True, options=(("5 lot", "5"), ("10 lot", "10"), ("30 lot", "30"))),
    ],
    "red-flag-scanner": [S("text", "flow.scan_text")],
    "signal-verifier": [
        S("price", "flow.ver_price", number=True),
        S("date", "flow.ver_date", optional=True),
        S("time", "flow.ver_time", optional=True, when=lambda a: bool(a.get("date"))),
    ],
    "influencer-audit": [
        S("handle", "flow.inf_handle"),
        S("text", "flow.inf_text", optional=True),
    ],
}


def build(slug, a):
    """The command the flow's answers amount to."""
    if slug == "gold-watch":
        return "/watch XAUUSD" if a.get("mode") == "price" else "/watch XAUUSD %s %s" % (a["mode"], a["level"])
    if slug == "prop-calculator":
        return "/propcalc %s %s %s" % (a["fee"], a["size"], a["pass"])
    if slug == "ib-revenue-calculator":
        return "/ibcalc %s %s %s %s" % (a["lots"], a["rate"], a["clients"], a["claw"])
    if slug == "gold-calendar":
        return "/calendar"
    if slug == "rebate-auditor":
        return "/rebateaudit"
    if slug == "churn-radar":
        return "/ibchurn"
    if slug == "broker-comparator":
        return "/goldspread %s %s" % (a["lots"], a["nights"])
    if slug == "tokenized-gold":
        return "/paxg"
    if slug == "miner-divergence":
        return "/miners"
    if slug == "exposure-monitor":
        return "/exposure " + a["positions"].replace("\n", ", ")
    if slug == "monte-carlo-sim":
        return "/simulate %s %s %s %s" % (a["wr"], a["rr"], a["risk"], a["firm"])
    if slug == "drawdown-sentinel":
        return "/sentinel link %s %s %s" % (a["name"].replace(" ", "_"), a["firm"], a["balance"])
    if slug == "link-attribution":
        return ("/newlink %s %s" % (a["channel"], a.get("url") or "")).strip()
    if slug == "bot-scam-detector":
        return ("/audit %s %s" % (a["handle"], a.get("text") or "")).strip()
    if slug == "copy-trade-audit":
        parts = ["/copyaudit", a["broker"]] + [str(a[k]) for k in ("spread", "lots") if a.get(k) is not None]
        return " ".join(parts)
    if slug == "red-flag-scanner":
        return "/scan " + a["text"]
    if slug == "signal-verifier":
        return " ".join(["/verify GOLD", str(a["price"])] + [a[k] for k in ("date", "time") if a.get(k)])
    if slug == "influencer-audit":
        return ("/influencer %s %s" % (a["handle"], a.get("text") or "")).strip()
    raise KeyError(slug)


# --- engine ------------------------------------------------------------------ #

def _label(label, lang):
    return t(label, lang) if label.startswith("flow.") else label


def _parse_number(raw):
    cleaned = raw.strip().replace(",", "").replace("$", "").replace("%", "").replace("k", "000").replace("K", "000")
    value = float(cleaned)
    return ("%d" % value) if value == int(value) else ("%g" % value)


def _keyboard(step, lang):
    from .telegram import btn, kb
    rows, row = [], []
    for label, value in step["options"]:
        row.append(btn(_label(label, lang), "fl_o:%s" % value))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    tail = []
    if step["optional"]:
        tail.append(btn(t("flow.skip", lang), "fl_skip"))
    tail.append(btn(t("flow.cancel", lang), "fl_cancel"))
    rows.append(tail)
    return kb(rows)


def _prompt(step, lang):
    text = t(step["prompt"], lang)
    if step["options"] and step["text"]:
        text += "\n" + t("flow.typed", lang)
    return text


def _next_index(steps, answers, start):
    i = start
    while i < len(steps):
        when = steps[i]["when"]
        if when is None or when(answers):
            return i
        i += 1
    return None


def start(slug, chat_id, lang=DEFAULT_LANG):
    """Begin the flow for a product: the first prompt, or the answer straight away when there is nothing to ask."""
    if slug not in FLOWS:
        return []
    state = {"slug": slug, "step": 0, "answers": {}}
    return _advance(state, chat_id, lang, from_index=0)


def _advance(state, chat_id, lang, from_index):
    from .telegram import _base_url, _product_by_slug, reply_for, result_keyboard
    steps = FLOWS[state["slug"]]
    nxt = _next_index(steps, state["answers"], from_index)
    if nxt is None:
        store.tg_set_state(chat_id, None)
        product = _product_by_slug(state["slug"])
        command = build(state["slug"], state["answers"])
        return [("send", chat_id, reply_for(command, _base_url(), chat_id=chat_id, lang=lang),
                 result_keyboard(product, lang, chat_id))]
    state["step"] = nxt
    store.tg_set_state(chat_id, state)
    step = steps[nxt]
    return [("send", chat_id, _prompt(step, lang), _keyboard(step, lang))]


def on_text(text, chat_id, lang=DEFAULT_LANG):
    """A typed message while a flow is open. Returns actions, or None when no flow is open."""
    state = store.tg_state(chat_id)
    if not state or state["slug"] not in FLOWS:
        return None
    step = FLOWS[state["slug"]][state["step"]]
    if not step["text"]:
        return [("send", chat_id, _prompt(step, lang), _keyboard(step, lang))]
    value = text.strip()
    if step["number"]:
        try:
            value = _parse_number(value)
        except ValueError:
            return [("send", chat_id, t("flow.not_number", lang), _keyboard(step, lang))]
    state["answers"][step["key"]] = value
    return _advance(state, chat_id, lang, from_index=state["step"] + 1)


def on_callback(data, chat_id, message_id, lang=DEFAULT_LANG):
    """A tapped flow button: fl_cancel, fl_skip, or fl_o:<value>."""
    from .telegram import menu_keyboard
    state = store.tg_state(chat_id)
    if data == "fl_cancel" or not state or state["slug"] not in FLOWS:
        store.tg_set_state(chat_id, None)
        return [("edit", chat_id, message_id, t("flow.cancelled", lang), menu_keyboard(lang))]
    step = FLOWS[state["slug"]][state["step"]]
    if data == "fl_skip":
        state["answers"][step["key"]] = None
        shown = t("flow.skip", lang)
    else:
        value = data[len("fl_o:"):]
        state["answers"][step["key"]] = value
        shown = next((_label(l, lang) for l, v in step["options"] if v == value), value)
    actions = [("edit", chat_id, message_id, t("flow.chosen", lang, prompt=t(step["prompt"], lang), value=shown), None)]
    return actions + _advance(state, chat_id, lang, from_index=state["step"] + 1)


def cancel(chat_id):
    if store.tg_state(chat_id):
        store.tg_set_state(chat_id, None)
