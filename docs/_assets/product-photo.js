/* product-photo.js — the ONE place that says how a product is opened online.
 *
 * 11.10.2026 — Lauren, first on /pricing/: "בכל מוצר יהיה לינק שאם לוחצים עליו זה פותח את המוצר
 * אונליין - תמונה של המוצר", then on the crew recount sheet: "אם איש צוות לא יודע מה המוצר אז
 * הוא יכול ללחוץ על תמונה".
 *
 * OCTOPOS holds no product image, and a URL copied into a state file is one more thing that rots
 * (IRON RULE #27). So the link is a web image search built from what the product IS — its name,
 * or its barcode (which finds the exact item when the name is generic).
 *
 * WHY HERE, on the PUBLIC site: two pages need it on two origins — the crew sheet
 * (events.themakeupblowout.com/recount-count/, public, no login) and /pricing/ on the dashboard
 * (behind Cloudflare Access, which a crew phone cannot pass). The public origin is the only one
 * both can load, so the rule lives here once and the dashboard loads it from here.
 * Nothing secret is or may ever be in this file.
 */
(function () {
  "use strict";
  function url(q) {
    q = String(q == null ? "" : q).trim();
    return q ? "https://www.google.com/search?udm=2&q=" + encodeURIComponent(q) : "";
  }
  window.MbsProductPhoto = { url: url };
})();
