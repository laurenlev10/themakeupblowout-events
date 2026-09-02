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
import json, pathlib, sys, datetime, re, html as _html

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                    else "/sessions/awesome-focused-ramanujan/themakeupblowout-events")
DOCS = REPO / "docs"

# ---------------------------------------------------------------------------
# 🛑 IRON RULE #23 — every time this system writes into the world is anchored to
# the VENUE's timezone through lib/venue_tz.py in lauren-agent-infra. There is
# no second copy of the state table here (IRON RULE #27): the workflow checks
# infra out next to this repo, and a session has it at /tmp/infra. If neither
# exists the build refuses — a JSON-LD startDate with a guessed offset is the
# Boise bug again, published to every search engine and AI assistant.
# ---------------------------------------------------------------------------
def _find_infra_lib():
    cands = [pathlib.Path(p) for p in (_os.environ.get("INFRA_LIB", ""),) if p]
    cands += [REPO / "infra" / "lib", REPO.parent / "infra" / "lib", pathlib.Path("/tmp/infra/lib")]
    for c in cands:
        if (c / "venue_tz.py").exists():
            return c
    raise RuntimeError(
        "lauren-agent-infra/lib/venue_tz.py not found (looked in INFRA_LIB, "
        f"{REPO/'infra'/'lib'}, {REPO.parent/'infra'/'lib'}, /tmp/infra/lib). "
        "The build refuses to publish event times without the venue timezone — "
        "IRON RULE #23. In Actions this is the 'Checkout infra' step; in a session "
        "it is the initial clone to /tmp/infra.")

import os as _os
sys.path.insert(0, str(_find_infra_lib()))
from venue_tz import resolve_tz, venue_local_iso, assert_venue_local  # noqa: E402

# ---------------------------------------------------------------------------
# Event hours — ONE definition. The templates carry {{HOURS_LABEL}} /
# {{HOURS_SHORT}}; the JSON-LD startDate/endDate are computed from the same
# two numbers. Before 2026-09-02 "10AM – 5PM" was typed 14 times across six
# templates and would have become a 15th copy inside the structured data.
# ---------------------------------------------------------------------------
OPEN_HOUR, CLOSE_HOUR = 10, 17

def _h12(h):
    return f"{(h % 12) or 12}{'AM' if h < 12 else 'PM'}"

HOURS_LABEL = f"{_h12(OPEN_HOUR)} – {_h12(CLOSE_HOUR)}"   # "10AM – 5PM"
HOURS_SHORT = f"{_h12(OPEN_HOUR)}–{_h12(CLOSE_HOUR)}"     # "10AM–5PM"

SITE = "https://events.themakeupblowout.com"
BRAND_URL = "https://themakeupblowout.com/"
ORG_NAME = "The Makeup Blowout Sale"
# What the page says about itself to Google / Bing / every AI assistant that
# reads the page on "what to do this weekend in <city>". Plain facts, the words
# people search with, nothing the page does not also show a human.
SHARED_OG_IMAGE = "/_assets/shared/women-bags-poster.jpg"
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

def _parse_address(street, city, state):
    """'7699 W Spectrum St, Boise, ID 83709' -> PostalAddress parts.
    The street line is whatever precedes the city; the zip is the trailing 5 digits.
    Missing parts stay missing — a guessed zip is worse than none."""
    s = (street or "").strip()
    m = re.search(r"\b(\d{5})(?:-\d{4})?\s*$", s)
    zipcode = m.group(1) if m else None
    first = s.split(",")[0].strip() if s else None
    out = {"@type": "PostalAddress", "addressLocality": city, "addressRegion": state,
           "addressCountry": "US"}
    if first and first.lower() != city.lower():
        out["streetAddress"] = first
    if zipcode:
        out["postalCode"] = zipcode
    return out


def _event_image(slug):
    """Per-event hero if the file exists in the repo, else the shared brand photo.
    Printed, never silent — a page whose picture is the brand shot is a fact Lauren
    can act on (IRON RULE #11: check all three image places before deciding)."""
    hero = DOCS / "_assets" / "events" / slug / "hero.png"
    if hero.exists():
        return f"{SITE}/_assets/events/{slug}/hero.png"
    print(f"    (no per-event hero for {slug} — JSON-LD/og:image use the shared brand photo)")
    return f"{SITE}{SHARED_OG_IMAGE}"


def _dates_words(sd, ed):
    if sd.month == ed.month:
        return f"{MONTH_NAMES[sd.month-1]} {sd.day}–{ed.day}, {ed.year}"
    return f"{MONTH_NAMES[sd.month-1]} {sd.day} – {MONTH_NAMES[ed.month-1]} {ed.day}, {ed.year}"


def event_facts(ev):
    """Everything the machines are told about one event, computed ONCE from the
    row in upcoming-events.json. Landing pages, the events index, the sitemap and
    the self-check all read this — there is no second place that knows a date."""
    sd = datetime.date.fromisoformat(ev["start_date"])
    ed = datetime.date.fromisoformat(ev["end_date"])
    slug = ev.get("slug") or make_slug(ev["city"], ev["state"], ed.year)
    tz, tz_src, warn = resolve_tz(state=ev["state"], tz=ev.get("tz"))
    if warn:
        # A split-timezone state: the table's majority zone is used, and the
        # warning is printed on every build so it is never a silent guess.
        print(f"    ⚠ {slug}: {warn}")
    city_state = f"{ev['city']}, {ev['state']}"
    venue = ev.get("venue_name") or ""
    street = ev.get("venue_address") or ""
    url = f"{SITE}/events/{slug}/"
    return {
        "slug": slug, "sd": sd, "ed": ed, "tz": tz, "tz_source": tz_src,
        "city": ev["city"], "state": ev["state"], "city_state": city_state,
        "venue": venue, "street": street, "url": url,
        "url_es": f"{SITE}/events/{slug}/index-es.html",
        "start_iso": venue_local_iso(ev["start_date"], OPEN_HOUR, tz),
        "end_iso":   venue_local_iso(ev["end_date"],   CLOSE_HOUR, tz),
        "dates_words": _dates_words(sd, ed),
        "image": _event_image(slug),
        "eventbrite_url": (ev.get("eventbrite_url") or "").strip(),
        "name": f"Makeup Blowout Sale — {city_state} — {_dates_words(sd, ed)}",
    }


def _description(f, lang="en"):
    where = f"at {f['venue']}, {f['street']}" if f["venue"] and f["street"] else f"in {f['city_state']}"
    if lang == "es":
        where = f"en {f['venue']}, {f['street']}" if f["venue"] and f["street"] else f"en {f['city_state']}"
        return (f"Venta de maquillaje con hasta 75% de descuento en {f['city_state']} — "
                f"{f['dates_words']}, viernes a domingo {HOURS_SHORT}, {where}. "
                f"Más de 40 marcas de prestigio de maquillaje, cuidado de la piel, cabello y fragancias. "
                f"Entrada y estacionamiento gratis, no se necesitan boletos.")
    return (f"The Makeup Blowout Sale in {f['city_state']}: a 3-day pop-up beauty sale "
            f"{f['dates_words']}, Friday–Sunday {HOURS_SHORT}, {where}. "
            f"Up to 75% off 40+ prestige makeup, skincare, haircare and fragrance brands. "
            f"Free entry and free parking, no tickets needed — one of the things to do "
            f"this weekend in {f['city']}.")


def event_jsonld(f, lang="en"):
    """schema.org Event — the object Google Events, Bing and the AI assistants read."""
    place = {
        "@type": "Place",
        "name": f["venue"] or f["city_state"],
        "address": _parse_address(f["street"], f["city"], f["state"]),
    }
    obj = {
        "@context": "https://schema.org",
        "@type": ["Event", "SaleEvent"],
        "name": f["name"],
        "description": _description(f, lang),
        "startDate": f["start_iso"],
        "endDate": f["end_iso"],
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": place,
        "image": [f["image"]],
        "url": f["url"] if lang == "en" else f["url_es"],
        "inLanguage": lang,
        "isAccessibleForFree": True,
        "offers": {
            "@type": "Offer",
            "name": "Free entry",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": f["url"],
            "validFrom": datetime.date.today().isoformat(),
        },
        "organizer": {"@type": "Organization", "name": ORG_NAME, "url": BRAND_URL},
        "performer": {"@type": "Organization", "name": ORG_NAME},
        "keywords": ", ".join([
            f"things to do in {f['city']} this weekend", f"{f['city']} events",
            "makeup sale", "beauty sale", "cosmetics sale", "pop-up shop",
            f"makeup blowout sale {f['city']}", "free event"]),
    }
    if f["eventbrite_url"]:
        obj["sameAs"] = [f["eventbrite_url"]]
    return obj


def head_seo(f, lang="en"):
    """<head> block: description, canonical, hreflang, Open Graph, and the JSON-LD."""
    esc = _html.escape
    desc = _description(f, lang)
    title = page_title(f, lang)
    canon = f["url"] if lang == "en" else f["url_es"]
    ld = json.dumps(event_jsonld(f, lang), ensure_ascii=False, indent=1)
    # A "</" inside the JSON would close the script tag; escape it (json.dumps
    # does not, and a venue name can carry anything).
    ld = ld.replace("</", "<\\/")
    return "\n".join([
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{canon}">',
        f'<link rel="alternate" hreflang="en" href="{f["url"]}">',
        f'<link rel="alternate" hreflang="es" href="{f["url_es"]}">',
        f'<link rel="alternate" hreflang="x-default" href="{f["url"]}">',
        '<meta property="og:type" content="event">',
        f'<meta property="og:site_name" content="{esc(ORG_NAME)}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{canon}">',
        f'<meta property="og:image" content="{f["image"]}">',
        f'<meta property="og:locale" content="{"es_US" if lang == "es" else "en_US"}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
        f'<meta name="twitter:image" content="{f["image"]}">',
        f'<script type="application/ld+json">{ld}</script>',
    ])


def page_title(f, lang="en"):
    if lang == "es":
        return f"Makeup Blowout Sale {f['city_state']} — {f['dates_words']} · Hasta 75% de descuento · Entrada gratis"
    return f"Makeup Blowout Sale {f['city_state']} — {f['dates_words']} · Up to 75% Off · Free Entry"


def render_event(ev):
    """Return dict of variables for this event."""
    f = event_facts(ev)
    sd, ed, slug = f["sd"], f["ed"], f["slug"]
    year = ed.year
    return {
        "CITY":       f["city_state"],
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
        "HOURS_LABEL": HOURS_LABEL,
        "HOURS_SHORT": HOURS_SHORT,
        # Language-specific head — filled per template in main(), see fill_lang()
        "PAGE_TITLE": page_title(f, "en"),
        "HEAD_SEO":   head_seo(f, "en"),
        "_PAGE_TITLE_ES": page_title(f, "es"),
        "_HEAD_SEO_ES":   head_seo(f, "es"),
    }, slug, f


def fill_lang(template, vars, lang):
    """Same variables, but the Spanish template gets the Spanish head."""
    if lang == "es":
        vars = {**vars, "PAGE_TITLE": vars["_PAGE_TITLE_ES"], "HEAD_SEO": vars["_HEAD_SEO_ES"]}
    return fill(template, vars)


# ---------------------------------------------------------------------------
# /events/ index, sitemap.xml, robots.txt — the three doors a crawler uses to
# find the per-city pages. The site root redirects to Shopify on purpose, so
# without these the event pages are only reachable from an ad click.
# ---------------------------------------------------------------------------
def events_index_html(facts):
    rows = []
    items = []
    for i, f in enumerate(facts, 1):
        venue = _html.escape(f["venue"]) if f["venue"] else ""
        where = f"{venue} · {_html.escape(f['street'])}" if f["venue"] and f["street"] else _html.escape(f["city_state"])
        rows.append(
            f'<li class="ev"><a href="{f["url"]}"><span class="dt">{_html.escape(f["dates_words"])}</span>'
            f'<span class="ci">{_html.escape(f["city_state"])}</span>'
            f'<span class="wh">{where} · Fri–Sun {HOURS_SHORT} · Free entry</span></a></li>')
        items.append({"@type": "ListItem", "position": i, "url": f["url"], "name": f["name"]})
    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Makeup Blowout Sale — upcoming events",
        "description": "Every upcoming Makeup Blowout Sale: a 3-day pop-up beauty sale with up to 75% off 40+ prestige brands, free entry, a new city every weekend.",
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(items),
        "itemListElement": items,
    }
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": ORG_NAME,
        "url": BRAND_URL,
        "sameAs": ["https://www.instagram.com/themakeupblowoutsale/",
                   "https://www.facebook.com/themakeupblowoutsale/",
                   "https://www.tiktok.com/@makeupblowoutsale"],
    }
    tpl = (DOCS / "_template" / "events-index.html.tpl").read_text(encoding="utf-8")
    return (tpl.replace("{{ROWS}}", "\n".join(rows))
               .replace("{{COUNT}}", str(len(items)))
               .replace("{{JSONLD}}", json.dumps(ld, ensure_ascii=False, indent=1).replace("</", "<\\/"))
               .replace("{{ORG_JSONLD}}", json.dumps(org, ensure_ascii=False, indent=1))
               .replace("{{UPDATED}}", datetime.date.today().isoformat())
               .replace("{{HOURS_SHORT}}", HOURS_SHORT))


def sitemap_xml(facts):
    today = datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">',
             f'  <url><loc>{SITE}/events/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>']
    for f in facts:
        for loc, lang in ((f["url"], "en"), (f["url_es"], "es")):
            lines.append(
                f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{f["url"]}"/>'
                f'<xhtml:link rel="alternate" hreflang="es" href="{f["url_es"]}"/></url>')
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


ROBOTS_TXT = f"""User-agent: *
Allow: /
Disallow: /_template/
Disallow: /oauth/
Disallow: /recount-count/
Disallow: /team-availability/
Disallow: /manager-report/
Disallow: /collab/
Disallow: /scout-plan/
Disallow: /influencer-brief/
Disallow: /preview/

Sitemap: {SITE}/sitemap.xml
"""


# ---------------------------------------------------------------------------
# Self-check: read the JSON-LD BACK out of the written HTML and assert it says
# what the source row says — in the venue's clock. The check that would have
# caught the Boise bug, applied to the one artifact search engines read.
# ---------------------------------------------------------------------------
_LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

def verify_written_page(path, f, lang):
    src = path.read_text(encoding="utf-8")
    m = _LD_RE.search(src)
    if not m:
        raise RuntimeError(f"{path}: no application/ld+json block was written")
    obj = json.loads(m.group(1).replace("<\\/", "</"))
    if "Event" not in obj.get("@type", []):
        raise RuntimeError(f"{path}: JSON-LD @type is {obj.get('@type')!r}, not Event")
    for k in ("name", "startDate", "endDate", "location", "image", "url", "offers", "description"):
        if not obj.get(k):
            raise RuntimeError(f"{path}: JSON-LD is missing {k}")
    assert_venue_local(obj["startDate"], f["tz"], expect_hour=OPEN_HOUR,
                       expect_weekday=f["sd"].weekday(), label=f"{f['slug']} startDate")
    assert_venue_local(obj["endDate"], f["tz"], expect_hour=CLOSE_HOUR,
                       expect_weekday=f["ed"].weekday(), label=f"{f['slug']} endDate")
    if obj["startDate"][:10] != f["sd"].isoformat() or obj["endDate"][:10] != f["ed"].isoformat():
        raise RuntimeError(f"{path}: JSON-LD dates {obj['startDate']}…{obj['endDate']} ≠ row {f['sd']}…{f['ed']}")
    if obj["location"]["address"].get("addressLocality") != f["city"]:
        raise RuntimeError(f"{path}: JSON-LD city ≠ {f['city']}")
    if obj.get("inLanguage") != lang:
        raise RuntimeError(f"{path}: inLanguage {obj.get('inLanguage')!r} ≠ {lang!r}")
    if "{{" in src:
        left = sorted(set(re.findall(r"{{[A-Z_]+}}", src)))
        raise RuntimeError(f"{path}: unfilled placeholders {left}")
    if "10AM" in src.replace(HOURS_SHORT, "").replace(HOURS_LABEL, ""):
        raise RuntimeError(f"{path}: hours typed by hand somewhere — they must come from OPEN_HOUR/CLOSE_HOUR")
    return obj

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
    facts_all = []
    today = datetime.date.today()
    for ev in sorted(events, key=lambda e: e["start_date"]):
        # Skip past events — no need to rebuild landing pages for events that already happened
        ed = datetime.date.fromisoformat(ev["end_date"])
        if ed < today:
            continue
        vars, slug, f = render_event(ev)
        facts_all.append(f)
        target_dir = DOCS / "events" / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text(fill_lang(TPL_LANDING, vars, "en"), encoding="utf-8")
        (target_dir / "share.html").write_text(fill(TPL_SHARE,   vars), encoding="utf-8")
        if TPL_LANDING_ES:
            (target_dir / "index-es.html").write_text(fill_lang(TPL_LANDING_ES, vars, "es"), encoding="utf-8")
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
        # Also store metadata next to the page for the agent to inspect (the head
        # blocks are page content, not metadata — keep _meta.json readable).
        meta = {k: v for k, v in vars.items() if k not in ("HEAD_SEO", "_HEAD_SEO_ES")}
        meta.update({"start_iso": f["start_iso"], "end_iso": f["end_iso"], "tz": str(f["tz"]),
                     "canonical": f["url"], "jsonld_image": f["image"]})
        (target_dir / "_meta.json").write_text(json.dumps({"slug": slug, **meta}, indent=2, ensure_ascii=False), encoding="utf-8")
        # 🛑 Read the page back and assert what the machines will read.
        verify_written_page(target_dir / "index.html", f, "en")
        if TPL_LANDING_ES:
            verify_written_page(target_dir / "index-es.html", f, "es")
        written.append((slug, vars["CITY"]))
        print(f"  wrote {target_dir.relative_to(REPO)}/  ({vars['CITY']})  {f['start_iso']} → {f['end_iso']}")

    # The three crawler doors — rebuilt from the same facts on every run.
    (DOCS / "events" / "index.html").write_text(events_index_html(facts_all), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap_xml(facts_all), encoding="utf-8")
    (DOCS / "robots.txt").write_text(ROBOTS_TXT, encoding="utf-8")
    idx = (DOCS / "events" / "index.html").read_text(encoding="utf-8")
    if len(_LD_RE.findall(idx)) < 2 or "{{" in idx:
        raise RuntimeError("docs/events/index.html: ItemList/Organization JSON-LD missing or placeholders left")
    sm = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
    for f in facts_all:
        if f["url"] not in sm:
            raise RuntimeError(f"sitemap.xml does not list {f['url']}")
    print(f"  wrote docs/events/index.html ({len(facts_all)} upcoming), docs/sitemap.xml, docs/robots.txt")
    print(f"\n✓ generated {len(written)} landing pages")
    return written

if __name__ == "__main__":
    main()
