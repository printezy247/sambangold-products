"""The registry is the contract: every product ships both surfaces."""

from app.products import BY_NUMBER, BY_SLUG, PRODUCTS, command_index


def test_all_eighteen_are_registered():
    assert [p.number for p in PRODUCTS] == list(range(1, 19))
    assert len(BY_SLUG) == 18
    assert len(BY_NUMBER) == 18


def test_every_product_has_both_surfaces():
    for p in PRODUCTS:
        assert p.bot_commands, "%s has no Telegram half" % p.name
        assert p.dashboard_views, "%s has no dashboard half" % p.name
        assert p.free_tier, "%s has no free tier" % p.name
        assert p.primary in ("bot", "dashboard")
        assert p.status in ("shipped", "proposed")


def test_no_command_word_serves_two_products():
    index = command_index()
    words = [c.split()[0].lstrip("/") for p in PRODUCTS for c, _ in p.bot_commands]
    for word in set(words):
        owners = {p.number for p in PRODUCTS
                  for c, _ in p.bot_commands if c.split()[0].lstrip("/") == word}
        assert len(owners) == 1, "/%s is claimed by %s" % (word, sorted(owners))
    assert set(index) == set(words)


def test_asset_and_spec_paths_are_derived_not_typed():
    for p in PRODUCTS:
        assert p.icon == "assets/icons/ic-%02d.svg" % p.number
        assert p.spec == "products/product-%02d.md" % p.number
