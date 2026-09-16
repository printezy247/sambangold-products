"""#17 Tokenized-Gold Premium & Payout Health.

Premium: PAXG (Binance) and XAUT (Bitfinex) against a spot reference. There
is no free real-time LBMA spot, so the reference is Yahoo GC=F — the front
futures contract, which carries a small basis over spot — and every readout
says so. The PAXG–XAUT spread needs no reference at all and is the cleanest
number on the page.

Payout health: the USDT peg from Kraken's public USDT/USD ticker, typical
chain fees for a USDT transfer, and two offline wallet checks — the EIP-55
checksum on an Ethereum address, and address poisoning: the address you are
about to pay shares its first and last characters with the one in your
history but is not the same address.
"""

import hashlib
import time

import requests

TIMEOUT = 6
BINANCE_PAXG = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
BITFINEX_XAUT = "https://api-pub.bitfinex.com/v2/ticker/tXAUT:USD"
YAHOO_GC = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=5m"
KRAKEN_USDT = "https://api.kraken.com/0/public/Ticker?pair=USDTUSD"
CACHE_SECONDS = 60
_cache = {"at": 0.0, "snap": None}

# Facts about the tokens as of 2026-09. Attestation cadence and redemption terms
# change; each row links to the issuer's page so the reader verifies.
TOKENS = {
    "PAXG": {"issuer": "Paxos", "chain": "Ethereum (ERC-20)", "attestation": "monthly, independent accountant",
             "redemption": "from 1 oz via Paxos (KYC); physical bars from 430 oz", "fee": "0.02 % on-chain transfer fee (min 0.000002 PAXG); redemption fee tiered",
             "url": "https://paxos.com/paxgold/"},
    "XAUT": {"issuer": "Tether", "chain": "Ethereum (ERC-20), Tron", "attestation": "quarterly reserve report",
             "redemption": "from 430 oz (one bar) via Tether (KYC)", "fee": "0.25 % on purchase/redemption",
             "url": "https://gold.tether.to/"},
}
# The same rows in Bahasa Melayu. Kept beside the facts rather than in
# `brand.py`, so a fact and its translation are dated and revised as one row —
# a quarterly refresh that updates only one of the two would be worse than
# either language alone.
TOKENS_MS = {
    "PAXG": {"attestation": "bulanan, akauntan bebas",
             "redemption": "dari 1 oz melalui Paxos (KYC); jongkong fizikal dari 430 oz",
             "fee": "yuran pindahan on-chain 0.02 % (min 0.000002 PAXG); yuran tebusan berperingkat"},
    "XAUT": {"attestation": "laporan rizab suku tahunan",
             "redemption": "dari 430 oz (satu jongkong) melalui Tether (KYC)",
             "fee": "0.25 % semasa beli/tebus"},
}


def tokens(lang="ms"):
    """The facts table in the reader's language. Issuer, chain and URL are
    names, so they are never translated."""
    if lang != "ms":
        return TOKENS
    return {k: dict(v, **TOKENS_MS.get(k, {})) for k, v in TOKENS.items()}


FACTS_DATE = "2026-09"
FEES = {   # typical USDT transfer cost, USD, as of 2026-09; verify with your wallet
    "TRC20 (Tron)": 1.0, "ERC20 (Ethereum)": 3.0, "BEP20 (BNB Chain)": 0.10, "Polygon": 0.02, "Arbitrum": 0.10, "Solana": 0.01,
}
PREMIUM_WARN = 1.0      # % — push / flag beyond this
PEG_WARN = 0.003        # 0.3 % off $1


class FeedError(RuntimeError):
    pass


def _paxg():
    return float(requests.get(BINANCE_PAXG, timeout=TIMEOUT).json()["price"])


def _xaut():
    body = requests.get(BITFINEX_XAUT, timeout=TIMEOUT).json()
    return float(body[6])            # LAST_PRICE


def _gc():
    body = requests.get(YAHOO_GC, timeout=TIMEOUT, headers={"User-Agent": "sambangold/1.0"}).json()
    return float(body["chart"]["result"][0]["meta"]["regularMarketPrice"])


def _usdt():
    body = requests.get(KRAKEN_USDT, timeout=TIMEOUT).json()
    pair = next(iter(body["result"].values()))
    return float(pair["c"][0])


def fetch():
    """One snapshot; each source independent, missing ones are None."""
    snap = {"at": time.time(), "source_spot": "Yahoo GC=F (front futures)", "errors": []}
    for key, fn in (("paxg", _paxg), ("xaut", _xaut), ("spot", _gc), ("usdt", _usdt)):
        try:
            snap[key] = fn()
        except Exception as exc:  # noqa: BLE001 — one dead source must not hide the rest
            snap[key] = None
            snap["errors"].append("%s: %s" % (key, str(exc)[:60]))
    if snap["paxg"] is None and snap["xaut"] is None:
        raise FeedError("; ".join(snap["errors"]))
    return snap


def snapshot(max_age=CACHE_SECONDS):
    now = time.time()
    if _cache["snap"] is not None and now - _cache["at"] < max_age:
        return _cache["snap"]
    snap = fetch()
    _cache.update(at=now, snap=snap)
    return snap


def clear_cache():
    _cache.update(at=0.0, snap=None)


def premium(token_price, spot):
    if not token_price or not spot:
        return None
    return round((token_price / spot - 1) * 100, 3)


def analyse(snap):
    out = dict(snap)
    out["paxg_premium"] = premium(snap.get("paxg"), snap.get("spot"))
    out["xaut_premium"] = premium(snap.get("xaut"), snap.get("spot"))
    out["paxg_xaut"] = premium(snap.get("paxg"), snap.get("xaut"))
    usdt = snap.get("usdt")
    out["usdt_off"] = round((usdt - 1) * 100, 3) if usdt else None
    out["peg"] = None if usdt is None else ("ok" if abs(usdt - 1) < PEG_WARN else "off")
    out["flags"] = [k for k in ("paxg_premium", "xaut_premium") if out[k] is not None and abs(out[k]) >= PREMIUM_WARN]
    if out["peg"] == "off":
        out["flags"].append("peg")
    return out


# --- wallet ------------------------------------------------------------------ #

def keccak256(data):
    """Keccak-256 (pre-NIST padding), pure Python, for EIP-55 — small enough to keep."""
    RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
          0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
          0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
          0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
    M = (1 << 64) - 1

    def rol(x, n):
        return ((x << n) | (x >> (64 - n))) & M

    def f(st):
        for rc in RC:
            c = [st[x][0] ^ st[x][1] ^ st[x][2] ^ st[x][3] ^ st[x][4] for x in range(5)]
            d = [c[(x - 1) % 5] ^ rol(c[(x + 1) % 5], 1) for x in range(5)]
            st = [[st[x][y] ^ d[x] for y in range(5)] for x in range(5)]
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    b[y][(2 * x + 3 * y) % 5] = rol(st[x][y], ROT[x][y])
            st = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
            st[0][0] ^= rc
        return st

    rate = 136
    msg = bytearray(data) + b"\x01"
    msg += b"\x00" * ((-len(msg)) % rate)
    msg[-1] |= 0x80
    st = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            x, y = i % 5, i // 5
            st[x][y] ^= int.from_bytes(block[8 * i:8 * i + 8], "little")
        st = f(st)
    out = b""
    for y in range(5):
        for x in range(5):
            if len(out) < 32:
                out += st[x][y].to_bytes(8, "little")
    return out[:32].hex()


def eip55(addr):
    body = addr[2:].lower()
    h = keccak256(body.encode())
    return "0x" + "".join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(body))


def chain_of(addr):
    a = (addr or "").strip()
    if a.startswith("0x") and len(a) == 42 and all(c in "0123456789abcdefABCDEF" for c in a[2:]):
        return "evm"
    if a.startswith("T") and len(a) == 34:
        return "tron"
    if a.startswith(("1", "3", "bc1")) and 26 <= len(a) <= 62:
        return "bitcoin"
    if 32 <= len(a) <= 44 and all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in a):
        return "solana"
    return None


def check_wallet(addr, expected=None):
    addr = (addr or "").strip()
    chain = chain_of(addr)
    res = {"address": addr, "chain": chain, "checksum": None, "poisoning": None, "flags": []}
    if not chain:
        res["flags"].append("unknown_format")
        return res
    if chain == "evm":
        body = addr[2:]
        if body != body.lower() and body != body.upper():
            res["checksum"] = eip55(addr) == addr
            if not res["checksum"]:
                res["flags"].append("bad_checksum")
        else:
            res["checksum"] = None                      # no checksum encoded; cannot verify
            res["flags"].append("no_checksum")
    if expected:
        e = expected.strip()
        if e.lower() == addr.lower():
            res["poisoning"] = "same"
        elif e[:4].lower() == addr[:4].lower() and e[-4:].lower() == addr[-4:].lower():
            res["poisoning"] = "lookalike"
            res["flags"].append("poisoning")
        else:
            res["poisoning"] = "different"
    res["fees"] = FEES
    return res
