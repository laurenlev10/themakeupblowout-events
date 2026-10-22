#!/usr/bin/env node
/**
 * האם דף ה-callback שולח את לורן למקום שמסיים את העבודה.
 *
 * 🛑 עד 14.09.2026 הדף אמר על כל קוד: "תעתיקי ותשלחי לצ'אט של Claude". זה ממסר
 * דרך בן אדם וצ'אט פתוח, על קוד שחי עשר דקות — כלומר אישור שנעשה ברגע הלא-נכון
 * פשוט מת, והמשימה נדחית בחודש. עכשיו, כשה-state מזהה את המשימה, הדף מקשר ישר
 * לריצה שמסיימת אותה. הבדיקה מרנדרת את הקובץ האמיתי ובודקת את שלושת המסלולים:
 * משימה מוכרת · state לא מוכר · אישור שנדחה.
 *
 * הבדיקה קוראת רק את #next-steps-block ו-#lead, לא את ה-innerHTML של body —
 * שם יושב גם מקור ה-<script>, וכל טענה נגדו הייתה מאמתת את עצמה מול הקוד
 * במקום מול מה שלורן רואה.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = path.join(HERE, "..", "docs", "oauth", "callback", "index.html");
const html = fs.readFileSync(PAGE, "utf8");

let JSDOM;
try {
  ({ JSDOM } = await import("jsdom"));
} catch {
  console.log("jsdom is not installed here — run `npm install jsdom` first");
  process.exit(2);
}

let fails = 0;
const check = (name, cond, detail = "") => {
  console.log((cond ? "✓ " : "✗ ") + name + (detail ? "   " + detail : ""));
  if (!cond) fails++;
};

function shown(search) {
  const dom = new JSDOM(html, {
    url: "https://events.themakeupblowout.com/oauth/callback" + search,
    runScripts: "dangerously",
  });
  const d = dom.window.document;
  const grab = (id) => (d.getElementById(id) || {}).innerHTML || "";
  const ar = d.getElementById("auto-run");
  const out = {
    autoRun: ar ? ar.getAttribute("href") : null,
    next: grab("next-steps-block"),
    lead: (d.getElementById("lead") || {}).textContent || "",
    fields: grab("fields"),
    status: (d.getElementById("status-pill") || {}).textContent || "",
  };
  dom.window.close();                       // before the forward timer fires — we read where it WOULD go
  return out;
}

const ads = shown("?auth_code=ABC123&state=ads_read_2026");
check("a known job links straight to the run that finishes it",
      ads.next.includes("tiktok-ads-read-auth.yml"));
check("and it stops routing her through a chat",
      !ads.next.includes("לצ'אט"));
check("the code is still there to copy", ads.fields.includes("ABC123"));

const manage = shown("?auth_code=MNG456&state=ads_manage_2026");
check("the manage-token state routes to the same run and says to pick target=manage",
      manage.next.includes("tiktok-ads-read-auth.yml") && manage.next.includes("manage"));

// 🛑 22.10.2026 — approved on 20.10, nothing ran: the page only linked to the Actions page. A known
// job now FORWARDS to the Worker that dispatches the run server-side (behind Access, GH_PAT there).
const AUTO = "https://dashboard.themakeupblowout.com/api/octopos/tiktok/callback?";
check("a known job forwards to the Worker that starts the run, carrying the code and the state",
      manage.autoRun === AUTO + "auth_code=MNG456&state=ads_manage_2026", String(manage.autoRun));
check("the read job forwards too", ads.autoRun === AUTO + "auth_code=ABC123&state=ads_read_2026", String(ads.autoRun));
check("the manual fallback stays on the page while it forwards (IRON RULE #47)",
      manage.fields.includes("MNG456") && manage.next.includes("tiktok-ads-read-auth.yml"));

// The page holds NO copy of the state map (22.10.2026: three copies existed). Every code is forwarded;
// the Worker reads scripts/_shared/tiktok_auth_targets.json and answers a state it has no run for with
// the code and the chat instruction.
const other = shown("?auth_code=XYZ789&state=comments_2026");
check("any other state is forwarded too — the Worker decides, the page holds no map",
      other.autoRun === AUTO + "auth_code=XYZ789&state=comments_2026", String(other.autoRun));
check("…and the fallback on the page still says what to do for an approval that is not a run",
      other.next.includes("בצ'אט של Claude"));
check("the page carries no state map of its own", !/ads_manage_2026'\s*:|JOBS\s*=/.test(html));
const nostate = shown("?auth_code=XYZ789");
check("a code without a state is not forwarded; the chat steps stay", nostate.autoRun === null && nostate.next.includes("לצ'אט"));
const junk = shown("?auth_code=%3Cscript%3E&state=ads_manage_2026");
check("a code that is not a code is not forwarded", junk.autoRun === null, String(junk.autoRun));

const err = shown("?error=access_denied&state=ads_read_2026");
check("a denied authorization is an error, never a link that implies success",
      err.status.includes("failed") && !err.next.includes("tiktok-ads-read-auth.yml"));
check("the denial itself is shown", err.fields.includes("access_denied"));
check("a denial is not forwarded", err.autoRun === null);

console.log(fails ? `\n✗ ${fails} failure(s)` : "\n✓ all cases pass");
process.exit(fails ? 1 : 0);
