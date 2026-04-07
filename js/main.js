// Main JavaScript for Jorge Ramirez Real Estate Website

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
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
    });
    
    // Close menu when clicking a link
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            mobileMenuBtn.classList.remove('active');
        });
    });
}

// Communities rendering functionality
// County info for display
const countyInfo = {
    "Essex": {
        towns: 11,
        highlight: "Maplewood, South Orange, Montclair, Livingston",
        description: "Walkable downtowns, Midtown Direct trains, and diverse communities from Montclair to Livingston.",
        photo: "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=600&q=80&fit=crop"
    },
    "Hudson": {
        towns: 12,
        highlight: "Hoboken, Jersey City, Weehawken, Bayonne",
        description: "Waterfront living with NYC skyline views, PATH access, and vibrant urban neighborhoods.",
        photo: "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=600&q=80&fit=crop"
    },
    "Morris": {
        towns: 37,
        highlight: "Chatham, Madison, Morristown, Florham Park",
        description: "Top-rated schools, green space, and premier commuter towns along the Morris & Essex Line.",
        photo: "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&q=80&fit=crop"
    },
    "Middlesex": {
        towns: 22,
        highlight: "Edison, Metuchen, Woodbridge, South Plainfield",
        description: "Diverse communities with strong schools, major highway access, and excellent value.",
        photo: "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600&q=80&fit=crop"
    },
    "Union": {
        towns: 21,
        highlight: "Summit, Westfield, Cranford, Scotch Plains",
        description: "Jorge's home turf — top commuter towns with outstanding schools and strong resale values.",
        photo: "https://images.unsplash.com/photo-1598228723793-52759bba239c?w=600&q=80&fit=crop"
    }
};

let activeCounty = null;

function renderCountyCards() {
    const container = document.getElementById('communities-container');
    container.classList.remove('county-open');
    container.innerHTML = Object.keys(countyInfo).map(county => {
        const info = countyInfo[county];
        return `
        <div class="county-hero-card" data-county="${county}" onclick="openCounty('${county}')">
            <div class="county-hero-photo" style="background-image:url('${info.photo}')"></div>
            <div class="county-hero-body">
                <div class="county-hero-name">${county} County</div>
                <div class="county-hero-towns">${info.towns} Communities</div>
                <div class="county-hero-highlight">${info.highlight}</div>
                <p class="county-hero-desc">${info.description}</p>
                <div class="county-hero-cta">Explore ${county} County →</div>
            </div>
        </div>`;
    }).join('');
}

function openCounty(county) {
    activeCounty = county;
    const container = document.getElementById('communities-container');

    const towns = communitiesData[county] || [];

    const backBtn = `<div class="county-back-btn" onclick="closeCounty()">\u2190 All Counties</div>`;
    const countyTitle = `<div class="county-open-header">
        <h3>${county} County — ${towns.length} Communities</h3>
        <p>${countyInfo[county].description}</p>
    </div>`;

    const search = `<div class="county-search-wrap">
        <span class="search-icon">🔍</span>
        <input type="text" id="town-search" placeholder="Search towns in ${county} County..." oninput="filterTowns('${county}', this.value)">
    </div>`;

    const townCards = `<div class="communities-grid" id="towns-grid">` +
        towns.map(c => buildTownCard(c, county)).join('') +
    `</div>`;

    container.classList.add('county-open');
    container.innerHTML = backBtn + countyTitle + search + townCards;
    container.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function closeCounty() {
    activeCounty = null;
    renderCountyCards();
}

function filterTowns(county, term) {
    const grid = document.getElementById('towns-grid');
    if (!grid) return;
    const towns = communitiesData[county] || [];
    const filtered = term
        ? towns.filter(c => c.town.toLowerCase().includes(term.toLowerCase()) || (c.description && c.description.toLowerCase().includes(term.toLowerCase())))
        : towns;
    grid.innerHTML = filtered.map(c => buildTownCard(c, county)).join('');
}

function buildTownCard(c, county) {
    const slug = c.url_slug || c.town.toLowerCase().replace(/\s+/g, '-');
    const transitBadges = c.primary_transit
        ? `<div class="transit-badges"><span class="transit-badge">🚆 ${c.primary_transit.split(' ').slice(0,4).join(' ')}</span></div>`
        : '';
    return `
    <div class="community-card">
        <span class="county-badge">${county} County</span>
        <h3>${c.town}</h3>
        <p class="community-desc">${c.description || ''}</p>
        ${transitBadges}
        <div class="community-details">
            ${c.commute_to_nyc ? `<div class="detail-item"><span class="detail-label">NYC Commute:</span> ${c.commute_to_nyc}</div>` : ''}
            ${c.schools ? `<div class="detail-item"><span class="detail-label">Schools:</span> ${c.schools.substring(0,100)}...</div>` : ''}
        </div>
        <a href="communities/${slug}" class="community-link">Explore ${c.town} →</a>
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
    const slides = document.querySelectorAll('.hero-slide');
    if (slides.length === 0) return;

    // Load background images from data-bg attribute
    let loadedCount = 0;
    slides.forEach(slide => {
        const url = slide.getAttribute('data-bg');
        if (url) {
            const img = new Image();
            img.onload = () => {
                slide.style.backgroundImage = `url('${url}')`;
                loadedCount++;
            };
            img.onerror = () => {
                // Fallback to local hero image
                slide.style.backgroundImage = "url('images/hero.jpg')";
                loadedCount++;
            };
            img.src = url;
        }
    });

    // Set first slide background immediately as well (inline fallback)
    if (slides[0] && !slides[0].style.backgroundImage) {
        slides[0].style.backgroundImage = "url('images/hero.jpg')";
    }

    let current = 0;
    const INTERVAL = 5000;

    setInterval(() => {
        slides[current].classList.remove('active');
        current = (current + 1) % slides.length;
        slides[current].classList.add('active');
    }, INTERVAL);
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
