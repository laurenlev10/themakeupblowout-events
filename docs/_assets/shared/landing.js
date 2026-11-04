/* landing.js — THE one copy of the event pages' tracking and sign-up form code (4.11.2026).
 *
 * Until 4.11.2026 this code was pasted into every template (6 copies of the tracking block, 2 of the form
 * handler) and from there into every built page. Every page now loads this file:
 *   <script src="/_assets/shared/landing.js?v={{LANDING_JS_V}}"></script>   (build.py fills the version)
 * and a landing page starts its form with  joinWebForm('st-join-web-form-<FORM_ID>', '<share page>').
 *
 * What it sends (read daily by lauren-agent-hub-data scripts/landing_funnel.py → /experiments/):
 *   signup_form_seen       the sign-up form came into view (40% of it on screen)
 *   signup_form_tap        the FIRST interaction with the form, param via = focusin|click|input|change|submit.
 *                          4.11.2026: it was focusin only, and Meta's in-app browser fills the phone by autofill
 *                          without focusing the field, and on an iPhone a button tap focuses nothing — so on
 *                          Meta paid traffic more women "signed up" than "tapped" (Tucson 118%), while on
 *                          direct traffic tapped→signed was 56–93%. Not touchstart/pointerdown: a finger that
 *                          starts a scroll on the form is not a tap.
 *   signup_done            a NEW sign-up, ONCE per page (GA4 enhanced measurement sends its own form_submit
 *                          on every submit — 29.10.2026).
 *   signup_double_submit   a second submit while the first was still on its way — blocked. 4.11.2026: the
 *                          button had no lock; Tucson GA4 counted 646 new sign-ups 30.10–4.11 while the
 *                          SimpleTexting list grew by 485 (no TikTok there). Two requests both answered 200.
 * Meta gets Lead only for a NEW sign-up, once; a woman already on the list gets AlreadySubscribed (28.10.2026).
 * TikTok gets SubmitForm on the same rule.
 *
 * Page test (lpx): a page built with <html data-lpx="<test id>"> puts each browser in arm a or b (50/50,
 * kept for that browser), sets class lpx-b on <html> for arm b, and sends lpx_<arm>_view / lpx_<arm>_done
 * next to the normal events — so GA4 counts each arm by event name, no custom dimension needed.
 * A page without data-lpx is untouched.
 */
(function (w, d) {
  'use strict';

  /* ── page test arm ─────────────────────────────────────────────────────────────── */
  var html = d.documentElement, lpx = html.getAttribute('data-lpx'), arm = null;
  if (lpx) {
    var key = 'lpx_' + lpx;
    try { arm = w.localStorage.getItem(key); } catch (e) {}
    if (arm !== 'a' && arm !== 'b') {
      arm = Math.random() < 0.5 ? 'a' : 'b';
      try { w.localStorage.setItem(key, arm); } catch (e) {}
    }
    if (arm === 'b') {
      html.className += (html.className ? ' ' : '') + 'lpx-b';
      /* Arm B of test "form-above-fold" (4.11.2026): the same words, a shorter hero — the phone field AND the
         button inside the first 560px (Meta's in-app browser on an iPhone shows ~560–600px; on the normal page
         the button starts at 666px, below the first screen). Nothing is removed from the page: the title goes
         to one line, the category line moves under the form. */
      var css = d.createElement('style');
      css.textContent =
        '.lpx-b .hero{padding-top:54px}' +                               /* the language bar is fixed above it */
        '.lpx-b .hero .eyebrow{font-size:11px;letter-spacing:1px;padding:5px 12px;margin-bottom:6px}' +
        /* one line: the <br>s hide; the template carries a space before each one ("Makeup <br>Blowout <br>Sale.") */
        '.lpx-b .hero h1.an{font-size:clamp(24px,7.4vw,48px)!important;line-height:1;white-space:nowrap;text-shadow:2px 2px 0 var(--ink),-1px -1px 0 var(--ink),1px -1px 0 var(--ink),-1px 1px 0 var(--ink)!important}' +
        '.lpx-b .hero h1.an br{display:none}' +
        '.lpx-b .hero .city-tag{margin-top:4px;font-size:clamp(26px,8vw,44px)}' +
        '.lpx-b .hero .offer{margin-top:2px;font-size:clamp(20px,6vw,34px)}' +
        '.lpx-b .hero .offer small{display:none}' +
        '.lpx-b .hero-form{margin-top:10px;padding:14px 16px 12px}' +
        '.lpx-b .hero-form .hf-sub{margin:4px 0 8px;font-size:13px}' +
        '.lpx-b .hero-form .st-font-caption{font-size:11px;line-height:1.35}';   /* consent text: same words, smaller */
      d.head.appendChild(css);
    }
    html.setAttribute('data-lpx-arm', arm);
  }

  var doneSent = false;
  w.trackEvent = function (name, params) {
    params = params || {};
    try { if (w.gtag) gtag('event', name, params); } catch (e) {}
    if (name === 'form_submit' && !params.already_subscribed) {
      if (doneSent) return;               /* a NEW sign-up is counted once per page, whatever happens after */
      doneSent = true;
      try { if (w.gtag) gtag('event', 'signup_done', {}); } catch (e) {}
      try { if (w.gtag && arm) gtag('event', 'lpx_' + arm + '_done', { lpx: lpx }); } catch (e) {}
    }
    try { if (w.fbq && name === 'form_submit') { if (params.already_subscribed) fbq('trackCustom', 'AlreadySubscribed', params); else fbq('track', 'Lead', params); } } catch (e) {}
    try { if (w.fbq && name === 'share_click') fbq('track', 'ClickButton', params); } catch (e) {}
    try { if (w.ttq && name === 'form_submit' && !params.already_subscribed) ttq.track('SubmitForm', params); } catch (e) {}
    try { if (w.ttq && name === 'share_click') ttq.track('ClickButton', params); } catch (e) {}
    try { if (w.ttq && name === 'tiktok_arrival') ttq.track('CompleteRegistration', params); } catch (e) {}
  };

  function funnel() {
    var f = d.querySelector('form.st-signupform');
    if (!f) return;
    if (arm) trackEvent('lpx_' + arm + '_view', { lpx: lpx });
    var seen = false, tapped = false;
    try {
      if ('IntersectionObserver' in w) {
        var io = new IntersectionObserver(function (es) {
          es.forEach(function (x) { if (x.isIntersecting && !seen) { seen = true; trackEvent('signup_form_seen', {}); io.disconnect(); } });
        }, { threshold: 0.4 });
        io.observe(f);
      }
    } catch (e) {}
    function tap(ev) { if (tapped) return; tapped = true; trackEvent('signup_form_tap', { via: ev.type }); }
    ['focusin', 'click', 'input', 'change', 'submit'].forEach(function (t) { f.addEventListener(t, tap, true); });
  }

  d.addEventListener('DOMContentLoaded', function () {
    d.querySelectorAll('a[href*="instagram.com"]').forEach(function (a) { a.addEventListener('click', function () { trackEvent('share_click', { platform: 'instagram' }); }); });
    d.querySelectorAll('a[href*="facebook.com"], a[href*="fb.watch"]').forEach(function (a) { a.addEventListener('click', function () { trackEvent('share_click', { platform: 'facebook' }); }); });
    d.querySelectorAll('a[href*="tiktok.com"]').forEach(function (a) { a.addEventListener('click', function () { trackEvent('share_click', { platform: 'tiktok' }); }); });
    if (w.location.pathname.indexOf('tiktok') !== -1) { trackEvent('tiktok_arrival', {}); }
    funnel();
  });

  /* ── the SimpleTexting web form ─────────────────────────────────────────────────── */
  /* 418 DuplicateContactPhone/Email = she is already on the list → treated as success (2.7.2026,
     Santa Maria), sent as already_subscribed (never Lead). */
  var DUP = ['DuplicateContactPhoneException', 'DuplicateContactEmailException'];
  w.joinWebForm = function (formId, shareUrl) {
    var XHR = ('onload' in new w.XMLHttpRequest()) ? w.XMLHttpRequest : w.XDomainRequest;
    var form, errEl, tEl, busy = false;
    function se(m) { errEl.innerText = m; }
    function ta() { return form.querySelector('input[name="terms-agreed"]').checked; }
    function leave(params) {
      form.querySelector('.step1-form').style.display = 'none';
      try { trackEvent('form_submit', params); } catch (e) {}
      d.location.href = shareUrl;
      form.reset();
    }
    function load() {
      if (this.status === 200) { leave({}); return; }
      if (this.status === 418) {
        var e = null; try { e = w.JSON.parse(this.responseText); } catch (_) {}
        if (e && DUP.indexOf(e.code) !== -1) { leave({ already_subscribed: 1 }); return; }
        busy = false; se((e && (e.reason || e.message)) || 'Validation error.'); return;
      }
      busy = false; se('Internal Error. Please, try later.');
    }
    function err() { busy = false; se('Internal Error. Please, try later.'); }
    function send() {
      var data = {};
      Array.prototype.slice.call(form).forEach(function (f) { data[f.name] = f.value; });
      var x = new XHR();
      x.open(form.method, 'https://app2.simpletexting.com/join/joinContact?r=' + Date.now());
      x.onload = load; x.onerror = err; x.ontimeout = err;
      try { x.setRequestHeader('Content-Type', 'application/json; charset=UTF-8'); } catch (_) {}
      x.send(w.JSON.stringify(data));
    }
    function sub(e) {
      e.preventDefault();
      if (busy) { try { trackEvent('signup_double_submit', {}); } catch (_) {} return false; }
      se('');
      if (!ta()) { tEl.style.display = 'block'; return false; }
      busy = true; send();
      return false;
    }
    function fmt(v) { var n = v.replace(/\D/g, ''); var a = n.substring(0, 3), b = n.substring(3, 6), c = n.substring(6, 10), r = ''; if (a) r += '(' + a; if (b) r += ') ' + b; if (c) r += '-' + c; return r; }
    function pc(e) { e.currentTarget.value = fmt(e.currentTarget.value); }
    function go() {
      form = d.getElementById(formId);
      if (!form) return;
      errEl = form.querySelector('.st-signupform-server-error-message');
      tEl = form.querySelector('.st-signupform-terms-agreed-error');
      form.addEventListener('submit', sub);
      form.querySelectorAll('input[data-type="phone"]').forEach(function (f) { f.addEventListener('input', pc); });
    }
    if (d.readyState === 'loading') { d.addEventListener('DOMContentLoaded', go); } else { go(); }
  };
})(window, document);
