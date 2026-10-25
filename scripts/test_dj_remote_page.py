#!/usr/bin/env python3
"""test_dj_remote_page.py — docs/dj/ (the event manager's music remote) in headless Chromium.  (25.10.2026)

The page is public and holds no key: every tap is a POST to the danielle Worker (kind dj_*), which
answers with the speaker's state AFTER the action. Here the Worker is an in-memory speaker, and the
real page is served under its real hostname. What must hold:
  · what is playing, the artist, the city and the source chip are the Worker's answer;
  · Pause/Play sends the right kind and the button flips with the answer; Next sends dj_skip;
  · volume −/+ send delta ∓1, the bar and the number follow, + is disabled at the top;
  · a source switch needs TWO taps: the first arms it and sends nothing, the second sends dj_source;
    the playing source cannot be re-sent; only the Worker's two sources are offered;
  · offline → a red banner and disabled controls; Opening by hand → an amber banner;
  · a Worker error is a red banner, never a silent page;
  · no horizontal scroll on a phone (390) or a tablet (820); no page errors.
Exit 0 green · 1 a failure · 2 NOT RUN (no Chromium).
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
HOST = "https://events.themakeupblowout.com"
WORKER = "https://danielle.laurenlev10.workers.dev/"

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print("NOT RUN — playwright is not installed:", e); sys.exit(2)

SRC = [{"key": "schedule", "name": "MBS Event Weekend"}, {"key": "main", "name": "MBS Event — Main"}]
speaker = {}
calls = []
fail_next = {"on": False}


def reset(**kw):
    speaker.clear()
    speaker.update(dict(online=True, state="playing", volume=8, track="Walking on Sunshine",
                        artists="Katrina and the Waves", source="schedule"))
    speaker.update(kw)
    calls.clear()


def answer():
    names = {"schedule": "MBS Event Weekend", "main": "MBS Event — Main", "opening": "MBS Event — Opening"}
    return {"ok": True, "online": speaker["online"], "state": speaker["state"], "volume": speaker["volume"], "volume_max": 16,
            "track": ({"title": speaker["track"], "artists": speaker["artists"]} if speaker["track"] else None),
            "source": {"name": names.get(speaker["source"], speaker["source"]), "key": speaker["source"] if speaker["source"] in names else "other"},
            "sources": SRC, "location": {"city": "Albuquerque", "state": "NM", "timezone": "America/Denver"}}


def worker(route):
    req = route.request
    if req.method == "OPTIONS":
        return route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST, OPTIONS"})
    body = json.loads(req.post_data or "{}")
    calls.append(body)
    hdr = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    if fail_next["on"]:
        fail_next["on"] = False
        return route.fulfill(status=502, headers=hdr, body=json.dumps({"ok": False, "error": "Soundtrack HTTP 503"}))
    k = body.get("kind")
    if k == "dj_pause": speaker["state"] = "paused"
    if k == "dj_play": speaker["state"] = "playing"
    if k == "dj_skip": speaker["track"] = "Dancing Queen"; speaker["artists"] = "ABBA"
    if k == "dj_volume": speaker["volume"] = max(0, min(16, speaker["volume"] + int(body.get("delta", 0))))
    if k == "dj_source": speaker["source"] = body.get("source")
    return route.fulfill(status=200, headers=hdr, body=json.dumps(answer()))


def site(route):
    p = route.request.url.split(HOST, 1)[1].split("?")[0]
    if p.endswith("/"): p += "index.html"
    f = DOCS / p.lstrip("/")
    if not f.exists(): return route.fulfill(status=404, body="")
    ct = "text/html; charset=utf-8" if f.suffix == ".html" else "application/octet-stream"
    return route.fulfill(status=200, headers={"Content-Type": ct}, body=f.read_bytes())


bad = 0
def t(name, ok, more=""):
    global bad
    print(("✓ " if ok else "✗ ") + name + ("" if ok or not more else " — " + str(more)))
    if not ok: bad += 1


with sync_playwright() as pw:
    try:
        b = pw.chromium.launch()
    except Exception as e:
        print("NOT RUN — Chromium could not start:", str(e).splitlines()[0]); sys.exit(2)
    ctx = b.new_context(viewport={"width": 820, "height": 1180})
    errs = []
    ctx.route(WORKER + "**", worker)
    ctx.route(HOST + "/**", site)
    ctx.route("**/*", lambda r: r.fallback() if r.request.url.startswith((HOST, WORKER)) else r.fulfill(status=404, body=""))
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    txt = lambda sel: pg.inner_text(sel)

    def open_page():
        pg.goto(HOST + "/dj/")
        pg.wait_for_function("document.getElementById('title').textContent !== 'Loading…'", timeout=8000)

    def tap(sel):
        pg.click(sel); pg.wait_for_timeout(250)

    reset(); open_page()
    t("now playing: title and artist are the Worker's", txt("#title") == "Walking on Sunshine" and txt("#artist") == "Katrina and the Waves", txt("#title"))
    t("the city is in the header", "Albuquerque, NM" in txt("#where"))
    t("chips: online · playing · Event schedule", all(x in txt("#chips") for x in ("Speaker online", "Playing", "Event schedule")), txt("#chips"))
    t("no banner when all is well", "show" not in pg.get_attribute("#banner", "class"))
    t("the first request is a read (dj_state)", calls and calls[0] == {"kind": "dj_state"}, calls)

    calls.clear(); tap("#btnPlay")
    t("Pause sends dj_pause and the button flips to Play", calls == [{"kind": "dj_pause"}] and "Play" in txt("#btnPlay"), calls)
    t("paused → amber banner says so", "paused" in txt("#banner").lower())
    calls.clear(); tap("#btnPlay")
    t("Play sends dj_play", calls == [{"kind": "dj_play"}] and "Pause" in txt("#btnPlay"), calls)
    calls.clear(); tap("#btnSkip")
    t("Next song sends dj_skip and shows the new song", calls == [{"kind": "dj_skip"}] and txt("#title") == "Dancing Queen", calls)

    calls.clear(); tap("#volUp")
    t("+ sends delta +1 and the number follows", calls == [{"kind": "dj_volume", "delta": 1}] and "Volume 9 of 16" in txt("#volNum"), (calls, txt("#volNum")))
    calls.clear(); tap("#volDown")
    t("− sends delta −1", calls == [{"kind": "dj_volume", "delta": -1}] and "Volume 8 of 16" in txt("#volNum"))
    reset(volume=16); open_page()
    t("+ is disabled at the top of the volume", pg.is_disabled("#volUp") and not pg.is_disabled("#volDown"))

    reset(); open_page()
    keys = pg.eval_on_selector_all("#sources button", "bs => bs.map(b => b.getAttribute('data-src'))")
    t("only the Worker's two sources are offered", keys == ["schedule", "main"], keys)
    calls.clear(); tap('#sources button[data-src="main"]')
    t("first tap on Main arms it and sends nothing", calls == [] and "Tap again" in txt('#sources button[data-src="main"]'), calls)
    tap('#sources button[data-src="main"]')
    t("second tap sends dj_source main and Main shows as playing", calls == [{"kind": "dj_source", "source": "main"}] and "on" in pg.get_attribute('#sources button[data-src="main"]', "class"), calls)
    calls.clear(); tap('#sources button[data-src="main"]'); tap('#sources button[data-src="main"]')
    t("the source already playing is not re-sent", calls == [], calls)

    reset(online=False, state="paused", track=None); open_page()
    t("offline: red banner with what to do", "show bad" in pg.get_attribute("#banner", "class") and "offline" in txt("#banner").lower() and "Soundtrack" in txt("#banner"))
    t("offline: play, skip, volume and sources are disabled",
      pg.is_disabled("#btnPlay") and pg.is_disabled("#btnSkip") and pg.is_disabled("#volUp") and pg.is_disabled('#sources button[data-src="main"]'))

    reset(source="opening"); open_page()
    t("Opening by hand: amber banner that it loops", "show warn" in pg.get_attribute("#banner", "class") and "4 songs" in txt("#banner"))

    reset(); open_page(); fail_next["on"] = True; tap("#btnSkip")
    t("a Worker error is a red banner, not silence", "show bad" in pg.get_attribute("#banner", "class") and "did not reach" in txt("#banner"), txt("#banner"))

    for w in (390, 820):
        pg.set_viewport_size({"width": w, "height": 900}); reset(); open_page()
        sx = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        t(f"no horizontal scroll at {w}px", sx <= 1, f"{sx}px")
    big = pg.evaluate("Math.min(...['btnPlay','btnSkip','volUp','volDown'].map(i => document.getElementById(i).getBoundingClientRect().height))")
    t("every control is a big tap target (≥ 80px)", big >= 80, big)
    t("no page errors", not errs, errs)
    b.close()

if bad:
    print(f"✗ {bad} check(s) failed"); sys.exit(1)
print("✓ /dj/: now playing, play/pause/skip, volume, a two-tap source switch, offline + Opening + error banners, phone and tablet")
