document.addEventListener("DOMContentLoaded", () => {

    const productGrid = document.getElementById("productGrid");
    const searchInput = document.getElementById("searchInput");
    const priceFilter = document.getElementById("priceFilter");
    const ratingFilter = document.getElementById("ratingFilter");
    const resultsLabel = document.getElementById("resultsLabel");
    const toast = document.getElementById("toast");

    let products = [];
    let activeCategory = "All";
    let cart = [];

    /* ============= PRODUCT DATA ============= */
    const PRODUCTS = [
        { id: 1, name: "Premium Indoor Potting Mix", category: "Soil & Compost", price: 14.99, rating: 4.8, reviews: 142, seller: "@GrowZenOfficial", image: "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?w=400&fit=crop", badge: "Bestseller" },
        { id: 2, name: "Liquid Fertilizer Concentrate", category: "Fertilizers", price: 9.99, rating: 4.5, reviews: 87, seller: "@GreenThumb", image: "https://images.unsplash.com/photo-1581577141536-42d4a51eb8d1?w=400&fit=crop" },
        { id: 3, name: "Monstera Deliciosa Live Plant", category: "Live Plants", price: 39.99, rating: 4.9, reviews: 203, seller: "@SeedBankHQ", image: "https://images.unsplash.com/photo-1599598425947-5202edd56fde?w=400&fit=crop", badge: "Popular" },
        { id: 4, name: "Terracotta Pot Set (3 sizes)", category: "Pots & Planters", price: 24.00, rating: 4.6, reviews: 65, seller: "@CeramicArts", image: "https://images.unsplash.com/photo-1598539962383-7c0147cb2320?w=400&fit=crop" },
        { id: 5, name: "Herb Seed Collection (12 varieties)", category: "Seeds", price: 12.50, rating: 4.7, reviews: 119, seller: "@SeedBankHQ", image: "https://images.unsplash.com/photo-1473973266408-ed4e27abdd47?w=400&fit=crop" },
        { id: 6, name: "Long-Handle Pruning Shears", category: "Tools", price: 19.99, rating: 4.4, reviews: 44, seller: "@ToolMaster", image: "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=400&fit=crop" },
        { id: 7, name: "Orchid Bark Potting Mix", category: "Soil & Compost", price: 11.99, rating: 4.3, reviews: 38, seller: "@GrowZenOfficial", image: "https://images.unsplash.com/photo-1501856628765-f4c82bb0a9e7?w=400&fit=crop" },
        { id: 8, name: "Self-Watering Hanging Planter", category: "Pots & Planters", price: 32.00, rating: 4.8, reviews: 91, seller: "@CeramicArts", image: "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&fit=crop", badge: "New" },
        { id: 9, name: "Succulent & Cactus Fertilizer", category: "Fertilizers", price: 7.50, rating: 4.2, reviews: 29, seller: "@GreenThumb", image: "https://images.unsplash.com/photo-1459156212016-c812468e2115?w=400&fit=crop" },
        { id: 10, name: "Pacific Island Pothos (Live)", category: "Live Plants", price: 18.99, rating: 4.7, reviews: 156, seller: "@PlantShop", image: "https://images.unsplash.com/photo-1602923668104-8f9e03e77e62?w=400&fit=crop" },
        { id: 11, name: "Vegetable Seed Bundle (20 packs)", category: "Seeds", price: 21.00, rating: 4.6, reviews: 73, seller: "@SeedBankHQ", image: "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&fit=crop" },
        { id: 12, name: "Stainless Steel Watering Can", category: "Tools", price: 28.99, rating: 4.9, reviews: 88, seller: "@ToolMaster", image: "https://images.unsplash.com/photo-1459156212016-c812468e2115?w=400&fit=crop" },
    ];
    products = PRODUCTS;

    /* ============= TOAST ============= */
    function showToast(msg, type = "") {
        if (!toast) return;
        toast.textContent = msg;
        toast.className = `toast show ${type === "success" ? "toast-success" : type === "error" ? "toast-error" : ""}`;
        setTimeout(() => { toast.classList.remove("show"); setTimeout(() => toast.classList.add("hidden"), 300); }, 2200);
    }

    /* ============= RENDER ============= */
    function renderProducts() {
        const q = (searchInput?.value || "").toLowerCase();
        const priceV = priceFilter?.value || "";
        const ratingV = parseFloat(ratingFilter?.value || "0");

        const filtered = products.filter(p => {
            if (activeCategory !== "All" && p.category !== activeCategory) return false;
            if (q && !p.name.toLowerCase().includes(q) && !p.category.toLowerCase().includes(q)) return false;
            if (ratingV && p.rating < ratingV) return false;
            if (priceV) {
                const parts = priceV.split("-");
                if (priceV === "50+") { if (p.price < 50) return false; }
                else if (parts.length === 2) { if (p.price < +parts[0] || p.price > +parts[1]) return false; }
            }
            return true;
        });

        resultsLabel.textContent = `${filtered.length} product${filtered.length !== 1 ? "s" : ""} found`;
        productGrid.innerHTML = "";

        if (filtered.length === 0) {
            productGrid.innerHTML = `<div class="mp-empty" style="grid-column:1/-1; text-align:center; padding:60px; color:var(--gray-400);">
        <div class="mp-empty-icon">🌱</div>
        <p>No products match your search. Try different filters.</p>
      </div>`;
            return;
        }

        filtered.forEach(p => {
            const stars = renderStars(p.rating);
            const card = document.createElement("div");
            card.className = "product-card";
            card.innerHTML = `
        <div class="product-img-wrap">
          <img class="product-img" src="${p.image}" alt="${p.name}" onerror="this.src='https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=400'">
          ${p.badge ? `<span class="product-badge">${p.badge}</span>` : ""}
          <button class="product-wishlist" data-id="${p.id}">🤍</button>
        </div>
        <div class="product-body">
          <div class="product-category">${p.category}</div>
          <div class="product-name">${p.name}</div>
          <div class="product-seller">by ${p.seller}</div>
          <div class="product-rating">
            <span class="stars">${stars}</span>
            <span class="rating-count">${p.rating} (${p.reviews})</span>
          </div>
          <div class="product-price-row">
            <div style="display:flex; align-items:baseline; gap:6px;">
              <div class="product-price">$${p.price.toFixed(2)}</div>
            </div>
          </div>
          <div class="product-actions">
            <button class="btn-buy-now" data-id="${p.id}">Buy Now</button>
            <button class="btn-cart" data-id="${p.id}">🛒 Cart</button>
          </div>
        </div>
      `;

            // Wishlist toggle
            card.querySelector(".product-wishlist").addEventListener("click", (e) => {
                e.stopPropagation();
                const btn = e.currentTarget;
                btn.textContent = btn.textContent === "🤍" ? "❤️" : "🤍";
            });

            card.querySelector(".btn-buy-now").addEventListener("click", () => openCheckout(p));
            card.querySelector(".btn-cart").addEventListener("click", (e) => {
                e.stopPropagation();
                cart.push(p);
                showToast(`"${p.name}" added to cart 🛒`, "success");
                e.currentTarget.textContent = "✅ Added";
                setTimeout(() => (e.currentTarget.textContent = "🛒 Cart"), 1800);
            });

            productGrid.appendChild(card);
        });
    }

    function renderStars(rating) {
        const full = Math.floor(rating);
        const half = rating % 1 >= 0.5 ? 1 : 0;
        const empty = 5 - full - half;
        return "★".repeat(full) + (half ? "½" : "") + "☆".repeat(empty);
    }

    /* ============= CATEGORY TABS ============= */
    document.getElementById("mpCategories")?.addEventListener("click", (e) => {
        const btn = e.target.closest(".mp-cat-btn");
        if (!btn) return;
        document.querySelectorAll(".mp-cat-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeCategory = btn.dataset.cat;
        renderProducts();
    });

    searchInput?.addEventListener("input", renderProducts);
    priceFilter?.addEventListener("change", renderProducts);
    ratingFilter?.addEventListener("change", renderProducts);

    /* ============= CHECKOUT MODAL ============= */
    let checkoutProduct = null;

    function openCheckout(product) {
        checkoutProduct = product;
        const cartItems = document.getElementById("cartItemsContainer");
        cartItems.innerHTML = `
      <div class="cart-item">
        <img class="cart-item-img" src="${product.image}" alt="${product.name}" onerror="this.src='https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=300'">
        <div>
          <div class="cart-item-name">${product.name}</div>
          <div class="cart-item-seller">${product.seller}</div>
        </div>
        <div class="cart-item-price">$${product.price.toFixed(2)}</div>
      </div>
    `;
        document.getElementById("cartTotal").textContent = `$${product.price.toFixed(2)}`;
        setCheckoutStep(1);
        document.getElementById("checkoutModal").classList.remove("hidden");
    }

    function setCheckoutStep(step) {
        [1, 2, 3].forEach(n => {
            document.getElementById(`checkoutPage${n}`).style.display = (n === step) ? "block" : "none";
            document.getElementById(`cstep${n}`)?.classList.toggle("active", n === step);
        });
    }

    document.getElementById("nextToShipping")?.addEventListener("click", () => setCheckoutStep(2));

    document.getElementById("placeOrderBtn")?.addEventListener("click", () => {
        setCheckoutStep(3);
        showToast("🎉 Order placed successfully!", "success");
    });

    ["closeCheckout", "closeSuccessBtn"].forEach(id => {
        document.getElementById(id)?.addEventListener("click", () => {
            document.getElementById("checkoutModal").classList.add("hidden");
            setCheckoutStep(1);
        });
    });

    /* ============= INIT ============= */
    renderProducts();
});
