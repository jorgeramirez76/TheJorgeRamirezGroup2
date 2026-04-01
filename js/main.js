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
        photo: "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&q=80&fit=crop"
    },
    "Hudson": {
        towns: 12,
        highlight: "Hoboken, Jersey City, Weehawken, Bayonne",
        description: "Waterfront living with NYC skyline views, PATH access, and vibrant urban neighborhoods.",
        photo: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80&fit=crop"
    },
    "Morris": {
        towns: 37,
        highlight: "Chatham, Madison, Morristown, Florham Park",
        description: "Top-rated schools, green space, and premier commuter towns along the Morris & Essex Line.",
        photo: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600&q=80&fit=crop"
    },
    "Middlesex": {
        towns: 22,
        highlight: "Edison, Metuchen, Woodbridge, South Plainfield",
        description: "Diverse communities with strong schools, major highway access, and excellent value.",
        photo: "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600&q=80&fit=crop"
    },
    "Union": {
        towns: 21,
        highlight: "Summit, Westfield, Cranford, Scotch Plains",
        description: "Jorge's home turf — top commuter towns with outstanding schools and strong resale values.",
        photo: "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=600&q=80&fit=crop"
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

// Add fade-in animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.community-card, .stat-card, .info-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    fadeInObserver.observe(el);
});
