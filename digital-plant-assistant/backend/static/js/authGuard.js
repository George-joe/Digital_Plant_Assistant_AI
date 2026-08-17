// Centralized Auth & New User Guard
(function() {
    const userStr = localStorage.getItem("user");
    const isNewUser = localStorage.getItem("isNewUser") === "true";
    const path = window.location.pathname;

    // ROOT CONNECTION FIX: Global Fetch Interceptor
    // Automatically injects the active Bearer token into headers across the entire app
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        let [resource, config] = args;
        if (!config) config = {};
        if (!config.headers) config.headers = {};
        
        let token = localStorage.getItem("access_token");
        if (!token && userStr) {
            try {
                const parsed = JSON.parse(userStr);
                if (parsed && parsed.id) {
                    token = String(parsed.id);
                    localStorage.setItem("access_token", token);
                }
            } catch(e) {}
        }
        
        if (token) {
            if (config.headers instanceof Headers) {
                if (!config.headers.has("Authorization")) {
                    config.headers.append("Authorization", `Bearer ${token}`);
                }
            } else {
                if (!config.headers["Authorization"]) {
                    config.headers["Authorization"] = `Bearer ${token}`;
                }
            }
        }
        config.credentials = "include";
        return await originalFetch(resource, config);
    };

    console.log("[AuthGuard] Checking path:", path);
    console.log("[AuthGuard] User logged in:", !!userStr);
    console.log("[AuthGuard] isNewUser flag:", isNewUser);

    // 1. If NOT logged in -> redirect to login (unless on auth/home)
    if (!userStr) {
        if (path !== "/login" && path !== "/signup" && path !== "/") {
            console.log("[AuthGuard] Guest attempted access to protected page, redirecting to login");
            window.location.href = "/login";
            return;
        }
    } 
    // 2. If logged in but IS NEW -> redirect to onboarding (unless on onboarding)
    else if (isNewUser) {
        if (path !== "/onboarding") {
            console.log("[AuthGuard] New user must complete onboarding, redirecting...");
            window.location.href = "/onboarding";
            return;
        }
    }
    // 3. If logged in and NOT NEW -> prevent going back to auth/onboarding
    else {
        if (path === "/login" || path === "/signup" || path === "/onboarding") {
            console.log("[AuthGuard] Existing user on auth/onboarding page, redirecting to dashboard");
            window.location.href = "/dashboard";
            return;
        }
    }

    // 4. Session validity check (run in background)
    async function verifySession() {
        const token = localStorage.getItem("access_token");
        const headers = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        try {
            const res = await fetch('/api/auth/me', { headers });
            if (res.status === 401) {
                console.warn("[AuthGuard] Session expired or unauthorized");
                localStorage.removeItem('user');
                localStorage.removeItem('access_token');
                localStorage.removeItem('isNewUser');
                if (path !== "/login" && path !== "/signup" && path !== "/") {
                    window.location.href = '/login';
                }
            } else if (res.ok) {
                const data = await res.json();
                localStorage.setItem('user', JSON.stringify(data.user));
            }
        } catch (err) {
            console.error("[AuthGuard] Auth check failed:", err);
        }
    }

    // Only verify session if we have a user and aren't on auth/home pages
    if (userStr && path !== "/login" && path !== "/signup" && path !== "/") {
        verifySession();
    }
})();
