document.addEventListener("DOMContentLoaded", () => {

  /* ── AUTH ────────────────────────────────────────────────────── */
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) return; // authGuard handles the redirect

  /* ── ELEMENT REFS ──────────────────────────────────────────────── */
  const addPlantBtn        = document.getElementById("addPlantBtn");
  const addPlantBtnSec     = document.getElementById("addPlantBtnSecondary");
  const emptyAddBtn        = document.getElementById("emptyAddBtn");
  const addPlantModal      = document.getElementById("addPlantModal");
  const uploadStep         = document.getElementById("uploadStep");
  const previewStep        = document.getElementById("previewStep");
  const confirmStep        = document.getElementById("confirmStep");
  const dropZone           = document.getElementById("dropZone");
  const browseBtn          = document.getElementById("browseBtn");
  const plantFileInput     = document.getElementById("plantFileInput");
  const previewImg         = document.getElementById("previewImg");
  const confirmPreviewImg  = document.getElementById("confirmPreviewImg");
  const detectingText      = document.getElementById("detectingText");
  const confirmedName      = document.getElementById("confirmedPlantName");
  const confirmedSci       = document.getElementById("confirmedPlantSci");
  const confidenceBadge    = document.getElementById("confidenceBadge");
  const addToGardenBtn     = document.getElementById("addToGardenBtn");
  const plantGrid          = document.getElementById("plantGrid");
  const emptyState         = document.getElementById("emptyState");
  const loadingState       = document.getElementById("loadingState");
  const gardenStats        = document.getElementById("gardenStats");
  const widgetRow          = document.getElementById("widgetRow");
  const plantsSectionHeader= document.getElementById("plantsSectionHeader");
  const toast              = document.getElementById("toast");
  const todayTasksList     = document.getElementById("todayTasksList");

  let detectedData = null;
  let selectedFile = null;
  let allPlants    = [];

  /* ── SIDEBAR USER ──────────────────────────────────────────────── */
  const sn = document.getElementById("sidebarUsername");
  const sl = document.getElementById("sidebarLevel");
  if (sn) sn.textContent = user.name || "User";
  if (sl) sl.textContent = user.level || "Rookie";

  /* ── TOAST ─────────────────────────────────────────────────────── */
  function showToast(msg, type = "default") {
    if (!toast) return;
    toast.textContent = msg;
    toast.className = `toast show ${type === "success" ? "toast-success" : type === "error" ? "toast-error" : ""}`;
    setTimeout(() => { toast.classList.remove("show"); setTimeout(() => toast.classList.add("hidden"), 300); }, 2800);
  }

  /* ── XP AWARD ──────────────────────────────────────────────────── */
  async function awardXP(action) {
    try {
      const res = await fetch(`/api/user/${user.id}/award-xp`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.id}`
        },
        body: JSON.stringify({ action })
      });
      const data = await res.json();
      if (data.success) {
        showToast(`+${data.earned} XP — ${data.level}`, "success");
        loadStats(); // refresh XP display
      }
    } catch(e) { /* silent fail */ }
  }

  /* ── HEALTH STATUS LOGIC ───────────────────────────────────────── */
  function getHealthStatus(plant) {
    const hasDisease = plant.disease && !plant.disease.toLowerCase().includes("healthy");
    const health = plant.health_score || 0;

    if (!hasDisease) {
      return { label: "Healthy", cls: "status-healthy", color: "#16a34a" };
    } else if (health >= 50) {
      return { label: "Monitor", cls: "status-monitor", color: "#2563eb" };
    } else {
      return { label: "Sick", cls: "status-sick", color: "#dc2626" };
    }
  }

  function getHealthBarColor(status) {
    if (status === "healthy") return "#16a34a"; // Green 600
    if (status === "monitor") return "#2563eb"; // Blue 600
    return "#dc2626"; // Red 600
  }

  /* ── LOAD STATS (XP, streak, summary) ─────────────────────────── */
  async function loadStats() {
    try {
      const [userRes, anRes] = await Promise.all([
        fetch(`/api/user/${user.id}/stats`, { headers: { "Authorization": `Bearer ${user.id}` } }),
        fetch(`/api/analytics/summary`, { headers: { "Authorization": `Bearer ${user.id}` } })
      ]);
      const data = await userRes.json();
      const anData = await anRes.json();
      
      if (!data.success) return;

      const setEl = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

      // 1. Analytics Summary Binding (Part 5 FIX)
      if (anData.success) {
          setEl("statTotal",      anData.total_plants || 0);
          setEl("statHealthy",    anData.healthy_plants || 0);
          // Third stat is Avg Health
          setEl("statAvgHealth",  (anData.avg_health_score || 0) + "%");
          // Fourth stat is Water Consistency
          setEl("statConsistency", (anData.water_consistency || 0) + "%");
      }

      // XP + level
      setEl("statXp",    data.xp);
      setEl("streakCount", data.streak);
      setEl("levelBadge",  data.level);

      const xpFill = document.getElementById("xpBarFill");
      if (xpFill) xpFill.style.width = (data.xp_progress || 0) + "%";

      // Garden subtitle
      const sub = document.getElementById("gardenSubtitle");
      if (sub) sub.textContent = `${data.summary.total} plant${data.summary.total !== 1 ? "s" : ""} · ${data.summary.healthy} healthy`;

      // Pending Plants Task Summary
      loadPendingPlants();

    } catch(e) { /* ignore */ }
  }

  /* ── RENDER PENDING PLANTS ─────────────────────────────────────── */
  async function loadPendingPlants() {
    const listEl = document.getElementById("pendingPlantsList");
    if (!listEl) return;
    try {
      const res = await fetch("/api/tasks?plant_id=ALL", {
        headers: { "Authorization": `Bearer ${user.id}` }
      });
      const data = await res.json();
      const allTasks = data.tasks || [];
      console.log("TASKS:", allTasks);
      
      const pendingTasks = allTasks.filter(t => t.completed === false);
      const groups = {};
      
      pendingTasks.forEach(t => {
          if (!groups[t.plant_id]) {
              groups[t.plant_id] = {
                  plant_id: t.plant_id,
                  plant_name: t.plant_name,
                  image_url: t.image_url,
                  pending_count: 0
              };
          }
          groups[t.plant_id].pending_count++;
      });
      
      const plantSummaries = Object.values(groups);
      
      const badge = document.getElementById("tasksBadge");
      if (badge) badge.textContent = plantSummaries.length;
      
      if (plantSummaries.length === 0) {
          listEl.innerHTML = `<div class="db-task-empty" style="padding: 24px; text-align: center; color: var(--gray-500);">All plants are healthy and up to date 🌱</div>`;
          return;
      }
      
      listEl.innerHTML = plantSummaries.map(p => {
          const imgSrc = p.image_url ? (p.image_url.startsWith('/') || p.image_url.startsWith('http') ? p.image_url : '/static/' + p.image_url) : "https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=400";
          return `
            <div class="db-task-item" style="cursor:pointer; display:flex; align-items:center; gap:12px; padding:12px; border-bottom:1px solid #e5e8ec; transition: background 0.2s;" onclick="localStorage.setItem('selectedPlantId', ${p.plant_id}); window.location.href='/plant?tab=careplan';" onmouseover="this.style.background='#f9fafb';" onmouseout="this.style.background='transparent';">
              <img class="db-task-item-img" style="width:40px; height:40px; border-radius:8px; object-fit:cover;" src="${imgSrc}" onerror="this.src='https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=400'">
              <div class="db-task-info" style="flex:1;">
                <div class="db-task-plant" style="font-weight:600; color:#111827; margin-bottom: 2px;">${p.plant_name}</div>
                <div class="db-task-label" style="color:#6b7280; font-size:12px;">This plant has ${p.pending_count} tasks today</div>
              </div>
              <span class="db-task-priority priority-high" style="background:#eff6ff; color:#2563eb; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:600;">View Care Plan →</span>
            </div>
          `;
      }).join("");
      
    } catch (e) {
      console.error(e);
      listEl.innerHTML = `<div class="db-task-empty">Failed to load tasks</div>`;
    }
  }

  /* ── MODAL ─────────────────────────────────────────────────────── */
  function openModal() { resetModal(); addPlantModal.classList.remove("hidden"); }
  function closeModal() { addPlantModal.classList.add("hidden"); }
  function resetModal() { showStep("upload"); plantFileInput.value = ""; detectedData = null; selectedFile = null; }
  function showStep(step) {
    uploadStep.style.display  = step === "upload"  ? "block" : "none";
    previewStep.style.display = step === "preview" ? "block" : "none";
    confirmStep.style.display = step === "confirm" ? "block" : "none";
  }

  [addPlantBtn, addPlantBtnSec, emptyAddBtn].forEach(btn => btn?.addEventListener("click", openModal));
  ["closeAddModal", "closePreviewModal", "closeConfirmModal"].forEach(id => {
    document.getElementById(id)?.addEventListener("click", closeModal);
  });
  addPlantModal?.addEventListener("click", (e) => { if (e.target === addPlantModal) closeModal(); });

  /* ── DRAG & DROP ─────────────────────────────────────────────── */
  dropZone?.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone?.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone?.addEventListener("drop", (e) => {
    e.preventDefault(); dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) handleFile(file);
  });
  dropZone?.addEventListener("click", () => plantFileInput.click());
  browseBtn?.addEventListener("click", (e) => { e.stopPropagation(); plantFileInput.click(); });
  plantFileInput?.addEventListener("change", () => { if (plantFileInput.files[0]) handleFile(plantFileInput.files[0]); });

  function handleFile(file) {
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      confirmPreviewImg.src = e.target.result;
      showStep("preview");
      detectPlant(file);
    };
    reader.readAsDataURL(file);
  }

  /* ── DETECT PLANT ──────────────────────────────────────────────── */
  async function detectPlant(file) {
    const msgs = ["Analyzing plant species...", "Checking leaf patterns...", "Matching our database..."];
    let mi = 0;
    const interval = setInterval(() => { if (detectingText) detectingText.textContent = msgs[mi++ % msgs.length]; }, 1500);

    try {
      const fd = new FormData();
      fd.append("image", file);
      fd.append("user_id", user.id);
      const res = await fetch("/api/identify-plant", { method: "POST", body: fd });
      const data = await res.json();
      clearInterval(interval);

      if (data.error) { if (detectingText) detectingText.textContent = "⚠️ " + data.error; return; }

      console.log("Plant name:", data.plant_name || data.name);

      detectedData = data;
      confirmedName.textContent    = data.name;
      confirmedSci.textContent     = data.scientific || "";
      confidenceBadge.textContent  = `${data.confidence}% match`;
      
      const confirmDiseaseName = document.getElementById("confirmDiseaseName");
      const confirmHealthScore = document.getElementById("confirmHealthScore");
      
      if (confirmDiseaseName) {
        confirmDiseaseName.textContent = data.is_healthy ? "Healthy" : data.disease;
        confirmDiseaseName.style.color = data.is_healthy ? "#16a34a" : "#dc2626";
      }
      if (confirmHealthScore) {
        confirmHealthScore.textContent = `${data.health_score || 0}%`;
        confirmHealthScore.style.color = getHealthBarColor(data.health_score || 0);
      }
      
      showStep("confirm");
    } catch(e) {
      clearInterval(interval);
      if (detectingText) detectingText.textContent = "Detection failed. Check your connection.";
    }
  }

  /* ── ADD TO GARDEN ─────────────────────────────────────────────── */
  const scanAgainBtn = document.getElementById("scanAgainBtn");
  if (scanAgainBtn) {
    scanAgainBtn.addEventListener("click", resetModal);
  }

  addToGardenBtn?.addEventListener("click", async () => {
    if (!detectedData) return;
    try {
      const nickname  = document.getElementById("nicknameInput")?.value;
      const location  = document.getElementById("locationInput")?.value;
      const potSize   = document.getElementById("potSizeInput")?.value;
      
      const payload = {
          user_id: user.id,
          name: detectedData.name,
          scientific: detectedData.scientific,
          confidence: detectedData.confidence,
          image_url: detectedData.image_url,
          is_healthy: detectedData.is_healthy,
          disease: detectedData.disease,
          treatment: detectedData.treatment,
          health_score: detectedData.health_score,
          severity: detectedData.severity,
          disease_confidence: detectedData.disease_confidence,
          nickname: nickname,
          location: location,
          pot_size: potSize
      };

      await fetch("/api/plants", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.id}`
        },
        body: JSON.stringify(payload)
      });
      
    } catch(e) { console.error("Error saving plant", e); }
    closeModal();
    await awardXP("add_plant");
    loadPlants();
    showToast("🌿 Plant saved to your garden!", "success");
  });

  /* ── LOAD PLANTS ───────────────────────────────────────────────── */
  async function loadPlants() {
    loadingState.style.display  = "flex";
    plantGrid.style.display     = "none";
    emptyState.style.display    = "none";
    gardenStats.style.display   = "none";
    widgetRow.style.display     = "none";
    plantsSectionHeader.style.display = "none";

    try {
      console.log("Fetching plants for user:", user.id);
      const res = await fetch(`/api/plants`, {
        headers: {
          "Authorization": `Bearer ${user.id}`
        }
      });
      
      const payload = await res.json();
      console.log("API response:", payload);
      loadingState.style.display = "none";

      // Fix mismatch: check for .plants or .data or payload itself
      const plants = payload.plants || payload.data || (Array.isArray(payload) ? payload : []);
      allPlants = Array.isArray(plants) ? plants : [];
      
      console.log("Plants array length:", allPlants.length);
      if (allPlants.length > 0) {
        console.log("First plant structure:", allPlants[0]);
      }

      if (!allPlants.length) {
        emptyState.style.display = "flex";
      } else {
        gardenStats.style.display        = "grid";
        widgetRow.style.display          = "grid";
        plantsSectionHeader.style.display= "flex";
        plantGrid.style.display          = "grid";
        renderPlants(allPlants);
      }
      loadStats();

    } catch(e) {
      console.error("Error in loadPlants:", e);
      loadingState.style.display = "none";
      emptyState.style.display   = "flex";
      showToast("Failed to load plants", "error");
    }
  }

  /* ── RENDER PLANTS ─────────────────────────────────────────────── */
  function renderPlants(plants) {
    plantGrid.innerHTML = "";
    const plantsSubLabel = document.getElementById("plantsSubLabel");
    if (plantsSubLabel) plantsSubLabel.textContent = `${plants.length} plant${plants.length !== 1 ? "s" : ""} in your garden`;

    plants.forEach(p => {
      const score  = p.health_score ?? 0;
      const status = getHealthStatus(p);
      const statusKey = status.cls.replace("status-", "");
      const barColor = getHealthBarColor(statusKey);

      const today     = new Date(); today.setHours(0,0,0,0);
      const nextWater = p.next_watering_date ? new Date(p.next_watering_date) : null;
      const isDue     = nextWater && nextWater <= today;
      const waterLabel = nextWater
        ? isDue ? "⚠️ Due Today" : nextWater.toLocaleDateString("en-US", { month: "short", day: "numeric" })
        : "Not set";

      let imgSrc = p.image_url || "https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=400";
      // [GROWZEN] LOGGING for verification
      console.log(`[GROWZEN] Rendering plant ${p.id} with image: ${imgSrc}`);

      const card = document.createElement("div");
      card.className = "plant-card";
      card.dataset.status = status.label.toLowerCase().replace(" ", "-");
      card.innerHTML = `
        <div class="plant-card-img-wrap">
          <img class="plant-card-img" src="${imgSrc}" alt="${p.name}"
            onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">
          <div class="plant-card-img-placeholder" style="display:none;">🌿</div>
          <div class="plant-card-status-overlay">
            <span class="status-badge ${status.cls}">${status.label}</span>
          </div>
        </div>
        <div class="plant-card-body">
          <div class="plant-card-name-row">
            <div>
              <div class="plant-card-name">${p.name}</div>
              <div class="plant-card-sci">${p.scientific || "Unknown species"}</div>
            </div>
          </div>
          <div class="pc-health-row">
            <span class="pc-health-label">Health</span>
            <div class="pc-health-bar-wrap">
              <div class="pc-health-bar-fill" style="width:${score}%; background:${barColor}"></div>
            </div>
            <span class="pc-health-score" style="color:${barColor}">${score}%</span>
          </div>
          <div class="pc-meta-row">
            <div class="pc-meta-item">
              <span class="pc-meta-label">Next Water</span>
              <span class="pc-meta-val" style="color:${isDue ? '#dc2626' : '#374151'}">${waterLabel}</span>
            </div>
            <div class="pc-meta-item">
              <span class="pc-meta-label">Confidence</span>
              <span class="pc-meta-val">${p.confidence || "—"}%</span>
            </div>
          </div>
          <div class="plant-card-actions">
            <button class="btn-view-plant">View Profile →</button>
            <button class="btn-delete-plant" title="Remove plant">🗑</button>
          </div>
        </div>`;

      card.querySelector(".btn-view-plant").addEventListener("click", (e) => {
        e.stopPropagation();
        localStorage.setItem("selectedPlantId", p.id);
        window.location.href = "/plant";
      });
      card.querySelector(".btn-delete-plant").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`Remove "${p.name}" from your garden?`)) return;
        try {
          await fetch(`/api/plant/${p.id}`, { method: "DELETE" });
          loadPlants();
          showToast("Plant removed");
        } catch(err) { showToast("Failed to remove plant", "error"); }
      });
      card.addEventListener("click", () => {
        localStorage.setItem("selectedPlantId", p.id);
        window.location.href = "/plant";
      });

      plantGrid.appendChild(card);
    });
  }

  /* ── FILTER TABS ─────────────────────────────────────────────── */
  document.querySelectorAll(".db-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".db-filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const filter = btn.dataset.filter;
      document.querySelectorAll(".plant-card").forEach(card => {
        const st = card.dataset.status || "";
        if (filter === "all") {
          card.classList.remove("filtered-out");
        } else if (filter === "healthy") {
          card.classList.toggle("filtered-out", !st.includes("healthy"));
        } else if (filter === "monitor") {
          card.classList.toggle("filtered-out", !st.includes("monitor"));
        } else if (filter === "sick") {
          card.classList.toggle("filtered-out", !st.includes("sick") && !st.includes("attn") && !st.includes("needs"));
        }
      });
    });
  });

  /* ── WEATHER ─────────────────────────────────────────────────── */
  if (typeof initWeatherWidget === "function") {
    initWeatherWidget("#weatherWidgetBody", () => {
      document.getElementById("aiTipBlock").style.display = "block";
      loadAITip();
    });
  }

  document.getElementById("citySubmitBtn")?.addEventListener("click", async () => {
    const city = document.getElementById("cityInput")?.value.trim();
    if (!city) return;
    try {
      const geoRes  = await fetch(`/api/geocode?q=${encodeURIComponent(city)}`);
      const geoData = await geoRes.json();
      if (geoData.lat && geoData.lon) {
        const weatherRes = await fetch(`/api/weather?lat=${geoData.lat}&lon=${geoData.lon}`);
        const data = await weatherRes.json();
        const el = document.getElementById("weatherWidgetBody");
        if (el && typeof buildWeatherHTML === "function") el.innerHTML = buildWeatherHTML(data);
        document.getElementById("locationFormRow").style.display = "none";
        document.getElementById("aiTipBlock").style.display = "block";
        loadAITip(geoData.lat, geoData.lon);
      }
    } catch(e) { showToast("Could not locate city", "error"); }
  });

  async function loadAITip(lat, lon) {
    const tipEl = document.getElementById("aiTipText");
    if (!tipEl) return;
    try {
      const coords = lat && lon ? `?lat=${lat}&lon=${lon}` : "";
      const res    = await fetch(`/api/garden-tip${coords}`, {
        headers: {
          "Authorization": `Bearer ${user.id}`
        }
      });
      const data   = await res.json();
      tipEl.textContent = data.tip || "Keep your plants well-watered and in indirect sunlight today!";
    } catch(e) { tipEl.textContent = "Check moisture levels and ensure adequate sunlight!"; }
  }

  /* ── INIT ────────────────────────────────────────────────────── */
  loadPlants();

  // Handle ?action=scan from global sidebar
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("action") === "scan") {
    setTimeout(openModal, 500); // Small delay to ensure everything is ready
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
