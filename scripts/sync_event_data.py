#!/usr/bin/env python3
"""
Cross-repo sync: pull authoritative event data from lauren-agent-hub-data
into themakeupblowout-events/docs/upcoming-events.json.

Sources — the two REQUIRED ones come from git through the Worker (no auth needed;
the Worker holds the token), the third from a Pages-served URL:
  - launch/notes.json     → ig_url / fb_url / tiktok_url  (IRON RULE #5, authoritative)
                            via Worker {kind:"get_launch_notes"}
  - event_form_ids.json   → form_id per event
                            via Worker {kind:"get_event_form_ids"}
  - data/venue_details.md → venue_name, venue_address per event
                            over Pages — docs/data/ IS published and this file changes
                            on a human timescale, so no deploy race can reach it

🛑 A hub file that must be CURRENT is never read over dashboard.themakeupblowout.com.
Two separate ways that URL lies, both measured, both fixed here on 2026-08-24:
the Pages deploy lags the commit that woke us by minutes (Reno's FB reel link), and
docs/state/** is not in the Pages build at all since 2026-08-18 (event_form_ids.json),
so that path answers 200 with whatever an unrelated deploy last baked in. Guarded by
`hub-state-is-not-read-over-pages` in the hub repo.

🛑 EVERY fetch here MUST carry a real User-Agent. dashboard.themakeupblowout.com
sits behind Cloudflare, which 403s the default `Python-urllib/3.x` UA. That is
exactly how this script spent weeks reporting SUCCESS while syncing nothing —
see the 2026-08-18 note below.

For each event in upcoming-events.json:
  - If form_id starts with "TODO_" or is missing, fill from event_form_ids.json
  - If venue_name/venue_address contain "(...— please update)", fill from venue_details.md
  - Mirror the reel links Lauren pasted (notes.json) into ig_url / fb_url / tiktok_url

Writes back upcoming-events.json. The downstream build-landing-pages.yml will then
auto-rebuild the affected pages.
"""
import json, re, urllib.request, urllib.error, datetime, sys
from pathlib import Path


# Public state files: served by GitHub Pages at the dashboard custom domain
# (docs/ = site root). Public + CORS-enabled, and STAYS public after
# lauren-agent-hub-data goes private (GitHub Pro keeps Pages serving).
HUB_PAGES = "https://dashboard.themakeupblowout.com"
# 🛑 2026-08-18 — venue_details.md used to be pulled from raw.githubusercontent
# (`scripts/data/venue_details.md`), which 404s now that the hub repo is private.
# The file already exists at docs/data/venue_details.md — byte-identical, and
# Pages-served. There is no reason for a second transport: everything this
# script needs is public at HUB_PAGES.
VENUE_URL = f"{HUB_PAGES}/data/venue_details.md"

REPO = Path(__file__).resolve().parent.parent
EVENTS_JSON = REPO / "docs/upcoming-events.json"

# notes.json is the SOURCE OF TRUTH for per-event reel links (IRON RULE #5).
# Lauren pastes IG / New-Reel / FB / TikTok links via the launch-dashboard chips,
# which write here. We mirror them into upcoming-events.json so build.py can
# put the REAL per-event reel into the SHARE / landing / tiktok page buttons
# (instead of the generic brand-channel fallback).
#
# 🛑 2026-08-24 — this is read through the Worker, NOT over HUB_PAGES.
# ~~NOTES_URL = f"{HUB_PAGES}/launch/notes.json"~~ lost Reno's 📘 FB Reel link.
# Lauren pasted it at 21:43:17; the hub's notify workflow fired the dispatch at
# 21:43:22; this script ran at 21:43:39 and read the Pages copy — which was still
# mid-deploy and therefore still the PREVIOUS notes.json. It had the IG and TikTok
# links (pasted 2 and 4 minutes earlier, already deployed) and no fb_url. The sync
# reported ✅, committed, and the SHARE button kept the generic brand link.
#
# The dispatch is ~20s behind the commit and a Pages deploy takes minutes, so the
# fast path could never win — a faster notification only made the read staler. The
# Worker serves the file out of git, so what we read IS the commit that woke us.
# There is no Pages fallback on purpose: falling back would restore exactly the
# stale read this replaces, and a wrong reel link is worse than a failed job.
# Guarded by `hub-state-is-not-read-over-pages` in the hub repo.
WORKER_URL = "https://danielle.laurenlev10.workers.dev/"


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


# 🛑 2026-08-18 — the silent-sync bug, and why both of these look like this.
#
# Lauren pasted the Salt Lake City and Bakersfield reel links via the launch-
# dashboard chips. notes.json got them, the hub notify workflow fired, the
# repository_dispatch arrived, THIS workflow ran and reported ✅ success — and
# the SHARE pages kept pointing at the generic brand profiles.
#
# Cause: every request to dashboard.themakeupblowout.com came back 403. It is
# behind Cloudflare, which blocks the default `Python-urllib/3.x` User-Agent.
# Measured that day: no UA → 403, any real UA → 200, on all three dashboard
# paths (events.themakeupblowout.com is NOT affected — no bot rule there).
#
# The 403 was not the dangerous part. A `fetch_json(...) or {}` turned a dead
# source into an EMPTY one, the loop then found nothing to change, and the
# workflow exited 0. A green check mark on a job that did nothing is worse than
# a red one: nobody looks. So notes.json and event_form_ids.json are now HARD
# REQUIRED — if they cannot be read, this script raises and the workflow fails
# loudly (and texts Lauren). Never re-add an `or {}` fallback to a required
# source; a reel link that does not reach the buttons must never be silent.
# (2026-08-24: both of those sources moved to worker_read(), which has the same
# refusal built in and no url argument to point back at Pages. fetch_json itself
# was deleted — with no callers left it was only a way to reintroduce the bug.)
UA = "Mozilla/5.0 (compatible; makeupblowout-sync/1.0; +https://events.themakeupblowout.com)"


def _get(url, timeout=20):
    """Raw GET with a real User-Agent. Raises on any failure — callers decide."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def worker_read(kind, field):
    """Read one hub file from git through the Worker. Never Pages, never a fallback.

    Every source this script calls REQUIRED comes through here, so the failure is
    one shape in one place: anything short of `ok:true` plus a populated payload
    raises, and the workflow goes red. A fallback to the published copy is exactly
    the stale read this replaces — see the 2026-08-24 note on WORKER_URL.
    """
    body = json.dumps({"kind": kind}).encode("utf-8")
    req = urllib.request.Request(
        WORKER_URL, data=body, method="POST",
        headers={"User-Agent": UA, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"REQUIRED source unreadable: Worker {kind} → {type(e).__name__}: {e}. "
            "Refusing to 'succeed' with nothing synced — the SHARE-page reel buttons "
            "would silently keep the previous (or generic) link."
        ) from e
    got = payload.get(field)
    if not payload.get("ok") or not isinstance(got, dict) or not got:
        raise RuntimeError(
            f"REQUIRED source unreadable: Worker {kind} answered "
            f"{payload.get('error') or payload!r} — refusing to sync nothing.")
    return got


def fetch_text(url, required=False):
    try:
        return _get(url)
    except Exception as e:
        if required:
            raise RuntimeError(f"REQUIRED source unreadable: {url} → {type(e).__name__}: {e}") from e
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


def main():
    print("Fetching upstream data sources...")
    # required=True: an unreadable source fails the run instead of syncing nothing.
    form_ids = worker_read("get_event_form_ids", "form_ids")
    notes_mt = worker_read("get_launch_notes", "notes")
    venue_md = fetch_text(VENUE_URL, required=True)
    venues = parse_venue_details(venue_md)
    print(f"  form_ids: {len(form_ids.get('events',{}))} entries")
    print(f"  venue_details.md: {len(venues)} venues")
    print(f"  notes.json: {len(notes_mt)} event entries")
    if not notes_mt:
        raise RuntimeError(
            "notes.json fetched but contains no event entries — the reel links "
            "cannot be synced. Failing loudly rather than leaving the SHARE "
            "buttons on their previous value."
        )

    data = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    events = data.get("events", [])
    n_form = n_venue = n_reel = 0

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

        # No caption fallback any more. It read docs/state/recent_meta_posts.json,
        # which the octopos-proxy Worker replaced on 2026-08-16 — the file is gone,
        # so the "fallback" was a guaranteed 404 pretending to be a safety net.
        # notes.json is the only source for these buttons (IRON RULE #5); an event
        # with no reel pasted yet correctly keeps the generic brand link.

    if n_form + n_venue + n_reel > 0:
        data["_updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        EVENTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n✓ Updated {n_form} form_ids, {n_venue} venues, {n_reel} reel-links")
    else:
        print("\n  no changes needed")

    # Exit code 0 either way; the workflow's git diff check decides whether to commit


if __name__ == "__main__":
    main()
