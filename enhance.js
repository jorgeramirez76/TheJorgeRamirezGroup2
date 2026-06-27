/* ============================================================
   Jorge Ramirez Group — scroll enhancement layer
   Lenis smooth scroll + GSAP ScrollTrigger reveals.
   Loaded with `defer`. Safe to remove anytime (purely additive).
   ============================================================ */
(function () {
  'use strict';

  var docEl = document.documentElement;
  function revealAll() { docEl.classList.remove('gsap-enhance'); }

  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Bail safely if reduced motion or libraries missing — content stays visible.
  if (reduce || !window.gsap || !window.ScrollTrigger) { revealAll(); return; }

  gsap.registerPlugin(ScrollTrigger);

  /* ---- Lenis smooth scroll, synced to the GSAP ticker ---- */
  var lenis = null;
  if (window.Lenis) {
    lenis = new Lenis({
      duration: 1.1,
      easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      smoothWheel: true
    });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(function (time) { lenis.raf(time * 1000); });
    gsap.ticker.lagSmoothing(0);

    // Lenis-aware in-page anchor links (header nav, scroll indicator, etc.)
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
      var id = a.getAttribute('href');
      if (id.length > 1) {
        a.addEventListener('click', function (e) {
          var target = document.querySelector(id);
          if (target) { e.preventDefault(); lenis.scrollTo(target, { offset: -70 }); }
        });
      }
    });
  }

  /* ---- Hero entrance (fromTo so it overrides the CSS pre-hide cleanly) ---- */
  var heroBits = gsap.utils.toArray('.hero-content > *');
  if (heroBits.length) {
    gsap.timeline({ defaults: { ease: 'power3.out' } })
      .fromTo(heroBits,
        { autoAlpha: 0, y: 34 },
        { autoAlpha: 1, y: 0, duration: 0.9, stagger: 0.12, delay: 0.2 }
      );
  } else {
    revealAll();
  }

  /* ---- Section header reveals (each, once) ---- */
  gsap.utils.toArray('.section-header').forEach(function (el) {
    gsap.from(el, {
      autoAlpha: 0, y: 40, duration: 0.8, ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 82%', once: true }
    });
  });

  /* ---- Card/grid reveals, batched with a gentle stagger (once) ---- */
  ScrollTrigger.batch(
    '.listing-card, .stat-card, .testimonial-card, .resource-card, .community-card, .press-strip',
    {
      start: 'top 86%',
      once: true,
      onEnter: function (batch) {
        gsap.from(batch, {
          autoAlpha: 0, y: 48, duration: 0.7, ease: 'power2.out', stagger: 0.1
        });
      }
    }
  );

  /* ---- Subtle hero parallax (background drifts slower than foreground) ---- */
  var carousel = document.querySelector('.hero-carousel');
  if (carousel) {
    gsap.to(carousel, {
      yPercent: 14, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true }
    });
  }

  // Recalculate once everything (fonts/images) settles.
  window.addEventListener('load', function () { ScrollTrigger.refresh(); });
})();
