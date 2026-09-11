/**
 * PlanDashboard Module - Handles "Plan for What Matters" Sub-Homepage & Category Dashboards
 */

const PlanDashboard = {
  currentCategory: null,
  summaryData: null,
  cachedDashboardData: {},

  // Initialize and load category summary for the grid
  async initPlanHome(coords, locationName) {
    const gridContainer = document.getElementById("categoryGrid");
    const indicatorBanner = document.getElementById("planLiveIndicator");
    
    if (!gridContainer) return;
    
    // Show Loading Skeleton
    gridContainer.innerHTML = this.renderSkeletonGrid();

    try {
      const res = await fetch(`/api/planning/summary?lat=${coords.lat}&lon=${coords.lon}&location_name=${encodeURIComponent(locationName)}`);
      const payload = await res.json();
      
      if (payload.status === "success") {
        this.summaryData = payload;
        
        // Update Live Weather Indicator Banner
        const curr = payload.current_weather;
        if (indicatorBanner) {
          indicatorBanner.innerHTML = `
            <div class="indicator-left">
              <span class="indicator-weather-icon">${curr.icon || '☀️'}</span>
              <div>
                <div class="indicator-temp">${Math.round(curr.temperature)}°C</div>
                <div class="indicator-desc">${curr.condition || 'Clear'} • Feels ${Math.round(curr.feels_like)}°C</div>
              </div>
            </div>
            <div class="indicator-right">
              <div>💨 ${Math.round(curr.wind_speed)} km/h</div>
              <div>🫁 AQI ${curr.aqi}</div>
            </div>
          `;
        }

        // Render 2-Column Category Grid
        this.renderCategoryGrid(payload.categories, gridContainer);
      } else {
        gridContainer.innerHTML = this.renderEmptyState("Unable to load planning categories.", "Try refreshing or check connection.");
      }
    } catch (err) {
      console.error("Error fetching planning summary:", err);
      gridContainer.innerHTML = this.renderEmptyState("Network issue loading intelligence.", "Please try again shortly.");
    }
  },

  // Render 2-Column Mobile Category Cards
  renderCategoryGrid(categories, container) {
    container.innerHTML = categories.map(cat => `
      <div class="category-card cat-${cat.id}" onclick="PlanDashboard.openCategory('${cat.id}')">
        <div>
          <div class="cat-top-row">
            <div class="cat-icon-wrap">${cat.icon}</div>
            <div class="cat-chevron">➔</div>
          </div>
          <div class="cat-name">${cat.name}</div>
          <div class="cat-desc">${cat.description}</div>
        </div>
        <div class="cat-indicator-pill">
          <span>●</span>
          <span>${cat.micro_indicator}</span>
        </div>
      </div>
    `).join("");
  },

  // Open Dedicated Category Dashboard
  async openCategory(categoryId) {
    this.currentCategory = categoryId;
    const coords = AppState.coords;
    const locationName = AppState.locationName;
    
    // Switch to category detail view
    AppNav.showView("view-category-detail");
    const container = document.getElementById("categoryDetailContent");
    container.innerHTML = this.renderSkeletonDashboard();

    try {
      const res = await fetch(`/api/planning/category/${categoryId}?lat=${coords.lat}&lon=${coords.lon}&location_name=${encodeURIComponent(locationName)}`);
      const payload = await res.json();
      
      if (payload.status === "success") {
        this.renderCategoryDashboard(payload, container);
      } else {
        container.innerHTML = this.renderEmptyState("Failed to load category details.", "Please try again.");
      }
    } catch (err) {
      console.error("Error loading category dashboard:", err);
      container.innerHTML = this.renderEmptyState("Network issue loading category dashboard.", "Check your internet connection.");
    }
  },

  // Render Category Sub-Dashboard
  renderCategoryDashboard(data, container) {
    const evalData = data.evaluation;
    const curr = data.current_weather;
    const locName = data.location_name;
    const dateStr = new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    const timeStr = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

    let specificSectionHtml = "";

    // 1. HEALTH & WELLNESS SPECIFIC
    if (evalData.id === "health") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>Allergy & Respiratory Guidance</span>
          <span style="font-size:0.75rem;color:var(--primary);">Actionable Insights</span>
        </div>
        <div class="recommendation-card" style="border-left-color: var(--success);">
          <div class="rec-title-row">
            <span>🌿</span>
            <span>Allergy / Asthma / Skin Sensitivity Protocol</span>
          </div>
          <div class="packing-checklist" style="margin-top:6px;">
            ${evalData.guidance_list.map(item => `
              <div class="packing-item">
                <span class="packing-item-check">ℹ️</span>
                <span>${item}</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    // 2. OUTDOOR FITNESS SPECIFIC (Best Time to Run Timeline)
    else if (evalData.id === "fitness") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>Best Time to Run & Workout</span>
          <span style="font-size:0.75rem;color:var(--primary);">12-Hour Scoring</span>
        </div>
        <div class="horizontal-timeline-scroll">
          ${(evalData.timeline || []).map(slot => `
            <div class="timeline-card ${slot.badge === 'success' ? 'optimal' : ''}">
              <div class="timeline-time">${slot.time}</div>
              <div class="timeline-icon">${slot.rating === 'Excellent' ? '🏃‍♂️' : (slot.rating === 'Moderate' ? '🚶' : '⛔')}</div>
              <div class="timeline-temp">${slot.temp}</div>
              <div class="timeline-rating-pill ${slot.badge}">${slot.rating}</div>
              <div style="font-size:0.65rem;color:var(--text-muted);margin-top:4px;">${slot.reason}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    // 3. BEACH & WATER ACTIVITIES SPECIFIC (Tide & Waves Timeline)
    else if (evalData.id === "beach") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>Tide & Surf Timings</span>
          <span style="font-size:0.75rem;color:var(--accent-cyan);">Coastal Cycle</span>
        </div>
        <div class="horizontal-timeline-scroll">
          ${(evalData.tide_timeline || []).map(tide => `
            <div class="timeline-card">
              <div class="timeline-time">${tide.time}</div>
              <div class="timeline-icon">${tide.type.includes('High') ? '🌊' : '🏖️'}</div>
              <div class="timeline-temp" style="font-size:0.85rem;">${tide.height}</div>
              <div class="timeline-rating-pill success">${tide.type}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    // 4. TRAVEL SPECIFIC (Origin -> Destination Search & Packing List)
    else if (evalData.id === "travel") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>Trip Destination Planner</span>
          <span style="font-size:0.75rem;color:var(--primary);">Origin → Destination</span>
        </div>
        <div class="travel-planner-box">
          <div style="font-size:0.82rem;color:var(--text-secondary);">Planning travel from <strong>${locName}</strong>:</div>
          <div class="travel-input-group">
            <input type="text" id="destinationQuery" class="travel-input" placeholder="Search destination (e.g., London, Goa, Tokyo)" value="London" />
            <button class="btn-search-dest" onclick="PlanDashboard.searchDestinationForecast()">Explore</button>
          </div>
          <div id="destinationForecastResult">
            ${this.renderDestinationDetails(evalData, data.daily)}
          </div>
        </div>
      `;
    }

    // 5. PARENTS & FAMILIES SPECIFIC (School Commute Slots)
    else if (evalData.id === "parents") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>School Commute & Family Schedule</span>
          <span style="font-size:0.75rem;color:var(--warning);">Kids Safety</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;">
          ${(evalData.commute_slots || []).map(slot => `
            <div class="packing-item" style="display:flex;justify-content:space-between;align-items:center;background:white;border:1px solid var(--border-subtle);padding:10px 14px;">
              <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.4rem;">${slot.icon}</span>
                <div>
                  <div style="font-size:0.86rem;font-weight:700;">${slot.title} (${slot.hours})</div>
                  <div style="font-size:0.74rem;color:var(--text-secondary);">${slot.advice}</div>
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:0.88rem;font-weight:800;">${slot.temp}</div>
                <div class="timeline-rating-pill ${slot.badge}">${slot.status}</div>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    // 6. DAILY COMMUTE SPECIFIC (Rush-Hour Periods & Road Safety)
    else if (evalData.id === "commute") {
      specificSectionHtml = `
        <div class="section-heading">
          <span>Rush Hour & Transit Windows</span>
          <span style="font-size:0.75rem;color:var(--primary);">Traffic Flow</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;">
          ${(evalData.commute_periods || []).map(slot => `
            <div class="packing-item" style="display:flex;justify-content:space-between;align-items:center;background:white;border:1px solid var(--border-subtle);padding:10px 14px;">
              <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.4rem;">${slot.icon}</span>
                <div>
                  <div style="font-size:0.86rem;font-weight:700;">${slot.period}</div>
                  <div style="font-size:0.74rem;color:var(--text-secondary);">${slot.hours}</div>
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:0.78rem;font-weight:700;color:var(--text-primary);">Rain: ${slot.rain}</div>
                <span class="timeline-rating-pill ${slot.status.includes('Clear') || slot.status.includes('Optimal') || slot.status.includes('Smooth') ? 'success' : 'warning'}">${slot.status}</span>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    // General Hourly Timeline for All Dashboards
    const hourlyScrollHtml = `
      <div class="section-heading">
        <span>Hourly Weather Timeline</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">Next 12 Hours</span>
      </div>
      <div class="horizontal-timeline-scroll">
        ${(data.hourly || []).map(h => `
          <div class="timeline-card">
            <div class="timeline-time">${h.time}</div>
            <div class="timeline-icon">${h.icon || '☀️'}</div>
            <div class="timeline-temp">${h.temp}°</div>
            <div style="font-size:0.68rem;color:var(--text-secondary);margin-top:4px;">💧 ${h.humidity}%</div>
            <div style="font-size:0.68rem;color:var(--text-secondary);">🌧️ ${h.rain_prob}%</div>
          </div>
        `).join("")}
      </div>
    `;

    // Compose Full Category Dashboard DOM
    container.innerHTML = `
      <div class="category-dashboard">
        <!-- Top Navigation -->
        <div class="dash-nav-header">
          <button class="btn-icon-back" onclick="AppNav.backToPlanHome()" title="Back to categories">➔</button>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:1.3rem;">${evalData.icon}</span>
            <span style="font-weight:800;font-size:1.05rem;">${evalData.name}</span>
          </div>
          <div class="dash-meta-info">
            <div>📍 ${locName}</div>
            <div>${dateStr} • ${timeStr}</div>
          </div>
        </div>

        <!-- Hero Weather Card -->
        <div class="dash-hero-card">
          <div class="hero-header-row">
            <div class="hero-cat-tag">
              <span>Current Conditions</span>
            </div>
            <div class="status-pill ${evalData.status_color}">
              <span>●</span>
              <span>${evalData.status}</span>
            </div>
          </div>

          <div class="hero-main-data">
            <div>
              <div class="hero-temp-large">${Math.round(curr.temperature)}°</div>
              <div class="hero-cond-group">
                <div class="hero-condition-text">${curr.condition}</div>
                <div class="hero-feels-like">Feels like ${Math.round(curr.feels_like)}°C • Wind ${curr.wind_speed} km/h</div>
              </div>
            </div>
            <div class="hero-weather-symbol">${curr.icon}</div>
          </div>

          <div class="hero-primary-callout">
            <span class="callout-label">${evalData.primary_metric.label}</span>
            <span class="callout-value">${evalData.primary_metric.value}</span>
          </div>
        </div>

        <!-- Actionable Recommendation Card -->
        <div class="recommendation-card">
          <div class="rec-title-row">
            <span>💡</span>
            <span>Action Recommendation</span>
          </div>
          <div class="rec-body-text">${evalData.action_recommendation}</div>
          <div class="rec-window-highlight">
            <span>⏱️</span>
            <span><strong>Optimal Window:</strong> ${evalData.best_window}</span>
          </div>
        </div>

        <!-- Alert Banner Card -->
        <div class="recommendation-card" style="border-left-color: ${evalData.status_color === 'danger' ? 'var(--danger)' : (evalData.status_color === 'warning' ? 'var(--warning)' : 'var(--success)')}; background: #fafafa;">
          <div class="rec-title-row">
            <span>🔔</span>
            <span>Safety & Weather Advisory</span>
          </div>
          <div class="rec-body-text" style="font-weight:500;">${evalData.headline}</div>
        </div>

        <!-- Specialized Persona Feature Section -->
        ${specificSectionHtml}

        <!-- Relevant Metrics 2-Column Grid -->
        <div class="section-heading">
          <span>Key Atmospheric Factors</span>
          <span style="font-size:0.75rem;color:var(--text-muted);">${evalData.name}</span>
        </div>
        <div class="metric-cards-grid">
          ${evalData.metrics.map(m => `
            <div class="metric-card">
              <div class="metric-top">
                <span class="metric-icon">${m.icon}</span>
                <span class="metric-badge">${m.badge}</span>
              </div>
              <div class="metric-value">${m.value}</div>
              <div class="metric-label">${m.label}</div>
            </div>
          `).join("")}
        </div>

        <!-- Hourly Timeline -->
        ${hourlyScrollHtml}
      </div>
    `;
  },

  // Dedicated Destination Forecast for Travel Feature
  async searchDestinationForecast() {
    const destInput = document.getElementById("destinationQuery");
    const resultDiv = document.getElementById("destinationForecastResult");
    if (!destInput || !resultDiv) return;

    const query = destInput.value.trim();
    if (!query) return;

    resultDiv.innerHTML = `<div style="padding:15px;text-align:center;color:var(--text-muted);font-size:0.82rem;">Analyzing destination weather for "${query}"...</div>`;

    try {
      // 1. Geocode destination
      const geoRes = await fetch(`/api/location/search?q=${encodeURIComponent(query)}`);
      const geoData = await geoRes.json();

      if (!geoData.results || geoData.results.length === 0) {
        resultDiv.innerHTML = `<div style="padding:12px;color:var(--danger);font-size:0.82rem;">No matching destination found for "${query}". Try another city name.</div>`;
        return;
      }

      const dest = geoData.results[0];
      const travelRes = await fetch(`/api/planning/travel?dest_lat=${dest.latitude}&dest_lon=${dest.longitude}&dest_name=${encodeURIComponent(dest.name)}&origin_name=${encodeURIComponent(AppState.locationName)}`);
      const travelPayload = await travelRes.json();

      if (travelPayload.status === "success") {
        resultDiv.innerHTML = this.renderDestinationDetails(travelPayload.evaluation, travelPayload.daily_forecast);
      }
    } catch (err) {
      console.error("Error searching travel destination:", err);
      resultDiv.innerHTML = `<div style="padding:12px;color:var(--danger);font-size:0.82rem;">Failed to fetch travel forecast. Please try again.</div>`;
    }
  },

  renderDestinationDetails(evalData, dailyForecast) {
    const packing = evalData.packing_suggestions || [];
    const warnings = evalData.travel_warnings || [];

    return `
      <div style="margin-top:14px;border-top:1px solid #e2e8f0;padding-top:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:0.88rem;font-weight:700;color:var(--text-primary);">📍 ${evalData.location} Forecast</span>
          <span class="status-pill ${evalData.status_color}">Travel: ${evalData.status}</span>
        </div>
        
        <!-- Travel Warnings -->
        <div style="margin-bottom:10px;">
          ${warnings.map(w => `
            <div style="font-size:0.78rem;color:#b45309;background:#fef3c7;padding:6px 10px;border-radius:6px;margin-bottom:4px;">
              ⚠️ ${w}
            </div>
          `).join("")}
        </div>

        <!-- Packing Suggestions -->
        <div style="font-size:0.82rem;font-weight:700;color:var(--text-secondary);margin-bottom:6px;">
          🎒 Dynamic Weather Packing Suggestions:
        </div>
        <div class="packing-checklist">
          ${packing.map(item => `
            <div class="packing-item">
              <span class="packing-item-check">✓</span>
              <span>${item}</span>
            </div>
          `).join("")}
        </div>

        <!-- Multi-Day Forecast -->
        <div style="font-size:0.82rem;font-weight:700;color:var(--text-secondary);margin:12px 0 6px 0;">
          📅 7-Day Destination Outlook:
        </div>
        <div class="horizontal-timeline-scroll">
          ${(dailyForecast || []).map(day => `
            <div class="timeline-card">
              <div class="timeline-time">${day.day}</div>
              <div class="timeline-icon">${day.icon || '🌤️'}</div>
              <div class="timeline-temp">${day.max_temp}° / ${day.min_temp}°</div>
              <div style="font-size:0.65rem;color:var(--text-muted);margin-top:4px;">🌧️ ${day.rain_prob}%</div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  },

  // Reusable Skeletons and Empty States
  renderSkeletonGrid() {
    return Array(6).fill(0).map(() => `
      <div class="category-card skeleton-box" style="height:158px;opacity:0.7;"></div>
    `).join("");
  },

  renderSkeletonDashboard() {
    return `
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div class="skeleton-box" style="height:38px;width:100%;"></div>
        <div class="skeleton-box" style="height:180px;width:100%;"></div>
        <div class="skeleton-box" style="height:90px;width:100%;"></div>
        <div class="skeleton-box" style="height:140px;width:100%;"></div>
      </div>
    `;
  },

  renderEmptyState(title, subtitle) {
    return `
      <div style="text-align:center;padding:35px 20px;grid-column:span 2;">
        <div style="font-size:2.5rem;margin-bottom:8px;">🌦️</div>
        <div style="font-size:0.95rem;font-weight:700;color:var(--text-primary);">${title}</div>
        <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">${subtitle}</div>
      </div>
    `;
  }
};
