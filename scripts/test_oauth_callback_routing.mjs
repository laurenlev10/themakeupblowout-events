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
  return {
    next: grab("next-steps-block"),
    lead: (d.getElementById("lead") || {}).textContent || "",
    fields: grab("fields"),
    status: (d.getElementById("status-pill") || {}).textContent || "",
  };
}

const ads = shown("?auth_code=ABC123&state=ads_read_2026");
check("a known job links straight to the run that finishes it",
      ads.next.includes("tiktok-ads-read-auth.yml"));
check("and it stops routing her through a chat",
      !ads.next.includes("לצ'אט"));
check("the code is still there to copy", ads.fields.includes("ABC123"));

const other = shown("?auth_code=XYZ789&state=comments_2026");
check("an unknown state keeps the old instructions rather than a wrong link",
      other.next.includes("לצ'אט") && !other.next.includes("tiktok-ads-read-auth.yml"));

const err = shown("?error=access_denied&state=ads_read_2026");
check("a denied authorization is an error, never a link that implies success",
      err.status.includes("failed") && !err.next.includes("tiktok-ads-read-auth.yml"));
check("the denial itself is shown", err.fields.includes("access_denied"));

console.log(fails ? `\n✗ ${fails} failure(s)` : "\n✓ all cases pass");
process.exit(fails ? 1 : 0);
