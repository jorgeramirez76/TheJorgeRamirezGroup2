/* ============================================================
   Jorge Ramirez Group — town-aware intent capture.
   Reads the town from the page itself, so all 139 town pages
   get a page-specific ask with no per-page editing.
   Fires once, at real reading depth, with an explicit out.
   Self-contained. EN/ES aware. Mobile-safe.
   ============================================================ */
(function () {
  'use strict';
  if (document.getElementById('jrg-town-ask')) return;

  // Town pages only.
  var m = location.pathname.match(/\/towns\/([a-z0-9-]+)(?:\.html)?$/i);
  if (!m) return;

  try { if (sessionStorage.getItem('jrg_town_ask') === m[1]) return; } catch (e) { /* ignore */ }

  // Prefer the rendered H1 over the slug — it carries the real casing.
  var town = '';
  var h1 = document.querySelector('h1');
  if (h1) {
    var t = (h1.textContent || '').match(/^\s*([A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*)\s+NJ\b/);
    if (t) town = t[1].trim();
  }
  if (!town) {
    town = m[1].split('-').map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(' ');
  }

  var isES = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0;
  var T = isES ? {
    head: '¿Es dueño en ' + town + '?',
    body: 'La mayoría de los estimados en línea para ' + town + ' fallan porque no conocen la calle. Puedo darle el número real y lo que lo respalda.',
    cta: 'Conversemos honestamente',
    out: 'No, gracias',
    aria: 'Cerrar'
  } : {
    head: 'Own a home in ' + town + '?',
    body: 'Most online estimates for ' + town + ' miss because they do not know the street. I can walk you through the real number and what is behind it.',
    cta: 'Have an honest conversation',
    out: 'No thanks',
    aria: 'Dismiss'
  };

  var css = [
    '#jrg-town-ask{position:fixed;right:20px;bottom:20px;z-index:2147482000;width:min(360px,calc(100vw - 40px));',
    'background:var(--white,#fff);border:1px solid var(--border-light,#E8E4DC);border-radius:var(--radius,8px);',
    'box-shadow:0 12px 40px rgba(0,0,0,.14);padding:20px 20px 18px;',
    'font-family:var(--font-body,Inter,-apple-system,sans-serif);',
    'opacity:0;transform:translateY(12px);transition:opacity .7s ease-in-out,transform .7s ease-in-out}',
    '#jrg-town-ask.jrg-in{opacity:1;transform:none}',
    '#jrg-town-ask h3{font-family:var(--font-display,"Playfair Display",Georgia,serif);font-weight:400;',
    'font-size:1.22rem;line-height:1.3;margin:0 0 8px;color:var(--dark-gray,#1A1A1A);padding-right:26px}',
    '#jrg-town-ask p{font-size:.9rem;line-height:1.6;color:var(--text-light,#666);margin:0 0 16px}',
    '#jrg-town-ask .ta-cta{display:inline-flex;align-items:center;justify-content:center;min-height:46px;',
    'padding:0 22px;background:var(--dark-gray,#1A1A1A);color:#fff;text-decoration:none;',
    'font-size:.78rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;',
    'border-radius:var(--radius,8px);transition:background-color .2s ease}',
    '#jrg-town-ask .ta-cta:hover{background:var(--gold-text,#8A6D14)}',
    '#jrg-town-ask .ta-out{display:block;margin:12px 0 0;background:none;border:0;padding:4px 2px;cursor:pointer;',
    'font-size:.82rem;color:var(--text-light,#666);text-decoration:underline;font-family:inherit}',
    '#jrg-town-ask .ta-x{position:absolute;top:10px;right:10px;width:30px;height:30px;line-height:1;',
    'background:none;border:0;cursor:pointer;font-size:20px;color:#9a9a9a;border-radius:var(--radius,8px)}',
    '#jrg-town-ask .ta-x:hover{color:var(--dark-gray,#1A1A1A)}',
    '#jrg-town-ask :focus-visible{outline:2px solid var(--gold-text,#8A6D14);outline-offset:2px}',
    '@media (max-width:640px){#jrg-town-ask{right:10px;left:10px;width:auto;bottom:76px}}',
    '@media (prefers-reduced-motion:reduce){#jrg-town-ask{transition:none}}'
  ].join('');

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var box = document.createElement('aside');
  box.id = 'jrg-town-ask';
  box.setAttribute('role', 'complementary');
  box.setAttribute('aria-label', T.head);
  box.style.position = 'fixed';
  box.innerHTML =
    '<button class="ta-x" type="button" aria-label="' + T.aria + '">&times;</button>' +
    '<h3>' + T.head + '</h3>' +
    '<p>' + T.body + '</p>' +
    '<a class="ta-cta" href="/home-valuation?town=' + encodeURIComponent(town) + '&src=town-ask">' + T.cta + '</a>' +
    '<button class="ta-out" type="button">' + T.out + '</button>';

  function dismiss() {
    try { sessionStorage.setItem('jrg_town_ask', m[1]); } catch (e) { /* ignore */ }
    box.classList.remove('jrg-in');
    setTimeout(function () { if (box.parentNode) box.remove(); }, 700);
  }

  var shown = false;
  function show() {
    if (shown) return;
    shown = true;
    window.removeEventListener('scroll', onScroll);
    document.body.appendChild(box);
    // Not rAF alone — it is throttled in background tabs, which would strand the card at opacity 0.
    setTimeout(function () { box.classList.add('jrg-in'); }, 30);
    box.querySelector('.ta-x').addEventListener('click', dismiss);
    box.querySelector('.ta-out').addEventListener('click', dismiss);
    box.querySelector('.ta-cta').addEventListener('click', function () {
      try { sessionStorage.setItem('jrg_town_ask', m[1]); } catch (e) { /* ignore */ }
    });
  }

  // Half a screen past the fold — far enough in to have read something.
  function onScroll() {
    var h = document.documentElement;
    if ((h.scrollTop || document.body.scrollTop) > window.innerHeight * 1.5) show();
  }

  function init() {
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
