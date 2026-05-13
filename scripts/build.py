#!/usr/bin/env python3
"""
Build per-event landing pages from the master events JSON + Lauren's templates.

Reads:
  - {repo}/docs/upcoming-events.json   (extended schema with venue/form/IG fields)
  - {repo}/docs/_template/landing.html.tpl
  - {repo}/docs/_template/share.html.tpl

Writes:
  - {repo}/docs/events/{slug}/index.html
  - {repo}/docs/events/{slug}/share.html

Run from anywhere (it resolves the repo from a CLI arg or default).
"""
import json, pathlib, sys, datetime, re

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                    else "/sessions/awesome-focused-ramanujan/themakeupblowout-events")
DOCS = REPO / "docs"
TPL_LANDING = (DOCS / "_template" / "landing.html.tpl").read_text(encoding="utf-8")
TPL_SHARE   = (DOCS / "_template" / "share.html.tpl").read_text(encoding="utf-8")
TPL_LANDING_ES = (DOCS / "_template" / "landing-es.html.tpl").read_text(encoding="utf-8") if (DOCS / "_template" / "landing-es.html.tpl").exists() else None
TPL_SHARE_ES   = (DOCS / "_template" / "share-es.html.tpl").read_text(encoding="utf-8") if (DOCS / "_template" / "share-es.html.tpl").exists() else None
TPL_TIKTOK     = (DOCS / "_template" / "tiktok.html.tpl").read_text(encoding="utf-8") if (DOCS / "_template" / "tiktok.html.tpl").exists() else None
TPL_TIKTOK_ES  = (DOCS / "_template" / "tiktok-es.html.tpl").read_text(encoding="utf-8") if (DOCS / "_template" / "tiktok-es.html.tpl").exists() else None
TPL_STATS      = (DOCS / "_template" / "stats.html.tpl").read_text(encoding="utf-8") if (DOCS / "_template" / "stats.html.tpl").exists() else None
DATA        = json.loads((DOCS / "upcoming-events.json").read_text(encoding="utf-8"))

MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def ord_suffix(n):
    if 10 <= n % 100 <= 20: return "th"
    return {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")

def make_slug(city, state, year):
    s = f"{city.lower()}-{state.lower()}-{year}"
    return re.sub(r"[^a-z0-9-]+", "-", s).strip("-")

def render_event(ev):
    """Return dict of variables for this event."""
    sd = datetime.date.fromisoformat(ev["start_date"])
    ed = datetime.date.fromisoformat(ev["end_date"])
    year = ed.year
    slug = ev.get("slug") or make_slug(ev["city"], ev["state"], year)
    return {
        "CITY":       f"{ev['city']}, {ev['state']}",
        "STREET":     ev.get("venue_address", "(venue address — to be filled in)"),
        "HOTEL":      ev.get("venue_name",    "(venue name — to be filled in)"),
        "MONTH":      MONTH_NAMES[sd.month - 1],
        "START_DAY":  f"{sd.day}{ord_suffix(sd.day)}",
        "END_DAY":    f"{ed.day}{ord_suffix(ed.day)}",
        "YEAR":       str(year),
        "FORM_ID":    ev.get("form_id",   "TODO_GET_FORM_ID_FROM_LAUREN"),
        "SHARE_URL":  "share.html",  # relative within the event folder
        "IG_URL":     ev.get("ig_url",    "https://www.instagram.com/themakeupblowoutsale/"),
        "FB_URL":     ev.get("fb_url",    "https://www.facebook.com/themakeupblowoutsale/"),
        "TIKTOK_URL": ev.get("tiktok_url","https://www.tiktok.com/@themakeupblowoutsale"),
        "EVENT_SLUG": slug,
        "HERO_IMAGE": f"/_assets/events/{slug}/hero.png",
    }, slug

import os as _os

# Pixel IDs from env (GitHub Secrets in workflow).
#
# IRON RULE (set 2026-05-13 after the silent-zero incident): the build MUST
# fail loudly when a pixel secret is missing. Falling back to a placeholder
# ("0000000000000000" etc.) silently ships pages that look correct but never
# fire the pixel — so Meta/TikTok/GA4 can't see traffic, ad optimization runs
# blind, and the failure isn't visible until weeks later when someone notices
# zero events in the pixel dashboard.
#
# The previous behavior caused 15,447 landing_page_view events vs 16
# ViewContent events in the last 7 days (May 6-13) — a 99.9% miss rate.
# All three secrets were unset in this repo (themakeupblowout-events) and
# the build had been substituting placeholders since the repo was created.
#
# If a secret is legitimately missing during development, set it locally
# in the env before running build.py. There is no longer a default fallback.
def _required_secret(name: str, looks_like: str) -> str:
    v = _os.environ.get(name, "").strip()
    if not v:
        raise RuntimeError(
            f"{name} env var is missing — build refuses to ship pages with "
            f"placeholder pixel IDs. Set it in GitHub Secrets "
            f"(Settings > Secrets and variables > Actions) or export locally. "
            f"Expected format like {looks_like!r}."
        )
    # Reject the old placeholder values too, in case someone literally pasted them.
    if v in ("0000000000000000", "C00000000000", "G-NOT-SET-YET"):
        raise RuntimeError(
            f"{name} is set to a placeholder value {v!r} — replace with the real ID."
        )
    return v

_PIXEL_VARS = {
    "__GA4_MEASUREMENT_ID__": _required_secret("GA4_MEASUREMENT_ID", "G-XXXXXXXXXX"),
    "__META_PIXEL_ID__":      _required_secret("META_PIXEL_ID",      "149055399513134"),
    "__TIKTOK_PIXEL_ID__":    _required_secret("TIKTOK_PIXEL_ID",    "C00000000000000000"),
}

def fill(template, vars):
    out = template
    for k, v in vars.items():
        out = out.replace("{{" + k + "}}", v)
    # Apply pixel substitutions on every render
    for placeholder, value in _PIXEL_VARS.items():
        out = out.replace(placeholder, value)
    return out

def main():
    events = DATA.get("events", [])
    written = []
    for ev in events:
        # Skip past events — no need to rebuild landing pages for events that already happened
        ed = datetime.date.fromisoformat(ev["end_date"])
        if ed < datetime.date.today():
            continue
        vars, slug = render_event(ev)
        target_dir = DOCS / "events" / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text(fill(TPL_LANDING, vars), encoding="utf-8")
        (target_dir / "share.html").write_text(fill(TPL_SHARE,   vars), encoding="utf-8")
        if TPL_LANDING_ES:
            (target_dir / "index-es.html").write_text(fill(TPL_LANDING_ES, vars), encoding="utf-8")
        if TPL_SHARE_ES:
            (target_dir / "share-es.html").write_text(fill(TPL_SHARE_ES, vars), encoding="utf-8")
        # TikTok variants — same look as landing, but sign-up form replaced with thank-you/share.
        # Lead is captured upstream via TikTok's lead form + Zapier; this page's job is to
        # convert the new SMS subscriber into a social share.
        if TPL_TIKTOK:
            (target_dir / "tiktok.html").write_text(fill(TPL_TIKTOK, vars), encoding="utf-8")
        if TPL_TIKTOK_ES:
            (target_dir / "tiktok-es.html").write_text(fill(TPL_TIKTOK_ES, vars), encoding="utf-8")
        if TPL_STATS:
            (target_dir / "stats.html").write_text(fill(TPL_STATS, vars), encoding="utf-8")
        # Also store metadata next to the page for the agent to inspect
        (target_dir / "_meta.json").write_text(json.dumps({"slug": slug, **vars}, indent=2), encoding="utf-8")
        written.append((slug, vars["CITY"]))
        print(f"  wrote {target_dir.relative_to(REPO)}/  ({vars['CITY']})")
    print(f"\n✓ generated {len(written)} landing pages")
    return written

if __name__ == "__main__":
    main()
