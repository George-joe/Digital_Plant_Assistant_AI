/**
 * weather.js — Real-time weather widget using OpenWeather via /api/weather
 * Works on both dashboard and plant profile pages.
 */

async function initWeatherWidget(containerSelector, onLoaded) {
    const el = document.querySelector(containerSelector);
    if (!el) return;

    // Show loading
    el.innerHTML = `<div style="display:flex;align-items:center;gap:10px;color:#9ca3af"><div class="spinner" style="width:18px;height:18px;border-width:2px;"></div> Fetching weather...</div>`;

    try {
        let url = "/api/weather";
        const pos = await getLocation();
        if (pos) {
            url += `?lat=${pos.lat}&lon=${pos.lon}`;
        }

        const res = await fetch(url);
        const data = await res.json();

        if (!data || !data.ok) {
            el.innerHTML = `<div style="color:#9ca3af;font-size:13px;padding:8px 0;">🌦️ Weather data unavailable right now. Check back later.</div>`;
            if (typeof onLoaded === 'function') onLoaded(null);
            return;
        }

        el.innerHTML = buildWeatherHTML(data);
        if (typeof onLoaded === 'function') onLoaded(data);
    } catch (err) {
        el.innerHTML = `<div style="color:#9ca3af;font-size:13px;padding:8px 0;">🌦️ Weather unavailable — check your connection.</div>`;
        if (typeof onLoaded === 'function') onLoaded(null);
    }

    // Auto refresh every 30 minutes
    if (!window.__weatherIntervals) window.__weatherIntervals = {};
    if (!window.__weatherIntervals[containerSelector]) {
        window.__weatherIntervals[containerSelector] = setInterval(() => {
            initWeatherWidget(containerSelector, onLoaded);
        }, 30 * 60 * 1000);
    }
}

function buildWeatherHTML(d) {
    const tempColor = d.temp > 35 ? "var(--danger)" : d.temp < 5 ? "#3b82f6" : "var(--primary)";
    const cityName = d.city || "Your Location";
    
    return `
    <div class="weather-card-inner">
      <div class="weather-city-badge">${cityName}</div>
      <div class="weather-main-row">
        <div class="weather-icon-big">${d.icon}</div>
        <div>
          <div class="weather-temp" style="color:${tempColor}">${d.temp}°C</div>
          <div class="weather-condition">${d.condition}</div>
        </div>
      </div>
      <div class="weather-metrics">
        <div class="wmetric"><span class="wm-icon">💧</span><span>${d.humidity}%</span><span class="wm-label">Humidity</span></div>
        <div class="wmetric"><span class="wm-icon">💨</span><span>${d.wind} m/s</span><span class="wm-label">Wind</span></div>
        <div class="wmetric"><span class="wm-icon">🌡️</span><span>${d.apparent}°C</span><span class="wm-label">Feels like</span></div>
      </div>
      <div class="weather-advice">
        <div class="advice-icon">💡</div>
        <div class="advice-text">${d.advice}</div>
      </div>
    </div>
  `;
}

async function getLocation() {
    return new Promise(resolve => {
        if (!navigator.geolocation) { resolve(null); return; }
        navigator.geolocation.getCurrentPosition(
            pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
            () => resolve(null),
            { timeout: 5000 }
        );
    });
}
