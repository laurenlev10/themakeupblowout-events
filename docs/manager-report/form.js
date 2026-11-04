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
 * the answer is an array of the ticked option strings, in option order) · crew (04.11.2026).
 *
 * `crew` — tick people of THIS event's team (Lauren 04.11.2026: "who slept alone in a room").
 * Its options are not in form.json: the page asks the Worker (kind get_event_crew, after the
 * manager types her name) and hands the answer to setCrew(). The answer is an array of roster
 * slugs; a name typed into the fallback box (the list did not load) is "name:<typed>". The
 * snapshot carries the crew that was shown as `options` [{m,name,lead}] and anyone ticked from
 * "someone else" as `extra`, so a report keeps who was there even after the schedule changes.
 * The rule that reads it is docs/_assets/solo-rooms.js (lauren-agent-hub-data). A crew field
 * never becomes an ordering line (manager_report_sync.py skips the type).
 *
 * `required: true` (27.10.2026, Lauren — the Simply Bella shades have no per-shade barcode,
 * so the manager's weekly check is the ONLY source): the field gets a
 * "✓ Checked — nothing missing" button whose answer is form.json `none_value`, and a final
 * report will not submit while the field is empty. Empty means "she did not check", never
 * "nothing is missing" — the two used to print the same.
 *
 * A submitted report carries snapshot() as `form`, so the report describes its own
 * questions: the read-only view and manager_report_sync.py read THAT, never today's
 * form — a field renamed or removed later cannot change what an old report said.
 */
(function (root) {
  "use strict";
  var FORM = null;
  /* the crew a `crew` field ticks from — set by the page through setCrew() */
  var CREW = { status: "wait", crew: [], others: [], msg: "" };
  var CREW_WANT = [];      // slugs a draft ticked before the list arrived
  function NONE() { return (FORM && FORM.none_value) || "nothing-missing"; }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c];
    });
  }

  /* Resolve option-list names ("BOX_ONHAND") to arrays. A field whose list does not
     exist is a broken definition — say so, do not render an empty select. */
  function normalize(def) {
    if (!def || !Array.isArray(def.sections) || !def.sections.length) throw new Error("form.json has no sections");
    if (!def.none_value) throw new Error("form.json has no none_value");
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
        if (f.type === "crew" && f.options) throw new Error("field '" + f.key + "' (crew) takes its options from the schedule, not form.json");
        if (f.required && f.type !== "multicheck" && f.type !== "text" && f.type !== "crew")
          throw new Error("field '" + f.key + "': required is supported on multicheck, text and crew fields");
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
      none_value: NONE(),
      sections: sections().map(function (sec) {
        return {
          title: sec.title,
          fields: sec.fields.map(function (f) {
            var o = { key: f.key, label: f.label, short: f.short || f.label, type: f.type, supplier: f.supplier || "" };
            if (f.type === "multicheck") o.options = f.options.slice();
            if (f.type === "crew") {
              o.options = CREW.status === "ok" ? CREW.crew.map(function (c) { return { m: c.m, name: c.name, lead: !!c.lead }; }) : [];
              var ticked = (typeof document !== "undefined") ? read(f) : [], extra = [];
              if (Array.isArray(ticked)) CREW.others.forEach(function (c) { if (ticked.indexOf(c.m) >= 0) extra.push({ m: c.m, name: c.name }); });
              o.extra = extra;
              if (f.none_label) o.none_label = f.none_label;
            }
            if (f.required) o.required = true;
            if (f.product_id) o.product_id = Number(f.product_id);   // the OCTOPOS product the ask is about (2.11.2026)
            return o;
          })
        };
      })
    };
  }

  function fieldHtml(f) {
    var id = "f-" + f.key;
    var h = '<div class="field' + (f.required ? ' req-field' : '') + '" id="w-' + f.key + '"><label class="lab" for="' + id + '">' + esc(f.label) +
            (f.required ? ' <span class="req">*</span>' : '') +
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
    } else if (f.type === "crew") {
      h += '<div class="crew" id="' + id + '" data-crew="1">' + crewInner(f) + '</div>';
    } else if (f.type === "number") {
      h += '<input type="number" inputmode="numeric" id="' + id + '" placeholder="0">';
    } else {
      h += '<input type="text" id="' + id + '" placeholder="">';
    }
    if (f.required) {
      var nl = f.none_label || "✓ Checked — nothing missing";
      h += '<button type="button" class="none-btn" data-none="' + esc(f.key) + '" aria-pressed="false">' + esc(nl) + '</button>' +
           '<div class="req-msg">' + (f.type === "crew" ? "Answer this: tick who slept alone, or tap “" + esc(nl.replace(/^✓\s*/, "")) + "”."
                                                         : "Answer this: tick / type what is missing, or tap “Checked — nothing missing”.") + '</div>';
    }
    return h + '</div>';
  }

  function crewBox(c, cls) {
    return '<label class="mc-opt crew-opt' + (cls || "") + '"><input type="checkbox" value="' + esc(c.m) + '"><span>' +
           esc(c.name) + (c.lead ? ' 👑' : '') + '</span></label>';
  }
  function crewInner(f) {
    if (CREW.status === "wait")
      return '<div class="crew-msg">👆 Type your name at the top — this weekend\'s team loads from the schedule.</div>';
    if (CREW.status === "err")
      return '<div class="crew-msg warn">⚠️ The team list did not load (' + esc(CREW.msg) + '). Type the names of who slept alone:</div>' +
             '<input type="text" class="crew-typed" placeholder="e.g. Razi, Goni">';
    var h = '<div class="mc crew-grid">' + CREW.crew.map(function (c) { return crewBox(c); }).join("") + '</div>';
    if (CREW.others.length)
      h += '<details class="crew-more"><summary>Someone else worked this weekend?</summary><div class="mc crew-grid">' +
           CREW.others.map(function (c) { return crewBox(c, " other"); }).join("") + '</div></details>';
    return h;
  }
  /* The page hands the crew in: {crew, others} from the Worker, or {error} when it could not.
     Every crew field is redrawn with what was ticked / typed kept. */
  function setCrew(x) {
    var keep = {};
    sections().forEach(function (sec) { sec.fields.forEach(function (f) { if (f.type === "crew") keep[f.key] = read(f); }); });
    if (x && x.error) CREW = { status: "err", crew: [], others: [], msg: String(x.error) };
    else if (x && Array.isArray(x.crew)) CREW = { status: "ok", crew: x.crew, others: x.others || [], msg: "" };
    else CREW = { status: "wait", crew: [], others: [], msg: "" };
    sections().forEach(function (sec) {
      sec.fields.forEach(function (f) {
        if (f.type !== "crew") return;
        var el = typeof document !== "undefined" && document.getElementById("f-" + f.key);
        if (!el) return;
        el.innerHTML = crewInner(f);
        wireCrew(f, el);
        var v = keep[f.key];
        if (Array.isArray(v) && v.length) apply(f, v);
        else if (CREW_WANT.length) apply(f, CREW_WANT);
      });
    });
  }
  function crewState() { return CREW.status; }
  function wireCrew(f, el) {
    var clear = function () {
      var answered = !!el.querySelector("input:checked") || !!((el.querySelector(".crew-typed") || {}).value || "").trim();
      if (answered) { var b = noneBtn(f); if (b) { b.classList.remove("on"); b.setAttribute("aria-pressed", "false"); }
                      var w = document.getElementById("w-" + f.key); if (w) w.classList.remove("req-miss"); }
    };
    el.addEventListener("change", clear); el.addEventListener("input", clear);
  }

  function noneBtn(f) { return document.querySelector('.none-btn[data-none="' + f.key + '"]'); }
  function setNone(f, on) {
    var b = noneBtn(f); if (!b) return;
    b.classList.toggle("on", !!on); b.setAttribute("aria-pressed", on ? "true" : "false");
    if (on) {
      var el = document.getElementById("f-" + f.key);
      if (el && (f.type === "multicheck" || f.type === "crew")) {
        Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) { c.checked = false; });
        var ty = el.querySelector(".crew-typed"); if (ty) ty.value = "";
        CREW_WANT = [];
      }
      else if (el) el.value = "";
    }
  }
  function read(f) {
    var el = typeof document !== "undefined" && document.getElementById("f-" + f.key);
    if (!el) return undefined;
    var nb = noneBtn(f);
    if (nb && nb.classList.contains("on")) return NONE();
    if (f.type === "yesno") return el.getAttribute("data-val") || "";
    if (f.type === "multicheck" || f.type === "crew") {
      var out = [];
      Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) { if (c.checked && out.indexOf(c.value) < 0) out.push(c.value); });
      if (f.type === "crew") {
        var ty = el.querySelector(".crew-typed");
        if (ty) String(ty.value || "").split(/[,\n]+/).map(function (x) { return x.trim(); }).filter(Boolean)
                  .forEach(function (n) { out.push("name:" + n); });
        // ticked in a draft before the list loaded — still the answer until the list arrives
        if (CREW.status !== "ok") CREW_WANT.forEach(function (x) { if (out.indexOf(x) < 0 && x.indexOf("name:") !== 0) out.push(x); });
      }
      return out;
    }
    return (el.value || "").trim();
  }

  function apply(f, v) {
    var el = document.getElementById("f-" + f.key);
    if (!el || v === undefined || v === null || v === "") return;
    if (v === NONE()) { setNone(f, true); return; }
    if (f.type === "yesno") {
      el.setAttribute("data-val", v);
      Array.prototype.forEach.call(el.querySelectorAll("button"), function (x) { x.classList.remove("on-yes", "on-no"); });
      var b = el.querySelector('button[data-yn="' + v + '"]');
      if (b) b.classList.add(v === "yes" ? "on-yes" : "on-no");
    } else if (f.type === "multicheck") {
      var want = Array.isArray(v) ? v.map(String) : String(v).split(/[\s,]+/).filter(Boolean);
      Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) { c.checked = want.indexOf(c.value) >= 0; });
    } else if (f.type === "crew") {
      var wc = (Array.isArray(v) ? v : [v]).map(String);
      var shown = {};
      Array.prototype.forEach.call(el.querySelectorAll("input[type=checkbox]"), function (c) {
        c.checked = wc.indexOf(c.value) >= 0; if (c.checked) { shown[c.value] = 1; var d = c.closest("details"); if (d) d.open = true; }
      });
      var typed = wc.filter(function (x) { return x.indexOf("name:") === 0; }).map(function (x) { return x.slice(5); });
      CREW_WANT = wc.filter(function (x) { return x.indexOf("name:") !== 0 && !shown[x]; });
      var ty = el.querySelector(".crew-typed");
      if (ty) ty.value = typed.concat(CREW.status === "err" ? CREW_WANT : []).join(", ");
    } else {
      el.value = v;
    }
  }

  /* How an answer reads in the text copy and the read-only view. "" = not answered. */
  function display(f, v, none) {
    if (v === (none || NONE())) return (f && f.none_label) || "✓ Checked — nothing missing";
    if (f && f.type === "crew") {
      if (!Array.isArray(v) || !v.length) return "";
      var nm = {};
      (f.options || []).concat(f.extra || []).concat(CREW.crew).concat(CREW.others)
        .forEach(function (o) { if (o && o.m) nm[o.m] = o.name; });
      return "Alone: " + v.map(function (x) { x = String(x); return x.indexOf("name:") === 0 ? x.slice(5) : (nm[x] || x); }).join(", ");
    }
    if (f && f.type === "yesno") return v === "yes" ? "✅ Yes — need it" : (v === "no" ? "No" : "");
    if (Array.isArray(v)) return v.length ? (f && f.type === "multicheck" ? "Missing: " : "") + v.join(", ") : "";
    return v == null ? "" : String(v);
  }

  /* Required fields with no answer — [] when the report may be submitted. */
  function unanswered() {
    var out = [];
    sections().forEach(function (sec) {
      sec.fields.forEach(function (f) {
        if (!f.required) return;
        var v = read(f);
        var empty = v === undefined || v === "" || (Array.isArray(v) && !v.length);
        var w = document.getElementById("w-" + f.key);
        if (w) w.classList.toggle("req-miss", empty);
        if (empty) out.push(f);
      });
    });
    return out;
  }

  /* yes/no buttons are wired once per render, for every .yn inside `scope`. */
  function wire(scope) {
    var root = scope || document;
    Array.prototype.forEach.call(root.querySelectorAll(".none-btn"), function (b) {
      b.addEventListener("click", function () {
        var f = fieldByKey(b.getAttribute("data-none")); if (!f) return;
        setNone(f, !b.classList.contains("on"));
        var w = document.getElementById("w-" + f.key); if (w) w.classList.remove("req-miss");
      });
    });
    sections().forEach(function (sec) {
      sec.fields.forEach(function (f) {
        if (!f.required) return;
        var el = document.getElementById("f-" + f.key); if (!el) return;
        if (f.type === "crew") { wireCrew(f, el); return; }
        var clear = function () {
          var answered = f.type === "multicheck" ? !!el.querySelector("input:checked") : !!(el.value || "").trim();
          if (answered) { var b = noneBtn(f); if (b) { b.classList.remove("on"); b.setAttribute("aria-pressed", "false"); }
                          var w = document.getElementById("w-" + f.key); if (w) w.classList.remove("req-miss"); }
        };
        el.addEventListener("change", clear); el.addEventListener("input", clear);
      });
    });
    Array.prototype.forEach.call(root.querySelectorAll(".yn"), function (yn) {
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
    ".mc-opt:has(input:checked){background:#fce7f3;border-color:#be185d;color:#9d174d}" +
    ".none-btn{margin-top:8px;width:100%;font:inherit;font-size:14px;font-weight:800;padding:10px;border-radius:10px;" +
    "border:1.5px dashed #9ca3af;background:#fff;color:#4b5563;cursor:pointer}" +
    ".none-btn.on{border-style:solid;border-color:#15803d;background:#dcfce7;color:#14532d}" +
    ".req-msg{display:none;margin-top:6px;font-size:12.5px;font-weight:700;color:#b91c1c}" +
    ".crew-grid{grid-template-columns:repeat(3,1fr)}.crew-opt{font-size:14px}.crew-opt.other{font-weight:600}" +
    ".crew-msg{font-size:13.5px;color:#4b5563;padding:6px 2px}.crew-msg.warn{color:#9a3412;font-weight:700}" +
    ".crew-typed{margin-top:6px}.crew-more{margin-top:8px;font-size:13px}.crew-more summary{cursor:pointer;color:#6b7280;font-weight:700;padding:4px 0}" +
    ".req-miss{background:#fef2f2;border-radius:10px;box-shadow:0 0 0 2px #f87171}.req-miss .req-msg{display:block}";
  function injectCss() {
    if (document.getElementById("mbs-report-form-css")) return;
    var s = document.createElement("style"); s.id = "mbs-report-form-css"; s.textContent = CSS;
    document.head.appendChild(s);
  }

  root.MbsReportForm = {
    load: load, sections: sections, fieldByKey: fieldByKey, snapshot: snapshot,
    fieldHtml: fieldHtml, read: read, apply: apply, display: display, wire: wire, unanswered: unanswered,
    injectCss: injectCss, normalize: normalize, setCrew: setCrew, crewState: crewState
  };
})(typeof window !== "undefined" ? window : globalThis);
