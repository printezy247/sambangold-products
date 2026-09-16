"""Seed data for the team file library: docs/pics/vids that ship in this
repo under `library/`, plus external links (e.g. Sam's shared Drive folder)
that aren't hosted here.

This is internal-team content, not a public download — some of it (the
Gold Recruit Manual, the Field Manual, ...) is sold as a paid ebook on
website_sam. `/team/library/<path>` is gated by `team_required` for
exactly that reason.
"""

import os

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library")

CATEGORY_DIRS = {"docs": "doc", "pics": "pic", "vids": "vid"}


def _title_from_filename(name):
    return os.path.splitext(name)[0].replace("_", " ").strip()


def scan_repo_files():
    """Every file under library/{docs,pics,vids}/, walked recursively
    (pics/logo included), as seed rows keyed by their path relative to
    `library/` — that relative path is also what `/team/library/<path>`
    serves."""
    items = []
    for subdir, category in CATEGORY_DIRS.items():
        base = os.path.join(ROOT, subdir)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fname in sorted(files):
                rel = os.path.relpath(os.path.join(dirpath, fname), ROOT).replace(os.sep, "/")
                sub = os.path.relpath(dirpath, base)
                items.append({
                    "category": category,
                    "title": _title_from_filename(fname),
                    "source": "repo_asset",
                    "url": rel,
                    "tags": "" if sub == "." else sub.replace(os.sep, "/"),
                })
    return items


# Links to content that lives outside this repo — not scanned, just recorded.
EXTERNAL_LINKS = (
    {"category": "doc", "title": "Sam's shared Drive folder (working files)", "source": "drive",
     "url": "https://drive.google.com/drive/folders/1KlzuoDsmWqxNtaTnoctMx4Taj61J-wRg", "tags": "drive"},
)


def seed_data():
    return scan_repo_files() + list(EXTERNAL_LINKS)
