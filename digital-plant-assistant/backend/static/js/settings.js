document.addEventListener("DOMContentLoaded", () => {
    const settingsModal = document.getElementById("settingsModal");
    const closeSettingsBtn = document.getElementById("closeSettingsBtn");
    const sidebarProfileBtn = document.getElementById("sidebarProfileBtn");
    const settingsBtn = Array.from(document.querySelectorAll('.nav-item')).find(el => el.textContent.includes('Settings'));

    const settingsName = document.getElementById("settingsName");
    const settingsPassword = document.getElementById("settingsPassword");
    const settingsPlantsCount = document.getElementById("settingsPlantsCount");
    const settingsStreak = document.getElementById("settingsStreak");
    const settingsXp = document.getElementById("settingsXp");
    const saveSettingsBtn = document.getElementById("saveSettingsBtn");
    const avatarUpload = document.getElementById("avatarUpload");
    const settingsAvatarPreview = document.getElementById("settingsAvatarPreview");
    const sidebarAvatar = document.getElementById("sidebarAvatar");

    let newAvatarFile = null;

    function openSettings() {
        fetch("/api/user/settings")
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    settingsName.value = data.user.name || "";
                    settingsPassword.value = "";
                    settingsPlantsCount.textContent = data.user.plants_owned || 0;
                    settingsStreak.textContent = (data.user.streak_days || 0) + " Days";
                    settingsXp.textContent = data.user.xp_points || 0;

                    if (data.user.profile_url) {
                        settingsAvatarPreview.src = data.user.profile_url;
                        if (sidebarAvatar) sidebarAvatar.src = data.user.profile_url;
                    }

                    settingsModal.classList.remove("hidden");
                }
            });
    }

    if (sidebarProfileBtn) sidebarProfileBtn.addEventListener("click", openSettings);
    if (settingsBtn) {
        settingsBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openSettings();
        });
    }

    closeSettingsBtn.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
    });

    avatarUpload.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            newAvatarFile = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                settingsAvatarPreview.src = e.target.result;
            };
            reader.readAsDataURL(newAvatarFile);
        }
    });

    saveSettingsBtn.addEventListener("click", async () => {
        saveSettingsBtn.disabled = true;
        saveSettingsBtn.innerText = "Saving...";

        const formData = new FormData();
        formData.append("name", settingsName.value);
        if (settingsPassword.value) formData.append("password", settingsPassword.value);
        if (newAvatarFile) formData.append("avatar", newAvatarFile);

        try {
            const res = await fetch("/api/user/update", {
                method: "POST",
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                alert("Profile updated successfully!");
                document.getElementById("sidebarUsername").textContent = settingsName.value;
                if (data.profile_url && sidebarAvatar) sidebarAvatar.src = data.profile_url;
                settingsModal.classList.add("hidden");
            } else {
                alert(data.error || "Failed to update profile");
            }
        } catch (err) {
            console.error(err);
        } finally {
            saveSettingsBtn.disabled = false;
            saveSettingsBtn.innerText = "Save Changes";
        }
    });
});
