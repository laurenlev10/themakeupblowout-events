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
  7. closing the search modal releases the camera.

The camera and the worker are both stubbed — no OCTOPOS, no hardware.
"""
import json, sys, http.server, threading, functools, pathlib
from playwright.sync_api import sync_playwright

DOCS = str(pathlib.Path(__file__).resolve().parent.parent / "docs")
PORT = 8731

CATALOG = {"ok": True, "kind": "get_catalog", "count": 3, "products": [
    {"id": 29,   "name": "Amuse Bloom & Shine Powder Blush", "sku": "BL3132", "supplier": "Amuse",
     "threshold": 15, "barcode": "4713616471794", "barcodes": []},
    {"id": 1245, "name": "Amuse Makeup Cleansing wipes - charcoal", "sku": "AM624-Charcoal",
     "supplier": "Amuse", "threshold": 72, "barcode": "4713616470216", "barcodes": ["9999900000011"]},
    {"id": 77,   "name": "Zoe Lip Gloss Set", "sku": "ZG-100", "supplier": "Zoe",
     "threshold": 10, "barcode": "1234567890123", "barcodes": []},
]}

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

        # worker stub
        def worker(route):
            body = json.loads(route.request.post_data or "{}")
            k = body.get("kind")
            if k == "get_catalog":  return route.fulfill(status=200, content_type="application/json", body=json.dumps(CATALOG))
            if k == "get_field_counts": return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"counts":{}}))
            if k == "banana_read":  return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"items":[]}))
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True}))
        pg.route("https://danielle.laurenlev10.workers.dev/**", worker)
        pg.route("https://*.themakeupblowout.com/**", lambda r: r.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"events":{"visalia-2026-08-14":{"worklist":[
                {"id":29,"name":"Amuse Bloom & Shine Powder Blush","sku":"BL3132","qty":54,"barcode":"4713616471794"}]}}})))

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
        check("8. no page errors", not errs, errs)
        br.close()

    print()
    if fails:
        print("FAILED: " + "; ".join(fails)); sys.exit(1)
    print("ALL CHECKS PASSED")

main()
