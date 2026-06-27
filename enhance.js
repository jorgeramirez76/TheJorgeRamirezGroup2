/* ============================================================
   Jorge Ramirez Group — smooth-scroll enhancement (Lenis only).
   Purely additive: the site's existing IntersectionObserver reveals,
   counters, and hero animation in main.js are left fully intact.
   Loaded with `defer`. Safe to remove anytime.
   ============================================================ */
(function () {
  'use strict';

  // Respect reduced-motion and bail if the library didn't load.
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!window.Lenis) return;

  var lenis = new Lenis({
    duration: 1.05,
    easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
    smoothWheel: true,
    wheelMultiplier: 1,
    touchMultiplier: 1.6
  });

  function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);

  // Lenis-aware in-page anchor links (nav, footer, scroll cues).
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    var id = a.getAttribute('href');
    if (id.length > 1) {
      a.addEventListener('click', function (e) {
        var target = document.querySelector(id);
        if (target) { e.preventDefault(); lenis.scrollTo(target, { offset: -70 }); }
      });
    }
  });
})();
