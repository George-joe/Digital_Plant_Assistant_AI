document.addEventListener('DOMContentLoaded', () => {
    // 1. Highlight active navigation
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-path') === currentPath) {
            item.classList.add('active');
        }
    });

    // 2. Populate User Profile
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('sidebarUsername').innerText = user.name || 'User';
        document.getElementById('sidebarLevel').innerText = user.level || '🌱 Rookie';

        // Load live XP + streak from API
        (async () => {
            try {
                const res  = await fetch(`/api/user/${user.id}/stats`);
                const data = await res.json();
                if (data.success) {
                    const streakEl = document.getElementById('sidebarStreak');
                    const xpPtsEl  = document.getElementById('sidebarXpPts');
                    const xpFill   = document.getElementById('sidebarXpFill');
                    const levelEl  = document.getElementById('sidebarLevel');
                    if (streakEl) streakEl.textContent = `🔥 ${data.streak || 0} day streak`;
                    if (xpPtsEl)  xpPtsEl.textContent  = `${data.xp || 0} XP`;
                    if (xpFill)   xpFill.style.width   = (data.xp_progress || 0) + '%';
                    if (levelEl)  levelEl.textContent   = data.level || '🌱 Rookie';
                }
            } catch(e) { /* silent fail */ }
        })();

    }

    // 3. Logout Logic
    const logoutBtn = document.getElementById('sidebarLogoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
            } catch (err) {
                console.error(err);
            }
            localStorage.removeItem('user');
            localStorage.removeItem('onboardingComplete');
            window.location.href = '/login';
        });
    }

    // 4. Global Scanner Route
    const globalScannerBtn = document.getElementById('globalScannerBtn');
    if (globalScannerBtn) {
        globalScannerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPath === '/dashboard') {
                const addPlantBtn = document.getElementById('addPlantBtn');
                if (addPlantBtn) addPlantBtn.click();
            } else {
                window.location.href = '/dashboard?action=scan';
            }
        });
    }
});
