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
function renderCommunities(filter = 'all', searchTerm = '') {
    const container = document.getElementById('communities-container');
    
    if (!communitiesData) {
        container.innerHTML = '<p class="loading">Community data could not be loaded.</p>';
        return;
    }
    
    container.innerHTML = '';
    
    let communitiesToShow = [];
    
    // Gather communities based on filter
    if (filter === 'all') {
        Object.keys(communitiesData).forEach(county => {
            communitiesData[county].forEach(community => {
                communitiesToShow.push({...community, county});
            });
        });
    } else {
        if (communitiesData[filter]) {
            communitiesData[filter].forEach(community => {
                communitiesToShow.push({...community, county: filter});
            });
        }
    }
    
    // Filter by search term
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        communitiesToShow = communitiesToShow.filter(c => 
            (c.town && c.town.toLowerCase().includes(term)) ||
            (c.description && c.description.toLowerCase().includes(term)) ||
            (c.schools && c.schools.toLowerCase().includes(term)) ||
            (c.primary_transit && c.primary_transit.toLowerCase().includes(term)) ||
            (c.county && c.county.toLowerCase().includes(term)) ||
            (c.notes && c.notes.toLowerCase().includes(term))
        );
    }
    
    // Render community cards
    if (communitiesToShow.length === 0) {
        container.innerHTML = '<p class="loading">No communities found matching your search.</p>';
        return;
    }
    
    communitiesToShow.forEach(community => {
        const card = document.createElement('div');
        card.className = 'community-card';
        
        // Truncate text for display
        const truncate = (text, length) => {
            if (!text) return '';
            return text.length > length ? text.substring(0, length) + '...' : text;
        };
        
        card.innerHTML = `
            <h3>${community.town || 'Unknown'}</h3>
            <span class="county-badge">${community.county} County</span>
            <p class="community-desc">${truncate(community.description, 150)}</p>
            <div class="community-details">
                ${community.schools ? `
                <div class="detail-item">
                    <span class="detail-label">Schools:</span> ${truncate(community.schools, 100)}
                </div>
                ` : ''}
                ${community.commute_to_nyc ? `
                <div class="detail-item">
                    <span class="detail-label">NYC Commute:</span> ${truncate(community.commute_to_nyc, 100)}
                </div>
                ` : ''}
                ${community.primary_transit ? `
                <div class="detail-item">
                    <span class="detail-label">Transit:</span> ${truncate(community.primary_transit, 100)}
                </div>
                ` : ''}
                ${community.highways ? `
                <div class="detail-item">
                    <span class="detail-label">Highways:</span> ${truncate(community.highways, 80)}
                </div>
                ` : ''}
            </div>
            ${renderTransitBadges(community)}
        `;
        container.appendChild(card);
    });
}

// Render transit badges based on transit type
function renderTransitBadges(community) {
    if (!community.primary_transit) return '';
    
    const transit = community.primary_transit.toLowerCase();
    let badges = '<div class="transit-badges">';
    
    if (transit.includes('path') || transit.includes('train') || transit.includes('nj transit') || transit.includes('rail')) {
        badges += '<span class="transit-badge">🚆 Train Access</span>';
    }
    if (transit.includes('bus')) {
        badges += '<span class="transit-badge">🚌 Bus Service</span>';
    }
    if (transit.includes('ferry')) {
        badges += '<span class="transit-badge">⛴️ Ferry Service</span>';
    }
    if (transit.includes('light rail')) {
        badges += '<span class="transit-badge">🚊 Light Rail</span>';
    }
    if (community.commute_to_nyc && (community.commute_to_nyc.includes('10') || community.commute_to_nyc.includes('15') || community.commute_to_nyc.includes('20'))) {
        badges += '<span class="transit-badge">⚡ Fast Commute</span>';
    }
    
    badges += '</div>';
    return badges;
}

// County tab functionality
document.querySelectorAll('.county-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Update active state
        document.querySelectorAll('.county-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        // Clear search
        const searchInput = document.getElementById('community-search');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Render communities
        renderCommunities(this.dataset.county);
    });
});

// Search functionality
const searchInput = document.getElementById('community-search');
if (searchInput) {
    let searchTimeout;
    searchInput.addEventListener('input', function(e) {
        // Debounce search
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const activeTab = document.querySelector('.county-tab.active');
            const countyFilter = activeTab ? activeTab.dataset.county : 'all';
            renderCommunities(countyFilter, e.target.value);
        }, 300);
    });
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

// Initialize - render all communities on page load
document.addEventListener('DOMContentLoaded', () => {
    renderCommunities('all');
});

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
