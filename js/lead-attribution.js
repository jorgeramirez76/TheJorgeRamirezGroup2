/* ============================================================
   Jorge Ramirez Group — automatic lead attribution.
   Stamps every form on the page with first-touch campaign data
   so an inbound lead arrives knowing where it came from.
   Self-contained. Safe to include on any page once.
   ============================================================ */
(function () {
  'use strict';
  if (window.__jrgAttribution) return;
  window.__jrgAttribution = true;

  var STORE = 'jrg_first_touch';
  var UTM = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid', 'msclkid'];

  function read() {
    try { return JSON.parse(localStorage.getItem(STORE) || 'null'); } catch (e) { return null; }
  }

  // First touch wins: an ad click months ago is the acquisition source, not today's direct visit.
  function firstTouch() {
    var stored = read();
    if (stored && stored.landing) return stored;

    var qs = new URLSearchParams(location.search);
    var touch = { landing: location.pathname + location.search, at: new Date().toISOString() };
    UTM.forEach(function (k) { if (qs.get(k)) touch[k] = qs.get(k); });

    var ref = document.referrer || '';
    if (ref) {
      try {
        var h = new URL(ref).hostname;
        if (h && h !== location.hostname) touch.referrer = h;
      } catch (e) { /* malformed referrer — not worth failing over */ }
    }
    if (!touch.utm_source && !touch.referrer) touch.utm_source = 'direct';

    try { localStorage.setItem(STORE, JSON.stringify(touch)); } catch (e) { /* private mode */ }
    return touch;
  }

  function setHidden(form, name, value) {
    if (!value) return;
    if (form.querySelector('[name="' + name + '"]')) return;
    var i = document.createElement('input');
    i.type = 'hidden';
    i.name = name;
    i.value = String(value).slice(0, 300);
    form.appendChild(i);
  }

  function stamp(form) {
    if (form.__jrgStamped) return;
    form.__jrgStamped = true;

    var t = firstTouch();
    setHidden(form, 'source_page', location.pathname);
    setHidden(form, 'first_touch', t.utm_source || t.referrer || 'direct');
    setHidden(form, 'landing_page', t.landing);
    setHidden(form, 'first_seen', t.at);
    UTM.forEach(function (k) { setHidden(form, k, t[k]); });

    // Every form gets a honeypot, not just the hand-authored ones.
    if (!form.querySelector('[name="_honey"]')) {
      var hp = document.createElement('input');
      hp.type = 'text';
      hp.name = '_honey';
      hp.tabIndex = -1;
      hp.setAttribute('aria-hidden', 'true');
      hp.setAttribute('autocomplete', 'off');
      hp.style.display = 'none';
      form.appendChild(hp);
    }

    // Hand the identity to stage two on /thank-you.
    form.addEventListener('submit', function () {
      var get = function (n) {
        var el = form.querySelector('[name="' + n + '"]');
        return el && el.value ? el.value.trim() : '';
      };
      try {
        localStorage.setItem('jrg_last_lead', JSON.stringify({
          name: get('name'),
          email: get('email'),
          phone: get('phone'),
          interest: get('interest'),
          at: Date.now()
        }));
      } catch (e) { /* private mode */ }
    });
  }

  function run() { Array.prototype.forEach.call(document.querySelectorAll('form'), stamp); }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();

  // Forms injected later (modals, lead magnets) get stamped too.
  if (window.MutationObserver) {
    new MutationObserver(run).observe(document.documentElement, { childList: true, subtree: true });
  }
})();
