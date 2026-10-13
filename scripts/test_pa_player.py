#!/usr/bin/env python3
"""Headless proof of docs/pa/ — the event speaker page.  (13.10.2026)

Runs the real page in Chromium against a local copy of docs/pa/ and asserts:
  1. it loads: 9 clip rows, Start enabled, no red bar
  2. Start with music loaded → the first slot is an announcement (welcome, EN),
     then a song from the phone plays
  3. after `every_songs` song endings the next announcement plays, in the OTHER language
  4. a manual "Announce now" button plays that clip and the song resumes
  5. tamper: announcements.json changed without a rebuild → the red OUT OF DATE bar
  6. scripts/build_pa_announcements.py check fails on that tampered copy, too

usage: python3 scripts/test_pa_player.py     (needs: pip install playwright; ffmpeg)
"""
import functools, http.server, json, pathlib, shutil, subprocess, sys, tempfile, threading, time
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAIL = []


def ok(cond, what):
    print(("✓ " if cond else "❌ ") + what)
    if not cond:
        FAIL.append(what)


def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def song(path, secs):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"sine=frequency=440:duration={secs}", str(path)], check=True)


def wait(page, js, secs=20):
    t = time.time()
    while time.time() - t < secs:
        if page.evaluate(js):
            return True
        time.sleep(0.2)
    return False


def main():
    tmp = pathlib.Path(tempfile.mkdtemp())
    site = tmp / "site"
    shutil.copytree(ROOT / "docs/pa", site / "pa")
    songs = [tmp / f"song{i}.mp3" for i in range(3)]
    for s in songs:
        song(s, 60)
    srv = serve(site)
    base = f"http://127.0.0.1:{srv.server_address[1]}/pa/"
    every = json.loads((site / "pa/announcements.json").read_text())["rotation"]["every_songs"]

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        page = b.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base)
        ok(wait(page, "!document.getElementById('go').disabled"), "page loads and Start is enabled")
        ok(page.locator("#clips .t").count() == 9, "9 announcement rows")
        ok(not page.locator("#err.on").count(), "no red bar on a fresh build")

        page.set_input_files("#pick", [str(s) for s in songs])
        ok("3 songs" in page.inner_text("#musicInfo"), "3 songs loaded from the phone")

        page.click("#go")
        st = page.evaluate("__pa.state()")
        ok(st["running"] and st["voiceSrc"] and "welcome_en" in st["voiceSrc"], f"Start opens with the welcome, in English ({st['voiceSrc']})")
        ok(wait(page, "!!__pa.state().musicSrc && !__pa.state().busy", 30), "after the announcement a song plays")

        first_voice = page.evaluate("__pa.state().voiceSrc")
        for i in range(every - 1):
            page.evaluate("__pa.end()")
            time.sleep(0.3)
        ok(page.evaluate("__pa.state().voiceSrc") == first_voice, f"no announcement before song {every}")
        page.evaluate("__pa.end()")
        ok(wait(page, "__pa.state().busy", 5), f"song {every} ended → an announcement starts")
        v = page.evaluate("__pa.state().voiceSrc")
        ok("deal_75_es" in v, f"the second slot is the next clip, in Spanish ({v})")
        ok(wait(page, "!__pa.state().busy", 30), "the announcement finishes and music goes on")

        page.locator("#clips button").nth(7).click()   # share_reel ES (rows: 2 buttons each, 0-based → row 3)
        ok(wait(page, "(__pa.state().voiceSrc||'').indexOf('share_reel_es')>=0", 5), "the manual button plays that clip")
        ok(wait(page, "!__pa.state().busy && !document.getElementById('music').paused", 40), "the song resumes after the manual clip")
        ok(not errors, "no JavaScript errors " + ("; ".join(errors) if errors else ""))
        ok(not page.locator("#err.on").count(), "still no red bar after playing")

        # tamper: text changed, audio not rebuilt
        src = site / "pa/announcements.json"
        src.write_text(src.read_text().replace("Hey beauties", "Hi beauties"))
        page.goto(base)
        ok(wait(page, "document.getElementById('err').classList.contains('on')", 10)
           and "OUT OF DATE" in page.inner_text("#err"), "changed text without rebuild → red OUT OF DATE bar")
        b.close()

    # the build script's own check agrees
    shutil.copytree(ROOT / "scripts", tmp / "scripts")
    (tmp / "docs").mkdir()
    shutil.move(str(site / "pa"), tmp / "docs/pa")
    r = subprocess.run([sys.executable, str(tmp / "scripts/build_pa_announcements.py"), "check"], capture_output=True, text=True)
    ok(r.returncode != 0 and "run build" in r.stdout, "build_pa_announcements.py check fails on the tampered source")
    srv.shutdown()

    print(f"\n{'✓ all passed' if not FAIL else f'❌ {len(FAIL)} failed'}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
