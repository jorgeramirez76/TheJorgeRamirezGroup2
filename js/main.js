// Main JavaScript for Jorge Ramirez Real Estate Website

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]:not(.skip-link)').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Mobile menu toggle
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const navLinks = document.getElementById('navLinks');

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        mobileMenuBtn.classList.toggle('active');
        mobileMenuBtn.setAttribute('aria-expanded', navLinks.classList.contains('active'));
    });

    // Close menu when clicking a link
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            mobileMenuBtn.classList.remove('active');
            mobileMenuBtn.setAttribute('aria-expanded', 'false');
        });
    });
}

// Communities rendering functionality
const communityLanguage = (document.documentElement.lang || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
const isSpanishCommunityUi = communityLanguage === 'es';
const countyInfoByLanguage = {
    en: {
        "Essex": {
            highlight: "Bloomfield, Maplewood, Millburn, Montclair",
            description: "Six maintained guides connecting Essex County addresses to municipal, property, tax, transit, and district sources.",
            photo: "/images/county-cards/essex.webp"
        },
        "Hudson": {
            highlight: "Guttenberg, Hoboken, Jersey City, West New York",
            description: "Four maintained guides connecting Hudson County addresses to municipal, property, transit, and tax sources.",
            photo: "/images/county-cards/hudson.webp"
        },
        "Morris": {
            highlight: "Chatham, Denville, Madison, Morristown",
            description: "Eight maintained guides for municipal records, property research, transportation sources, and district information.",
            photo: "/images/county-cards/morris.webp"
        },
        "Middlesex": {
            highlight: "East Brunswick, Helmetta, Middlesex, Woodbridge",
            description: "Five maintained guides for municipal, property, transportation, tax, and district-source research.",
            photo: "/images/county-cards/middlesex.webp"
        },
        "Union": {
            highlight: "Berkeley Heights, Cranford, Summit, Westfield",
            description: "Jorge's Summit office is in Union County, with eight maintained guides for property and municipal research.",
            photo: "/images/county-cards/union.webp"
        },
        "Somerset": {
            highlight: "Basking Ridge",
            description: "The maintained Basking Ridge guide connects an address to Bernards Township, property, tax, transit, and district sources.",
            photo: "/images/county-cards/somerset.webp"
        }
    },
    es: {
        "Essex": {
            highlight: "Bloomfield, Maplewood, Millburn, Montclair",
            description: "Seis guías revisadas conectan las direcciones del condado de Essex con fuentes municipales, de propiedad, impuestos, transporte y distritos escolares.",
            photo: "/images/county-cards/essex.webp"
        },
        "Hudson": {
            highlight: "Guttenberg, Hoboken, Jersey City, West New York",
            description: "Cuatro guías revisadas conectan las direcciones del condado de Hudson con fuentes municipales, de propiedad, transporte e impuestos.",
            photo: "/images/county-cards/hudson.webp"
        },
        "Morris": {
            highlight: "Chatham, Denville, Madison, Morristown",
            description: "Ocho guías revisadas permiten consultar registros municipales, propiedades, transporte y distritos escolares.",
            photo: "/images/county-cards/morris.webp"
        },
        "Middlesex": {
            highlight: "East Brunswick, Helmetta, Middlesex, Woodbridge",
            description: "Cinco guías revisadas permiten consultar fuentes municipales, de propiedad, transporte, impuestos y distritos escolares.",
            photo: "/images/county-cards/middlesex.webp"
        },
        "Union": {
            highlight: "Berkeley Heights, Cranford, Summit, Westfield",
            description: "La oficina de Jorge en Summit está en el condado de Union, con ocho guías revisadas para investigar propiedades y registros municipales.",
            photo: "/images/county-cards/union.webp"
        },
        "Somerset": {
            highlight: "Basking Ridge",
            description: "La guía revisada de Basking Ridge conecta una dirección con fuentes de Bernards Township, propiedad, impuestos, transporte y distrito escolar.",
            photo: "/images/county-cards/somerset.webp"
        }
    }
};
const countyInfo = countyInfoByLanguage[communityLanguage];
const communityUi = isSpanishCommunityUi ? {
    countyName: county => `Condado de ${county}`,
    exploreCounty: county => `Explorar el condado de ${county}`,
    guideCount: count => `${count} ${count === 1 ? 'guía' : 'guías'} locales`,
    allCounties: 'Todos los condados',
    searchPlaceholder: county => `Buscar municipio en el condado de ${county}...`,
    searchLabel: county => `Buscar en las guías del condado de ${county}`,
    resultStatus: count => count === 0
        ? 'No hay guías locales que coincidan con la búsqueda.'
        : `${count} ${count === 1 ? 'guía local disponible' : 'guías locales disponibles'}.`,
    emptyState: 'No hay guías locales que coincidan. Prueba con otro municipio.',
    exploreTown: town => `Explorar ${town}`,
    commuteLabel: 'Viaje a NYC:',
    districtLabel: 'Distrito escolar:',
    townPath: slug => `/es/towns/${slug}`,
    description: community => {
        const sources = community.url_slug === 'basking-ridge'
            ? 'fuentes oficiales de Bernards Township, de propiedad, impuestos, transporte y distrito escolar'
            : 'fuentes oficiales municipales, de propiedad, impuestos, transporte y distrito escolar';
        return `Usa la guía revisada de ${community.town} para consultar ${sources} para una dirección específica.`;
    }
} : {
    countyName: county => `${county} County`,
    exploreCounty: county => `Explore ${county} County`,
    guideCount: count => `${count} ${count === 1 ? 'Town Guide' : 'Town Guides'}`,
    allCounties: 'All Counties',
    searchPlaceholder: county => `Search towns in ${county} County...`,
    searchLabel: county => `Search ${county} County town guides`,
    resultStatus: count => count === 0
        ? 'No town guides match this search.'
        : `${count} ${count === 1 ? 'town guide available' : 'town guides available'}.`,
    emptyState: 'No town guides match. Try another town name.',
    exploreTown: town => `Explore ${town}`,
    commuteLabel: 'NYC Commute:',
    districtLabel: 'School district:',
    townPath: slug => `/towns/${slug}`,
    description: community => community.description || ''
};

let activeCounty = null;

function renderCountyCards() {
    const container = document.getElementById('communities-container');
    if (!container) return; /* section only exists on homepage */
    container.classList.remove('county-open');
    container.innerHTML = Object.keys(countyInfo).map(county => {
        const info = countyInfo[county];
        const townGuideCount = (communitiesData[county] || []).length;
        return `
        <button type="button" class="county-hero-card" data-county="${county}" aria-label="${communityUi.exploreCounty(county)}" onclick="openCounty('${county}')">
            <span class="county-hero-photo" data-bg="${info.photo}" aria-hidden="true"></span>
            <span class="county-hero-body">
                <span class="county-hero-name">${communityUi.countyName(county)}</span>
                <span class="county-hero-towns">${communityUi.guideCount(townGuideCount)}</span>
                <span class="county-hero-highlight">${info.highlight}</span>
                <span class="county-hero-desc">${info.description}</span>
                <span class="county-hero-cta">${communityUi.exploreCounty(county)} →</span>
            </span>
        </button>`;
    }).join('');
    observeCountyPhotos(container);
}

function observeCountyPhotos(container) {
    const photos = Array.from(container.querySelectorAll('.county-hero-photo[data-bg]'));
    const load = photo => {
        photo.style.backgroundImage = `url('${photo.dataset.bg}')`;
        delete photo.dataset.bg;
    };
    if (!('IntersectionObserver' in window)) {
        photos.forEach(load);
        return;
    }
    const observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            load(entry.target);
            currentObserver.unobserve(entry.target);
        });
    }, { rootMargin: '300px 0px' });
    photos.forEach(photo => observer.observe(photo));
}

(function observeRevealTilePhotos() {
    const tiles = Array.from(document.querySelectorAll('.reveal-tile[data-reveal-img]'));
    const load = tile => {
        tile.style.setProperty('--reveal-img', `url('${tile.dataset.revealImg}')`);
        delete tile.dataset.revealImg;
    };
    if (!('IntersectionObserver' in window)) {
        tiles.forEach(load);
        return;
    }
    const observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            load(entry.target);
            currentObserver.unobserve(entry.target);
        });
    }, { rootMargin: '300px 0px' });
    tiles.forEach(tile => observer.observe(tile));
})();

(function observeListingPhotos() {
    const photos = Array.from(document.querySelectorAll('.listing-img[data-listing-img]'));
    const load = photo => {
        photo.style.backgroundImage = `url('${photo.dataset.listingImg}')`;
        delete photo.dataset.listingImg;
    };
    if (!('IntersectionObserver' in window)) {
        photos.forEach(load);
        return;
    }
    const observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            load(entry.target);
            currentObserver.unobserve(entry.target);
        });
    }, { rootMargin: '300px 0px' });
    photos.forEach(photo => observer.observe(photo));
})();

function openCounty(county) {
    activeCounty = county;
    const container = document.getElementById('communities-container');

    const towns = communitiesData[county] || [];

    const backBtn = `<button type="button" class="county-back-btn" onclick="closeCounty()">\u2190 ${communityUi.allCounties}</button>`;
    const countyTitle = `<div class="county-open-header">
        <h3>${communityUi.countyName(county)} — ${communityUi.guideCount(towns.length)}</h3>
        <p>${countyInfo[county].description}</p>
    </div>`;

    const search = `<div class="county-search-wrap">
        <span class="search-icon" aria-hidden="true">🔍</span>
        <input type="text" id="town-search" aria-label="${communityUi.searchLabel(county)}" aria-describedby="town-search-status" placeholder="${communityUi.searchPlaceholder(county)}" oninput="filterTowns('${county}', this.value)">
    </div>
    <p id="town-search-status" class="visually-hidden" role="status" aria-live="polite">${communityUi.resultStatus(towns.length)}</p>`;

    const townCards = `<div class="communities-grid" id="towns-grid">` +
        towns.map(c => buildTownCard(c, county)).join('') +
    `</div>`;

    container.classList.add('county-open');
    container.innerHTML = backBtn + countyTitle + search + townCards;
    const backButton = container.querySelector('.county-back-btn');
    if (backButton) backButton.focus({ preventScroll: true });
    container.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function closeCounty() {
    const closingCounty = activeCounty;
    activeCounty = null;
    renderCountyCards();
    const container = document.getElementById('communities-container');
    const returningCard = container && closingCounty
        ? container.querySelector(`.county-hero-card[data-county="${closingCounty}"]`)
        : null;
    if (returningCard) returningCard.focus({ preventScroll: true });
}

function filterTowns(county, term) {
    const grid = document.getElementById('towns-grid');
    if (!grid) return;
    const towns = communitiesData[county] || [];
    const filtered = term
        ? towns.filter(c => c.town.toLowerCase().includes(term.toLowerCase()) || communityUi.description(c).toLowerCase().includes(term.toLowerCase()))
        : towns;
    grid.innerHTML = filtered.length
        ? filtered.map(c => buildTownCard(c, county)).join('')
        : `<p class="community-empty-state">${communityUi.emptyState}</p>`;
    const status = document.getElementById('town-search-status');
    if (status) status.textContent = communityUi.resultStatus(filtered.length);
}

function buildTownCard(c, county) {
    const slug = c.url_slug || c.town.toLowerCase().replace(/\s+/g, '-');
    const transitBadges = c.primary_transit
        ? `<div class="transit-badges"><span class="transit-badge">🚆 ${c.primary_transit.split(' ').slice(0,4).join(' ')}</span></div>`
        : '';
    return `
    <div class="community-card">
        <span class="county-badge">${communityUi.countyName(county)}</span>
        <h3>${c.town}</h3>
        <p class="community-desc">${communityUi.description(c)}</p>
        ${transitBadges}
        <div class="community-details">
            ${c.commute_to_nyc ? `<div class="detail-item"><span class="detail-label">${communityUi.commuteLabel}</span> ${c.commute_to_nyc}</div>` : ''}
            ${c.schools ? `<div class="detail-item"><span class="detail-label">${communityUi.districtLabel}</span> ${c.schools.substring(0,100)}...</div>` : ''}
        </div>
        <a href="${communityUi.townPath(slug)}" class="community-link">${communityUi.exploreTown(c.town)} →</a>
    </div>`;
}

// Form submission handler
const contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        // Form will be handled by Formspree or your backend
        // Add any custom handling here if needed
        console.log('Form submitted');
    });
}

// Initialize — show county cards
// Scripts load at bottom of page so DOM is already ready; call directly + also handle DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderCountyCards);
} else {
    renderCountyCards();
}

// Lazy load images for performance
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}

// ============================
// HERO IMAGE CAROUSEL
// ============================
(function initHeroCarousel() {
    const slides = Array.from(document.querySelectorAll('.hero-slide'));
    if (slides.length === 0) return;

    function loadSlide(slide) {
        if (slide.style.backgroundImage) return Promise.resolve(true);
        if (slide.dataset.loadState === 'failed') return Promise.resolve(false);
        if (slide.dataset.loadState === 'loading' && slide._imagePromise) return slide._imagePromise;

        const url = slide.getAttribute('data-bg');
        if (!url) return Promise.resolve(false);
        slide.dataset.loadState = 'loading';
        slide._imagePromise = new Promise(resolve => {
            const img = new Image();
            img.onload = () => {
                slide.style.backgroundImage = `url('${url}')`;
                slide.dataset.loadState = 'loaded';
                resolve(true);
            };
            img.onerror = () => {
                slide.dataset.loadState = 'failed';
                resolve(false);
            };
            img.src = url;
        });
        return slide._imagePromise;
    }

    let current = 0;
    const INTERVAL = 12000;

    // Keep the first locally painted slide static for reduced-motion and save-data users.
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (navigator.connection && navigator.connection.saveData) return;

    let rotating = false;
    async function rotate() {
        if (rotating) return;
        rotating = true;
        const next = (current + 1) % slides.length;
        const ready = await loadSlide(slides[next]);
        if (ready) {
            slides[current].classList.remove('active');
            slides[next].classList.add('active');
            current = next;
            // Warm only the following slide after the current transition. This
            // keeps the carousel smooth without downloading every background at startup.
            setTimeout(() => loadSlide(slides[(current + 1) % slides.length]), 1500);
        }
        rotating = false;
    }

    const warmNext = () => loadSlide(slides[1 % slides.length]);
    if ('requestIdleCallback' in window) {
        window.requestIdleCallback(warmNext, { timeout: 6000 });
    } else {
        setTimeout(warmNext, 3500);
    }
    setInterval(rotate, INTERVAL);
})();

// ============================
// HERO PARALLAX ON SCROLL
// ============================
(function initParallax() {
    const hero = document.querySelector('.hero');
    const carousel = document.querySelector('.hero-carousel');
    if (!hero || !carousel) return;

    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                const scrolled = window.scrollY;
                if (scrolled < window.innerHeight) {
                    carousel.style.transform = `translateY(${scrolled * 0.3}px)`;
                }
                ticking = false;
            });
            ticking = true;
        }
    });
})();

// ============================
// ANIMATED NUMBER COUNTERS
// ============================
(function initCounters() {
    const counters = document.querySelectorAll('.stat-number[data-target]');
    const statsBar = document.querySelector('.stats-bar');
    if (counters.length === 0 || !statsBar) return;

    let counted = false;

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !counted) {
                counted = true;
                counterObserver.disconnect();

                counters.forEach(counter => {
                    const target = parseInt(counter.getAttribute('data-target'));
                    const suffix = counter.getAttribute('data-suffix') || '';
                    // Reset to 0 right before animating
                    counter.textContent = '0' + suffix;
                    const duration = 2000;
                    const startTime = performance.now();

                    function updateCounter(currentTime) {
                        const elapsed = currentTime - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3);
                        const value = Math.round(eased * target);
                        counter.textContent = value + suffix;

                        if (progress < 1) {
                            requestAnimationFrame(updateCounter);
                        }
                    }
                    requestAnimationFrame(updateCounter);
                });
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px 50px 0px' });

    counterObserver.observe(statsBar);
})();

// ============================
// STAGGERED FADE-IN ON SCROLL
// ============================
(function initStaggeredReveal() {
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Find all animatable children in this section
                const cards = entry.target.querySelectorAll('.feature-card, .resource-card, .stat-card, .info-card, .community-card, .faq-item, .credential-item, .testimonial-card');
                cards.forEach((card, i) => {
                    card.style.transitionDelay = `${i * 100}ms`;
                    card.classList.add('revealed');
                });
                // Also reveal the section header
                const header = entry.target.querySelector('.section-header');
                if (header) header.classList.add('revealed');

                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    // Observe all content sections
    document.querySelectorAll('.content-section, .stats-bar, #communities').forEach(section => {
        // Mark children as hidden initially
        section.querySelectorAll('.feature-card, .resource-card, .stat-card, .info-card, .community-card, .faq-item, .credential-item, .testimonial-card').forEach(card => {
            card.classList.add('reveal-item');
        });
        const header = section.querySelector('.section-header');
        if (header) header.classList.add('reveal-item');

        revealObserver.observe(section);
    });
})();

// ============================
// TESTIMONIAL STAR ANIMATION
// ============================
(function initStarAnimation() {
    const starObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const stars = entry.target.querySelectorAll('.testimonial-stars');
                stars.forEach((el, i) => {
                    setTimeout(() => {
                        el.classList.add('stars-animated');
                    }, i * 150);
                });
                starObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });

    const testimonialSection = document.getElementById('testimonials');
    if (testimonialSection) starObserver.observe(testimonialSection);
})();

// ═══════════════════════════════════════════════════════════════════
// Testimonial ↔ Listing auto-link (2026-04-17)
// Reads town from .testimonial-location text, matches to .listing-card[data-town],
// wires bidirectional hover + click-to-scroll highlighting.
// ═══════════════════════════════════════════════════════════════════
(function () {
  const slugify = s => s.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');
  const testimonials = document.querySelectorAll('.testimonial-card');
  const listings = document.querySelectorAll('.listing-card[data-town]');
  const listingByTown = {};
  listings.forEach(l => { listingByTown[l.dataset.town] = l; });

  testimonials.forEach(t => {
    const loc = t.querySelector('.testimonial-location');
    if (!loc) return;
    // Extract town name before any comma/bullet
    const m = loc.textContent.match(/^([A-Za-z\s]+?)(?:,|\s*•)/);
    if (!m) return;
    const town = slugify(m[1].trim());
    t.dataset.matchTown = town;
    if (listingByTown[town]) {
      t.classList.add('has-listing-match');
      listingByTown[town].classList.add('has-testimonial-match');
      listingByTown[town].dataset.matchedTestimonial = 'true';
    }
  });

  function highlight(town) {
    document.querySelectorAll('.testimonial-card, .listing-card').forEach(c => c.classList.remove('highlighted'));
    if (!town) return;
    const t = document.querySelector(`.testimonial-card[data-match-town="${town}"]`);
    const l = document.querySelector(`.listing-card[data-town="${town}"]`);
    if (t) t.classList.add('highlighted');
    if (l) l.classList.add('highlighted');
  }

  testimonials.forEach(t => {
    t.addEventListener('mouseenter', () => highlight(t.dataset.matchTown));
    t.addEventListener('mouseleave', () => highlight(null));
    t.addEventListener('click', e => {
      const town = t.dataset.matchTown;
      if (!town || !listingByTown[town] || e.target.closest('a')) return;
      listingByTown[town].scrollIntoView({behavior:'smooth', block:'center'});
      setTimeout(() => highlight(town), 400);
      setTimeout(() => highlight(null), 2600);
    });
  });
  listings.forEach(l => {
    l.addEventListener('mouseenter', () => highlight(l.dataset.town));
    l.addEventListener('mouseleave', () => highlight(null));
    l.addEventListener('click', e => {
      const town = l.dataset.town;
      const t = document.querySelector(`.testimonial-card[data-match-town="${town}"]`);
      if (!t || e.target.closest('a')) return;
      t.scrollIntoView({behavior:'smooth', block:'center'});
      setTimeout(() => highlight(town), 400);
      setTimeout(() => highlight(null), 2600);
    });
  });
})();

// ============================
// CINEMATIC HERO VIDEO (lazy)
// Loads after window load; carousel remains the fallback for
// reduced-motion, save-data, and any playback failure.
// ============================
(function initHeroVideo() {
    const hero = document.querySelector('.hero');
    const carousel = document.querySelector('.hero-carousel');
    if (!hero || !carousel) return;
    // The carousel is the mobile hero. Do not download or autoplay the 2.95 MB
    // enhancement on small screens where it adds cost without improving the layout.
    if (window.matchMedia && window.matchMedia('(max-width: 768px)').matches) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const conn = navigator.connection;
    if (conn && (conn.saveData || /(^|-)2g/.test(conn.effectiveType || ''))) return;

    function load() {
        const v = document.createElement('video');
        v.className = 'hero-video';
        v.muted = true;
        v.loop = true;
        v.playsInline = true;
        v.setAttribute('muted', '');
        v.setAttribute('playsinline', '');
        v.setAttribute('aria-hidden', 'true');
        v.preload = 'metadata';
        v.src = '/videos/hero-loop.mp4';
        v.addEventListener('error', () => v.remove(), { once: true });
        carousel.insertAdjacentElement('afterend', v);
        const playback = v.play();
        if (playback && typeof playback.then === 'function') {
            playback.then(() => hero.classList.add('video-on')).catch(() => v.remove());
        } else {
            hero.classList.add('video-on');
        }
    }

    if (document.readyState === 'complete') setTimeout(load, 400);
    else window.addEventListener('load', () => setTimeout(load, 400));
})();
