/* ================================================================
   analytics.js — GrowZen Analytics Dashboard
   ================================================================ */

document.addEventListener("DOMContentLoaded", async () => {

  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) return; // authGuard handles redirect

  const userId = user.id;
  const loading = document.getElementById("anLoading");
  const empty   = document.getElementById("anEmpty");
  const content = document.getElementById("anContent");

  const setEl = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

  function chartDefaults() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#111827", titleColor: "#f9fafb", bodyColor: "#d1d5db",
          borderColor: "#374151", borderWidth: 1, padding: 10, cornerRadius: 8
        }
      }
    };
  }

  try {
    const [analyticsRes, statsRes] = await Promise.all([
      fetch(`/api/analytics/summary`, { 
        headers: { "Authorization": `Bearer ${userId}` }
      }),
      fetch(`/api/user/${userId}/stats`, {
        headers: { "Authorization": `Bearer ${userId}` }
      })
    ]);

    const data = await analyticsRes.json();
    const statsData = await statsRes.json();

    console.log("Analytics API:", data);

    if (loading) loading.style.display = "none";

    // Spec explicit requirement: Only show "No data yet" when total_plants == 0
    if (data.total_plants === 0) {
      if (empty) empty.style.display = "flex";
      return;
    }

    if (content) content.style.display = "block";

    // 1. Summary Stats — keys must match backend response exactly
    setEl("statTotal",   data.summary.plant_count);
    setEl("statHealthy", data.summary.healthy_count);
    setEl("statAttn",    data.summary.sick_count);        // backend returns sick_count
    setEl("statAvg",     (data.summary.avg_health ?? 0) + "%");
    setEl("statScans",   data.summary.total_scans);
    setEl("statTasks",   data.summary.tasks_completed);

    if (statsData.success) {
      const badge = document.getElementById("anUserBadge");
      if (badge) badge.style.display = "flex";
      setEl("anLevel", statsData.level);
      setEl("anXp",    statsData.xp);
    }

    // AI Insights
    const aiBox = document.getElementById("aiInsightsBox");
    if (aiBox && data.ai_insights) {
      aiBox.style.display = "flex";
      setEl("aiInsightsText", data.ai_insights);
    }

    // 2. Health Trend Line Chart
    const trendCtx = document.getElementById("healthTrendChart");
    if (trendCtx && data.health_trend) {
      new Chart(trendCtx, {
        type: "line",
        data: {
          labels: data.health_trend.labels,
          datasets: [{
            label: "Avg. Health",
            data: data.health_trend.scores,
            fill: true,
            borderColor: "#16a34a",
            backgroundColor: "rgba(22, 163, 74, 0.1)",
            tension: 0.4,
            pointBackgroundColor: "#16a34a",
            pointBorderColor: "#fff",
            pointBorderWidth: 2, pointRadius: 4
          }]
        },
        options: {
          ...chartDefaults(),
          scales: {
            y: { min: 0, max: 100, grid: { color: "#f3f4f6" }, ticks: { callback: v => v+"%" } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 3. Disease Distribution Pie Chart
    const distCtx = document.getElementById("distributionChart");
    if (distCtx && data.disease_distribution) {
      const labels = Object.keys(data.disease_distribution);
      const values = Object.values(data.disease_distribution);
      
      // Assign dynamic colors: healthy gets green, others get warm colors
      const colors = labels.map(l => l.toLowerCase() === "healthy" ? "#22c55e" : 
                                      (l.toLowerCase().includes("blight") ? "#dc2626" : "#f59e0b"));

      new Chart(distCtx, {
        type: "doughnut",
        data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 2, borderColor: "#fff" }] },
        options: {
          ...chartDefaults(), cutout: "65%",
          plugins: { ...chartDefaults().plugins, legend: { display: true, position: 'bottom' } }
        }
      });
    }

    // 4. Watering Consistency Bar Chart
    const waterCtx = document.getElementById("wateringChart");
    if (waterCtx && data.watering_history) {
      new Chart(waterCtx, {
        type: "bar",
        data: {
          labels: data.watering_history.labels,
          datasets: [{
            label: "Watering Tasks",
            data: data.watering_history.data,
            backgroundColor: "#3b82f6",
            borderRadius: 4
          }]
        },
        options: {
          ...chartDefaults(),
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 5. Scan Activity Bar Chart
    const scanCtx = document.getElementById("scanActivityChart");
    if (scanCtx && data.scan_activity) {
      new Chart(scanCtx, {
        type: "bar",
        data: {
          labels: data.scan_activity.labels,
          datasets: [{
            label: "Scans",
            data: data.scan_activity.data,
            backgroundColor: "#8b5cf6",
            borderRadius: 4
          }]
        },
        options: {
          ...chartDefaults(),
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 6. Care Task Performance
    if (data.task_analytics) {
      setEl("perfCompleted", data.task_analytics.completed);
      setEl("perfMissed", data.task_analytics.missed);
      setEl("perfPct", data.task_analytics.percentage);
      const bar = document.getElementById("perfPctBar");
      if (bar) bar.style.width = data.task_analytics.percentage + "%";
    }

    // 7. Plant Growth Progress
    const growthList = document.getElementById("growthProgressList");
    if (growthList && data.growth_progress) {
      if (data.growth_progress.length === 0) {
        growthList.innerHTML = `<div class="an-empty-list">No plants recorded.</div>`;
      } else {
        growthList.innerHTML = data.growth_progress.map(p => `
          <div class="growth-item">
            <div class="growth-header">
              <span class="growth-name">${p.name}</span>
              <span class="growth-stage-badge">${p.stage}</span>
            </div>
            <div class="growth-score-label">Health: ${p.health}%</div>
            <div class="completion-bar-wrap" style="height: 6px; margin-top: 4px;">
                <div class="completion-bar-fill" style="width: ${p.health}%; background-color: ${p.health > 70 ? '#16a34a' : (p.health > 40 ? '#f59e0b' : '#dc2626')}"></div>
            </div>
          </div>
        `).join('');
      }
    }

  } catch (err) {
    console.error("Analytics Error:", err);
    if (loading) loading.innerHTML = `<p style="color:#ef4444;">Failed to load analytics.</p>`;
  }
});
