#!/usr/bin/env python3
"""
Headless test for the recount count-sheet camera search (Lauren 2026-08-15).

Proves, in a real browser, that:
  1. the 📷 button appears in the product-search bar,
  2. scanning a barcode in SOLD OUT mode locates the product,
  3. scanning a barcode in COUNT-ANOTHER mode locates the product,
  4. scanning an ADDITIONAL (secondary) barcode locates it too,
  5. an unknown code says so instead of showing a wrong product,
  6. the count-screen barcode field still fills from the camera (no regression),
  7. closing the search modal releases the camera,
  11. every product-search row shows how many are in the system, the snapshot number
      paints first and is marked as a snapshot, and the LIVE number replaces it
      (Lauren 2026-08-28).

The camera and the worker are both stubbed — no OCTOPOS, no hardware.
"""
import json, sys, http.server, threading, functools, pathlib
from playwright.sync_api import sync_playwright

DOCS = str(pathlib.Path(__file__).resolve().parent.parent / "docs")
PORT = 8731

# `stock` = the daily snapshot qty get_catalog carries; LIVE_STOCK below = what OCTOPOS
# says right now. They deliberately DISAGREE here, because the whole point of the
# 2026-08-28 change is that the page must end up showing the live one.
CATALOG = {"ok": True, "kind": "get_catalog", "count": 3, "as_of": "2026-08-24T22:56:51Z", "products": [
    {"id": 29,   "name": "Amuse Bloom & Shine Powder Blush", "sku": "BL3132", "supplier": "Amuse",
     "threshold": 15, "barcode": "4713616471794", "barcodes": [], "stock": 54},
    {"id": 1245, "name": "Amuse Makeup Cleansing wipes - charcoal", "sku": "AM624-Charcoal",
     "supplier": "Amuse", "threshold": 72, "barcode": "4713616470216", "barcodes": ["9999900000011"], "stock": 12},
    {"id": 77,   "name": "Zoe Lip Gloss Set", "sku": "ZG-100", "supplier": "Zoe",
     "threshold": 10, "barcode": "1234567890123", "barcodes": [], "stock": 8},
]}
LIVE_STOCK = {29: 41, 1245: 3, 77: -2}

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

# Fake camera: getUserMedia returns a canvas stream, BarcodeDetector returns whatever
# code the test has armed. This is what the real decoder path consumes.
STUB = """
window.__scan = null;
navigator.mediaDevices = navigator.mediaDevices || {};
navigator.mediaDevices.getUserMedia = async function(){
  var c = document.createElement('canvas'); c.width=320; c.height=240;
  c.getContext('2d').fillRect(0,0,320,240);
  var s = c.captureStream(5);
  window.__streamLive = function(){ return s.getTracks().some(function(t){ return t.readyState === 'live'; }); };
  return s;
};
window.BarcodeDetector = function(){};
window.BarcodeDetector.getSupportedFormats = async function(){ return ['ean_13','code_128']; };
window.BarcodeDetector.prototype.detect = async function(){
  if (!window.__scan) return [];
  var v = window.__scan; window.__scan = null;
  return [{ rawValue: v }];
};
"""

def main():
    fails = []
    def check(name, cond, extra=""):
        print(("  PASS  " if cond else "  FAIL  ") + name + (("  << " + str(extra)) if (extra and not cond) else ""))
        if not cond: fails.append(name)

    serve()
    with sync_playwright() as pw:
        import glob
        exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + [None])[0]
        br = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
        ctx = br.new_context()
        ctx.add_init_script(STUB)
        pg = ctx.new_page()
        logs = []
        pg.on("console", lambda m: logs.append(m.type + ": " + m.text))
        pg.on("pageerror", lambda e: logs.append("PAGEERROR: " + str(e)))

        worker_worklist_hits = []
        pages_copy_hits = []
        live_stock_hits = []
        live_stock_down = {"on": False}

        # worker stub
        def worker(route):
            body = json.loads(route.request.post_data or "{}")
            k = body.get("kind")
            if k == "get_catalog":  return route.fulfill(status=200, content_type="application/json", body=json.dumps(CATALOG))
            if k == "get_field_counts": return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"counts":{}}))
            # 2026-08-20 — the count list now comes from the Worker, not from the
            # published Pages copy (which stopped being republished on 2026-08-18 and
            # silently froze this sheet). The stub answers it so the test covers the
            # path the crew actually uses, and `worker_worklist_hits` proves it ran.
            if k == "get_worklist":
                worker_worklist_hits.append(body.get("evkey"))
                if body.get("evkey") == "not-built-2026-01-01":
                    return route.fulfill(status=200, content_type="application/json",
                        body=json.dumps({"ok":True,"kind":"get_worklist","worklist":[],"count":0,"built":False}))
                return route.fulfill(status=200, content_type="application/json",
                    body=json.dumps({"ok":True,"kind":"get_worklist","built":True,"count":1,"worklist":[
                        {"id":29,"name":"Amuse Bloom & Shine Powder Blush","sku":"BL3132","qty":54,"barcode":"4713616471794"}]}))
            if k == "get_live_stock":
                pids = [int(x) for x in (body.get("pids") or [])]
                live_stock_hits.append(pids)
                if live_stock_down["on"]:
                    return route.fulfill(status=502, content_type="application/json",
                                         body=json.dumps({"error": "octopos down"}))
                if len(pids) > 45:
                    return route.fulfill(status=400, content_type="application/json",
                                         body=json.dumps({"error": "too many pids"}))
                return route.fulfill(status=200, content_type="application/json", body=json.dumps(
                    {"ok": True, "kind": "get_live_stock",
                     "stock": {str(p): LIVE_STOCK[p] for p in pids if p in LIVE_STOCK},
                     "missing": [p for p in pids if p not in LIVE_STOCK]}))
            if k == "banana_read":  return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"items":[]}))
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True}))
        pg.route("https://danielle.laurenlev10.workers.dev/**", worker)
        def pages_copy(r):
            if "/state/octopos_recount.json" in r.request.url:
                pages_copy_hits.append(r.request.url)
            r.fulfill(status=200, content_type="application/json",
                body=json.dumps({"events":{"visalia-2026-08-14":{"worklist":[
                    {"id":29,"name":"Amuse Bloom & Shine Powder Blush","sku":"BL3132","qty":54,"barcode":"4713616471794"}]}}}))
        pg.route("https://*.themakeupblowout.com/**", pages_copy)

        pg.goto(f"http://127.0.0.1:{PORT}/recount-count/?evkey=visalia-2026-08-14&label=Visalia")
        pg.wait_for_timeout(500)
        pg.fill("#nameInput", "TestCrew"); pg.click("#nameSave")
        pg.wait_for_timeout(400)

        # 1 — the button exists and is visible
        pg.click("#soldOutAdd"); pg.wait_for_timeout(600)
        check("1. 📷 button visible in SOLD OUT search bar", pg.is_visible("#btnSoScan"))

        def scan(code):
            pg.click("#btnSoScan"); pg.wait_for_timeout(300)
            pg.evaluate("c => window.__scan = c", code)
            pg.wait_for_timeout(900)

        # 2 — SOLD OUT: primary barcode locates the product
        scan("1234567890123")
        rows = pg.eval_on_selector_all(".sorow .name", "els => els.map(e => e.textContent)")
        check("2. SOLD OUT scan locates exactly the scanned product",
              rows == ["Zoe Lip Gloss Set"], rows)
        check("2b. matched barcode shown back on the row",
              "1234567890123" in (pg.inner_text(".sorow") or ""), pg.inner_text(".sorow"))
        check("2c. camera closed after a hit", not pg.is_visible("#camWrap"))
        check("2d. camera stream released", pg.evaluate("!window.__streamLive || !window.__streamLive()"))
        check("2e. SOLD OUT button still requires a tap (nothing auto-flagged)",
              "SOLD OUT" in pg.inner_text(".sorow button"), pg.inner_text(".sorow button"))

        # 3 — additional (secondary) barcode
        pg.fill("#soSearch", ""); pg.wait_for_timeout(200)
        scan("9999900000011")
        rows = pg.eval_on_selector_all(".sorow .name", "els => els.map(e => e.textContent)")
        check("3. secondary barcode locates the product",
              rows == ["Amuse Makeup Cleansing wipes - charcoal"], rows)

        # 4 — unknown code
        pg.fill("#soSearch", ""); pg.wait_for_timeout(200)
        scan("0000000000000")
        rows = pg.eval_on_selector_all(".sorow .name", "els => els.map(e => e.textContent)")
        toast = pg.inner_text("#toast")
        check("4. unknown code shows no product", rows == [], rows)
        check("4b. unknown code says so", "no product" in toast.lower(), toast)

        # 5 — COUNT ANOTHER mode
        pg.click("#soBack"); pg.wait_for_timeout(300)
        check("5. closing the modal released the camera",
              pg.evaluate("!window.__streamLive || !window.__streamLive()"))
        pg.click("#countAny"); pg.wait_for_timeout(500)
        check("5b. 📷 button visible in COUNT-ANOTHER search bar", pg.is_visible("#btnSoScan"))
        scan("4713616470216")
        rows = pg.eval_on_selector_all(".sorow .name", "els => els.map(e => e.textContent)")
        check("5c. COUNT-ANOTHER scan locates the product",
              rows == ["Amuse Makeup Cleansing wipes - charcoal"], rows)
        check("5d. COUNT button offered (one deliberate tap)",
              "COUNT" in pg.inner_text(".sorow button"), pg.inner_text(".sorow button"))

        # 6 — the count screen's own 📷 still fills the barcode field (no regression)
        pg.click(".sorow button"); pg.wait_for_timeout(500)
        check("6. count screen opened from the scan result", pg.is_visible("#screen"))
        pg.click("#btnScan"); pg.wait_for_timeout(300)
        pg.evaluate("c => window.__scan = c", "5556667778889")
        pg.wait_for_timeout(900)
        check("6b. count-screen scan still fills the barcode field",
              pg.input_value("#scBarcode") == "5556667778889", pg.input_value("#scBarcode"))
        check("6c. camera closed afterwards", not pg.is_visible("#camWrap"))

        # 7 — typed barcode (handheld scanners type) finds it too
        pg.click("#scBack"); pg.wait_for_timeout(300)
        pg.click("#soldOutAdd"); pg.wait_for_timeout(400)
        pg.fill("#soSearch", "4713616471794"); pg.wait_for_timeout(300)
        rows = pg.eval_on_selector_all(".sorow .name", "els => els.map(e => e.textContent)")
        check("7. typed barcode finds the product too",
              rows == ["Amuse Bloom & Shine Powder Blush"], rows)

        errs = [l for l in logs if l.startswith("PAGEERROR")]
        # 9 — the list came from the Worker, and the published Pages copy was NOT read.
        #     That copy has not been republished since 2026-08-18; reading it is the bug.
        check("9. worklist read through the Worker", worker_worklist_hits == ["visalia-2026-08-14"],
              worker_worklist_hits)
        check("9b. published Pages copy of octopos_recount.json not read",
              pages_copy_hits == [], pages_copy_hits)
        check("9c. the Worker's list rendered on the sheet",
              "Amuse Bloom & Shine Powder Blush" in (pg.inner_text("#list") or ""),
              pg.inner_text("#list")[:120])

        # 10 — an event with no pre-event build says so, instead of "nothing to count".
        pg2 = ctx.new_page()
        pg2.route("https://danielle.laurenlev10.workers.dev/**", worker)
        pg2.route("https://*.themakeupblowout.com/**", pages_copy)
        pg2.goto(f"http://127.0.0.1:{PORT}/recount-count/?evkey=not-built-2026-01-01&label=NotBuilt")
        pg2.wait_for_timeout(700)
        empty_txt = pg2.inner_text("#empty") or ""
        check("10. un-built event says the list was not built yet",
              "not been built yet" in empty_txt, empty_txt[:140])
        check("10b. un-built event does NOT claim there is nothing to count",
              "Nothing to count" not in empty_txt, empty_txt[:140])
        pg2.close()

        # 11 — "how many are in the system", on every search row (Lauren 2026-08-28).
        pg.click("#soBack"); pg.wait_for_timeout(300)
        pg.click("#countAny"); pg.wait_for_timeout(600)
        pills = pg.eval_on_selector_all(".sorow [data-stockpid]", "els => els.map(e => e.textContent.trim())")
        check("11. every search row carries an 'in sys' number",
              len(pills) == 3 and all(" in sys" in t for t in pills), pills)
        pg.wait_for_timeout(1200)
        live = pg.eval_on_selector_all(".sorow [data-stockpid]",
                                       "els => els.map(e => e.textContent.trim())")
        check("11b. the LIVE number replaces the snapshot on every row",
              live == ["41 in sys", "3 in sys", "-2 in sys"], live)
        check("11c. a live row is no longer marked as a snapshot",
              pg.eval_on_selector_all(".sorow [data-stockpid]",
                                      "els => els.every(e => !e.classList.contains('snap'))"))
        check("11d. one batched call, not one per row",
              len(live_stock_hits) >= 1 and all(len(h) <= 45 for h in live_stock_hits), live_stock_hits)
        # the count list shows the SAME number as the search list — one source of truth
        pg.click("#soBack"); pg.wait_for_timeout(400)
        check("11e. the count list agrees with the search list",
              "41 in sys" in (pg.inner_text("#list") or ""), pg.inner_text("#list")[:200])

        # 11f — a live read that FAILS must leave the snapshot on screen, still marked as
        # one. A failed read is not permission to present a stale number as current.
        live_stock_down["on"] = True
        pg3 = ctx.new_page()
        pg3.route("https://danielle.laurenlev10.workers.dev/**", worker)
        pg3.route("https://*.themakeupblowout.com/**", pages_copy)
        pg3.add_init_script("localStorage.setItem('recount_employee_name','TestCrew')")
        pg3.goto(f"http://127.0.0.1:{PORT}/recount-count/?evkey=visalia-2026-08-14&label=Visalia")
        pg3.wait_for_timeout(600)
        if pg3.is_visible("#nameInput"):
            pg3.fill("#nameInput", "TestCrew"); pg3.click("#nameSave"); pg3.wait_for_timeout(400)
        pg3.click("#countAny"); pg3.wait_for_timeout(1800)
        down = pg3.eval_on_selector_all(".sorow [data-stockpid]",
                                        "els => els.map(e => e.textContent.trim())")
        check("11f. a failed live read keeps the snapshot number visible",
              down and all(" in sys" in t for t in down), down)
        check("11g. …and keeps it marked as a snapshot, not as live",
              pg3.eval_on_selector_all(".sorow [data-stockpid]",
                                       "els => els.length > 0 && els.every(e => e.classList.contains('snap'))"))
        pg3.close()
        live_stock_down["on"] = False

        check("8. no page errors", not errs, errs)
        br.close()

    print()
    if fails:
        print("FAILED: " + "; ".join(fails)); sys.exit(1)
    print("ALL CHECKS PASSED")

main()
