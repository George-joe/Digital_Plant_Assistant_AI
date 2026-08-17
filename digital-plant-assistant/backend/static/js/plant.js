document.addEventListener("DOMContentLoaded", () => {
    const selectedPlantId = localStorage.getItem("selectedPlantId");
    const user = JSON.parse(localStorage.getItem("user"));
    if (!selectedPlantId) { window.location.href = "/dashboard"; return; }
    if (!user) { window.location.href = "/login"; return; }

    // ── DOM refs ──────────────────────────────────────────────────────────
    const backBtn         = document.getElementById("backBtn");
    const plantHeroImg    = document.getElementById("plantHeroImg");
    const plantHeroName   = document.getElementById("plantHeroName");
    const plantHeroSci    = document.getElementById("plantHeroSci");
    const topNavName      = document.getElementById("topNavPlantName");
    const plantStatusPill = document.getElementById("plantStatusPill");
    const heroBadgeStatus = document.getElementById("heroBadgeStatus");
    const heroConfidence  = document.getElementById("heroConfidence");
    const ringScore       = document.getElementById("ringScore");
    const healthRingFill  = document.getElementById("healthRingFill");
    const statDaysGarden  = document.getElementById("statDaysInGarden");
    const healthAlert     = document.getElementById("healthAlertBanner");
    const toast           = document.getElementById("toast");

    let currentPlantData = {
        name: "Loading...",
        scientific: "",
        species: "",
        disease: null,
        disease_name: "",
        last_disease: "",
        confidence: 0,
        health_score: 0,
        status: "Healthy",
        tasks: [],
        timeline: [],
        created_at: new Date().toISOString()
    };
    let tasksDoneCount = 0;
    let totalTasks = 3;

    // ── LOADING HELPERS ───────────────────────────────────────────────────
    function showLoading(msg = "Connecting to GrowZen AI services...") {
        const overlay = document.getElementById("loadingOverlay");
        if (overlay) {
            overlay.classList.remove("fade-out");
            const sub = overlay.querySelector(".loading-sub");
            if (sub) sub.textContent = msg;
        }
    }

    function hideLoading() {
        const overlay = document.getElementById("loadingOverlay");
        if (overlay) {
            overlay.classList.add("fade-out");
            setTimeout(() => { if (overlay) overlay.style.display = "none"; }, 500);
        }
    }

    function showError(msg) {
        const overlay = document.getElementById("errorOverlay");
        const msgEl = document.getElementById("errorMsg");
        if (overlay) overlay.style.display = "flex";
        if (msgEl) msgEl.textContent = msg || "We couldn't load your plant data. Please check your connection.";
        hideLoading();
    }

    // ── Tabs ──────────────────────────────────────────────────────────────
    document.querySelectorAll(".ptab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(`panel-${tab.dataset.tab}`)?.classList.add("active");
        });
    });

    // ptab-link (section-level "view all" links)
    document.querySelectorAll(".ptab-link").forEach(link => {
        link.addEventListener("click", () => {
            const tabId = link.dataset.tab;
            document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
            document.querySelector(`.ptab[data-tab="${tabId}"]`)?.classList.add("active");
            document.getElementById(`panel-${tabId}`)?.classList.add("active");
        });
    });

    backBtn?.addEventListener("click", () => window.location.href = "/dashboard");

    // ── Toast ─────────────────────────────────────────────────────────────
    function showToast(msg, type = "success") {
        if (!toast) return;
        toast.textContent = msg;
        toast.className = `toast show ${type === "error" ? "toast-error" : "toast-success"}`;
        setTimeout(() => toast.classList.remove("show"), 3500);
    }

    // ── SVG Health Ring ───────────────────────────────────────────────────
    function updateHealthRing(score) {
        const plant = currentPlantData;
        const hasDisease = plant?.disease && !plant.disease.toLowerCase().includes("healthy");
        
        let strokeColor;
        if (!hasDisease) strokeColor = "#16a34a"; // Green 600
        else if (score >= 50) strokeColor = "#2563eb"; // Blue 600
        else strokeColor = "#dc2626"; // Red 600

        const circumference = 214; // 2 * π * 34
        const offset = circumference - (score / 100) * circumference;
        if (healthRingFill) {
            healthRingFill.style.strokeDashoffset = offset;
            healthRingFill.style.stroke = strokeColor;
        }
        if (ringScore) ringScore.textContent = score + "%";

        // Also update overview ring if it exists
        const ovRingFill = document.getElementById("ovRingFill");
        if (ovRingFill) {
            ovRingFill.style.strokeDashoffset = 427 - (score / 100) * 427;
            ovRingFill.style.stroke = strokeColor;
        }
        const ovRingScore = document.getElementById("ovRingScore");
        if (ovRingScore) ovRingScore.textContent = score + "%";
    }

    // ── Overview — Metric Row ─────────────────────────────────────────────
    function updateInsightCards(p) {
        const score = p.health_score ?? 0;
        const hasDisease = p.disease && !p.disease.toLowerCase().includes("healthy");

        // Health Score
        const scoreEl = document.getElementById("ovHealthScore");
        const labelEl = document.getElementById("ovHealthLabel");
        const barEl   = document.getElementById("ovHealthBar");
        
        let barColor, healthLabel;
        if (!hasDisease) {
            barColor = "#16a34a";
            healthLabel = "Excellent condition";
        } else if (score >= 50) {
            barColor = "#2563eb";
            healthLabel = "Monitor closely";
        } else {
            barColor = "#dc2626";
            healthLabel = "Critical — act now";
        }

        if (scoreEl) scoreEl.textContent = `${score}%`;
        if (labelEl) labelEl.textContent = healthLabel;
        if (barEl) {
            barEl.style.width = `${score}%`;
            barEl.style.background = barColor;
        }

        // Disease Status Table
        const diseaseStatusEl = document.getElementById("ovDiseaseStatus");
        const diseaseTagEl = document.getElementById("ovDiseaseTag");
        const diseaseSubEl = document.getElementById("ovDiseaseSub");

        if (diseaseStatusEl) {
            diseaseStatusEl.textContent = hasDisease ? (p.disease || "Issues detected") : "No Issues";
        }
        if (diseaseTagEl) {
            if (!hasDisease) {
                diseaseTagEl.textContent = "Healthy";
                diseaseTagEl.className = "metric-tag metric-tag-success";
            } else if (score >= 50) {
                diseaseTagEl.textContent = "Monitor";
                diseaseTagEl.className = "metric-tag metric-tag-info";
            } else {
                diseaseTagEl.textContent = "Sick";
                diseaseTagEl.className = "metric-tag metric-tag-error";
            }
        }
        if (diseaseSubEl) {
            const scanDate = p.lastScan || p.last_scanned;
            diseaseSubEl.textContent = scanDate ? `Last scan: ${new Date(scanDate).toLocaleDateString()}` : "Last scan: never";
        }

        // Water Status
        const nextWater = p.next_watering_date ? new Date(p.next_watering_date) : null;
        const today = new Date();
        const daysUntil = nextWater ? Math.ceil((nextWater - today) / 86400000) : null;
        const ovWaterNext = document.getElementById("ovWaterNext");
        const ovWaterSub  = document.getElementById("ovWaterSub");
        const ovWaterTag  = document.getElementById("ovWaterTag");
        if (ovWaterNext) ovWaterNext.textContent = nextWater ? nextWater.toLocaleDateString() : "Not set";
        if (ovWaterSub) ovWaterSub.textContent = p.water_freq ? `Every ${p.water_freq} days` : "Schedule not set";
        if (ovWaterTag) {
            if (!nextWater) {
                ovWaterTag.textContent = "Not scheduled";
                ovWaterTag.className = "metric-tag metric-tag-warn";
            } else if (daysUntil < 0) {
                ovWaterTag.textContent = "Overdue";
                ovWaterTag.className = "metric-tag metric-tag-error";
            } else if (daysUntil === 0) {
                ovWaterTag.textContent = "Water today";
                ovWaterTag.className = "metric-tag metric-tag-warn";
            } else {
                ovWaterTag.textContent = `In ${daysUntil}d`;
                ovWaterTag.className = "metric-tag";
            }
        }

        // Sunlight
        const ovSunPref = document.getElementById("ovSunPreference");
        const ovSunTag  = document.getElementById("ovSunTag");
        if (ovSunPref) ovSunPref.textContent = p.sunlight || "Indirect Light";
        if (ovSunTag)  ovSunTag.textContent = "Optimal";
    }
 
    function updateOverviewPanel(p) {
        const score = p.health_score ?? p.healthScore ?? 0;
        const diseaseName = p.disease || p.disease_name || p.last_disease;
        const hasDisease = diseaseName && !diseaseName.toLowerCase().includes("healthy");

        let statusText, statusClass, badgeClass, healthColor, healthLevel;
        if (!hasDisease) {
            statusText = "Healthy";
            statusClass = "status-healthy";
            badgeClass = "badge-green";
            healthColor = "#16a34a"; // Green 600
            healthLevel = "Excellent";
        } else if (score >= 50) {
            statusText = "Monitor";
            statusClass = "status-monitor";
            badgeClass = "badge-blue";
            healthColor = "#2563eb"; // Blue 600
            healthLevel = "Good";
        } else {
            statusText = "Sick";
            statusClass = "status-sick";
            badgeClass = "badge-red";
            healthColor = "#dc2626"; // Red 600
            healthLevel = "Critical";
        }

        // HEALTH CARD + CIRCLE LOGIC
        // Sync Health Ring
        const ringFill  = document.getElementById("ovRingFill");
        const ringScore = document.getElementById("ovRingScore");
        if (ringFill) {
            const circumference = 427; 
            const offset = circumference - (score / 100) * circumference;
            ringFill.style.strokeDashoffset = offset;
            ringFill.style.stroke = healthColor;
        }
        if (ringScore) ringScore.textContent = `${score}%`;

        // Sync Health Card
        const $ = id => document.getElementById(id);
        if ($("ovCardHealth")) $("ovCardHealth").textContent = `${score}%`;
        if ($("ovCardHealthSub")) $("ovCardHealthSub").textContent = `${healthLevel} condition`;
        if ($("ovCardHealthBar")) {
            $("ovCardHealthBar").style.width = `${score}%`;
            $("ovCardHealthBar").style.background = healthColor;
        }

        // DISEASE CARD
        const actualDisease = diseaseName || "No Issues";
        if ($("ovCardDisease")) $("ovCardDisease").textContent = actualDisease;
        const scanDate = p.lastScan || p.last_scanned;
        if ($("ovCardDiseaseSub")) $("ovCardDiseaseSub").textContent = scanDate ? `Scanned: ${new Date(scanDate).toLocaleDateString()}` : "No scan yet";
        if ($("ovCardDiseaseChip")) {
            $("ovCardDiseaseChip").textContent = statusText;
            $("ovCardDiseaseChip").className = `ov-card-chip badge ${badgeClass}`;
        }
        
        // Sync Top Status Pill too for consistency
        const ovStatusBadge = $("ovStatusBadge");
        if (ovStatusBadge) {
            ovStatusBadge.innerHTML = `<span class="ov-status-dot" style="background:${healthColor}"></span>${statusText}`;
            ovStatusBadge.className = `ov-status-badge ${statusClass}`;
        }

        // PART 4: WATERING CARD
        const lastWateredStr = p.last_watered_at || p.last_watered || p.schedule?.last_watered;
        const intervalDays = p.watering_interval || p.schedule?.watering_interval || p.schedule?.water_frequency_days || 7;
        let lastWatered = lastWateredStr ? new Date(lastWateredStr) : null;
        let nextWater = null;
        if (lastWatered) {
             nextWater = new Date(lastWatered.getTime());
             nextWater.setDate(nextWater.getDate() + intervalDays);
        }
        const daysUntil = nextWater ? Math.ceil((nextWater - new Date()) / 86400000) : null;
        
        if ($("ovCardWater")) $("ovCardWater").textContent = nextWater ? nextWater.toLocaleDateString() : "Not set";
        if ($("ovCardWaterSub")) {
            if (lastWateredStr) {
                // strictly display the date and time
                $("ovCardWaterSub").textContent = `Last watered: ${lastWatered.toLocaleString()}`;
            } else {
                $("ovCardWaterSub").textContent = "Not watered yet";
            }
        }
        if ($("ovCardWaterChip")) {
            if (!nextWater) { 
                $("ovCardWaterChip").textContent = "Not Set"; 
                $("ovCardWaterChip").className = "ov-card-chip ov-chip-warn"; 
            } else if (daysUntil < 0) { 
                $("ovCardWaterChip").textContent = "Overdue"; 
                $("ovCardWaterChip").className = "ov-card-chip ov-chip-error"; 
            } else if (daysUntil === 0) { 
                $("ovCardWaterChip").textContent = "Due Today"; 
                $("ovCardWaterChip").className = "ov-card-chip ov-chip-warn"; 
            } else { 
                $("ovCardWaterChip").textContent = `In ${daysUntil}d`; 
                $("ovCardWaterChip").className = "ov-card-chip"; 
            }
        }

        // AI Insight
        const aiInsightEl = $("ovAiInsight");
        if (aiInsightEl) {
            if (hasDisease) {
                aiInsightEl.textContent = `🚨 Critical: ${diseaseName} detected. Your plant's health is at ${score}%. Apply the recommended treatment from your Care Plan immediately.`;
            } else if (score < 85) {
                aiInsightEl.textContent = `⚠️ Moderate: Your plant is recovering. Health improved to ${score}%. Monitor moisture levels and ensure adequate light.`;
            } else {
                aiInsightEl.textContent = `✅ Healthy: Great job! Your plant is at ${score}% health. Maintain its current environment and watering schedule for optimal growth.`;
            }
        }

        // PART 5 & 6: TODAY'S TASKS
        loadCareTasks();

        // PART 7: HEALTH TREND -> ATIVITY SUMMARY (computed only)
        const trendContainer = document.getElementById("ovMiniTrendChart")?.parentElement;
        if (trendContainer) {
            const userStreak = user.streak_days || user.streak || 0;
            const lwStr = p.last_watered_at || p.last_watered || p.schedule?.last_watered;
            const lwDate = lwStr ? new Date(lwStr).toLocaleDateString() : 'Never';
            const lsDate = (p.last_scanned || p.lastScan) ? new Date(p.last_scanned || p.lastScan).toLocaleDateString() : 'Never';
            
            trendContainer.innerHTML = `
                <div style="display:flex; flex-direction:column; justify-content:center; height:100%; border:1px solid var(--border-color); border-radius:12px; padding:16px;">
                    <h4 style="margin:0 0 10px 0; font-size:14px; font-weight:600; color:var(--text-100);">Activity Summary</h4>
                    <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px; color: var(--text-200); line-height:1.8;">
                        <li>✅ Tasks done today: <strong>${tasksDoneCount} of ${totalTasks}</strong></li>
                        <li>💧 Last watered: <strong>${lwDate}</strong></li>
                        <li>🔍 Last scanned: <strong>${lsDate}</strong></li>
                        <li>🔥 Current streak: <strong style="color:#f59e0b">${userStreak} days</strong></li>
                    </ul>
                </div>
            `;
        }
        
        // Disable water button if under 7 hours
        const wBtn = document.getElementById("waterNowBtn");
        if (wBtn) {
            const isDisabled = p.last_watered_at && (Date.now() - new Date(p.last_watered_at)) < 7 * 60 * 60 * 1000;
            if (isDisabled) {
                wBtn.disabled = true;
                wBtn.style.opacity = "0.5";
                wBtn.style.cursor = "not-allowed";
                wBtn.textContent = "Watered Recently";
            } else {
                wBtn.disabled = false;
                wBtn.style.opacity = "1";
                wBtn.style.cursor = "pointer";
                wBtn.innerHTML = '<span class="icon">💧</span> Water Now';
            }
        }
    }


    // Backwards-compatible dummy wrapper for old instances calling it directly
    function renderTrendAndCompare(data, score) {
        // Obsoleted. Replaced by Activity Summary.
    }

    // Wire overview diagnose button to the heroDiagnoseBtn scroll/click
    document.getElementById("ovDiagnoseBtn")?.addEventListener("click", () => {
        document.getElementById("heroDiagnoseBtn")?.click();
        console.log(`[DEBUG] ovDiagnoseBtn clicked, triggering heroDiagnoseBtn click.`);
    });

    // Wire water now button explicitly
    document.getElementById("waterNowBtn")?.addEventListener("click", async (e) => {
        e.preventDefault();
        const btn = e.currentTarget;
        if (btn.disabled) return;
        btn.disabled = true;
        btn.innerHTML = '<span class="icon">💧</span> Watering...';

        try {
            const res = await fetch(`/api/plant/${selectedPlantId}/water`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${user.id}` }
            });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, "success");
                // Update local XP
                const localUser = JSON.parse(localStorage.getItem("user") || "{}");
                if (localUser.xp_points !== undefined) {
                    localUser.xp_points += (data.xp_earned || 5);
                    localStorage.setItem("user", JSON.stringify(localUser));
                    if (window.updateUserHeader) window.updateUserHeader();
                }
                await loadPlantData();
                await loadCareTasks();
            } else {
                showToast(data.error || "Failed to water plant", "error");
                btn.disabled = false;
                btn.innerHTML = '<span class="icon">💧</span> Water Now';
            }
        } catch(err) {
            console.error("Watering Error:", err);
            showToast("Network error trying to water plant", "error");
            btn.disabled = false;
            btn.innerHTML = '<span class="icon">💧</span> Water Now';
        }
    });

    // Wire ov-view-all buttons to switch tabs
    document.querySelectorAll(".ov-view-all[data-goto-tab]").forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.dataset.gotoTab;
            console.log(`[DEBUG] ov-view-all button clicked. Switching to tab: ${tabId}`);
            document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
            document.querySelector(`.ptab[data-tab="${tabId}"]`)?.classList.add("active");
            document.getElementById(`panel-${tabId}`)?.classList.add("active");
        });
    });



    // ── Load plant data — REFACTORED FOR SPEED & STABILITY ────────────────
    async function loadPlantData() {
        console.log(`[GROWZEN] API Start: Fetching core data for plant_id: ${selectedPlantId}`);
        showLoading("Gathering Plant Insights...");

        try {
            // STEP 1: Fetch ONLY core plant data first (Blocking for UI start)
            const plantRes = await fetch(`/api/plant/${selectedPlantId}`, { 
                headers: { "Authorization": `Bearer ${user.id}` } 
            });

            if (!plantRes.ok) {
                console.error(`[GROWZEN] Plant API Error: ${plantRes.status}`);
                throw new Error(`Critical: Could not load plant details (Status ${plantRes.status})`);
            }
            const jsonRes = await plantRes.json();
            
            // Build plant object safely — always guarantee all fields exist
            const flatData = jsonRes.data || {};
            const nestedPlant = (flatData && typeof flatData === 'object' && flatData.plant) ? flatData.plant : {};
            const plant = {
                name: "Unknown Plant",
                status: "Healthy",
                health_score: 0,
                confidence: 0,
                ...nestedPlant,
                // Top-level fields take priority for these critical fields:
                disease: flatData.disease || nestedPlant.disease || nestedPlant.disease_name || nestedPlant.last_disease || null,
                confidence: flatData.confidence ?? nestedPlant.confidence ?? 0,
                last_scanned: flatData.last_scanned || nestedPlant.last_scanned || null,
                last_watered_at: flatData.last_watered_at || nestedPlant.last_watered_at || null
            };
            console.log("PLANT:", plant); 

            if (jsonRes.error) {
                showError(jsonRes.error);
                return;
            }

            // NO caching of old state (PART 6)
            currentPlantData = plant;
            const p = plant;

            // STEP 2: Render Core UI IMMEDIATELY
            if (topNavName) topNavName.textContent = p.name || "My Plant";
            if (plantHeroName) plantHeroName.textContent = p.name || "My Plant";
            if (plantHeroSci) plantHeroSci.textContent = p.scientific || p.species || "";

            const statusClass = p.status?.toLowerCase() === "sick" ? "badge-red" : p.status?.toLowerCase() === "needs attention" ? "badge-amber" : "badge-green";
            if (plantStatusPill) { plantStatusPill.textContent = p.status || "Healthy"; plantStatusPill.className = `badge ${statusClass}`; }
            if (heroBadgeStatus) { heroBadgeStatus.textContent = p.status || "Healthy"; heroBadgeStatus.className = `badge ${statusClass}`; }
            if (heroConfidence) heroConfidence.textContent = p.confidence || 0;

            if (plantHeroImg) {
                const imgSource = p.image || p.image_url;
                if (imgSource) {
                    plantHeroImg.src = imgSource.startsWith("http") || imgSource.startsWith("/uploads/")
                        ? imgSource : "/uploads/" + imgSource;
                }
            }

            const score = p.health_score ?? 0;
            requestAnimationFrame(() => updateHealthRing(score));

            const lastScanEl = document.getElementById("lastScanTime");
            if (lastScanEl) lastScanEl.textContent = p.last_scanned ? new Date(p.last_scanned).toLocaleDateString() : "Never";
            if (statDaysGarden) {
                const age = Math.floor((new Date() - new Date(p.created_at)) / 86400000);
                statDaysGarden.textContent = `${age}d`;
            }

            if (typeof updateGrowthStageBar === 'function') updateGrowthStageBar(p.growth_stage);
            const stageLabel = document.getElementById("statGrowthStage");
            if (stageLabel) stageLabel.textContent = p.growth_stage || "Seedling";

            if (score < 50 && healthAlert) {
                healthAlert.style.display = "flex";
                const alertMsg = document.getElementById("healthAlertMsg");
                if (alertMsg) alertMsg.textContent = `${p.name} health is low (${score}%). Run a diagnosis.`;
            }

            // Safe guards for functions that may not be defined:
            // updateInsightCards and syncCarePlanFields are stub-guarded
            try { if (typeof updateInsightCards === 'function') updateInsightCards(p); } catch(e) { console.warn("updateInsightCards err:", e); }
            try { if (typeof syncCarePlanFields === 'function') syncCarePlanFields(p); } catch(e) { console.warn("syncCarePlanFields err:", e); }
            try { updateOverviewPanel(p); } catch(e) { console.warn("updateOverviewPanel err:", e); }

            // STEP 3: RELEASE UI BARRIER (HIDE LOADER)
            console.log("[GROWZEN] Core UI Ready. Releasing loader.");
            hideLoading();

            // STEP 4: FETCH SECONDARY DATA ASYNC (NON-BLOCKING)
            console.log("[GROWZEN] Initiating secondary fetches in background...");
            
            // Timeline
            loadTimeline(); 
            
            // Tasks
            loadCareTasks();

            // Reminders
            if (typeof loadReminders === 'function') loadReminders();

            // AI Advice & Weather (Async with timeout)
            if (typeof initWeatherWidget === "function") initWeatherWidget("#plantWeatherBody");
            setTimeout(() => {
                console.log("[GROWZEN] Start Background AI Advice...");
                if (typeof loadSmartAdvice === 'function') loadSmartAdvice(p);
            }, 500);

        } catch(e) {
            console.error("[GROWZEN] Critical Loading Error:", e);
            showError("We encountered a problem loading your plant. Please try refreshing or check your connection.");
        }
    }


    // Helper to render tasks from data (extracted from loadCareTasks)
    function renderTaskItems(tasks) {
        const list = document.getElementById("dailyTasksList");
        const treatmentList = document.getElementById("carePlanTreatmentList");
        
        if (!list && !treatmentList) return;

        if (list) {
            if (tasks.length === 0) {
                list.innerHTML = `<div class="empty-state-sm">No tasks for this plant</div>`;
            } else {
                list.innerHTML = tasks.map(t => {
                    const isDone = t.completed !== undefined ? t.completed : t.is_completed;
                    const displayTitle = t.title || t.label || 'Task';
                    const iconHtml = t.task_type.toLowerCase().includes("water") 
                        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C6 8 4 13 4 16a8 8 0 0016 0c0-3-2-8-8-14z"/></svg>`
                        : t.task_type.toLowerCase().includes("environment") || t.task_type.toLowerCase().includes("sun")
                        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></svg>`
                        : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;

                    return `
                        <div class="task-item ${isDone ? 'completed' : ''}" id="task-${t.id}">
                            <button class="task-check ${isDone ? 'checked' : ''}" 
                                onclick="completeTaskWithAnim(${t.id}, this)" 
                                ${isDone ? 'disabled' : ''}
                                aria-label="Mark task done"></button>
                            <div class="task-item-icon task-icon-${t.task_type.toLowerCase().includes("water") ? "water" : t.task_type.toLowerCase().includes("sun") ? "sun" : "inspect"}">${iconHtml}</div>
                            <div class="task-item-info">
                                <div class="task-item-name" style="${isDone ? 'text-decoration:line-through; color:var(--gray-500);' : ''}">${displayTitle}</div>
                                <div class="task-item-desc">${t.task_type}</div>
                            </div>
                            <span class="task-freq-badge">${isDone ? 'Done' : 'Today'}</span>
                        </div>`;
                }).join("");
            }
        }
        
        // Hide Treatment Section entirely to meet PART 4 specs (rendering all tasks in Today's Tasks list)
        const treatmentSection = document.getElementById("treatmentSection");
        if (treatmentSection) {
            treatmentSection.style.display = "none";
        }
        
        tasksDoneCount = tasks.filter(t => t.completed !== undefined ? t.completed : t.is_completed).length;
        totalTasks = tasks.length;
        updateTaskProgress();
    }

    // Helper for Care Plan fields
    function syncCarePlanFields(p) {
        const cpWatering  = document.getElementById("cpWatering");
        const cpNextWater = document.getElementById("cpNextWater");
        const cpWaterFreqEdit = document.getElementById("cpWaterFreqEdit");
        const taskWaterDesc   = document.getElementById("taskWaterDesc");
        const nextWater = p.next_watering_date ? new Date(p.next_watering_date) : null;
        if (cpWatering) cpWatering.textContent = p.water_freq ? `Every ${p.water_freq} days` : "Every 7 days";
        if (cpNextWater) cpNextWater.textContent = nextWater ? nextWater.toLocaleDateString() : "—";
        if (cpWaterFreqEdit) cpWaterFreqEdit.value = p.water_freq || 7;
        if (taskWaterDesc) taskWaterDesc.textContent = nextWater && new Date(nextWater) <= new Date() ? "Overdue — water now!" : `Next: ${nextWater ? nextWater.toLocaleDateString() : "not scheduled"}`;
        const chatPlantName = document.getElementById("chatPlantName");
        if (chatPlantName) chatPlantName.textContent = p.name;
    }

    // Helper for Reminders
    function renderReminderItems(reminders) {
        const list = document.getElementById("remindersList2");
        if (!list) return;
        if (!reminders || !reminders.length) {
            list.innerHTML = `<div style="color:var(--gray-400);font-size:13px;padding:12px 0;">No active reminders for this plant.</div>`;
            return;
        }
        list.innerHTML = reminders.map(r => `
            <div class="reminder-item" style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:var(--bg-100); border-radius:8px; margin-bottom:8px; border:1px solid var(--border-color);">
                <div class="reminder-item-info" style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:16px;">${r.reminder_type === "telegram" ? "🔹" : "📱"}</span>
                    <div style="display:flex; flex-direction:column;">
                        <span style="font-weight:600; font-size:14px;">${r.reminder_time}</span>
                        <span style="font-size:11px; color:var(--gray-500); text-transform:capitalize;">${r.repeat.replace(/_/g, ' ')}</span>
                    </div>
                </div>
                <button class="btn btn-ghost btn-sm" onclick="deleteReminder(${r.id})" style="color:var(--danger); padding:4px;">✕</button>
            </div>`).join("");
    }

    // ── refreshUI: Force-render ALL DOM elements from currentPlantData ────
    function refreshUI() {
        const p = currentPlantData;
        if (!p || !p.name) return;

        console.log("FINAL PLANT STATE:", JSON.parse(JSON.stringify(p)));

        // Name
        const displayName = (p.name && p.name !== "Loading...") ? p.name : (p.scientific || p.species || "My Plant");
        if (topNavName)     topNavName.textContent = displayName;
        if (plantHeroName)  plantHeroName.textContent = displayName;
        if (plantHeroSci)   plantHeroSci.textContent = p.scientific || p.species || "";
        const chatName = document.getElementById("chatPlantName");
        if (chatName) chatName.textContent = displayName;

        // Image
        if (plantHeroImg && p.image_url) {
            console.log(`[GROWZEN] Rendering plant hero with image_url: ${p.image_url}`);
            plantHeroImg.src = p.image_url;
        }

        // Bug 6 Fix: normalize both camelCase (from diagnose API) and snake_case (from database GET)
        const score = p.healthScore ?? p.health_score ?? 0;
        if (ringScore) ringScore.textContent = score + "%";
        requestAnimationFrame(() => updateHealthRing(score));

        // Status logic
        const hasDisease = p.disease && !p.disease.toLowerCase().includes("healthy");
        const healthScore = p.health_score ?? 0;
        
        let statusText, statusClass;
        if (!hasDisease) {
            statusText = "Healthy";
            statusClass = "badge-green";
        } else if (healthScore >= 50) {
            statusText = "Monitor";
            statusClass = "badge-blue";
        } else {
            statusText = "Sick";
            statusClass = "badge-red";
        }
        
        if (plantStatusPill) { plantStatusPill.textContent = statusText; plantStatusPill.className = `badge ${statusClass}`; }
        if (heroBadgeStatus) { heroBadgeStatus.textContent = statusText; heroBadgeStatus.className = `badge ${statusClass}`; }

        // Confidence
        if (heroConfidence) heroConfidence.textContent = p.confidence ? p.confidence + "%" : "0%";

        // Last scan
        const lastScanEl = document.getElementById("lastScanTime");
        const scanDate = p.lastScan || p.last_scanned;
        if (lastScanEl) lastScanEl.textContent = scanDate ? new Date(scanDate).toLocaleDateString() : "Never";

        // Overview panel (ring, badges, insight cards)
        updateInsightCards(p);
        updateOverviewPanel(p);
    }

    // ── CARE TASKS ────────────────────────────────────────────────────────
    window.completeTaskWithAnim = async function(taskId, el) {
        if (!el || el.classList.contains("checked")) return;
        const item = el.closest(".task-item") || el.closest(".ov-task-item") || el.closest(".treatment-item");
        if (!item) return;

        // Visual feedback
        el.classList.add("checked");
        item.classList.add("completed");
        
        try {
            const res = await fetch(`/api/tasks/${taskId}/complete`, { 
                method: "POST",
                headers: { "Authorization": `Bearer ${user.id}` }
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message || "Task completed!", "success");
                
                // Refresh local XP
                const localUser = JSON.parse(localStorage.getItem("user") || "{}");
                if (localUser.xp_points !== undefined) {
                    localUser.xp_points += (data.xp_earned || 10);
                    localStorage.setItem("user", JSON.stringify(localUser));
                    if (window.updateUserHeader) window.updateUserHeader();
                }

                // Refresh UI (Single Source of Truth)
                await loadPlantData();
                await loadCareTasks();
            }
        } catch(e) {
            console.error("Task completion error", e);
            item.classList.remove("completed");
            el.classList.remove("checked");
        }
    };

    window.toggleCareTask = function(checkEl, taskId) {
        window.completeTaskWithAnim(taskId, checkEl);
    };

    async function loadCareTasks() {
        if (!currentPlantData || !currentPlantData.id) return;
        console.log(`[GROWZEN] Fetching tasks for plant_id: ${currentPlantData.id}`);
        try {
            // [FIX] PART 5: Fetch from SAME API as Dashboard
            const res = await fetch(`/api/tasks?plant_id=${currentPlantData.id}`, {
                headers: { "Authorization": `Bearer ${user.id}` }
            });
            const data = await res.json();
            const tasks = data.tasks || [];
            
            // [MANDATORY DEBUG]
            console.log("CURRENT PLANT ID:", currentPlantData.id);
            console.log("ALL TASKS:", tasks);
            
            // [FIX] PART 2: Strict filter by plant_id
            const plantTasks = tasks.filter(
                (task) => String(task.plant_id) === String(currentPlantData.id)
            );
            
            // [MANDATORY DEBUG]
            console.log("FILTERED TASKS:", plantTasks);
            
            renderTaskItems(plantTasks);
        } catch(e) { console.error("[GROWZEN] Error loading tasks:", e); }
    }

    window.handleTaskClick = function(type) {
        const t = (type || "").toLowerCase();
        if (t.includes("water")) {
            // Already on care plan or overview, scroll to watering if on careplan
            const panel = document.getElementById("panel-careplan");
            if (panel && panel.classList.contains("active")) {
                document.querySelector(".watering-schedule-section")?.scrollIntoView({ behavior: "smooth" });
            } else {
                // Switch to careplan
                document.querySelector('[data-tab="careplan"]')?.click();
            }
        } else if (t.includes("diagnos") || t.includes("scan") || t.includes("photo")) {
            document.querySelector('[data-tab="timeline"]')?.click();
        } else if (t.includes("treatment")) {
            document.querySelector('[data-tab="careplan"]')?.click();
        }
    };

    function updateGrowthStageBar(stage) {
        const stages = ["seedling", "juvenile", "mature", "thriving"];
        const idx = stages.indexOf((stage || "seedling").toLowerCase());
        stages.forEach((_, i) => {
            const el = document.getElementById(`stage${i}`);
            if (el) el.classList.toggle("active", i <= idx);
        });
        // Update progress bar
        const fill = document.getElementById("growthStageBarFill");
        const pct = idx < 0 ? 12.5 : (idx / (stages.length - 1)) * 100;
        if (fill) fill.style.width = pct + "%";
    }

    // ── Smart advice ──────────────────────────────────────────────────────
    async function loadSmartAdvice(plant) {
        const recoBody = document.getElementById("smartRecoBody");
        const ovInsight = document.getElementById("ovAiInsight");
        if (!recoBody && !ovInsight) return;
        
        console.log(`[GROWZEN] AI Start: Fetching smart advice for: ${plant.name}`);
        
        // Local loader UI
        const loaderHtml = `<div class="ai-local-loader"><span class="ai-sparkle">✨</span> Analyzing ${plant.name} health and weather...</div>`;
        if (recoBody) recoBody.innerHTML = loaderHtml;
        if (ovInsight) ovInsight.innerHTML = loaderHtml;

        // Timer to prevent UI block if AI is slow
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.warn("[GROWZEN] AI Insight Timeout (6s) reached.");
            controller.abort();
        }, 6000); 

        try {
            const lat = 19.076, lon = 72.877;
            const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`, {
                headers: { "Authorization": `Bearer ${user.id}` },
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
            const weather = await res.json();
            console.log("[GROWZEN] AI Insight Response:", weather);

            if (weather.ok) {
                const adviceHtml = `
                    <div style="margin-bottom:10px; font-size:13px;"><strong>${weather.city}:</strong> ${weather.condition}, ${weather.temp}°C</div>
                    <div class="advice-highlight">${weather.advice}</div>`;
                
                if (recoBody) {
                    recoBody.innerHTML = adviceHtml + 
                        `<div style="margin-top:10px;font-size:12px;color:var(--gray-500);">Based on your <strong>${plant.name}</strong> profile and today's weather.</div>`;
                }
                if (ovInsight) {
                    ovInsight.innerHTML = weather.advice;
                }
            } else {
                const failHtml = `<div class="empty-state-sm" style="color:var(--gray-500);">AI insights unavailable right now.</div>`;
                if (recoBody) recoBody.innerHTML = failHtml;
                if (ovInsight) ovInsight.textContent = "AI insights unavailable.";
            }
        } catch(e) { 
            console.error("[GROWZEN] AI Advice Error:", e);
            const errHtml = `<div class="empty-state-sm" style="color:var(--gray-500);">AI insights unavailable (timed out or connection error).</div>`;
            if (recoBody) recoBody.innerHTML = errHtml;
            if (ovInsight) ovInsight.textContent = "AI insights unavailable (timed out).";
        }
    }

    // ── WATER NOW (STEP 6: droplet + bounce + XP popup) ──────────────────
    const waterNowBtn = document.getElementById("waterNowBtn");
    waterNowBtn?.addEventListener("click", async (e) => {
        try {
            const res = await fetch(`/api/plant/${selectedPlantId}/water`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${user.id}`
                }
            });
            const data = await res.json();

            if (!res.ok) {
                if (data.error === "Already watered recently") {
                    showToast(`Already watered! Wait ${data.wait_time}`, "warning");
                    return;
                }
                throw new Error(data.error || "Watering failed");
            }

            // Success Animation
            waterNowBtn.style.transform = "scale(1.25)";
            waterNowBtn.style.transition = "transform 0.15s cubic-bezier(.4,1.6,.6,1)";
            setTimeout(() => { waterNowBtn.style.transform = "scale(1)"; }, 300);

            // Droplet particles
            const rect = waterNowBtn.getBoundingClientRect();
            for (let d = 0; d < 5; d++) {
                const drop = document.createElement("div");
                drop.textContent = "💧";
                drop.style.cssText = `position:fixed;font-size:18px;pointer-events:none;z-index:9999;
                    left:${rect.left + rect.width/2 + (Math.random()-0.5)*40}px;
                    top:${rect.top}px;
                    animation:dropletFall 0.9s ease-in forwards;
                    animation-delay:${d*80}ms;`;
                document.body.appendChild(drop);
                setTimeout(() => drop.remove(), 1200);
            }

            // XP Popup
            const xpPop = document.createElement("div");
            xpPop.textContent = "+10 XP 🌱";
            xpPop.style.cssText = `position:fixed;font-size:14px;font-weight:700;color:#16a34a;
                left:${rect.left + rect.width/2 - 30}px;
                top:${rect.top - 10}px;
                background:#dcfce7;border-radius:20px;padding:4px 12px;
                border:1px solid #bbf7d0;z-index:9999;
                animation:xpRise 1.2s ease-out forwards;pointer-events:none;`;
            document.body.appendChild(xpPop);
            setTimeout(() => xpPop.remove(), 1300);

            showToast("💧 Plant watered! +10 XP");
            await loadPlantData(); 
            await loadCareTasks();
        } catch(err) {
            console.error("Watering Error:", err);
            showToast(err.message || "Failed to water plant", "error");
        }
    });

    // ── HERO DIAGNOSE BUTTON → Go to Timeline & trigger upload (STEP 3) ──
    document.getElementById("heroDiagnoseBtn")?.addEventListener("click", () => {
        // Switch to Timeline tab
        document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
        document.querySelector('[data-tab="timeline"]')?.classList.add("active");
        document.getElementById("panel-timeline")?.classList.add("active");
        setTimeout(() => {
            document.getElementById("dropZone")?.scrollIntoView({ behavior: "smooth", block: "center" });
            document.getElementById("timelinePhotoInput")?.click();
        }, 300);
    });

    // Also wire the old overview diagnose button

    // ── DAILY TASKS ───────────────────────────────────────────────────────
    window.toggleTask = function(checkEl, taskId) {
        //taskId here might be a string ID like 'task-water', we need to find the numeric ID if possible
        // but toggleTask is legacy, we use completeTaskWithAnim now.
        // For compatibility with hardcoded HTML if any:
        if (taskId === 'task-water') {
            autoTriggerTask("Watering");
        }
    };

    async function autoTriggerTask(type) {
        try {
            const res = await fetch(`/api/plant/${selectedPlantId}/tasks`, {
                headers: { "Authorization": `Bearer ${user.id}` }
            });
            const data = await res.json();
            const tasks = data.tasks || [];
            const target = tasks.find(t => t.task_type.toLowerCase().includes(type.toLowerCase()) && !t.is_completed);
            if (target) {
                // Find element in UI to animate
                const el = document.querySelector(`[onclick*="toggleCareTask(this, ${target.id})"]`) || 
                           document.querySelector(`[onclick*="completeTaskWithAnim(${target.id}, this)"]`);
                
                if (el) {
                    window.completeTaskWithAnim(target.id, el);
                } else {
                    // Just hit API if no element found
                    await fetch(`/api/tasks/${target.id}/complete`, { 
                        method: "POST",
                        headers: { "Authorization": `Bearer ${user.id}` }
                    });
                    loadCareTasks();
                    showToast(`${type} task completed!`, "success");
                }
            }
        } catch(e) { console.error("Auto trigger error", e); }
    }

    function updateTaskProgress() {
        const badge = document.getElementById("taskProgressBadge");
        const fill  = document.getElementById("taskProgressFill");
        if (badge) badge.textContent = `${tasksDoneCount} of ${totalTasks} done`;
        if (fill)  fill.style.width  = `${(tasksDoneCount / totalTasks) * 100}%`;
    }

    // ── PHOTO TIMELINE ────────────────────────────────────────────────────
    let activeMode = "weekly";
    document.querySelectorAll(".tmode-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tmode-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeMode = btn.dataset.mode;
            document.querySelectorAll(".tlmode-ui").forEach(ui => ui.style.display = "none");
            const uiEl = document.getElementById(`${activeMode}UploadUI`);
            if (uiEl) uiEl.style.display = "flex";
            const desc = document.getElementById("timelineDesc");
            if (desc) {
                const msgs = {
                    weekly: "Upload a weekly photo to track your plant's journey. AI will compare each photo automatically.",
                    custom: "Set a custom upload interval and track your plant at your own pace.",
                    manual: "Upload older photos by selecting their original date — great for catching up on your plant's timeline."
                };
                desc.textContent = msgs[activeMode] || "";
            }
        });
    });

    const fileInput = document.getElementById("timelinePhotoInput");
    function triggerUpload() { if (fileInput) fileInput.click(); }
    document.getElementById("uploadWeeklyPhotoBtn")?.addEventListener("click", triggerUpload);
    document.getElementById("uploadCustomBtn")?.addEventListener("click", triggerUpload);
    document.getElementById("browseMultiBtn")?.addEventListener("click", () => {
        if (fileInput) { fileInput.multiple = true; fileInput.click(); }
    });
    document.getElementById("uploadManualBtn")?.addEventListener("click", () => uploadFiles());
    fileInput?.addEventListener("change", async () => {
        if (activeMode !== "manual") await uploadFiles();
        else {
            const preview = document.getElementById("multiFilePreview");
            if (preview) {
                preview.innerHTML = "";
                Array.from(fileInput.files).forEach(f => {
                    const item = document.createElement("div");
                    item.className = "multi-file-item";
                    item.innerHTML = `<span>${f.name}</span><span class="multi-file-size">${(f.size/1024).toFixed(0)} KB</span>`;
                    preview.appendChild(item);
                });
            }
        }
    });

    // Drop zone drag support
    const dropZone = document.getElementById("dropZone");
    if (dropZone) {
        dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.style.borderColor = "#1a5c37"; });
        dropZone.addEventListener("dragleave", () => { dropZone.style.borderColor = ""; });
        dropZone.addEventListener("drop", e => {
            e.preventDefault();
            dropZone.style.borderColor = "";
            if (fileInput) {
                const dt = new DataTransfer();
                Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
                fileInput.files = dt.files;
                uploadFiles();
            }
        });
    }

    async function uploadFiles() {
        const files = Array.from(fileInput?.files || []);
        if (!files.length) { showToast("Please select a photo first", "error"); return; }
        const progress = document.getElementById("uploadingProgress");
        const progressText = document.getElementById("uploadingProgressText");
        if (progress) progress.style.display = "flex";

        const noteInput = document.getElementById("timelineNoteInput");
        const noteValue = noteInput?.value?.trim() || "";

        for (let i = 0; i < files.length; i++) {
            if (progressText) progressText.textContent = `Analyzing photo ${i+1} of ${files.length} with AI...`;
            const fd = new FormData();
            fd.append("image", files[i]);
            fd.append("tracking_mode", activeMode);
            if (noteValue) fd.append("notes", noteValue);
            if (activeMode === "manual") {
                const dateVal = document.getElementById("manualPhotoDate")?.value;
                if (dateVal) fd.append("photo_date", dateVal);
            }
            try {
                const res = await fetch(`/api/plant/${selectedPlantId}/photo`, { 
                    method: "POST", 
                    body: fd,
                    headers: { "Authorization": `Bearer ${user.id}` }
                });
                const data = await res.json();
                if (!res.ok) { 
                    showToast(data.error || `Upload failed (${res.status})`, "error"); 
                    continue; 
                }
                const healthPct = data.health_score ?? 0;
                const diseaseLbl = data.disease_detected || data.disease_name || (data.is_healthy ? "Healthy" : "Unknown");
                showToast(`✅ Photo analyzed! Health: ${healthPct}% — ${diseaseLbl}`);
                autoTriggerTask("Photo");
            } catch(e) { 
                console.error("Upload error:", e);
                showToast("Upload failed — please check your connection and try again", "error"); 
            }
        }
        if (noteInput) noteInput.value = "";
        if (progress) progress.style.display = "none";
        if (fileInput) fileInput.value = "";
        await loadTimeline();
        await loadPlantData();
        // STEP 3: Scroll the timeline section into view after upload
        document.getElementById("panel-timeline")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function renderTimeline(data) {
        const grid = document.getElementById("photoTimelineGrid");
        const emptyState = document.getElementById("photoEmptyState");
        if (!grid) return;
        
        const timelineItems = data.timeline || data.data || [];
        console.log("Rendering timeline, items:", timelineItems.length);
        
        if (timelineItems.length > 0) {
            if (emptyState) emptyState.style.display = "none";
            grid.innerHTML = "";
            
            // First-Upload UX Toast
            if (timelineItems.length === 1) {
                const toast = document.createElement("div");
                toast.style.cssText = "background-color: #eaf1ed; color: #1a5c37; padding: 15px; border-radius: 8px; font-weight: 500; font-size: 15px; text-align: center; border: 1px solid #c9e0d1; margin-bottom: 24px;";
                toast.innerHTML = "🌱 Your plant journey starts today! This is your first scan.";
                grid.appendChild(toast);
            }
            timelineItems.slice().reverse().forEach((item, idx, arr) => {
                const prevItem = arr[idx + 1];
                const card = buildVTimelineEntry(item, timelineItems.length - idx, prevItem);
                grid.appendChild(card);
            });
            const latest = timelineItems[timelineItems.length - 1];
            if (latest?.image_url && plantHeroImg) plantHeroImg.src = latest.image_url;
        } else {
            // Explicitly show empty state when no photos
            if (emptyState) emptyState.style.display = "flex";
            grid.innerHTML = "";
        }
    }

    async function loadTimeline() {
        console.log(`[GROWZEN] Fetching timeline for plant_id: ${selectedPlantId}`);
        try {
            const res = await fetch(`/api/plant/${selectedPlantId}/timeline`, {
                headers: { "Authorization": `Bearer ${user.id}` }
            });
            const data = await res.json();
            console.log(`[GROWZEN] Timeline received: ${data.timeline?.length || data.data?.length || 0} items`);
            renderTimeline(data);
        } catch(e) { console.error("[GROWZEN] Timeline load error", e); }
    }

    function buildVTimelineEntry(item, entryNum, prevItem) {
        const score = item.health_score ?? 0;
        const prevScore = prevItem?.health_score ?? null;
        const scoreColor = score >= 80 ? "score-good" : score >= 50 ? "score-mid" : "score-bad";
        const dateStr = new Date(item.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
        const diseaseTag = (item.disease_detected && item.disease_detected.toLowerCase() !== "healthy")
            ? `<span class="disease-chip">${item.disease_detected}</span>`
            : `<span class="healthy-chip">Healthy</span>`;
        
        // [GROWZEN] Source Label: Auto Scan vs Manual Upload
        const isAuto = item.notes?.includes("Auto Scan") || item.is_diagnosis;
        const sourceLabel = isAuto 
            ? `<span class="badge badge-amber" style="font-size:10px; padding:2px 6px;">✨ Auto Scan</span>` 
            : `<span class="badge badge-blue" style="font-size:10px; padding:2px 6px;">📸 Manual Upload</span>`;

        const weekLabel = isAuto || activeMode === "weekly" ? `Week ${entryNum}` : `Entry #${entryNum}`;

        const modeTag = item.tracking_mode ? `<span class="mode-tag">${item.tracking_mode}</span>` : "";
        let trackingNote = "";
        if (item.entry_number === 1 || entryNum === 1) {
            trackingNote = `<span class="vt-score-change" style="color:#059669;font-weight:700;">🌱 First Scan — Baseline established</span>`;
        } else {
            const diff = prevScore !== null ? (score - prevScore) : 0;
            let statusStr, color, icon;
            if (diff > 5) { statusStr = "Improving"; color = "#16a34a"; icon = "📈"; }
            else if (diff < -5) { statusStr = "Worsening"; color = "#dc2626"; icon = "📉"; }
            else { statusStr = "Stable"; color = "#92400e"; icon = "📊"; }
            trackingNote = `<span class="vt-score-change" style="color:${color};font-weight:700;">${icon} ${statusStr} (${diff > 0 ? '+' : ''}${diff}%)</span>`;
        }

        const wrap = document.createElement("div");
        wrap.className = "vt-entry";
        wrap.innerHTML = `
            <div class="vt-dot"></div>
            <div class="vt-content">
                <div class="vt-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span class="vt-date">${dateStr}</span>
                    ${sourceLabel}
                </div>
                <div class="vt-img-row">
                    <img class="vt-img" src="${item.image_url}"
                        onerror="this.src='https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=200'" 
                        title="Click to enlarge" onclick="window.open('${item.image_url}', '_blank')">
                    <div class="vt-info">
                        <div class="vt-date">${dateStr}</div>
                        <div class="vt-label">${weekLabel}</div>
                        <div class="vt-tags">
                            <span class="vt-score-badge ${scoreColor}">Health: ${score}%</span>
                            <span class="vt-score-badge score-mid">AI Match: ${item.confidence || 0}%</span>
                            ${diseaseTag}
                            ${modeTag}
                        </div>
                        ${trackingNote}
                        ${item.ai_analysis ? `<div class="vt-ai-note">${item.ai_analysis}</div>` : ""}
                        ${item.notes ? `<div class="vt-user-note">📝 ${item.notes}</div>` : ""}
                    </div>
                </div>
            </div>`;
        return wrap;
    }


    // ── AI CHAT ───────────────────────────────────────────────────────────
    const chatInput  = document.getElementById("plantChatInput");
    const chatSend   = document.getElementById("plantChatSend");
    const chatMsgs   = document.getElementById("plantChatMessages");
    const chatTyping = document.getElementById("chatTyping");

    function nowTime() {
        return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function appendChat(msg, role) {
        if (!chatMsgs) return;
        const wrap = document.createElement("div");
        wrap.className = `chat-msg${role === "ai" ? " chat-msg-ai" : ""}`;
        wrap.innerHTML = role === "ai"
            ? `<div class="chat-msg-avatar">🌿</div><div class="chat-msg-bubble">${msg}<div class="chat-msg-time">${nowTime()}</div></div>`
            : `<div class="chat-msg-bubble">${msg}<div class="chat-msg-time">${nowTime()}</div></div>`;
        chatMsgs.appendChild(wrap);
        chatMsgs.scrollTop = chatMsgs.scrollHeight;
    }

    function showTyping() {
        if (chatTyping) chatTyping.style.display = "flex";
        if (chatMsgs)   chatMsgs.scrollTop = chatMsgs.scrollHeight;
    }

    function hideTyping() {
        if (chatTyping) chatTyping.style.display = "none";
    }

    async function sendChat(message) {
        const msg = message || chatInput?.value?.trim();
        if (!msg) return;
        appendChat(msg, "user");
        if (chatInput) chatInput.value = "";
        showTyping();
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg, plant_name: currentPlantData.name, health_score: currentPlantData.health_score })
            });
            const d = await res.json();
            hideTyping();
            appendChat(d.reply || "I'm not sure about that.", "ai");
        } catch(e) {
            hideTyping();
            appendChat("Sorry, I couldn't reach the AI right now.", "ai");
        }
    }

    chatSend?.addEventListener("click", () => sendChat());
    chatInput?.addEventListener("keydown", e => { if (e.key === "Enter") sendChat(); });

    document.querySelectorAll(".chat-chip").forEach(chip => {
        chip.addEventListener("click", () => sendChat(chip.dataset.msg));
    });

    // ── DIAGNOSIS (multi-step) ─────────────────────────────────────────────
    let currentReportId = null;
    let selectedAnswers = {};

    const uploadHealthBtn  = document.getElementById("uploadHealthBtn");
    const healthPhotoInput = document.getElementById("healthPhotoInput");
    const diagStep1 = document.getElementById("diagStep1");
    const diagStep2 = document.getElementById("diagStep2");
    const diagStep3 = document.getElementById("diagStep3");
    const diagLoading = document.getElementById("diagLoading");

    uploadHealthBtn?.addEventListener("click", () => {
        console.log("[DEBUG] Diagnosis button clicked (uploadHealthBtn)");
        healthPhotoInput?.click();
    });
    

    healthPhotoInput?.addEventListener("change", async () => {
        if (!healthPhotoInput.files[0]) return;
        
        console.log(`\n=== FRONTEND ===\n[STEP 1] Button Clicked:\n- plantId: ${selectedPlantId}\n- imageUrl: ${healthPhotoInput.files[0].name}`);

        diagStep1?.classList.remove("active");
        if (diagLoading) diagLoading.style.display = "block";

        const progressSteps = [
            { id: "dstep1", label: "Analyzing leaf patterns...",   pct: 33 },
            { id: "dstep2", label: "Matching disease database...",  pct: 66 },
            { id: "dstep3", label: "Generating treatment plan...", pct: 100 }
        ];
        const progressBar   = document.getElementById("diagProgressBar");
        const progressLabel = document.getElementById("diagProgressLabel");

        let stepIdx = 0;
        const stepTimer = setInterval(() => {
            if (stepIdx >= progressSteps.length) { clearInterval(stepTimer); return; }
            const s = progressSteps[stepIdx];
            if (stepIdx > 0) {
                const prev = document.getElementById(progressSteps[stepIdx - 1].id);
                prev?.classList.remove("active"); prev?.classList.add("done");
            }
            document.getElementById(s.id)?.classList.add("active");
            if (progressLabel) progressLabel.textContent = s.label;
            if (progressBar)   progressBar.style.width = s.pct + "%";
            stepIdx++;
        }, 1400);

        const formData = new FormData();
        formData.append("file", healthPhotoInput.files[0]);
        formData.append("plant_id", selectedPlantId);
        console.log(`\n[STEP 2] API Request Payload:\n- {\n  "plantId": "${selectedPlantId}",\n  "file": "${healthPhotoInput.files[0].name}",\n  "size": ${healthPhotoInput.files[0].size}\n}`);
        
        try {
            const res  = await fetch(`/api/detect-disease`, { method: "POST", body: formData });
            if (!res.ok) {
                console.error(`\n[STEP 3] API Response:\n- MISSING (API Failed: ${res.status})`);
            }
            
            const raw = await res.json();
            // STEP 2 FIX: backend returns both flat fields AND nested data.* envelope
            // Prefer flat fields, fall back to nested data object
            const data = {
                ...raw,
                plant: raw.plant || (raw.data && raw.data.plant) || raw.name,
                disease: raw.disease || (raw.data && raw.data.disease) || raw.diagnosis,
                confidence: raw.confidence ?? (raw.data && raw.data.confidence) ?? raw.aiConfidence ?? 0,
                status: raw.status || (raw.data && raw.data.status),
                image_path: raw.image_url || (raw.data && raw.data.image_path)
            };

            const scoreReport = data.healthScore ?? data.health_score ?? 0;
            const hasDiseaseReport = data.disease && !data.disease.toLowerCase().includes('healthy');
            const isHealthyReport = !hasDiseaseReport;

            let reportStatusText, reportStatusColor;
            if (!hasDiseaseReport) {
                reportStatusText = "Healthy";
                reportStatusColor = "#16a34a";
            } else if (scoreReport >= 50) {
                reportStatusText = "Monitor";
                reportStatusColor = "#2563eb";
            } else {
                reportStatusText = "Sick";
                reportStatusColor = "#dc2626";
            }

            if (!data.error && !data.plant && !data.disease && !data.name) {
                throw new Error("Invalid API response: missing plant/disease data");
            }

            const plant = data.plant;
            const disease = data.disease;
            const confidence = data.confidence; // Already 0-100
            
            console.log(`\n[STEP 3] API Response:\n- ${JSON.stringify(data, null, 2)}`);
            
            if (!data || Object.keys(data).length === 0) {
                console.error(`[DEBUG] RESPONSE EMPTY: Diagnosis endpoint returned empty data.`);
            } else if (data.error) {
                console.error(`[DEBUG] API ERROR Message: ${data.error}`);
            }
            
            clearInterval(stepTimer);
            progressSteps.forEach(s => {
                document.getElementById(s.id)?.classList.remove("active");
                document.getElementById(s.id)?.classList.add("done");
            });
            if (progressBar) progressBar.style.width = "100%";
            await new Promise(r => setTimeout(r, 400));
            if (diagLoading) diagLoading.style.display = "none";
            
            // Confidence is now 0-100 from backend
            const uiConfidence = data.confidence ?? 0;
            if (uiConfidence < 50) {
                showToast("Low confidence prediction. Try a clearer, well-lit leaf photo.", "warning");
            }

            // Only block UI rendering if there's an actual system failure (no plant and no disease data)
            if (data.error && !data.disease && !data.diagnosis && !data.plant && !data.name) {
                showToast(data.error, "error");
                diagStep1?.classList.add("active");
                return;
            }
            
            console.log("Plant:", data.plant);
            console.log("Disease:", data.disease);
            console.log("Health:", data.healthScore);
            
            currentReportId = data.report_id;

        // ALWAYS Use API source. Refetch backend to ensure strict synchronization.
        await loadPlantData();

        // ── STRICT UI MAPPING RULES ──
        const setId = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        
        let displayPlant = data.plant || data.name || "Unknown";
        let displayDisease = data.disease || data.diagnosis || "Unknown";
        
        // Normalize confidence: backend returns 0-100
        let rawFinalConf = data.aiConfidence !== undefined ? data.aiConfidence : (data.confidence !== undefined ? data.confidence : 0);
        // If confidence somehow got into 0-1 range (old API), scale up
        let finalConfidence = rawFinalConf <= 1.0 ? rawFinalConf * 100 : rawFinalConf;

        // Title: plant
        setId("hrPlant", displayPlant); 
        
        // Overview: disease
        setId("hrDiagnosis", displayDisease);
        
        // Health Status
        const hrStatusEl = document.getElementById("hrStatus");
        if (hrStatusEl) {
            hrStatusEl.textContent = reportStatusText;
            hrStatusEl.style.color = reportStatusColor;
            hrStatusEl.style.fontWeight = "bold";
        }
        
        // Confidence: show as integer percentage (backend now returns 0-100)
        setId("hrConfidence", Math.round(finalConfidence) + "%");
        
        setId("hrSeverity", data.severity || "Low");
        setId("hrFinalScore", `${data.healthScore ?? data.health_score ?? 0}%`);

            // Treatment list
            const treatList = document.getElementById("hrTreatmentList");
            if (treatList && data.treatment) {
                const items = data.treatment.split("\n").filter(l => l.trim().length > 3).map(i => i.replace(/^[-*]+/, "").trim());
                treatList.innerHTML = items.length > 0
                    ? items.map(i => `<li style="margin-bottom:6px;">• ${i}</li>`).join("")
                    : `<li>• ${data.treatment}</li>`;
            }

            // STEP 9: Redirection / Tab Switch
            if (!isHealthyReport) {
                // Switch to careplan tab and show step 3 (Result Card)
                diagStep1?.classList.remove("active");
                document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
                document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
                
                // Try both possible tab identifiers
                const careTab = document.querySelector('[data-tab="careplan"]') || document.querySelector('[data-tab="care"]');
                const carePanel = document.getElementById("panel-careplan") || document.getElementById("panel-care");
                
                if (careTab) careTab.classList.add("active");
                if (carePanel) carePanel.classList.add("active");
                
                diagStep3?.classList.add("active");
                console.log("[DEBUG] Redirected to Treatment Page (Care Plan) as disease was detected.");
            } else {
                // If healthy, just show result in modal or current tab
                diagStep3?.classList.add("active");
            }
            const dTitle = document.getElementById("diagTitle");
            if (dTitle) dTitle.textContent = "Diagnosis Complete";
            progressSteps.forEach(s => { document.getElementById(s.id)?.classList.remove("active", "done"); });
            if (progressBar)   progressBar.style.width = "0%";
            if (progressLabel) progressLabel.textContent = "Initializing analysis...";
        } catch(err) {
            console.error("Diagnosis error:", err);
            clearInterval(stepTimer);
            if (diagLoading) diagLoading.style.display = "none";
            diagStep1?.classList.add("active");
            showToast("Diagnosis failed", "error");
        }
    });

    document.querySelectorAll(".q-opt").forEach(opt => {
        opt.addEventListener("click", () => {
            const parent = opt.parentElement;
            const key = parent.dataset.key;
            parent.querySelectorAll(".q-opt").forEach(o => o.classList.remove("selected"));
            opt.classList.add("selected");
            selectedAnswers[key] = opt.dataset.val;
        });
    });

    document.getElementById("refineDiagnosisBtn")?.addEventListener("click", async () => {
        const notes = document.getElementById("diagUserNotes")?.value || "";
        if (Object.keys(selectedAnswers).length < 2) { showToast("Please answer the questions first", "error"); return; }
        diagStep2.classList.remove("active");
        diagLoading.style.display = "block";
        try {
            const res = await fetch(`/api/diagnosis/submit/${currentReportId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    answers: selectedAnswers,
                    note: notes 
                })
            });
            const data = await res.json();
            diagLoading.style.display = "none";
            if (data.success) {
                document.getElementById("hrFinalScore").textContent = `${data.final_health_score}%`;
                diagStep3.classList.add("active");
                document.getElementById("diagTitle").textContent = "Diagnosis Complete";
                document.getElementById("diagSubtitle").textContent = "Here is your refined health report";

                const list = document.getElementById("hrTreatmentList");
                if (list) {
                    const treatment = data.treatment || "Maintain regular care. Ensure proper drainage.";
                    const items = treatment.split("\n").filter(l => l.trim().length > 3).map(i => i.replace(/^[-*]+/, "").trim());
                    list.innerHTML = items.length > 0
                        ? items.map(i => `<li style="margin-bottom:6px;">• ${i}</li>`).join("")
                        : `<li>• ${treatment}</li>`;
                }

                showToast("Diagnosis complete! Timeline updated.", "success");
                await loadTimeline(); 
                await loadPlantData(); 
                await loadCareTasks();
            }
        } catch(e) {
            diagLoading.style.display = "none";
            diagStep2.classList.add("active");
            showToast("Failed to refine diagnosis", "error");
        }
    });

    document.getElementById("resetDiagnosisBtn")?.addEventListener("click", () => {
        diagStep3.classList.remove("active");
        diagStep1.classList.add("active");
        document.getElementById("diagTitle").textContent = "Plant Health Diagnosis";
        document.getElementById("diagSubtitle").textContent = "Upload a leaf photo for an interactive AI diagnosis";
        currentReportId = null;
        selectedAnswers = {};
        document.querySelectorAll(".q-opt").forEach(o => o.classList.remove("selected"));
        if (healthPhotoInput) healthPhotoInput.value = "";
    });

    // ── CARE PLAN ─────────────────────────────────────────────────────────
    document.getElementById("saveWaterFreq")?.addEventListener("click", () => {
        const val = document.getElementById("cpWaterFreqEdit")?.value;
        showToast(`Watering frequency saved: every ${val} days`);
    });

    const toggleReminderForm = document.getElementById("toggleReminderForm");
    const reminderFormWrap   = document.getElementById("reminderFormWrap");
    toggleReminderForm?.addEventListener("click", () => {
        reminderFormWrap.style.display = reminderFormWrap.style.display === "none" ? "block" : "none";
    });

    document.querySelectorAll(".reminder-type-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".reminder-type-btn").forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            document.getElementById("telegramFieldWrap").style.display = btn.dataset.type === "telegram" ? "block" : "none";
        });
    });

    document.getElementById("saveReminderBtn")?.addEventListener("click", async () => {
        const type = document.querySelector(".reminder-type-btn.selected")?.dataset.type || "in_app";
        const rawDate = document.getElementById("reminderDate")?.value; 
        const time = document.getElementById("reminderTime")?.value;
        const repeat = document.getElementById("reminderRepeat")?.value;
        const telegramChatId = document.getElementById("reminderTelegramChatId")?.value;

        // PART 3: VALIDATION
        if (!rawDate) { showToast("Please select a start date", "error"); return; }
        if (!time) { showToast("Please select a time", "error"); return; }
        if (!repeat) { showToast("Please select a repeat schedule", "error"); return; }
        if (type === "telegram" && !telegramChatId) {
            showToast("Telegram Chat ID is required", "error");
            return;
        }

        // PART 2: FIX FORM DATA STRUCTURE
        const payload = {
            plant_id: selectedPlantId,
            start_date: rawDate,
            time: time,
            repeat_type: repeat,
            notification_type: type,
            chat_id: telegramChatId
        };

        // PART 7: DEBUG LOGGING
        console.log("Form data before submit:", payload);
        console.log("Token:", user.id);

        try {
            const response = await fetch(`/api/reminders`, {
                method: "POST", 
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${user.id}`
                }, 
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // PART 4: FIX SAVE BUTTON
                showToast("Reminder saved successfully");
                
                // Clear form
                document.getElementById("reminderDate").value = "";
                document.getElementById("reminderTime").value = "";
                document.getElementById("reminderRepeat").value = "daily";
                document.getElementById("reminderTelegramChatId").value = "";
                
                if (reminderFormWrap) reminderFormWrap.style.display = "none";
                loadReminders();
                if (typeof loadPlantData === 'function') loadPlantData(); 
            } else {
                showToast(result.error || "Failed to save reminder", "error");
            }
        } catch(e) { 
             console.error("[GROWZEN] Reminder save error:", e);
             showToast("Connection error while saving reminder", "error");
        }
    });

    async function loadReminders() {
        if (!selectedPlantId) return;
        try {
            const res = await fetch(`/api/plant/${selectedPlantId}/reminders`);
            const reminders = await res.json();
            renderReminderItems(reminders);
        } catch(e) { console.error("[GROWZEN] Load reminders error:", e); }
    }

    window.deleteReminder = async (id) => {
        await fetch(`/api/reminder/${id}`, { 
            method: "DELETE",
            headers: { "Authorization": `Bearer ${user.id}` }
        });
        loadReminders();
        showToast("Reminder removed");
    };

    // ── FLOATING AI BUTTON ────────────────────────────────────────────────
    document.getElementById("floatingAiBtn")?.addEventListener("click", () => {
        document.querySelectorAll(".ptab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".plant-panel").forEach(p => p.classList.remove("active"));
        const chatTab   = document.querySelector('[data-tab="chat"]');
        const chatPanel = document.getElementById("panel-chat");
        chatTab?.classList.add("active");
        chatPanel?.classList.add("active");
        chatTab?.scrollIntoView({ behavior: "smooth", block: "start" });

        const disease = currentPlantData.disease_name || currentPlantData.last_disease;
        if (disease && disease !== "Healthy") {
            const autoMsg = `My plant has been diagnosed with ${disease}. What are the best treatment steps?`;
            const chatInputEl = document.getElementById("plantChatInput");
            if (chatInputEl) chatInputEl.value = autoMsg;
            setTimeout(() => sendChat(autoMsg), 600);
        }
    });

    // ── INIT ──────────────────────────────────────────────────────────────
    loadPlantData();
});
