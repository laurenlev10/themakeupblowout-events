#!/usr/bin/env python3
"""
Cross-repo sync: pull authoritative event data from lauren-agent-hub-data
into themakeupblowout-events/docs/upcoming-events.json.

Sources (all fetched from public Pages-served URLs — no auth needed):
  - event_form_ids.json   → form_id per event
  - venue_details.md      → venue_name, venue_address per event
  - recent_meta_posts.json → ig_url (auto-match by city)

For each event in upcoming-events.json:
  - If form_id starts with "TODO_" or is missing, fill from event_form_ids.json
  - If venue_name/venue_address contain "(...— please update)", fill from venue_details.md
  - If ig_url is the default themakeupblowoutsale page, try to find a city-matching reel
    in recent_meta_posts.json

Writes back upcoming-events.json. The downstream build-landing-pages.yml will then
auto-rebuild the affected pages.
"""
import json, re, urllib.request, urllib.error, datetime, sys
from pathlib import Path


HUB_RAW = "https://raw.githubusercontent.com/laurenlev10/lauren-agent-hub-data/main"
HUB_PAGES = "https://laurenlev10.github.io/lauren-agent-hub-data"

REPO = Path(__file__).resolve().parent.parent
EVENTS_JSON = REPO / "docs/upcoming-events.json"

# notes.json is the SOURCE OF TRUTH for per-event reel links (IRON RULE #5).
# Lauren pastes IG / New-Reel / FB / TikTok links via the launch-dashboard chips,
# which write here. We mirror them into upcoming-events.json so build.py can
# put the REAL per-event reel into the SHARE / landing / tiktok page buttons
# (instead of the generic brand-channel fallback).
NOTES_URL = f"{HUB_PAGES}/launch/notes.json"


def _slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def notes_key_for(ev):
    """notes.json key = slugify(FULL city) + '-' + start_date  (IRON RULE #17, no state)."""
    city = ev.get("city", "") or ""
    sd = (ev.get("start_date", "") or "")[:10]
    if not city or not sd:
        return None
    return f"{_slugify(city)}-{sd}"


def reel_links_from_notes(note):
    """Resolve the 3 share-button URLs from one event's notes entry.
    IG prefers the New Reel (slot 2) per IRON RULE #5; FB + TikTok as-is.
    Returns dict with only the keys that have a real value."""
    if not isinstance(note, dict):
        return {}
    out = {}
    ig = (note.get("insta_reel_url_2") or note.get("insta_reel_url") or "").strip()
    fb = (note.get("fb_url") or "").strip()
    tt = (note.get("tiktok_url") or "").strip()
    if ig:
        out["ig_url"] = ig
    if fb:
        out["fb_url"] = fb
    if tt:
        out["tiktok_url"] = tt
    return out


def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  ⚠ couldn't fetch {url}: {e}")
        return None


def fetch_text(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ⚠ couldn't fetch {url}: {e}")
        return ""


def parse_venue_details(md_text):
    """Parse the Markdown table in venue_details.md → list of dicts."""
    out = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 4 and cells[0] and cells[0] not in ("dates", "Event dates (Fri–Sun)", "Event dates (Fri-Sun)"):
            out.append({
                "dates_str": cells[0],
                "city_state": cells[1],
                "venue": cells[2],
                "address": cells[3],
            })
    return out


_MONTHS = {"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,
           "may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,
           "sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}


def parse_dates_range(s, year=2026):
    """'May 8–10' or 'Jul 31–Aug 2' → (start, end) date objects."""
    if not s: return None, None
    s = s.replace("–","-").replace("—","-").strip()
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2})$", s)
    if m:
        mo = _MONTHS.get(m.group(1).lower())
        if mo:
            try:
                return datetime.date(year, mo, int(m.group(2))), datetime.date(year, mo, int(m.group(3)))
            except ValueError: pass
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})\s*-\s*([A-Za-z]+)\s+(\d{1,2})$", s)
    if m:
        m1, m2 = _MONTHS.get(m.group(1).lower()), _MONTHS.get(m.group(3).lower())
        if m1 and m2:
            try:
                return datetime.date(year, m1, int(m.group(2))), datetime.date(year, m2, int(m.group(4)))
            except ValueError: pass
    return None, None


def match_venue(event, venues):
    """Match an event from upcoming-events.json to a venue_details.md row.
    Requires BOTH date AND city to match — guards against the case where
    upcoming-events.json has stale data (e.g. Nashville with Louisville dates)."""
    ev_start = event.get("start_date","")[:10]
    ev_city = (event.get("city","") or "").lower()
    if not ev_start or not ev_city:
        return None
    for v in venues:
        start, _ = parse_dates_range(v["dates_str"], year=int(ev_start[:4]))
        date_match = (start and start.isoformat() == ev_start)
        city_match = ev_city in v["city_state"].lower()
        if date_match and city_match:
            return v
    return None


def match_reel_by_city(city, state, posts):
    """Find a reel in recent_meta_posts.json whose caption matches the city."""
    if not posts or not city: return None
    needle = city.lower()
    state_l = (state or "").lower()
    items = posts.get("ig_media", [])
    # Score-based match (port of lauren_meta.match_by_city)
    best, best_score = None, 0
    for it in items:
        text = (it.get("caption") or "").lower()
        head = text[:80]
        score = 0
        if re.search(rf"sale\s+in\s+{re.escape(needle)}\s*,\s*{re.escape(state_l) if state_l else '[a-z]{2}'}", text):
            score += 10
        if re.search(rf"\bin\s+{re.escape(needle)}\s*,", head):
            score += 6
        if re.search(rf"\bin\s+{re.escape(needle)}\b", text):
            score += 3
        if re.search(rf"\b{re.escape(needle)}\b", text):
            score += 1
        if score > best_score:
            best, best_score = it, score
    return best


def main():
    print("Fetching upstream data sources...")
    form_ids = fetch_json(f"{HUB_PAGES}/state/event_form_ids.json") or {"events":{}}
    posts = fetch_json(f"{HUB_PAGES}/state/recent_meta_posts.json") or {}
    notes = fetch_json(NOTES_URL) or fetch_json(f"{HUB_RAW}/docs/launch/notes.json") or {}
    notes_mt = notes.get("MANUAL_TASKS", notes) if isinstance(notes, dict) else {}
    venue_md = fetch_text(f"{HUB_RAW}/scripts/data/venue_details.md")
    venues = parse_venue_details(venue_md)
    print(f"  form_ids: {len(form_ids.get('events',{}))} entries")
    print(f"  recent_meta_posts.json: {len(posts.get('ig_media',[]))} reels")
    print(f"  venue_details.md: {len(venues)} venues")
    print(f"  notes.json: {len(notes_mt)} event entries")

    data = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    events = data.get("events", [])
    n_form = n_venue = n_ig = n_reel = 0

    for ev in events:
        slug = ev.get("slug") or ""
        start_date = ev.get("start_date","")[:10]
        ev_form_id = ev.get("form_id","") or ""
        ev_venue = ev.get("venue_name","") or ""
        ev_addr = ev.get("venue_address","") or ""
        ev_ig = ev.get("ig_url","") or ""

        # form_id sync
        if (ev_form_id.startswith("TODO_") or not ev_form_id) and slug and start_date:
            key = f"{slug}-{start_date}"
            entry = form_ids.get("events", {}).get(key)
            if entry and entry.get("form_id"):
                ev["form_id"] = entry["form_id"]
                n_form += 1
                print(f"  ✓ form_id: {slug} → {entry['form_id']}")

        # venue sync
        if ("please update" in ev_venue.lower() or not ev_venue) or \
           ("please update" in ev_addr.lower() or not ev_addr):
            v = match_venue(ev, venues)
            if v:
                if "please update" in ev_venue.lower() or not ev_venue:
                    ev["venue_name"] = v["venue"]
                if "please update" in ev_addr.lower() or not ev_addr:
                    ev["venue_address"] = v["address"]
                n_venue += 1
                print(f"  ✓ venue:   {slug} → {v['venue']}")

        # Reel links — notes.json is authoritative (IRON RULE #5). Whatever
        # Lauren pasted via the launch-dashboard chips (IG / New Reel / FB /
        # TikTok) flows straight into the SHARE / landing / tiktok buttons.
        nkey = notes_key_for(ev)
        links = reel_links_from_notes(notes_mt.get(nkey)) if nkey else {}
        for field in ("ig_url", "fb_url", "tiktok_url"):
            new_val = links.get(field)
            if new_val and ev.get(field) != new_val:
                ev[field] = new_val
                n_reel += 1
                print(f"  ✓ {field:9s}: {slug} → {new_val}")

        # Fallback ONLY for IG: if notes has no reel yet, try the city-caption
        # auto-match from recent_meta_posts.json (legacy behavior, never overrides
        # a notes-provided link since that already set ev_ig above).
        ev_ig = ev.get("ig_url", "") or ""
        is_default_ig = "themakeupblowoutsale/" in ev_ig and "/reel/" not in ev_ig
        if not links.get("ig_url") and (is_default_ig or not ev_ig) and ev.get("city"):
            reel = match_reel_by_city(ev["city"], ev.get("state",""), posts)
            if reel and reel.get("permalink"):
                ev["ig_url"] = reel["permalink"]
                n_ig += 1
                print(f"  ✓ ig_url(cap): {slug} → {reel['permalink']}")

    if n_form + n_venue + n_ig + n_reel > 0:
        data["_updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        EVENTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n✓ Updated {n_form} form_ids, {n_venue} venues, {n_reel} reel-links, {n_ig} ig_urls(caption)")
    else:
        print("\n  no changes needed")

    # Exit code 0 either way; the workflow's git diff check decides whether to commit


if __name__ == "__main__":
    main()
