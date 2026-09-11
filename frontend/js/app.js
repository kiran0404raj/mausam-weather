/**
 * App Controller - Manages Global State, Navigation, Home Screen & Location Modal
 */

const AppState = {
  coords: { lat: 12.9716, lon: 77.5946 }, // Default Bengaluru
  locationName: "Bengaluru, India",
  currentView: "view-home",
  weatherData: null
};

const AppNav = {
  currentActiveTab: "home",

  switchTab(tabId) {
    this.currentActiveTab = tabId;

    // Update bottom nav active classes
    document.querySelectorAll(".nav-item").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tabId);
    });

    if (tabId === "home") {
      this.showView("view-home");
      App.loadHomeWeather();
    } else if (tabId === "plan") {
      this.showView("view-plan");
      PlanDashboard.initPlanHome(AppState.coords, AppState.locationName);
    } else if (tabId === "forecast") {
      this.showView("view-forecast");
      App.loadForecastView();
    } else if (tabId === "maps") {
      this.showView("view-maps");
    } else if (tabId === "alerts") {
      this.showView("view-alerts");
    } else if (tabId === "more") {
      this.showView("view-more");
    }
  },

  showView(viewId) {
    AppState.currentView = viewId;
    document.querySelectorAll(".app-view").forEach(view => {
      view.classList.toggle("active", view.id === viewId);
    });

    // Reset scroll to top
    const scroller = document.querySelector(".screen-scroll-container");
    if (scroller) scroller.scrollTop = 0;
  },

  backToPlanHome() {
    this.showView("view-plan");
  },

  backToHome() {
    this.switchTab("home");
  }
};

const LocationModal = {
  isOpen: false,
  searchTimer: null,

  open() {
    const backdrop = document.getElementById("locationModal");
    if (backdrop) {
      backdrop.classList.add("open");
      const input = document.getElementById("locationSearchInput");
      if (input) {
        input.value = "";
        input.focus();
      }
      this.isOpen = true;
    }
  },

  close() {
    const backdrop = document.getElementById("locationModal");
    if (backdrop) backdrop.classList.remove("open");
    this.isOpen = false;
  },

  handleSearchInput(event) {
    clearTimeout(this.searchTimer);
    const q = event.target.value.trim();
    if (q.length < 2) {
      document.getElementById("locationSearchResults").innerHTML = "";
      return;
    }
    this.searchTimer = setTimeout(() => this.executeSearch(q), 300);
  },

  async executeSearch(query) {
    const resultsContainer = document.getElementById("locationSearchResults");
    resultsContainer.innerHTML = `<div style="padding:10px;text-align:center;color:var(--text-muted);font-size:0.8rem;">Searching cities...</div>`;

    try {
      const res = await fetch(`/api/location/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      const results = data.results || [];

      if (results.length === 0) {
        resultsContainer.innerHTML = `<div style="padding:10px;text-align:center;color:var(--text-muted);font-size:0.8rem;">No cities found for "${query}"</div>`;
        return;
      }

      resultsContainer.innerHTML = results.map(r => `
        <div class="search-result-item" onclick="LocationModal.selectCity('${r.name}', '${r.country}', ${r.latitude}, ${r.longitude})">
          <div>
            <div class="res-city">${r.name}</div>
            <div class="res-country">${r.admin1 ? r.admin1 + ', ' : ''}${r.country}</div>
          </div>
          <span style="font-size:0.8rem;color:var(--primary);">Select</span>
        </div>
      `).join("");
    } catch (err) {
      console.error("Geocoding error:", err);
      resultsContainer.innerHTML = `<div style="padding:10px;text-align:center;color:var(--danger);font-size:0.8rem;">Error searching location</div>`;
    }
  },

  selectCity(name, country, lat, lon) {
    AppState.coords = { lat, lon };
    AppState.locationName = `${name}, ${country}`;
    this.updateLocationChips(AppState.locationName);
    this.close();
    App.showToast(`Switched to ${name}`);

    // Refresh active view
    if (AppState.currentView === "view-home") {
      App.loadHomeWeather();
    } else if (AppState.currentView === "view-plan") {
      PlanDashboard.initPlanHome(AppState.coords, AppState.locationName);
    } else if (AppState.currentView === "view-category-detail") {
      PlanDashboard.openCategory(PlanDashboard.currentCategory);
    }
  },

  updateLocationChips(name) {
    document.querySelectorAll(".loc-name").forEach(el => {
      el.textContent = name;
    });
  },

  useGps() {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    App.showToast("Detecting GPS location...");
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        AppState.coords = { lat, lon };
        AppState.locationName = "Current GPS Location";
        this.updateLocationChips(AppState.locationName);
        this.close();
        App.showToast("Updated to your live GPS coordinates!");

        if (AppState.currentView === "view-plan") {
          PlanDashboard.initPlanHome(AppState.coords, AppState.locationName);
        } else {
          App.loadHomeWeather();
        }
      },
      (err) => {
        console.warn("GPS error:", err);
        App.showToast("GPS permission denied or unavailable.");
      },
      { timeout: 8000 }
    );
  }
};

const App = {
  init() {
    this.updateClock();
    setInterval(() => this.updateClock(), 60000);

    // Initial load
    this.loadHomeWeather();

    // Check if initial URL was /plan
    if (window.location.pathname.includes("/plan")) {
      AppNav.switchTab("plan");
    }
  },

  updateClock() {
    const clockEl = document.getElementById("phoneClock");
    if (clockEl) {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    }
  },

  showToast(msg) {
    const toast = document.getElementById("appToast");
    if (toast) {
      toast.textContent = msg;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 2800);
    }
  },

  async loadHomeWeather() {
    const container = document.getElementById("homeWeatherMain");
    if (!container) return;

    try {
      const res = await fetch(`/api/weather/current?lat=${AppState.coords.lat}&lon=${AppState.coords.lon}&location_name=${encodeURIComponent(AppState.locationName)}`);
      const payload = await res.json();

      if (payload.status === "success") {
        AppState.weatherData = payload.data;
        const curr = payload.data.current;
        const daily = payload.data.daily || [];
        const hourly = payload.data.hourly || [];

        container.innerHTML = `
          <!-- Primary Weather Card -->
          <div class="home-weather-card">
            <div class="home-temp-row">
              <div>
                <div class="home-large-temp">${Math.round(curr.temperature)}°</div>
                <div class="home-cond-label">${curr.condition}</div>
                <div style="font-size:0.85rem;opacity:0.9;margin-top:2px;">Feels like ${Math.round(curr.feels_like)}°C</div>
              </div>
              <div class="home-weather-icon">${curr.icon}</div>
            </div>

            <div class="home-sub-stats">
              <div class="home-stat-col">
                <span>WIND</span>
                <strong>${curr.wind_speed} km/h</strong>
              </div>
              <div class="home-stat-col">
                <span>HUMIDITY</span>
                <strong>${curr.humidity}%</strong>
              </div>
              <div class="home-stat-col">
                <span>UV INDEX</span>
                <strong>${curr.uv_index}</strong>
              </div>
              <div class="home-stat-col">
                <span>AIR QUALITY</span>
                <strong>AQI ${curr.aqi}</strong>
              </div>
            </div>
          </div>

          <!-- Feature Spotlight Banner: "Plan for What Matters" -->
          <div class="plan-spotlight-banner" onclick="AppNav.switchTab('plan')">
            <div class="spotlight-top">
              <span class="spotlight-badge">New Feature</span>
              <span style="font-size:0.78rem;color:#a5b4fc;">Personalized Intelligence</span>
            </div>
            <div class="spotlight-title">🎯 Plan for What Matters</div>
            <div class="spotlight-text">
              Instead of generic forecasts, get weather intelligence curated for Health, Fitness, Travel, Beach, Commute, and Family.
            </div>
            <div class="spotlight-action-row">
              <span class="spotlight-pill">6 Personal Decision Categories</span>
              <button class="btn-spotlight-go">Explore Dashboard ➔</button>
            </div>
          </div>

          <!-- Hourly Forecast Section -->
          <div class="section-heading">
            <span>Today's Hourly Forecast</span>
            <span style="font-size:0.75rem;color:var(--text-muted);">24 Hours</span>
          </div>
          <div class="horizontal-timeline-scroll">
            ${hourly.slice(0, 10).map(h => `
              <div class="timeline-card">
                <div class="timeline-time">${h.time}</div>
                <div class="timeline-icon">${h.icon}</div>
                <div class="timeline-temp">${h.temp}°</div>
                <div style="font-size:0.65rem;color:var(--text-muted);margin-top:4px;">💧 ${h.humidity}%</div>
              </div>
            `).join("")}
          </div>

          <!-- 7-Day Forecast Section -->
          <div class="section-heading" style="margin-top:16px;">
            <span>7-Day Weather Outlook</span>
            <span style="font-size:0.75rem;color:var(--text-muted);">${AppState.locationName}</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:15px;">
            ${daily.map(d => `
              <div class="packing-item" style="display:flex;justify-content:space-between;align-items:center;background:white;padding:10px 14px;">
                <div style="display:flex;align-items:center;gap:12px;">
                  <span style="font-size:1.4rem;">${d.icon}</span>
                  <div>
                    <div style="font-size:0.88rem;font-weight:700;">${d.day}</div>
                    <div style="font-size:0.74rem;color:var(--text-secondary);">${d.condition}</div>
                  </div>
                </div>
                <div style="text-align:right;">
                  <span style="font-size:0.92rem;font-weight:800;color:var(--text-primary);">${d.max_temp}°</span>
                  <span style="font-size:0.82rem;color:var(--text-muted);margin-left:6px;">${d.min_temp}°</span>
                </div>
              </div>
            `).join("")}
          </div>
        `;
      }
    } catch (err) {
      console.error("Home weather load error:", err);
    }
  },

  loadForecastView() {
    const container = document.getElementById("forecastContent");
    if (!container || !AppState.weatherData) return;
    const daily = AppState.weatherData.daily || [];
    container.innerHTML = `
      <div class="section-heading"><span>Extended Multi-Day Forecast</span></div>
      <div style="display:flex;flex-direction:column;gap:10px;">
        ${daily.map(d => `
          <div class="metric-card" style="padding:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.8rem;">${d.icon}</span>
                <div>
                  <div style="font-weight:800;font-size:0.95rem;">${d.day} (${d.date})</div>
                  <div style="font-size:0.78rem;color:var(--text-secondary);">${d.condition}</div>
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-weight:800;font-size:1.1rem;">${d.max_temp}° / ${d.min_temp}°</div>
                <div style="font-size:0.72rem;color:var(--primary);">Rain: ${d.rain_prob}%</div>
              </div>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }
};

// Start application when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
