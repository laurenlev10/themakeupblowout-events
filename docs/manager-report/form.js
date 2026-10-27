/* MbsReportForm — the Event Manager Report's fields, in one place.
 *
 * The definition is ./form.json; this file is the only code that knows what a field
 * TYPE looks like on screen, how its answer is read back, restored from a draft and
 * printed. Loaded by BOTH copies of the form:
 *   · events.themakeupblowout.com/manager-report/        (public, the one managers open)
 *   · dashboard.themakeupblowout.com/manager-report/     (Lauren's, behind Access — loads
 *     this script and form.json from the events host)
 * Before 27.10.2026 each page carried its own SECTIONS literal and the sync a third
 * list; they drifted (guardrail `the-manager-form-is-defined-once`).
 *
 * Types: select · yesno · number · text · multicheck (tick every option that applies;
 * the answer is an array of the ticked option strings, in option order).
 *
 * A submitted report carries snapshot() as `form`, so the report describes its own
 * questions: the read-only view and manager_report_sync.py read THAT, never today's
 * form — a field renamed or removed later cannot change what an old report said.
 */
(function (root) {
  "use strict";
  var FORM = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c];
    });
  }

  /* Resolve option-list names ("BOX_ONHAND") to arrays. A field whose list does not
     exist is a broken definition — say so, do not render an empty select. */
  function normalize(def) {
    if (!def || !Array.isArray(def.sections) || !def.sections.length) throw new Error("form.json has no sections");
    var lists = def.lists || {};
    var seen = {};
    def.sections.forEach(function (sec) {
      (sec.fields || []).forEach(function (f) {
        if (!f.key) throw new Error("a field in '" + sec.title + "' has no key");
        if (seen[f.key]) throw new Error("field key '" + f.key + "' is defined twice");
        seen[f.key] = 1;
        if (typeof f.options === "string") {
          if (!Array.isArray(lists[f.options])) throw new Error("field '" + f.key + "' uses unknown list '" + f.options + "'");
          f.options = lists[f.options].slice();
        }
        if ((f.type === "select" || f.type === "multicheck") && !(Array.isArray(f.options) && f.options.length))
          throw new Error("field '" + f.key + "' (" + f.type + ") has no options");
      });
    });
    return def;
  }

  async function load(url) {
    var r = await fetch(url + (url.indexOf("?") < 0 ? "?" : "&") + "_=" + Date.now(), { cache: "no-store" });
    if (!r.ok) throw new Error("form.json HTTP " + r.status);
    FORM = normalize(await r.json());
    return FORM;
  }

  function sections() { return FORM ? FORM.sections : []; }
  function fieldByKey(k) {
    var s = sections();
    for (var i = 0; i < s.length; i++) for (var j = 0; j < s[i].fields.length; j++) if (s[i].fields[j].key === k) return s[i].fields[j];
    return null;
  }

  /* The questions this report answered — stored with the report. */
  function snapshot() {
    return {
      low_levels: (FORM && FORM.low_levels) || [],
      sections: sections().map(function (sec) {
        return {
          title: sec.title,
          fields: sec.fields.map(function (f) {
            var o = { key: f.key, label: f.label, short: f.short || f.label, type: f.type, supplier: f.supplier || "" };
            if (f.type === "multicheck") o.options = f.options.slice();
            return o;
          })
        };
      })
    };
  }

  function fieldHtml(f) {
    var id = "f-" + f.key;
    var h = '<div class="field"><label class="lab" for="' + id + '">' + esc(f.label) +
            (f.hint ? ' <span class="hint">' + esc(f.hint) + '</span>' : '') + '</label>';
    if (f.type === "select") {
      h += '<select id="' + id + '"><option value="">— Choose —</option>';
      f.options.forEach(function (o) { h += '<option value="' + esc(o) + '">' + esc(o) + '</option>'; });
      h += '</select>';
    } else if (f.type === "yesno") {
      h += '<div class="yn" id="' + id + '" data-val="">' +
           '<button type="button" data-yn="yes">✅ Yes — need it</button>' +
           '<button type="button" data-yn="no">— No</button></div>';
    } else if (f.type === "multicheck") {
      h += '<div class="mc" id="' + id + '" data-mc="1">';
      f.options.forEach(function (o) {
        h += '<label class="mc-opt"><input type="checkbox" value="' + esc(o) + '"><span>' + esc(o) + '</span></label>';
      });
      h += '</div>';
    } else if (f.type === "number") {
      h += '<input type="number" inputmode="numeric" id="' + id + '" placeholder="0">';
    } else {
      h += '<input type="text" id="' + id + '" placeholder="">';
    }
    return h + '</div>';
  }

  function read(f) {
    var el = document.getElementById("f-" + f.key);
    if (!el) return undefined;
    if (f.type === "yesno") return el.getAttribute("data-val") || "";
    if (f.type === "multicheck") {
      var out = [];
      Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) { if (c.checked) out.push(c.value); });
      return out;
    }
    return (el.value || "").trim();
  }

  function apply(f, v) {
    var el = document.getElementById("f-" + f.key);
    if (!el || v === undefined || v === null || v === "") return;
    if (f.type === "yesno") {
      el.setAttribute("data-val", v);
      Array.prototype.forEach.call(el.querySelectorAll("button"), function (x) { x.classList.remove("on-yes", "on-no"); });
      var b = el.querySelector('button[data-yn="' + v + '"]');
      if (b) b.classList.add(v === "yes" ? "on-yes" : "on-no");
    } else if (f.type === "multicheck") {
      var want = Array.isArray(v) ? v.map(String) : String(v).split(/[\s,]+/).filter(Boolean);
      Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) { c.checked = want.indexOf(c.value) >= 0; });
    } else {
      el.value = v;
    }
  }

  /* How an answer reads in the text copy and the read-only view. "" = not answered. */
  function display(f, v) {
    if (f && f.type === "yesno") return v === "yes" ? "✅ Yes — need it" : (v === "no" ? "No" : "");
    if (Array.isArray(v)) return v.length ? (f && f.type === "multicheck" ? "Missing: " : "") + v.join(", ") : "None missing";
    return v == null ? "" : String(v);
  }

  /* yes/no buttons are wired once per render, for every .yn inside `scope`. */
  function wire(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll(".yn"), function (yn) {
      yn.addEventListener("click", function (e) {
        var b = e.target.closest("button[data-yn]"); if (!b) return;
        var v = b.getAttribute("data-yn");
        yn.setAttribute("data-val", v);
        Array.prototype.forEach.call(yn.querySelectorAll("button"), function (x) { x.classList.remove("on-yes", "on-no"); });
        b.classList.add(v === "yes" ? "on-yes" : "on-no");
      });
    });
  }

  var CSS = ".mc{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}" +
    ".mc-opt{display:flex;align-items:center;justify-content:center;gap:5px;border:1.5px solid #e5e7eb;border-radius:10px;" +
    "padding:10px 4px;font-size:15px;font-weight:800;cursor:pointer;background:#fff;user-select:none}" +
    ".mc-opt input{width:18px;height:18px;margin:0;accent-color:#be185d}" +
    ".mc-opt:has(input:checked){background:#fce7f3;border-color:#be185d;color:#9d174d}";
  function injectCss() {
    if (document.getElementById("mbs-report-form-css")) return;
    var s = document.createElement("style"); s.id = "mbs-report-form-css"; s.textContent = CSS;
    document.head.appendChild(s);
  }

  root.MbsReportForm = {
    load: load, sections: sections, fieldByKey: fieldByKey, snapshot: snapshot,
    fieldHtml: fieldHtml, read: read, apply: apply, display: display, wire: wire,
    injectCss: injectCss, normalize: normalize
  };
})(typeof window !== "undefined" ? window : globalThis);
