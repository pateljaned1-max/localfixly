/* LocalFix Main Application Router & UI Engine */

class LocalFixApp {
  constructor() {
    this.user = window.api.user;
    this.userLocation = { lat: 28.6139, lng: 77.2090, label: 'Connaught Place, Central City' };
    this.activeMap = null;
    this.mapMarkers = [];
    
    this.initEvents();
  }

  initEvents() {
    window.addEventListener('hashchange', () => this.handleRoute());
    window.addEventListener('DOMContentLoaded', () => {
      this.detectUserLocation(false);
      this.handleRoute();
    });

    window.addEventListener('auth:unauthorized', () => {
      this.user = null;
      this.updateNavbar();
      this.showToast('Session expired. Please log in again.', 'info');
      window.location.hash = '#/login';
    });

    window.addEventListener('auth:forbidden', (e) => {
      this.showToast(e.detail.error || 'Access denied: 403 Forbidden', 'error');
    });
  }

  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const iconMap = { success: 'fa-check-circle', error: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    toast.innerHTML = `<i class="fas ${iconMap[type] || 'fa-info-circle'}"></i> <span>${message}</span>`;
    
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  detectUserLocation(showNotice = true) {
    if ('geolocation' in navigator) {
      if (showNotice) this.showToast('Detecting your location...', 'info');
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.userLocation = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            label: 'Your Current Location'
          };
          if (showNotice) this.showToast('Location updated via GPS!', 'success');
          // Refresh search if on search page
          if (window.location.hash.startsWith('#/search')) {
            this.renderSearchPage();
          }
        },
        (err) => {
          if (showNotice) this.showToast('Could not fetch GPS. Using default city center.', 'info');
        },
        { timeout: 8000 }
      );
    }
  }

  updateNavbar() {
    this.user = window.api.user;
    const navLinks = document.getElementById('nav-links');
    const navActions = document.getElementById('nav-actions');
    if (!navLinks || !navActions) return;

    let linksHtml = `
      <a href="#/" class="${window.location.hash === '#/' || window.location.hash === '' ? 'active' : ''}">Home</a>
      <a href="#/services" class="${window.location.hash.startsWith('#/services') ? 'active' : ''}">Categories</a>
      <a href="#/search" class="${window.location.hash.startsWith('#/search') ? 'active' : ''}">Find Services</a>
      <a href="#/how-it-works">How It Works</a>
    `;

    if (this.user) {
      if (this.user.role === 'customer') {
        linksHtml += `<a href="#/dashboard/customer">My Bookings</a>`;
      } else if (this.user.role === 'provider') {
        linksHtml += `<a href="#/dashboard/provider">Provider Portal</a>`;
      } else if (this.user.role === 'admin') {
        linksHtml += `<a href="#/admin">Admin Panel</a>`;
      }
    }

    navLinks.innerHTML = linksHtml;

    if (this.user) {
      navActions.innerHTML = `
        <div class="user-pill" style="display:flex;align-items:center;gap:0.5rem;background:#f1f5f9;padding:0.35rem 0.85rem;border-radius:99px;font-size:0.85rem;font-weight:600;">
          <i class="fas fa-user-circle" style="color:var(--primary);font-size:1.1rem;"></i>
          <span>${this.user.name}</span>
          <span style="font-size:0.7rem;text-transform:uppercase;background:#dbeafe;color:#1e40af;padding:2px 6px;border-radius:4px;">${this.user.role}</span>
        </div>
        <button onclick="app.logout()" class="btn btn-secondary btn-sm"><i class="fas fa-sign-out-alt"></i> Logout</button>
      `;
    } else {
      navActions.innerHTML = `
        <a href="#/login" class="btn btn-secondary btn-sm">Log In</a>
        <a href="#/signup" class="btn btn-primary btn-sm">Sign Up</a>
      `;
    }
  }

  logout() {
    window.api.clearSession();
    this.user = null;
    this.showToast('Logged out successfully.', 'success');
    window.location.hash = '#/';
  }

  handleRoute() {
    this.updateNavbar();
    const hash = window.location.hash || '#/';
    const main = document.getElementById('main-content');
    if (!main) return;

    if (hash === '#/' || hash === '') {
      this.renderHomePage(main);
    } else if (hash.startsWith('#/services')) {
      this.renderCategoriesPage(main);
    } else if (hash.startsWith('#/search')) {
      this.renderSearchPage(main);
    } else if (hash.startsWith('#/provider/')) {
      const id = hash.split('/')[2];
      this.renderProviderProfilePage(main, id);
    } else if (hash === '#/login') {
      this.renderLoginPage(main);
    } else if (hash === '#/signup') {
      this.renderSignupPage(main);
    } else if (hash === '#/dashboard/customer') {
      this.renderCustomerDashboard(main);
    } else if (hash === '#/dashboard/provider') {
      this.renderProviderDashboard(main);
    } else if (hash.startsWith('#/admin')) {
      this.renderAdminPage(main);
    } else if (hash === '#/how-it-works') {
      this.renderStaticPage(main, 'how-it-works');
    } else if (hash === '#/about') {
      this.renderStaticPage(main, 'about');
    } else if (hash === '#/terms') {
      this.renderStaticPage(main, 'terms');
    } else if (hash === '#/privacy') {
      this.renderStaticPage(main, 'privacy');
    } else {
      main.innerHTML = `<div class="section-container" style="text-align:center;"><h2>Page Not Found</h2><p><a href="#/">Return Home</a></p></div>`;
    }

    window.scrollTo(0, 0);
  }

  // --- HOME PAGE ---
  async renderHomePage(container) {
    container.innerHTML = `
      <section class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">Find Trusted Local Services <span>Near You</span></h1>
          <p class="hero-subhead">Plumbers, electricians, cleaners, mechanics and more — find available professionals in your area within 90 seconds.</p>

          <form id="hero-search-form" class="hero-search-card" onsubmit="app.onHeroSearch(event)">
            <div class="search-field-group">
              <i class="fas fa-tools"></i>
              <select id="hero-category-select" class="search-select">
                <option value="">Select Service Category...</option>
              </select>
            </div>
            
            <div class="search-field-group">
              <i class="fas fa-map-marker-alt"></i>
              <input type="text" id="hero-location-input" class="search-input" value="${this.userLocation.label}" placeholder="City or location...">
            </div>

            <button type="button" class="btn-geolocation" onclick="app.detectUserLocation(true)">
              <i class="fas fa-crosshairs"></i> Use My Location
            </button>

            <button type="submit" class="btn btn-primary btn-lg" style="flex-shrink:0;">
              <i class="fas fa-search"></i> Find Nearby Services
            </button>
          </form>

          <div class="hero-live-strip">
            <div class="pulse-dot"></div>
            <span><strong>1,240+</strong> verified local professionals &middot; <strong>340+</strong> available now</span>
          </div>
        </div>
      </section>

      <section class="section-container">
        <div class="section-header">
          <h2 class="section-title">Popular Service Categories</h2>
          <p class="section-subtitle">Browse trusted local experts available for instant dispatch</p>
        </div>
        <div id="home-category-grid" class="category-grid">
          <div style="grid-column:1/-1;text-align:center;padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading categories...</div>
        </div>
      </section>

      <section class="trust-strip">
        <div class="trust-container">
          <div class="trust-item">
            <div class="trust-icon"><i class="fas fa-user-shield"></i></div>
            <div>
              <h4 style="font-size:1.05rem;">100% Verified Providers</h4>
              <p style="font-size:0.85rem;color:var(--text-muted);">Background checked and document verified by our admin safety team.</p>
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-icon"><i class="fas fa-star"></i></div>
            <div>
              <h4 style="font-size:1.05rem;">Real Customer Reviews</h4>
              <p style="font-size:0.85rem;color:var(--text-muted);">Only verified customers can leave post-completion ratings and feedback.</p>
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-icon"><i class="fas fa-bolt"></i></div>
            <div>
              <h4 style="font-size:1.05rem;">Instant Direct Contact</h4>
              <p style="font-size:0.85rem;color:var(--text-muted);">Call or WhatsApp available providers directly or submit a formal job request.</p>
            </div>
          </div>
        </div>
      </section>
    `;

    try {
      const res = await window.api.getCategories();
      const select = document.getElementById('hero-category-select');
      const grid = document.getElementById('home-category-grid');

      if (select && res.categories) {
        select.innerHTML = `<option value="">Select Service Category...</option>` + 
          res.categories.map(c => `<option value="${c.slug}">${c.icon} ${c.name}</option>`).join('');
      }

      if (grid && res.categories) {
        grid.innerHTML = res.categories.map(c => `
          <div class="category-card" onclick="window.location.hash='#/search?category=${c.slug}'">
            <div class="category-icon-box">${c.icon}</div>
            <div class="category-name">${c.name}</div>
            <div class="category-count">
              <i class="fas fa-circle" style="font-size:0.5rem;color:var(--success);"></i>
              ${c.available_provider_count > 0 ? `${c.available_provider_count} available now` : 'Book in advance'}
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  onHeroSearch(e) {
    e.preventDefault();
    const cat = document.getElementById('hero-category-select').value;
    window.location.hash = `#/search?category=${encodeURIComponent(cat)}`;
  }

  // --- CATEGORIES PAGE ---
  async renderCategoriesPage(container) {
    container.innerHTML = `
      <div class="section-container">
        <div class="section-header">
          <h1 class="section-title">All Service Categories</h1>
          <p class="section-subtitle">Select a service category to discover nearby available providers</p>
        </div>
        <div id="all-category-grid" class="category-grid">
          <div style="grid-column:1/-1;text-align:center;padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>
        </div>
      </div>
    `;

    try {
      const res = await window.api.getCategories();
      const grid = document.getElementById('all-category-grid');
      if (grid && res.categories) {
        grid.innerHTML = res.categories.map(c => `
          <div class="category-card" onclick="window.location.hash='#/search?category=${c.slug}'">
            <div class="category-icon-box">${c.icon}</div>
            <div class="category-name">${c.name}</div>
            <p style="font-size:0.85rem;color:var(--text-muted);">${c.description}</p>
            <div class="category-count">
              <i class="fas fa-circle" style="font-size:0.5rem;color:var(--success);"></i>
              ${c.available_provider_count} available nearby
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- SEARCH RESULTS PAGE ---
  async renderSearchPage(container) {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const currentCat = urlParams.get('category') || '';
    const currentRadius = urlParams.get('radius') || '10';
    const currentSort = urlParams.get('sort_by') || 'availability';
    const currentAvail = urlParams.get('available_now') || 'false';

    container.innerHTML = `
      <div class="search-page-container">
        <!-- Sticky Filter Bar -->
        <div class="filter-bar">
          <div class="filter-controls">
            <div class="filter-item">
              <i class="fas fa-filter" style="color:var(--primary);"></i>
              <strong>Filters:</strong>
            </div>
            <select id="filter-category" class="filter-select" onchange="app.triggerSearchFilter()">
              <option value="">All Categories</option>
            </select>
            
            <select id="filter-radius" class="filter-select" onchange="app.triggerSearchFilter()">
              <option value="1" ${currentRadius==='1'?'selected':''}>Within 1 km</option>
              <option value="3" ${currentRadius==='3'?'selected':''}>Within 3 km</option>
              <option value="5" ${currentRadius==='5'?'selected':''}>Within 5 km</option>
              <option value="10" ${currentRadius==='10'?'selected':''}>Within 10 km</option>
              <option value="25" ${currentRadius==='25'?'selected':''}>Within 25 km</option>
            </select>

            <label class="filter-item" style="cursor:pointer;user-select:none;">
              <input type="checkbox" id="filter-available-now" ${currentAvail==='true'?'checked':''} onchange="app.triggerSearchFilter()">
              <span>🟢 Available Now</span>
            </label>

            <label class="filter-item" style="cursor:pointer;user-select:none;">
              <input type="checkbox" id="filter-verified-only" onchange="app.triggerSearchFilter()">
              <span><i class="fas fa-check-circle" style="color:var(--primary);"></i> Verified Only</span>
            </label>
          </div>

          <div class="filter-controls">
            <div class="filter-item">
              <span>Sort by:</span>
              <select id="filter-sort" class="filter-select" onchange="app.triggerSearchFilter()">
                <option value="availability" ${currentSort==='availability'?'selected':''}>Availability First</option>
                <option value="distance" ${currentSort==='distance'?'selected':''}>Distance (Nearest)</option>
                <option value="rating" ${currentSort==='rating'?'selected':''}>Highest Rating</option>
                <option value="price" ${currentSort==='price'?'selected':''}>Lowest Price</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Split Grid (List & Map) -->
        <div class="search-results-grid">
          <div class="provider-list-container">
            <div id="results-count-bar" style="margin-bottom:1rem;font-size:0.9rem;color:var(--text-muted);">
              Searching providers...
            </div>
            <div id="provider-cards-list" class="provider-list">
              <div style="text-align:center;padding:3rem;"><i class="fas fa-spinner fa-spin fa-2x"></i></div>
            </div>
          </div>

          <div class="map-container-wrapper">
            <div id="leaflet-map"></div>
          </div>
        </div>
      </div>
    `;

    // Populate category dropdown
    try {
      const catsRes = await window.api.getCategories();
      const select = document.getElementById('filter-category');
      if (select && catsRes.categories) {
        select.innerHTML = `<option value="">All Categories</option>` +
          catsRes.categories.map(c => `<option value="${c.slug}" ${c.slug===currentCat?'selected':''}>${c.icon} ${c.name}</option>`).join('');
      }
    } catch(err) {}

    // Init Leaflet Map
    this.initMap();

    // Execute Search
    this.executeSearch();
  }

  triggerSearchFilter() {
    this.executeSearch();
  }

  async executeSearch() {
    const cat = document.getElementById('filter-category')?.value || '';
    const radius = document.getElementById('filter-radius')?.value || '10';
    const availableNow = document.getElementById('filter-available-now')?.checked ? 'true' : 'false';
    const verifiedOnly = document.getElementById('filter-verified-only')?.checked ? 'true' : 'false';
    const sort = document.getElementById('filter-sort')?.value || 'availability';

    const container = document.getElementById('provider-cards-list');
    const countBar = document.getElementById('results-count-bar');
    if (container) container.innerHTML = `<div style="text-align:center;padding:3rem;"><i class="fas fa-spinner fa-spin fa-2x"></i></div>`;

    try {
      const res = await window.api.searchProviders({
        category: cat,
        lat: this.userLocation.lat,
        lng: this.userLocation.lng,
        radius: radius,
        available_now: availableNow,
        verified_only: verifiedOnly,
        sort_by: sort
      });

      const providers = res.providers || [];
      if (countBar) {
        countBar.innerHTML = `Showing <strong>${providers.length}</strong> providers within <strong>${radius} km</strong> of your location.`;
      }

      if (providers.length === 0) {
        if (container) {
          container.innerHTML = `
            <div class="empty-state">
              <div class="empty-icon"><i class="fas fa-search-location"></i></div>
              <h3>No providers found within ${radius} km</h3>
              <p style="color:var(--text-muted);margin-bottom:1.5rem;">Try expanding your search radius or turning off active filters.</p>
              <button class="btn btn-primary" onclick="document.getElementById('filter-radius').value='25'; app.executeSearch();">
                <i class="fas fa-expand-arrows-alt"></i> Search 25 km Radius
              </button>
            </div>
          `;
        }
        this.updateMapMarkers([]);
        return;
      }

      if (container) {
        container.innerHTML = providers.map(p => this.renderProviderCardHTML(p)).join('');
      }

      this.updateMapMarkers(providers);

    } catch (err) {
      if (container) container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:2rem;">Failed to load search results: ${err.message}</div>`;
    }
  }

  renderProviderCardHTML(p) {
    const statusMap = {
      available: { class: 'available', label: '🟢 Available Now', icon: 'fa-circle' },
      busy: { class: 'busy', label: '🟡 Busy', icon: 'fa-clock' },
      offline: { class: 'offline', label: '🔴 Offline', icon: 'fa-moon' }
    };
    const st = statusMap[p.availability_status] || statusMap.offline;

    const catsHtml = (p.categories || []).map(c => `<span style="font-size:0.75rem;background:#f1f5f9;padding:2px 8px;border-radius:4px;">${c.icon} ${c.name}</span>`).join(' ');

    return `
      <div class="provider-card">
        <div class="provider-avatar-box">
          <i class="fas fa-user-cog"></i>
        </div>
        <div class="provider-details">
          <div class="provider-header-row">
            <div>
              <span class="provider-title">${p.business_name || p.provider_user_name}</span>
              ${p.verified ? `<span class="verified-badge"><i class="fas fa-check-circle"></i> Verified</span>` : ''}
            </div>
            <span class="status-badge ${st.class}">${st.label}</span>
          </div>

          <div class="provider-meta">
            <span class="rating-stars"><i class="fas fa-star"></i> ${p.avg_rating || '5.0'} (${p.review_count || 0} reviews)</span>
            <span>&middot;</span>
            <span><i class="fas fa-map-marker-alt" style="color:var(--danger);"></i> <strong>${p.distance_km} km</strong> away</span>
            <span>&middot;</span>
            <span><i class="fas fa-briefcase"></i> ${p.experience_years} yrs exp</span>
          </div>

          <div style="margin:0.25rem 0;">${catsHtml}</div>
          <p style="font-size:0.85rem;color:var(--text-muted);">${p.description ? p.description.substring(0, 110) + '...' : ''}</p>

          <div style="font-size:0.85rem;font-weight:700;color:var(--primary);margin-top:0.2rem;">
            ${p.pricing_note || `$${p.starting_price} starting price`}
          </div>

          <div class="provider-actions">
            <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/provider/${p.id}'">View Profile</button>
            <a href="tel:${p.provider_phone}" class="btn btn-outline-primary btn-sm"><i class="fas fa-phone"></i> Call</a>
            <a href="https://wa.me/${(p.provider_phone||'').replace(/[^0-9]/g,'')}?text=Hi, I saw your profile on LocalFix." target="_blank" class="btn btn-whatsapp btn-sm"><i class="fab fa-whatsapp"></i> WhatsApp</a>
            <button class="btn btn-primary btn-sm" onclick="app.openRequestModal(${p.id}, '${p.business_name.replace(/'/g,"\\'")}')"><i class="fas fa-paper-plane"></i> Request Service</button>
          </div>
        </div>
      </div>
    `;
  }

  initMap() {
    const mapEl = document.getElementById('leaflet-map');
    if (!mapEl) return;

    if (this.activeMap) {
      this.activeMap.remove();
    }

    this.activeMap = L.map('leaflet-map').setView([this.userLocation.lat, this.userLocation.lng], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.activeMap);

    // User pin marker
    L.circleMarker([this.userLocation.lat, this.userLocation.lng], {
      radius: 9,
      fillColor: '#2563eb',
      color: '#ffffff',
      weight: 3,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(this.activeMap).bindPopup("<b>Your Search Location</b>");
  }

  updateMapMarkers(providers) {
    if (!this.activeMap) return;

    this.mapMarkers.forEach(m => this.activeMap.removeLayer(m));
    this.mapMarkers = [];

    const bounds = L.latLngBounds([[this.userLocation.lat, this.userLocation.lng]]);

    providers.forEach(p => {
      const colorMap = { available: '#10b981', busy: '#f59e0b', offline: '#64748b' };
      const marker = L.circleMarker([p.latitude, p.longitude], {
        radius: 8,
        fillColor: colorMap[p.availability_status] || '#64748b',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 0.9
      }).addTo(this.activeMap);

      marker.bindPopup(`
        <div style="font-family:var(--font-body);padding:4px;">
          <strong style="font-size:0.95rem;">${p.business_name}</strong><br/>
          <span style="font-size:0.8rem;color:#64748b;">${p.distance_km} km away &middot; ⭐ ${p.avg_rating}</span><br/>
          <a href="#/provider/${p.id}" style="display:inline-block;margin-top:6px;font-weight:700;color:#2563eb;font-size:0.85rem;">View Profile &rarr;</a>
        </div>
      `);

      this.mapMarkers.push(marker);
      bounds.extend([p.latitude, p.longitude]);
    });

    if (providers.length > 0) {
      this.activeMap.fitBounds(bounds, { padding: [30, 30] });
    }
  }

  // --- PROVIDER PROFILE PAGE ---
  async renderProviderProfilePage(container, id) {
    container.innerHTML = `<div style="text-align:center;padding:4rem;"><i class="fas fa-spinner fa-spin fa-2x"></i> Loading profile...</div>`;

    try {
      const res = await window.api.getProviderProfile(id);
      const p = res.provider;

      const statusMap = {
        available: { class: 'available', label: '🟢 Available Now' },
        busy: { class: 'busy', label: '🟡 Busy' },
        offline: { class: 'offline', label: '🔴 Offline' }
      };
      const st = statusMap[p.availability_status] || statusMap.offline;

      const catsHtml = (p.categories || []).map(c => `<span style="background:#e2e8f0;padding:4px 10px;border-radius:99px;font-size:0.85rem;font-weight:600;">${c.icon} ${c.name}</span>`).join(' ');

      const breakdown = p.rating_breakdown || {5:0,4:0,3:0,2:0,1:0};
      const totalRev = p.review_count || 1;

      const reviewsHtml = (p.reviews || []).length > 0 ? (p.reviews || []).map(r => `
        <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-md);padding:1rem;margin-bottom:1rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
            <strong>${r.customer_name}</strong>
            <span class="rating-stars"><i class="fas fa-star"></i> ${r.rating}.0</span>
          </div>
          <p style="font-size:0.9rem;color:var(--text-main);">${r.review}</p>
          <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.4rem;">Submitted on ${r.created_at}</div>
        </div>
      `).join('') : `<p style="color:var(--text-muted);">No reviews written yet.</p>`;

      const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
      const hoursHtml = (p.hours || []).map(h => `
        <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #f1f5f9;font-size:0.85rem;">
          <span>${daysOfWeek[h.day_of_week]}</span>
          <strong>${h.is_closed ? 'Closed' : `${h.open_time} - ${h.close_time}`}</strong>
        </div>
      `).join('');

      container.innerHTML = `
        <div class="profile-hero">
          <div class="profile-container">
            <div class="profile-header-card">
              <div class="profile-avatar-lg">
                <i class="fas fa-user-cog"></i>
              </div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem;">
                  <h1 style="font-size:2rem;">${p.business_name}</h1>
                  ${p.verified ? `<span class="verified-badge"><i class="fas fa-check-circle"></i> Verified Provider</span>` : ''}
                  <span class="status-badge ${st.class}">${st.label}</span>
                </div>
                <p style="color:var(--text-muted);font-size:1rem;margin-bottom:0.75rem;">Owner: ${p.provider_user_name} &middot; Base: ${p.address_text} (${p.service_radius_km} km service radius)</p>
                <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1rem;">${catsHtml}</div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--primary);">
                  ${p.pricing_note || `$${p.starting_price} base charge`}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="profile-grid-layout">
          <div>
            <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1.5rem;">
              <h3 style="margin-bottom:1rem;">About Business & Services</h3>
              <p style="color:var(--text-main);line-height:1.6;">${p.description || 'No description provided.'}</p>
            </div>

            <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1.5rem;">
              <h3 style="margin-bottom:1rem;">Ratings & Customer Reviews</h3>
              <div style="display:flex;gap:2rem;align-items:center;margin-bottom:1.5rem;flex-wrap:wrap;">
                <div style="text-align:center;">
                  <div style="font-size:3rem;font-weight:800;color:var(--text-main);line-height:1;">${p.avg_rating || '0.0'}</div>
                  <div class="rating-stars" style="margin:0.25rem 0;"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                  <div style="font-size:0.85rem;color:var(--text-muted);">${p.review_count} total reviews</div>
                </div>

                <div style="flex:1;min-width:200px;">
                  ${[5,4,3,2,1].map(star => `
                    <div class="rating-bar-row">
                      <span>${star} ★</span>
                      <div class="rating-bar-outer">
                        <div class="rating-bar-inner" style="width:${((breakdown[star]||0)/totalRev)*100}%;"></div>
                      </div>
                      <span>${breakdown[star]||0}</span>
                    </div>
                  `).join('')}
                </div>
              </div>

              ${reviewsHtml}
            </div>
          </div>

          <div>
            <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1.5rem;position:sticky;top:90px;">
              <h3 style="margin-bottom:1rem;">Contact & Booking</h3>
              
              <button class="btn btn-primary btn-lg" style="width:100%;margin-bottom:0.75rem;" onclick="app.openRequestModal(${p.id}, '${p.business_name.replace(/'/g,"\\'")}')">
                <i class="fas fa-paper-plane"></i> Request Service Now
              </button>

              <a href="tel:${p.provider_phone}" class="btn btn-secondary" style="width:100%;margin-bottom:0.75rem;">
                <i class="fas fa-phone"></i> Call ${p.provider_phone}
              </a>

              <a href="https://wa.me/${(p.provider_phone||'').replace(/[^0-9]/g,'')}?text=Hi, I saw your profile on LocalFix." target="_blank" class="btn btn-whatsapp" style="width:100%;margin-bottom:1.5rem;">
                <i class="fab fa-whatsapp"></i> Chat on WhatsApp
              </a>

              <h4 style="font-size:0.95rem;margin-bottom:0.5rem;">Working Hours</h4>
              ${hoursHtml}
            </div>
          </div>
        </div>
      `;
    } catch(err) {
      container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:3rem;">Failed to load profile: ${err.message}</div>`;
    }
  }

  // --- SERVICE REQUEST MODAL ---
  async openRequestModal(providerId, providerName) {
    if (!this.user) {
      this.showToast('Please log in as a customer to request a service.', 'info');
      window.location.hash = '#/login';
      return;
    }
    if (this.user.role !== 'customer') {
      this.showToast('Only customer accounts can submit service requests.', 'error');
      return;
    }

    let catsRes = { categories: [] };
    try {
      catsRes = await window.api.getCategories();
    } catch(e) {}

    const modalHtml = `
      <div id="request-modal" class="modal-backdrop" onclick="if(event.target===this) app.closeModal('request-modal')">
        <div class="modal-content">
          <div class="modal-header">
            <h3><i class="fas fa-paper-plane" style="color:var(--primary);"></i> Request Service</h3>
            <button onclick="app.closeModal('request-modal')" style="background:none;border:none;font-size:1.2rem;cursor:pointer;"><i class="fas fa-times"></i></button>
          </div>
          <form onsubmit="app.submitServiceRequest(event, ${providerId})">
            <div class="modal-body">
              <p style="margin-bottom:1rem;font-size:0.9rem;color:var(--text-muted);">
                Sending service request to <strong>${providerName}</strong>
              </p>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Select Service Required *</label>
                <select id="req-category-id" class="search-select" required>
                  ${catsRes.categories.map(c => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join('')}
                </select>
              </div>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Describe your problem *</label>
                <textarea id="req-description" class="search-input" style="height:90px;resize:vertical;" placeholder="E.g., Kitchen tap leaking continuously from main valve..." required></textarea>
              </div>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Service Address / Location *</label>
                <input type="text" id="req-address" class="search-input" value="${this.userLocation.label}" placeholder="Street, Flat #, Landmark" required />
              </div>

              <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem;">
                <div>
                  <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Preferred Date *</label>
                  <input type="date" id="req-date" class="search-input" value="${new Date().toISOString().split('T')[0]}" required />
                </div>
                <div>
                  <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Preferred Time *</label>
                  <input type="time" id="req-time" class="search-input" value="10:00" required />
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" onclick="app.closeModal('request-modal')">Cancel</button>
              <button type="submit" class="btn btn-primary"><i class="fas fa-check-circle"></i> Send Service Request</button>
            </div>
          </form>
        </div>
      </div>
    `;

    const div = document.createElement('div');
    div.id = 'modal-container';
    div.innerHTML = modalHtml;
    document.body.appendChild(div);
  }

  closeModal(id) {
    const el = document.getElementById(id) || document.getElementById('modal-container');
    if (el) el.remove();
  }

  async submitServiceRequest(e, providerId) {
    e.preventDefault();
    const catId = document.getElementById('req-category-id').value;
    const desc = document.getElementById('req-description').value;
    const address = document.getElementById('req-address').value;
    const date = document.getElementById('req-date').value;
    const time = document.getElementById('req-time').value;

    try {
      const res = await window.api.createBooking({
        provider_id: providerId,
        category_id: catId,
        description: desc,
        address_text: address,
        preferred_date: date,
        preferred_time: time,
        location_lat: this.userLocation.lat,
        location_lng: this.userLocation.lng
      });

      this.closeModal('request-modal');
      this.showToast('Service request sent successfully!', 'success');
      window.location.hash = '#/dashboard/customer';
    } catch(err) {
      this.showToast(err.message || 'Failed to submit request', 'error');
    }
  }

  // --- AUTH PAGES ---
  renderLoginPage(container) {
    container.innerHTML = `
      <div class="section-container" style="max-width:440px;">
        <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:2rem;box-shadow:var(--shadow-md);">
          <h2 style="text-align:center;margin-bottom:0.5rem;">Welcome Back</h2>
          <p style="text-align:center;color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem;">Log in to your LocalFix account</p>

          <form onsubmit="app.handleLoginSubmit(event)">
            <div style="margin-bottom:1rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Email Address</label>
              <input type="email" id="login-email" class="search-input" placeholder="name@example.com" required />
            </div>

            <div style="margin-bottom:1.5rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Password</label>
              <input type="password" id="login-password" class="search-input" placeholder="••••••••" required />
            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;padding:0.75rem;"><i class="fas fa-sign-in-alt"></i> Log In</button>
          </form>

          <div style="margin-top:1.5rem;text-align:center;font-size:0.85rem;color:var(--text-muted);">
            Don't have an account? <a href="#/signup" style="font-weight:700;">Sign Up</a>
          </div>

          <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid #f1f5f9;font-size:0.8rem;color:var(--text-muted);">
            <strong>Demo Credentials:</strong><br/>
            Customer: <code>customer@example.com</code> / <code>Password123!</code><br/>
            Provider: <code>rajesh.plumber@example.com</code> / <code>Password123!</code><br/>
            Admin: <code>admin@example.com</code> / <code>AdminPassword123!</code>
          </div>
        </div>
      </div>
    `;
  }

  async handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
      const res = await window.api.login(email, password);
      window.api.setSession(res.token, res.user);
      this.user = res.user;
      this.showToast(`Welcome back, ${res.user.name}!`, 'success');
      
      if (res.user.role === 'provider') {
        window.location.hash = '#/dashboard/provider';
      } else if (res.user.role === 'admin') {
        window.location.hash = '#/admin';
      } else {
        window.location.hash = '#/dashboard/customer';
      }
    } catch(err) {
      this.showToast(err.message || 'Login failed', 'error');
    }
  }

  renderSignupPage(container) {
    container.innerHTML = `
      <div class="section-container" style="max-width:520px;">
        <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:2rem;box-shadow:var(--shadow-md);">
          <h2 style="text-align:center;margin-bottom:0.5rem;">Create an Account</h2>
          <p style="text-align:center;color:var(--text-muted);font-size:0.9rem;margin-bottom:1.5rem;">Select your role to get started</p>

          <form onsubmit="app.handleSignupSubmit(event)">
            <div style="margin-bottom:1.25rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">I want to register as a *</label>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
                <label style="border:2px solid var(--primary);padding:0.75rem;border-radius:var(--radius-md);cursor:pointer;text-align:center;font-weight:600;">
                  <input type="radio" name="signup-role" value="customer" checked onchange="app.toggleProviderSignupFields(false)" /> Customer
                </label>
                <label style="border:2px solid var(--card-border);padding:0.75rem;border-radius:var(--radius-md);cursor:pointer;text-align:center;font-weight:600;">
                  <input type="radio" name="signup-role" value="provider" onchange="app.toggleProviderSignupFields(true)" /> Service Provider
                </label>
              </div>
            </div>

            <div style="margin-bottom:1rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Full Name *</label>
              <input type="text" id="signup-name" class="search-input" placeholder="Janendra Patel" required />
            </div>

            <div style="margin-bottom:1rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Email Address *</label>
              <input type="email" id="signup-email" class="search-input" placeholder="janendra@example.com" required />
            </div>

            <div style="margin-bottom:1rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Phone Number *</label>
              <input type="tel" id="signup-phone" class="search-input" placeholder="+91 98765 43210" required />
            </div>

            <div style="margin-bottom:1rem;">
              <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Password *</label>
              <input type="password" id="signup-password" class="search-input" placeholder="••••••••" required />
            </div>

            <!-- Provider specific fields -->
            <div id="provider-extra-fields" style="display:none;border-top:1px solid #e2e8f0;padding-top:1rem;margin-top:1rem;">
              <h4 style="margin-bottom:0.75rem;">Provider Profile Details</h4>
              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Business / Trade Name</label>
                <input type="text" id="signup-business" class="search-input" placeholder="Apex Plumbing Solutions" />
              </div>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Years of Experience</label>
                <input type="number" id="signup-exp" class="search-input" value="5" min="0" />
              </div>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Starting Price ($)</label>
                <input type="number" id="signup-price" class="search-input" value="30" min="0" />
              </div>
            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;padding:0.75rem;margin-top:1rem;"><i class="fas fa-user-plus"></i> Create Account</button>
          </form>
        </div>
      </div>
    `;
  }

  toggleProviderSignupFields(show) {
    const el = document.getElementById('provider-extra-fields');
    if (el) el.style.display = show ? 'block' : 'none';
  }

  async handleSignupSubmit(e) {
    e.preventDefault();
    const role = document.querySelector('input[name="signup-role"]:checked').value;
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const phone = document.getElementById('signup-phone').value;
    const password = document.getElementById('signup-password').value;

    const payload = { name, email, phone, password, role };

    if (role === 'provider') {
      payload.business_name = document.getElementById('signup-business').value;
      payload.experience_years = document.getElementById('signup-exp').value;
      payload.starting_price = document.getElementById('signup-price').value;
      payload.latitude = this.userLocation.lat;
      payload.longitude = this.userLocation.lng;
    }

    try {
      const res = await window.api.signup(payload);
      window.api.setSession(res.token, res.user);
      this.user = res.user;
      this.showToast('Account created successfully!', 'success');
      window.location.hash = role === 'provider' ? '#/dashboard/provider' : '#/dashboard/customer';
    } catch(err) {
      this.showToast(err.message || 'Signup failed', 'error');
    }
  }

  // --- CUSTOMER DASHBOARD ---
  async renderCustomerDashboard(container) {
    if (!this.user || this.user.role !== 'customer') {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `<div style="text-align:center;padding:4rem;"><i class="fas fa-spinner fa-spin fa-2x"></i> Loading your bookings...</div>`;

    try {
      const res = await window.api.getBookings();
      const bookings = res.bookings || [];

      const bookingsListHtml = bookings.length > 0 ? bookings.map(b => `
        <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1.25rem;box-shadow:var(--shadow-sm);">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem;margin-bottom:1rem;">
            <div>
              <h3 style="font-size:1.15rem;">${b.category_icon || '🔧'} ${b.category_name} &middot; ${b.business_name}</h3>
              <p style="font-size:0.85rem;color:var(--text-muted);">Provider: ${b.provider_name} &middot; Scheduled: ${b.preferred_date} at ${b.preferred_time}</p>
            </div>
            <span class="status-badge ${b.status}">${b.status.replace('_', ' ').toUpperCase()}</span>
          </div>

          <!-- Stepper UI -->
          <div class="stepper-container">
            <div class="stepper-step ${['pending','accepted','in_progress','completed'].includes(b.status)?'completed':''}">
              <div class="step-circle"><i class="fas fa-paper-plane"></i></div>
              <div class="step-label">Requested</div>
            </div>
            <div class="stepper-step ${['accepted','in_progress','completed'].includes(b.status)?'completed':b.status==='pending'?'active':''}">
              <div class="step-circle"><i class="fas fa-user-check"></i></div>
              <div class="step-label">Accepted</div>
            </div>
            <div class="stepper-step ${['in_progress','completed'].includes(b.status)?'completed':b.status==='accepted'?'active':''}">
              <div class="step-circle"><i class="fas fa-tools"></i></div>
              <div class="step-label">In Progress</div>
            </div>
            <div class="stepper-step ${b.status==='completed'?'completed':''}">
              <div class="step-circle"><i class="fas fa-check-double"></i></div>
              <div class="step-label">Completed</div>
            </div>
          </div>

          <p style="font-size:0.9rem;background:#f8fafc;padding:0.75rem;border-radius:var(--radius-md);margin-bottom:1rem;">
            <strong>Problem Note:</strong> ${b.description}
          </p>

          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <div>
              ${['accepted','in_progress','completed'].includes(b.status) ? `
                <a href="tel:${b.provider_phone}" class="btn btn-outline-primary btn-sm"><i class="fas fa-phone"></i> Call Provider (${b.provider_phone})</a>
              ` : '<span style="font-size:0.8rem;color:var(--text-muted);">Contact details unlock upon provider acceptance</span>'}
            </div>

            <div>
              ${['pending','accepted'].includes(b.status) ? `
                <button class="btn btn-danger btn-sm" onclick="app.cancelBookingPrompt(${b.id})">Cancel Request</button>
              ` : ''}

              ${b.status === 'completed' && !b.review_id ? `
                <button class="btn btn-success btn-sm" onclick="app.openReviewModal(${b.id}, '${b.business_name.replace(/'/g,"\\'")}')">
                  <i class="fas fa-star"></i> Leave Review
                </button>
              ` : ''}

              ${b.review_id ? `<span style="font-size:0.85rem;color:var(--success);font-weight:700;"><i class="fas fa-check-circle"></i> Review Submitted (${b.review_rating}★)</span>` : ''}
            </div>
          </div>
        </div>
      `).join('') : `
        <div class="empty-state">
          <div class="empty-icon"><i class="fas fa-calendar-times"></i></div>
          <h3>No service bookings yet</h3>
          <p style="color:var(--text-muted);margin-bottom:1.5rem;">Find a nearby provider and submit a request in under 90 seconds.</p>
          <a href="#/search" class="btn btn-primary"><i class="fas fa-search"></i> Find Services</a>
        </div>
      `;

      container.innerHTML = `
        <div class="dashboard-container">
          <div class="dashboard-header">
            <div>
              <h2>Customer Dashboard</h2>
              <p style="color:var(--text-muted);font-size:0.9rem;">Track active jobs and view booking history</p>
            </div>
            <a href="#/search" class="btn btn-primary"><i class="fas fa-search"></i> Request New Service</a>
          </div>

          ${bookingsListHtml}
        </div>
      `;

    } catch(err) {
      container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:3rem;">Failed to load bookings: ${err.message}</div>`;
    }
  }

  async cancelBookingPrompt(id) {
    const reason = prompt('Please enter a reason for cancellation:');
    if (!reason) return;
    try {
      await window.api.cancelBooking(id, reason);
      this.showToast('Booking cancelled.', 'info');
      this.renderCustomerDashboard(document.getElementById('main-content'));
    } catch(err) {
      this.showToast(err.message || 'Failed to cancel', 'error');
    }
  }

  openReviewModal(bookingId, businessName) {
    const modalHtml = `
      <div id="review-modal" class="modal-backdrop" onclick="if(event.target===this) app.closeModal('review-modal')">
        <div class="modal-content">
          <div class="modal-header">
            <h3><i class="fas fa-star" style="color:#f59e0b;"></i> Leave a Review</h3>
            <button onclick="app.closeModal('review-modal')" style="background:none;border:none;font-size:1.2rem;cursor:pointer;"><i class="fas fa-times"></i></button>
          </div>
          <form onsubmit="app.submitReview(event, ${bookingId})">
            <div class="modal-body">
              <p style="margin-bottom:1rem;color:var(--text-muted);">How was your experience with <strong>${businessName}</strong>?</p>
              
              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Rating *</label>
                <select id="review-rating" class="search-select" required>
                  <option value="5">5 Stars — Excellent Service</option>
                  <option value="4">4 Stars — Very Good</option>
                  <option value="3">3 Stars — Average</option>
                  <option value="2">2 Stars — Poor</option>
                  <option value="1">1 Star — Unacceptable</option>
                </select>
              </div>

              <div style="margin-bottom:1rem;">
                <label style="display:block;font-size:0.85rem;font-weight:600;margin-bottom:0.4rem;">Written Review *</label>
                <textarea id="review-text" class="search-input" style="height:90px;" placeholder="Describe what went well or how the service was performed..." required></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" onclick="app.closeModal('review-modal')">Cancel</button>
              <button type="submit" class="btn btn-success">Submit Review</button>
            </div>
          </form>
        </div>
      </div>
    `;
    const div = document.createElement('div');
    div.id = 'modal-container';
    div.innerHTML = modalHtml;
    document.body.appendChild(div);
  }

  async submitReview(e, bookingId) {
    e.preventDefault();
    const rating = document.getElementById('review-rating').value;
    const text = document.getElementById('review-text').value;

    try {
      await window.api.createReview({
        booking_id: bookingId,
        rating: rating,
        review: text
      });
      this.closeModal('review-modal');
      this.showToast('Thank you! Review submitted successfully.', 'success');
      this.renderCustomerDashboard(document.getElementById('main-content'));
    } catch(err) {
      this.showToast(err.message || 'Failed to submit review', 'error');
    }
  }

  // --- PROVIDER DASHBOARD ---
  async renderProviderDashboard(container) {
    if (!this.user || this.user.role !== 'provider') {
      window.location.hash = '#/login';
      return;
    }

    container.innerHTML = `<div style="text-align:center;padding:4rem;"><i class="fas fa-spinner fa-spin fa-2x"></i> Loading provider portal...</div>`;

    try {
      const meRes = await window.api.getMe();
      const provider = meRes.user.provider || {};
      const bookingsRes = await window.api.getBookings();
      const bookings = bookingsRes.bookings || [];

      const currentStatus = provider.availability_status || 'available';

      const pendingQueue = bookings.filter(b => b.status === 'pending');
      const activeJobs = bookings.filter(b => ['accepted', 'in_progress'].includes(b.status));
      const completedJobs = bookings.filter(b => b.status === 'completed');

      container.innerHTML = `
        <div class="dashboard-container">
          <div class="dashboard-header">
            <div>
              <h2>${provider.business_name || 'Provider Dashboard'}</h2>
              <p style="color:var(--text-muted);font-size:0.9rem;">Manage live availability, incoming job requests, and active work</p>
            </div>

            <!-- Always visible 1-tap Availability Widget -->
            <div class="availability-widget-card">
              <span style="font-weight:700;font-size:0.9rem;">My Status:</span>
              <button class="btn btn-sm ${currentStatus==='available'?'btn-success':'btn-secondary'}" onclick="app.toggleProviderAvailability('available')">🟢 Available</button>
              <button class="btn btn-sm ${currentStatus==='busy'?'btn-primary':'btn-secondary'}" onclick="app.toggleProviderAvailability('busy')">🟡 Busy</button>
              <button class="btn btn-sm ${currentStatus==='offline'?'btn-danger':'btn-secondary'}" onclick="app.toggleProviderAvailability('offline')">🔴 Offline</button>
            </div>
          </div>

          <!-- Tabs -->
          <div class="tabs-header">
            <button class="tab-btn active" onclick="app.switchTab('tab-requests', this)">Incoming Requests (${pendingQueue.length})</button>
            <button class="tab-btn" onclick="app.switchTab('tab-active', this)">Active Jobs (${activeJobs.length})</button>
            <button class="tab-btn" onclick="app.switchTab('tab-completed', this)">Completed Jobs (${completedJobs.length})</button>
          </div>

          <!-- Pending Requests Queue -->
          <div id="tab-requests" class="tab-pane">
            ${pendingQueue.length > 0 ? pendingQueue.map(b => `
              <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">
                  <div>
                    <h4>${b.category_icon || '🔧'} ${b.category_name} Request</h4>
                    <p style="font-size:0.85rem;color:var(--text-muted);">From: <strong>${b.customer_name}</strong> (${b.customer_phone}) &middot; Location: ${b.address_text}</p>
                  </div>
                  <span class="status-badge pending">PENDING ACTION</span>
                </div>
                <p style="font-size:0.9rem;background:#f8fafc;padding:0.75rem;border-radius:var(--radius-md);margin-bottom:1rem;">
                  ${b.description}
                </p>
                <div style="display:flex;gap:0.75rem;">
                  <button class="btn btn-success btn-sm" onclick="app.updateBookingState(${b.id}, 'accepted')"><i class="fas fa-check"></i> Accept Job</button>
                  <button class="btn btn-danger btn-sm" onclick="app.updateBookingState(${b.id}, 'rejected')"><i class="fas fa-times"></i> Reject</button>
                </div>
              </div>
            `).join('') : '<div class="empty-state">No pending incoming requests right now.</div>'}
          </div>

          <!-- Active Jobs -->
          <div id="tab-active" class="tab-pane" style="display:none;">
            ${activeJobs.length > 0 ? activeJobs.map(b => `
              <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">
                  <div>
                    <h4>${b.category_name} &middot; Customer: ${b.customer_name}</h4>
                    <p style="font-size:0.85rem;color:var(--text-muted);"><i class="fas fa-phone"></i> Phone: ${b.customer_phone} &middot; Address: ${b.address_text}</p>
                  </div>
                  <span class="status-badge ${b.status}">${b.status.toUpperCase()}</span>
                </div>
                <div style="display:flex;gap:0.75rem;">
                  ${b.status==='accepted' ? `
                    <button class="btn btn-primary btn-sm" onclick="app.updateBookingState(${b.id}, 'in_progress')"><i class="fas fa-play"></i> Mark In-Progress</button>
                  ` : ''}
                  ${b.status==='in_progress' ? `
                    <button class="btn btn-success btn-sm" onclick="app.updateBookingState(${b.id}, 'completed')"><i class="fas fa-check-double"></i> Mark Completed</button>
                  ` : ''}
                </div>
              </div>
            `).join('') : '<div class="empty-state">No active jobs in progress.</div>'}
          </div>

          <!-- Completed Jobs -->
          <div id="tab-completed" class="tab-pane" style="display:none;">
            ${completedJobs.length > 0 ? completedJobs.map(b => `
              <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:1.25rem;margin-bottom:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <strong>${b.category_name}</strong> for ${b.customer_name}<br/>
                    <span style="font-size:0.85rem;color:var(--text-muted);">${b.description}</span>
                  </div>
                  <span class="status-badge completed">COMPLETED</span>
                </div>
              </div>
            `).join('') : '<div class="empty-state">No completed jobs logged.</div>'}
          </div>
        </div>
      `;

    } catch(err) {
      container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:3rem;">Failed to load provider portal: ${err.message}</div>`;
    }
  }

  async toggleProviderAvailability(status) {
    try {
      await window.api.updateAvailability(status);
      this.showToast(`Status updated to ${status.toUpperCase()}`, 'success');
      this.renderProviderDashboard(document.getElementById('main-content'));
    } catch(err) {
      this.showToast(err.message || 'Failed to update status', 'error');
    }
  }

  async updateBookingState(id, status) {
    try {
      await window.api.updateBookingStatus(id, status);
      this.showToast(`Job status updated to ${status}`, 'success');
      this.renderProviderDashboard(document.getElementById('main-content'));
    } catch(err) {
      this.showToast(err.message || 'Failed to update job status', 'error');
    }
  }

  switchTab(paneId, btn) {
    document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    const pane = document.getElementById(paneId);
    if (pane) pane.style.display = 'block';
    if (btn) btn.classList.add('active');
  }

  // --- ADMIN PORTAL ---
  async renderAdminPage(container) {
    if (!this.user || this.user.role !== 'admin') {
      this.showToast('Forbidden: Admin role required (HTTP 403)', 'error');
      window.location.hash = '#/';
      return;
    }

    container.innerHTML = `<div style="text-align:center;padding:4rem;"><i class="fas fa-spinner fa-spin fa-2x"></i> Loading Admin Dashboard...</div>`;

    try {
      const statsRes = await window.api.getAdminStats();
      const stats = statsRes.stats || {};
      const provsRes = await window.api.getAdminProviders();
      const providers = provsRes.providers || [];

      container.innerHTML = `
        <div class="dashboard-container">
          <div class="dashboard-header">
            <div>
              <h2>Platform Admin Portal</h2>
              <p style="color:var(--text-muted);font-size:0.9rem;">Moderate reviews, verify provider documents, manage users and marketplace health</p>
            </div>
            <span class="brand-badge">ADMIN ACCESS ENFORCED</span>
          </div>

          <!-- Headline Stats Cards -->
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:1rem;margin-bottom:2rem;">
            <div style="background:white;border:1px solid var(--card-border);padding:1.25rem;border-radius:var(--radius-lg);">
              <div style="font-size:0.85rem;color:var(--text-muted);">Total Users</div>
              <div style="font-size:2rem;font-weight:800;color:var(--primary);">${stats.total_users}</div>
            </div>
            <div style="background:white;border:1px solid var(--card-border);padding:1.25rem;border-radius:var(--radius-lg);">
              <div style="font-size:0.85rem;color:var(--text-muted);">Total Providers</div>
              <div style="font-size:2rem;font-weight:800;color:var(--text-main);">${stats.total_providers}</div>
            </div>
            <div style="background:white;border:1px solid var(--card-border);padding:1.25rem;border-radius:var(--radius-lg);">
              <div style="font-size:0.85rem;color:var(--text-muted);">Active Available</div>
              <div style="font-size:2rem;font-weight:800;color:var(--success);">${stats.active_available_providers}</div>
            </div>
            <div style="background:white;border:1px solid var(--card-border);padding:1.25rem;border-radius:var(--radius-lg);">
              <div style="font-size:0.85rem;color:var(--text-muted);">Total Bookings</div>
              <div style="font-size:2rem;font-weight:800;color:var(--text-main);">${stats.total_bookings}</div>
            </div>
            <div style="background:white;border:1px solid var(--card-border);padding:1.25rem;border-radius:var(--radius-lg);">
              <div style="font-size:0.85rem;color:var(--text-muted);">Platform Rating</div>
              <div style="font-size:2rem;font-weight:800;color:#f59e0b;">${stats.platform_avg_rating} ★</div>
            </div>
          </div>

          <h3 style="margin-bottom:1rem;">Provider Verification Queue</h3>
          <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow-sm);">
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem;text-align:left;">
              <thead style="background:#f8fafc;border-bottom:1px solid var(--card-border);">
                <tr>
                  <th style="padding:0.75rem 1rem;">Business Name</th>
                  <th style="padding:0.75rem 1rem;">Owner</th>
                  <th style="padding:0.75rem 1rem;">Phone</th>
                  <th style="padding:0.75rem 1rem;">Status</th>
                  <th style="padding:0.75rem 1rem;">Action</th>
                </tr>
              </thead>
              <tbody>
                ${providers.map(p => `
                  <tr style="border-bottom:1px solid #f1f5f9;">
                    <td style="padding:0.75rem 1rem;font-weight:600;">${p.business_name}</td>
                    <td style="padding:0.75rem 1rem;">${p.provider_user_name}</td>
                    <td style="padding:0.75rem 1rem;">${p.phone}</td>
                    <td style="padding:0.75rem 1rem;">
                      <span class="status-badge ${p.verification_status==='approved'?'available':'busy'}">
                        ${p.verification_status.toUpperCase()}
                      </span>
                    </td>
                    <td style="padding:0.75rem 1rem;">
                      ${p.verification_status !== 'approved' ? `
                        <button class="btn btn-success btn-sm" onclick="app.adminVerifyProvider(${p.id}, 'approved')"><i class="fas fa-check-circle"></i> Verify Badge</button>
                      ` : `
                        <button class="btn btn-danger btn-sm" onclick="app.adminVerifyProvider(${p.id}, 'rejected')">Revoke</button>
                      `}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;

    } catch(err) {
      container.innerHTML = `<div style="color:var(--danger);text-align:center;padding:3rem;">Failed to load Admin Panel: ${err.message}</div>`;
    }
  }

  async adminVerifyProvider(providerId, status) {
    try {
      await window.api.verifyProvider(providerId, status);
      this.showToast(`Provider verification status set to ${status}`, 'success');
      this.renderAdminPage(document.getElementById('main-content'));
    } catch(err) {
      this.showToast(err.message || 'Verification update failed', 'error');
    }
  }

  // --- STATIC PAGES ---
  renderStaticPage(container, page) {
    const titles = {
      'how-it-works': 'How LocalFix Works',
      'about': 'About LocalFix',
      'terms': 'Terms of Service',
      'privacy': 'Privacy Policy'
    };

    container.innerHTML = `
      <div class="section-container" style="max-width:800px;">
        <h1 class="section-title">${titles[page] || 'Information'}</h1>
        <div style="background:white;border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:2rem;line-height:1.7;">
          <h3>Fast, Transparent, Local</h3>
          <p>LocalFix connects customers in urgent need of household and emergency services with ranked, distance-sorted, verified professionals.</p>
          <hr style="margin:1.5rem 0;border:0;border-top:1px solid #e2e8f0;" />
          <h4>Key Platform Guarantees:</h4>
          <ul>
            <li>Live Availability Status toggle (Available / Busy / Offline)</li>
            <li>Distance calculations using server-side Haversine metrics</li>
            <li>State machine persistency for requests and completion logs</li>
            <li>Role-enforced security on every protected route</li>
          </ul>
        </div>
      </div>
    `;
  }
}

window.app = new LocalFixApp();
