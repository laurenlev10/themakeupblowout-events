#!/usr/bin/env python3
"""Headless proof of docs/pa/ — the event speaker page.  (13.10.2026)

Runs the real page in Chromium against a local copy of docs/pa/ and asserts:
  1. it loads: 9 clip rows, Start enabled, no red bar
  2. Start with music loaded → the first slot is an announcement (welcome — one file,
     English then Spanish over the music bed), then a song from the phone plays
  3. after `every_songs` song endings the NEXT announcement plays (deal_75)
  4. a manual "Announce now" button plays that clip and the song resumes
  5. tamper: announcements.json changed without a rebuild → the red OUT OF DATE bar
  6. scripts/build_pa_announcements.py check fails on that tampered copy, too

usage: python3 scripts/test_pa_player.py     (needs: pip install playwright)
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
    # pure Python, no ffmpeg: the GitHub runner image does not promise one (13.10.2026 —
    # the first CI run failed here while the same test passed in the session).
    import math, struct, wave
    rate = 8000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate)))
                               for i in range(rate * secs)))


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
    songs = [tmp / f"song{i}.wav" for i in range(3)]
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
        ok(st["running"] and st["voiceSrc"] and "audio/welcome.mp3" in st["voiceSrc"], f"Start opens with the welcome ({st['voiceSrc']})")
        ok("English → Español" in page.inner_text("#rotInfo"), "the page says English, then Spanish")
        ok(wait(page, "!!__pa.state().musicSrc && !__pa.state().busy", 30), "after the announcement a song plays")

        first_voice = page.evaluate("__pa.state().voiceSrc")
        for i in range(every - 1):
            page.evaluate("__pa.end()")
            time.sleep(0.3)
        ok(page.evaluate("__pa.state().voiceSrc") == first_voice, f"no announcement before song {every}")
        page.evaluate("__pa.end()")
        ok(wait(page, "__pa.state().busy", 5), f"song {every} ended → an announcement starts")
        v = page.evaluate("__pa.state().voiceSrc")
        ok("audio/deal_75.mp3" in v, f"the second slot is the next clip ({v})")
        ok(wait(page, "!__pa.state().busy", 30), "the announcement finishes and music goes on")

        ok(page.locator("#clips button").count() == 9, "one ▶ EN+ES button per announcement")
        page.locator("#clips button").nth(3).click()   # row 3 = share_reel
        ok(wait(page, "(__pa.state().voiceSrc||'').indexOf('audio/share_reel.mp3')>=0", 5), "the manual button plays that clip")
        ok(wait(page, "!__pa.state().busy && !document.getElementById('music').paused", 40), "the song resumes after the manual clip")
        ok(not errors, "no JavaScript errors " + ("; ".join(errors) if errors else ""))
        ok(not page.locator("#err.on").count(), "still no red bar after playing")

        # `when`: the $5 brush set rotates ONLY Friday before 12:00 (Lauren 13.10.2026)
        for label, iso, expect in (("Fri 10:30", "2026-10-16T10:30:00", True),
                                   ("Fri 12:30", "2026-10-16T12:30:00", False),
                                   ("Sat 11:00", "2026-10-17T11:00:00", False)):
            ctx = b.new_context()
            ctx.add_init_script("""(() => { const T = new Date('%s').getTime(), R = Date;
              class F extends R { constructor(...a){ super(...(a.length ? a : [T])); } static now(){ return T; } }
              window.Date = F; })();""" % iso)
            pg = ctx.new_page(); pg.goto(base)
            wait(pg, "!document.getElementById('go').disabled")
            ids = pg.evaluate("__pa.autoIds()")
            ok(("deal_brush_set" in ids) == expect,
               f"{label}: brush-set deal {'in' if expect else 'NOT in'} the rotation ({len(ids)} clips)")
            ctx.close()

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
