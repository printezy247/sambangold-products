"""The two ways up the ladder that cost no money.

Both are ported from Sam's site, where they are how most members actually
reach a paid rank:

* **The broker door.** Open an HFM account under Sam and the deposit band
  decides the rank. The rank runs thirty days and renews while the account
  stays active. This is the main door — no card, no subscription, and the
  member was going to need a broker anyway.
* **Referral credit.** Bring someone in who then reaches a paid or broker
  rank, and you get a stretch of a higher rank yourself, once per person you
  brought.

Neither door is a discount on a paywall, because there is no paywall. They are
how a member reaches the automation and the scale without paying cash for them.
"""

import re
import time

from . import store
from .brand import DEFAULT_LANG, t
from .tiers import BY_KEY, TIERS, higher_tier, tier_for_deposit

IB_DAYS = 30          # a broker-door rank lasts a month, then the account is re-checked
REFERRAL_DAYS = 7     # what bringing one person in is worth
REFERRAL_CAP = "pro"  # a referral can reach A-Team; Rambo is earned or paid for
SLUG = "referral"

ACCOUNT_RE = re.compile(r"^[0-9]{4,16}$")


# --- the broker door -------------------------------------------------------- #

def claim(owner, account, deposit=None, note=""):
    """Register an HFM account for verification. (claim_row, error_key)."""
    account = str(account or "").strip()
    if not ACCOUNT_RE.match(account):
        return None, "br.bad_account"
    existing = store.broker_claim_by_account(account)
    if existing and str(existing["owner"]) != str(owner):
        return None, "br.taken"
    row = store.save_broker_claim(owner, account, deposit, note)
    return row, None


def approve(claim_id, deposit=None, now=None):
    """Verify a claim and grant the rank its deposit band earns. (tier, error_key)."""
    row = store.broker_claim(claim_id)
    if not row:
        return None, "br.unknown"
    now = time.time() if now is None else now
    deposit = float(row["deposit"] or 0) if deposit is None else float(deposit)
    tier = tier_for_deposit(deposit)
    store.set_broker_claim(claim_id, status="verified", deposit=deposit, verified_at=now)
    store.grant_entitlement(row["owner"], tier, source="ib", external_id="ib:%s" % row["account"],
                            expires_at=now + IB_DAYS * 86400, note="HFM %s" % row["account"])
    credit_referrer(row["owner"], now=now)
    return tier, None


def reject(claim_id, note=""):
    row = store.broker_claim(claim_id)
    if not row:
        return None, "br.unknown"
    store.set_broker_claim(claim_id, status="rejected", note=note)
    store.revoke_entitlement(external_id="ib:%s" % row["account"])
    return row, None


def door_rows():
    """What each rank's deposit band is, for the page and the bot."""
    return [(tier.key, tier.ib_min_deposit_usd) for tier in TIERS if tier.ib_min_deposit_usd is not None]


# --- referral --------------------------------------------------------------- #

def code_for(owner):
    """A stable short code per member, minted on first use."""
    owner = str(owner)
    code = store.get_setting(SLUG, owner, "code")
    if code:
        return code
    import hashlib
    code = hashlib.sha1(("sbg:%s" % owner).encode()).hexdigest()[:8]
    store.set_setting(SLUG, owner, "code", code)
    return code


def owner_of_code(code):
    return store.owner_by_setting(SLUG, "code", (code or "").strip().lower())


def deep_link(owner, bot_username):
    return "https://t.me/%s?start=ref_%s" % (bot_username, code_for(owner)) if bot_username else ""


def attach(owner, tag):
    """Record who brought this member in. Once, and never themselves."""
    owner = str(owner)
    if not tag or not str(tag).startswith("ref_"):
        return None
    if store.get_setting(SLUG, owner, "by"):
        return None                       # the first referrer keeps the credit
    referrer = owner_of_code(str(tag)[4:])
    if not referrer or str(referrer) == owner:
        return None
    store.set_setting(SLUG, owner, "by", str(referrer))
    return str(referrer)


def credit_referrer(owner, now=None):
    """Pay the person who brought `owner` in — once, when `owner` reaches a real rank.

    The credit is one rank above what the referrer holds, capped at A-Team,
    for REFERRAL_DAYS. Rambo is never handed out this way.
    """
    owner = str(owner)
    referrer = store.get_setting(SLUG, owner, "by")
    if not referrer:
        return None
    external = "ref:%s" % owner
    if any(row["external_id"] == external for row in store.entitlements_for(referrer, active_only=False)):
        return None                       # one credit per person brought in
    now = time.time() if now is None else now
    reward = _one_up(store.effective_tier(referrer))
    store.grant_entitlement(referrer, reward, source="referral", external_id=external,
                            expires_at=now + REFERRAL_DAYS * 86400, note="referral %s" % owner)
    return reward


def _one_up(tier):
    """The next rank up, never past the referral cap."""
    rank = BY_KEY[tier].rank if tier in BY_KEY else 0
    nxt = next((x.key for x in TIERS if x.rank == rank + 1), tier)
    return nxt if BY_KEY[nxt].rank <= BY_KEY[REFERRAL_CAP].rank else REFERRAL_CAP


def invited_by(owner):
    return store.get_setting(SLUG, str(owner), "by")


def invited(owner):
    """Everyone this member brought in, and whether the credit has landed."""
    owner = str(owner)
    out = []
    for other in store.owners_by_setting(SLUG, "by", owner):
        paid = any(row["external_id"] == "ref:%s" % other
                   for row in store.entitlements_for(owner, active_only=False))
        out.append({"owner": other, "credited": paid})
    return out


# --- bot -------------------------------------------------------------------- #

def bot_broker(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/broker <account number>` puts an HFM account in the verification queue."""
    from .brand import rank_label
    if not chat_id:
        return t("br.usage", lang)
    if not args:
        rows = "\n".join(t("br.row", lang, rank=rank_label(key, lang), usd=usd) for key, usd in door_rows())
        mine = store.broker_claims_for(chat_id)
        head = [t("br.head", lang), rows, "", t("br.usage", lang)]
        if mine:
            head += ["", t("br.mine", lang, account=mine[0]["account"], status=t("br.s_" + mine[0]["status"], lang))]
        return "\n".join(head)
    row, err = claim(chat_id, args[0], args[1] if len(args) > 1 else None)
    if err:
        return t(err, lang)
    return t("br.claimed", lang, account=row["account"])


def bot_invite(args, chat_id=None, lang=DEFAULT_LANG, **_):
    """`/invite` hands back the member's own deep link and what it is worth."""
    from .brand import rank_label
    from .telegram import bot_username
    if not chat_id:
        return t("rf.usage", lang)
    rows = invited(chat_id)
    return "\n".join([
        t("rf.head", lang, days=REFERRAL_DAYS, rank=rank_label(REFERRAL_CAP, lang)),
        deep_link(chat_id, bot_username()) or t("rf.no_link", lang),
        "",
        t("rf.count", lang, n=len(rows), credited=sum(1 for r in rows if r["credited"])),
    ])
