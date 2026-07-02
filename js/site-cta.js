/* ============================================================
   Jorge Ramirez Group — sticky mobile Call/Text bar.
   Self-contained: injects its own <style> + markup. Mobile-only.
   Language-aware (EN/ES). Safe to include on any page once.
   ============================================================ */
(function () {
  'use strict';
  if (document.getElementById('jrg-cta-bar')) return;

  var PHONE = '+19082307844';
  var isES = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0;
  var callLabel = isES ? 'Llamar' : 'Call';
  var textLabel = isES ? 'Texto' : 'Text';

  var css = [
    '#jrg-cta-bar{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;',
    'display:none;box-shadow:0 -2px 14px rgba(0,0,0,.18);font-family:inherit}',
    '#jrg-cta-bar a{flex:1;display:flex;align-items:center;justify-content:center;gap:7px;',
    'min-height:54px;text-decoration:none;font-weight:700;font-size:16px;letter-spacing:.02em}',
    '#jrg-cta-bar .jrg-call{background:#B8962E;color:#1A1A1A}',
    '#jrg-cta-bar .jrg-text{background:#1A1A1A;color:#FAFAF8}',
    '#jrg-cta-bar svg{width:19px;height:19px;fill:currentColor}',
    '@media(max-width:768px){#jrg-cta-bar{display:flex}body{padding-bottom:54px}}'
  ].join('');
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var phoneSvg = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.3 1.1.4 2.3.5 3.6.5.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.4 21 3 13.6 3 4.5c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.5 3.5.1.4 0 .7-.3 1l-2.1 1.8Z"/></svg>';
  var textSvg = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v10c0 1.1-.9 2-2 2H8l-4 4V6c0-1.1.9-2 2-2Z"/></svg>';

  var bar = document.createElement('div');
  bar.id = 'jrg-cta-bar';
  bar.setAttribute('aria-label', isES ? 'Llamar o enviar texto a Jorge' : 'Call or text Jorge');
  bar.innerHTML =
    '<a class="jrg-call" href="tel:' + PHONE + '">' + phoneSvg + '<span>' + callLabel + '</span></a>' +
    '<a class="jrg-text" href="sms:' + PHONE + '">' + textSvg + '<span>' + textLabel + '</span></a>';

  if (document.body) document.body.appendChild(bar);
  else document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(bar); });
})();

/* ============================================================
   Scroll-reveal micro-animations. Progressive enhancement only:
   content stays fully visible without JS, with reduced motion,
   or in browsers lacking IntersectionObserver.
   ============================================================ */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  function init() {
    var els = document.querySelectorAll('.section-header, .resource-card, .service-card');
    if (!els.length) return;

    var st = document.createElement('style');
    st.textContent =
      '.jrg-rv{opacity:0;transform:translateY(22px);' +
      'transition:opacity .65s ease,transform .65s cubic-bezier(.16,1,.3,1)}' +
      '.jrg-rv-in{opacity:1;transform:none}';
    document.head.appendChild(st);

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('jrg-rv-in');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    var vh = window.innerHeight;
    var n = 0;
    els.forEach(function (el) {
      /* only elements below the first viewport ever get hidden */
      if (el.getBoundingClientRect().top > vh * 0.85) {
        el.classList.add('jrg-rv');
        el.style.transitionDelay = (n++ % 6) * 55 + 'ms';
        io.observe(el);
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
