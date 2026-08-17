document.addEventListener("DOMContentLoaded", () => {
    const user = JSON.parse(localStorage.getItem("user"));

    /* ======= TAB SWITCHING ======= */
    window.switchCommunityTab = function (tabName) {
        document.querySelectorAll(".ctab").forEach(t => t.classList.toggle("active", t.dataset.tab === tabName));
        document.querySelectorAll(".ctab-panel").forEach(p => p.classList.toggle("active", p.id === "ctab-" + tabName));
        if (tabName === "leaderboard") loadLeaderboard("all");
    };

    document.querySelectorAll(".ctab").forEach(tab => {
        tab.addEventListener("click", () => switchCommunityTab(tab.dataset.tab));
    });

    /* ======= LEADERBOARD ======= */
    let activePeriod = "all";

    document.querySelectorAll(".lb-filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".lb-filter-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadLeaderboard(btn.dataset.period);
        });
    });

    async function loadLeaderboard(period) {
        const loading = document.getElementById("lbLoading");
        const podium = document.getElementById("lbPodium");
        const list = document.getElementById("lbList");
        const empty = document.getElementById("lbEmpty");

        loading.style.display = "block";
        podium.style.display = "none";
        list.style.display = "none";
        empty.style.display = "none";

        try {
            const res = await fetch(`/api/community/leaderboard?period=${period}`);
            const payload = await res.json();
            const data = payload.data || payload;

            loading.style.display = "none";

            if (!data || data.length === 0) {
                empty.style.display = "block"; return;
            }

            // TOP 3 PODIUM
            podium.innerHTML = "";
            const MEDALS = ["🥇", "🥈", "🥉"];
            const COLORS = ["gold", "silver", "bronze"];

            data.slice(0, 3).forEach((u, i) => {
                const initials = u.name.slice(0, 2).toUpperCase();
                const badgesHtml = u.badges.length
                    ? `<div class="lb-badges">${u.badges.map(b => `<span class="lb-badge">${b}</span>`).join("")}</div>`
                    : "";
                const card = document.createElement("div");
                card.className = `lb-podium-card ${COLORS[i]}`;
                card.innerHTML = `
          <div class="lb-medal">${MEDALS[i]}</div>
          <div class="lb-avatar">${initials}</div>
          <div class="lb-username">${u.name}</div>
          <div class="lb-level">${u.level}</div>
          <div class="lb-xp">${u.xp.toLocaleString()}</div>
          <div class="lb-xp-label">XP</div>
          <div class="lb-xp-bar-wrap"><div class="lb-xp-bar" style="width:${u.xp_progress}%"></div></div>
          <div style="display:flex; justify-content:center; gap:16px; margin-top:10px; font-size:12px; color:var(--gray-400);">
            <span>🌿 ${u.plants} plants</span>
            <span>💚 ${u.avg_health}% health</span>
          </div>
          ${badgesHtml}
        `;
                podium.appendChild(card);
            });
            podium.style.display = "grid";

            // RANKED LIST 4+
            list.innerHTML = "";
            data.slice(3).forEach(u => {
                const initials = u.name.slice(0, 2).toUpperCase();
                const row = document.createElement("div");
                row.className = "lb-row";
                row.innerHTML = `
          <div class="lb-rank">${u.rank}</div>
          <div class="lb-row-avatar">${initials}</div>
          <div>
            <div class="lb-row-name">${u.name}</div>
            <div class="lb-row-level">${u.level}</div>
          </div>
          <div class="lb-row-meta">
            <div class="lb-row-stat">
              <div class="lb-row-stat-val" style="color:var(--primary)">${u.xp.toLocaleString()}</div>
              <div class="lb-row-stat-label">XP</div>
            </div>
            <div class="lb-row-stat">
              <div class="lb-row-stat-val">🌿 ${u.plants}</div>
              <div class="lb-row-stat-label">Plants</div>
            </div>
            <div class="lb-row-stat">
              <div class="lb-row-stat-val">💚 ${u.avg_health}%</div>
              <div class="lb-row-stat-label">Health</div>
            </div>
            <div class="lb-row-stat">
              <div class="lb-row-stat-val">🔥 ${u.streak}d</div>
              <div class="lb-row-stat-label">Streak</div>
            </div>
          </div>
        `;
                list.appendChild(row);
            });
            list.style.display = data.length > 3 ? "flex" : "none";

        } catch (err) {
            loading.style.display = "none";
            empty.style.display = "block";
        }
    }

    /* ======= MINI LEADERBOARD ======= */
    async function loadMiniLeaderboard() {
        try {
            const res = await fetch("/api/community/leaderboard?period=all");
            const payload = await res.json();
            const data = payload.data || payload;
            const el = document.getElementById("miniLbList");
            if (!el) return;
            el.innerHTML = data.slice(0, 5).map(u => `
        <div class="mini-lb-row">
          <div class="mini-lb-rank">${u.rank === 1 ? "🥇" : u.rank === 2 ? "🥈" : u.rank === 3 ? "🥉" : u.rank}</div>
          <div class="mini-lb-name">${u.name}</div>
          <div class="mini-lb-xp">${u.xp} XP</div>
        </div>
      `).join("");
        } catch (_) { }
    }

    /* ======= MY XP CARD ======= */
    async function loadMyXP() {
        try {
            const res = await fetch("/api/auth/me", {
                headers: user ? { "Authorization": `Bearer ${user.id}` } : {}
            });
            const data = await res.json();
            if (!data.success) return;
            const u = data.user;
            const xpVal = document.getElementById("myXpVal");
            const lvlEl = document.getElementById("myLevel");
            const barEl = document.getElementById("myXpBar");
            const nxtEl = document.getElementById("myNextLevel");
            if (xpVal) xpVal.textContent = `${u.xp_points || 0} XP`;
            if (lvlEl) lvlEl.textContent = u.level || "🌱 Seedling";
            // Simple XP progress
            const xp = u.xp_points || 0;
            const thresholds = [[0, 100], [100, 300], [300, 700], [700, 1500], [1500, 1500]];
            for (const [lo, hi] of thresholds) {
                if (xp < hi) {
                    const pct = Math.round(((xp - lo) / (hi - lo)) * 100);
                    if (barEl) barEl.style.width = `${pct}%`;
                    if (nxtEl) nxtEl.textContent = `${xp}/${hi} XP to next level`;
                    break;
                }
            }
        } catch (_) { }
    }

    /* ======= COMMUNITY FEED ======= */
    const feedEl = document.getElementById("communityFeed");
    const loadingEl = document.getElementById("feedLoading");
    const toast = document.getElementById("toast");

    function showToast(msg, type = "") {
        if (!toast) return;
        toast.textContent = msg;
        toast.className = `toast show ${type === "success" ? "toast-success" : ""}`;
        setTimeout(() => { toast.classList.remove("show"); setTimeout(() => toast.classList.add("hidden"), 300); }, 2500);
    }

    function timeAgo(dateStr) {
        const diff = (Date.now() - new Date(dateStr)) / 1000;
        if (diff < 60) return "just now";
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    window.openImageModal = function(url) {
        const modal = document.getElementById("imageModal");
        const img = document.getElementById("modalImg");
        if (modal && img) {
            img.src = url;
            modal.classList.remove("hidden");
        }
    };

    async function loadFeed() {
        try {
            console.log("Loading community feed...");
            const res = await fetch("/api/community/feed", {
                headers: user ? { "Authorization": `Bearer ${user.id}` } : {}
            });
            const payload = await res.json();
            const posts = payload.data || payload;

            if (loadingEl) loadingEl.style.display = "none";
            if (!posts || posts.length === 0) {
                feedEl.innerHTML = `<div style="text-align:center;padding:60px;color:var(--gray-400);"><div style="font-size:36px;margin-bottom:12px;">💬</div><p>No posts yet. Be the first to share!</p></div>`;
                return;
            }
            feedEl.innerHTML = "";
            posts.forEach(p => {
                const card = document.createElement("div");
                card.className = "feed-card";
                card.dataset.postId = p.id;
                const isOwn = user && (p.user_id === user.id || p.user_id === parseInt(user.id));
                const initials = (p.user || "U").slice(0, 1).toUpperCase();
                
                // MOCK Plant Tag Logic
                const plantMatches = ["Tomato", "Corn", "Rose", "Aloe", "Basil", "Mint", "Monstera"];
                let plantName = "General";
                for (let m of plantMatches) {
                    if (p.content.toLowerCase().includes(m.toLowerCase())) {
                        plantName = m;
                        break;
                    }
                }
                if (plantName === "General" && p.id % 3 === 0) plantName = "Tomato"; // Just for the demo variety

                card.innerHTML = `
                    <div class="feed-card-header">
                        <div class="feed-avatar">${initials}</div>
                        <div class="feed-author">${p.user}</div>
                        <div style="color:#9ca3af; margin:0 4px;">•</div>
                        <div class="feed-time">${timeAgo(p.created_at)}</div>
                        ${isOwn ? `<button class="delete-post-btn" data-id="${p.id}" title="Delete" style="margin-left:auto; background:none; border:none; cursor:pointer; color:#ef4444; font-size:14px; opacity:0.6;">🗑</button>` : ""}
                    </div>
                    
                    <div class="plant-tag">🌿 ${plantName}</div>
                    
                    <div class="feed-content">${p.content}</div>
                    
                    ${p.image_url ? `<img class="feed-img-preview" src="${p.image_url}" alt="Post image" onclick="openImageModal('${p.image_url}')" style="width:100%; max-height:400px; object-fit:cover; border-radius:8px; margin:8px 0; cursor:pointer;">` : ""}
                    
                    <div class="feed-actions">
                        <button class="feed-action-btn upvote-btn" data-id="${p.id}" style="background:#f3f4f6; color:#6b7280; border-radius:20px; padding:4px 12px; border:none; cursor:pointer; display:flex; align-items:center; gap:6px;">
                            ⬆ <span class="like-count">${p.likes}</span>
                        </button>
                        <button class="feed-action-btn downvote-btn" data-id="${p.id}" style="background:#f3f4f6; color:#6b7280; border-radius:20px; padding:4px 12px; border:none; cursor:pointer;">⬇</button>
                        <button class="feed-action-btn like-btn ${p.user_liked ? "liked" : ""}" data-id="${p.id}" style="background:#f3f4f6; color:${p.user_liked ? "#ef4444" : "#6b7280"}; border-radius:20px; padding:4px 12px; border:none; cursor:pointer;">
                            ${p.user_liked ? "❤️" : "🤍"}
                        </button>
                    </div>
                `;

                // Like handler (serving as upvote for now)
                card.querySelector(".like-btn")?.addEventListener("click", async (e) => {
                    const btn = e.currentTarget;
                    const id = btn.dataset.id;
                    try {
                        const r = await fetch(`/api/community/like/${id}`, { 
                            method: "POST",
                            headers: user ? { "Authorization": `Bearer ${user.id}` } : {}
                        });
                        const d = await r.json();
                        btn.classList.toggle("liked", d.liked);
                        btn.style.color = d.liked ? "#ef4444" : "#6b7280";
                        const countEl = card.querySelector(".like-count");
                        if (countEl) countEl.textContent = d.likes;
                        btn.innerHTML = d.liked ? "❤️" : "🤍";
                    } catch (_) { }
                });

                // Upvote/Downvote UI only (logic uses same like endpoint)
                card.querySelector(".upvote-btn")?.addEventListener("click", () => card.querySelector(".like-btn").click());
                card.querySelector(".downvote-btn")?.addEventListener("click", () => card.querySelector(".like-btn").click());

                // Delete handler
                card.querySelector(".delete-post-btn")?.addEventListener("click", async (e) => {
                    if (!confirm("Delete post?")) return;
                    const btn = e.currentTarget;
                    const id = btn.dataset.id;
                    try {
                        const r = await fetch(`/api/community/post/${id}`, {
                            method: "DELETE",
                            headers: user ? { "Authorization": `Bearer ${user.id}` } : {}
                        });
                        const d = await r.json();
                        if (d.success) {
                            card.style.opacity = "0";
                            setTimeout(() => card.remove(), 300);
                        }
                    } catch (_) { }
                });

                feedEl.appendChild(card);
            });
        } catch (err) {
            if (loadingEl) loadingEl.style.display = "none";
            feedEl.innerHTML = `<div style="text-align:center;padding:40px;color:var(--gray-400);">Failed to load feed</div>`;
        }
    }

    /* ======= CREATE POST ======= */
    document.getElementById("submitPostBtn")?.addEventListener("click", async () => {
        const content = document.getElementById("postContent")?.value.trim();
        if (!content) { showToast("Please write something first"); return; }
        const btn = document.getElementById("submitPostBtn");
        btn.textContent = "Posting..."; btn.disabled = true;
        try {
            const fd = new FormData();
            fd.append("content", content);
            const photoInput = document.getElementById("photoInput");
            if (photoInput?.files[0]) fd.append("image", photoInput.files[0]);
            console.log("Submitting post with user:", user?.id);
            const postRes = await fetch("/api/community/post", { 
                method: "POST", 
                body: fd,
                headers: user ? { "Authorization": `Bearer ${user.id}` } : {}
            });
            const postData = await postRes.json();
            console.log("Post result:", postData);
            document.getElementById("postContent").value = "";
            // Clear photo input and preview
            if (photoInput) photoInput.value = "";
            const preview = document.getElementById("photoPreview");
            if (preview) { preview.src = ""; preview.style.display = "none"; }
            showToast("Posted! +10 XP 🌟", "success");
            loadFeed();
            loadMyXP();
        } catch (e) { showToast("Failed to post"); }
        finally { btn.textContent = "Share Post"; btn.disabled = false; }
    });

    document.getElementById("addPhotoBtn")?.addEventListener("click", () => document.getElementById("photoInput").click());

    // Photo preview when user selects a file
    document.getElementById("photoInput")?.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const preview = document.getElementById("photoPreview");
        if (!preview) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            preview.src = ev.target.result;
            preview.style.display = "block";
        };
        reader.readAsDataURL(file);
    });

    /* ======= INIT ======= */
    loadFeed();
    loadMyXP();
    loadMiniLeaderboard();
});
