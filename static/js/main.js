const menuButton = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
const sidebarNav = document.querySelector(".sidebar-nav");

if (menuButton && sidebarNav) {
  menuButton.addEventListener("click", () => {
    sidebarNav.classList.toggle("open");
  });
} else if (menuButton && navLinks) {
  menuButton.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });
}

const roleSelect = document.querySelector("#role-select");
const studentFields = document.querySelector(".student-fields");
const ownerFields = document.querySelector(".owner-fields");

if (roleSelect) {
  roleSelect.addEventListener("change", () => {
    const isStudent = roleSelect.value === "etudiant";
    studentFields.classList.toggle("hidden", !isStudent);
    ownerFields.classList.toggle("hidden", isStudent);
  });
}

const limitedDescription = document.querySelector(".limited-description");
const lineCounter = document.querySelector(".line-count");

if (limitedDescription && lineCounter) {
  const updateLineCounter = () => {
    const lines = limitedDescription.value.split(/\r\n|\r|\n/);
    if (lines.length > 30) {
      limitedDescription.value = lines.slice(0, 30).join("\n");
    }
    const currentLines = limitedDescription.value ? limitedDescription.value.split(/\r\n|\r|\n/).length : 0;
    lineCounter.textContent = currentLines;
    lineCounter.parentElement.classList.toggle("is-warning", currentLines >= 30);
  };

  limitedDescription.addEventListener("input", updateLineCounter);
  updateLineCounter();
}

const filterToggle = document.querySelector(".filter-toggle");
const advancedFilters = document.querySelector("#advanced-filters");

if (filterToggle && advancedFilters) {
  filterToggle.addEventListener("click", () => {
    const isOpen = advancedFilters.classList.toggle("is-open");
    filterToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
}

document.querySelectorAll(".favorite-star").forEach((favoriteButton) => {
  favoriteButton.addEventListener("click", async (event) => {
    const favoriteUrl = favoriteButton.dataset.favoriteUrl;
    if (!favoriteUrl) {
      return;
    }

    event.preventDefault();
    favoriteButton.classList.add("is-loading");

    try {
      const response = await fetch(favoriteUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });

      if (response.redirected) {
        window.location.href = response.url;
        return;
      }

      if (!response.ok) {
        throw new Error("Favorite request failed");
      }

      const data = await response.json();
      const label = data.active ? "Retirer des favoris" : "Ajouter aux favoris";
      favoriteButton.classList.toggle("is-active", Boolean(data.active));
      favoriteButton.setAttribute("aria-label", label);
      favoriteButton.setAttribute("title", label);
      const labelText = favoriteButton.querySelector("span");
      if (labelText) {
        labelText.textContent = label;
      }

      if (!data.active && window.location.pathname.includes("/favoris")) {
        const card = favoriteButton.closest(".card");
        if (card) {
          card.classList.add("is-removing");
          setTimeout(() => card.remove(), 180);
        }
      }
    } catch (error) {
      window.location.href = favoriteUrl;
    } finally {
      favoriteButton.classList.remove("is-loading");
    }
  });
});

const loginIdentifier = document.querySelector(".login-identifiant");
const loginPassword = document.querySelector(".login-password");

if (loginIdentifier && loginPassword) {
  const adminEmail = "redakouchtam@icloud.com";
  const updatePasswordRequirement = () => {
    const isAdminEmail = loginIdentifier.value.trim().toLowerCase() === adminEmail;
    loginPassword.required = !isAdminEmail;
    loginPassword.placeholder = isAdminEmail ? "Non requis pour cet administrateur" : "Mot de passe";
  };

  loginIdentifier.addEventListener("input", updatePasswordRequirement);
  updatePasswordRequirement();
}

const recoveryRole = document.querySelector(".recovery-role");
const recoveryIdentifier = document.querySelector(".recovery-identifier");

if (recoveryRole && recoveryIdentifier) {
  const updateRecoveryPlaceholder = () => {
    recoveryIdentifier.placeholder =
      recoveryRole.value === "etudiant"
        ? "Code Massar étudiant, exemple : G123456789"
        : "Téléphone propriétaire, exemple : 0612345678";
  };

  recoveryRole.addEventListener("change", updateRecoveryPlaceholder);
  updateRecoveryPlaceholder();
}

const mediaTriggers = document.querySelectorAll(".media-trigger");
const selectedMediaName = document.querySelector(".selected-media-name");

mediaTriggers.forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.target);
    if (input) {
      input.click();
    }
  });
});

document.querySelectorAll(".media-input").forEach((input) => {
  input.addEventListener("change", () => {
    const files = input.files ? Array.from(input.files) : [];
    if (files.length && selectedMediaName) {
      const firstNames = files.slice(0, 3).map((file) => file.name).join(", ");
      const moreText = files.length > 3 ? ` +${files.length - 3} autre(s)` : "";
      selectedMediaName.textContent = `${files.length} fichier(s) : ${firstNames}${moreText}`;
      const file = { name: `${files.length} fichier(s) : ${firstNames}${moreText}` };
      selectedMediaName.textContent = `Fichier sélectionné : ${file.name}`;
    }
  });
});

const galleryItems = Array.from(document.querySelectorAll(".gallery-item"));
const lightbox = document.querySelector(".media-lightbox");

if (galleryItems.length && lightbox) {
  const stage = lightbox.querySelector(".lightbox-stage");
  const closeButton = lightbox.querySelector(".lightbox-close");
  const prevButton = lightbox.querySelector(".lightbox-prev");
  const nextButton = lightbox.querySelector(".lightbox-next");
  let currentIndex = 0;

  const renderLightboxItem = () => {
    const item = galleryItems[currentIndex];
    const src = item.dataset.gallerySrc || item.getAttribute("src");
    const type = item.dataset.galleryType || "image";
    stage.innerHTML = "";

    const element = document.createElement(type === "video" ? "video" : "img");
    element.src = src;
    if (type === "video") {
      element.controls = true;
      element.autoplay = true;
      element.playsInline = true;
    } else {
      element.alt = item.getAttribute("alt") || "Photo du logement";
    }
    stage.appendChild(element);
  };

  const openLightbox = (index) => {
    currentIndex = index;
    renderLightboxItem();
    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  };

  const closeLightbox = () => {
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    stage.innerHTML = "";
    document.body.style.overflow = "";
  };

  const moveLightbox = (step) => {
    currentIndex = (currentIndex + step + galleryItems.length) % galleryItems.length;
    renderLightboxItem();
  };

  galleryItems.forEach((item, index) => {
    item.addEventListener("click", () => openLightbox(index));
  });

  closeButton.addEventListener("click", closeLightbox);
  prevButton.addEventListener("click", () => moveLightbox(-1));
  nextButton.addEventListener("click", () => moveLightbox(1));

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (!lightbox.classList.contains("is-open")) {
      return;
    }
    if (event.key === "Escape") {
      closeLightbox();
    }
    if (event.key === "ArrowLeft") {
      moveLightbox(-1);
    }
    if (event.key === "ArrowRight") {
      moveLightbox(1);
    }
  });
}

const housingMap = document.querySelector("#housing-map");
const mapToggle = document.querySelector(".map-toggle");

if (housingMap && window.L) {
  let map;
  const initMap = () => {
    if (map) {
      setTimeout(() => map.invalidateSize(), 120);
      return;
    }

    const logements = JSON.parse(housingMap.dataset.logements || "[]");
    const facultes = JSON.parse(housingMap.dataset.facultes || "{}");
    map = L.map(housingMap).setView([31.645, -8.015], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap"
    }).addTo(map);

    const facultyIcon = L.divIcon({
      className: "faculty-map-marker",
      html: '<span>U</span>',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    Object.entries(facultes).forEach(([code, faculte]) => {
      L.marker([faculte.lat, faculte.lng], { icon: facultyIcon })
        .addTo(map)
        .bindPopup(`<strong>${code}</strong><br>${faculte.nom}`);
    });

    logements.forEach((logement) => {
      L.circleMarker([logement.lat, logement.lng], {
        radius: 8,
        color: "#2563eb",
        fillColor: "#7c3aed",
        fillOpacity: 0.78
      })
        .addTo(map)
        .bindPopup(`<strong>${logement.titre}</strong><br>${logement.quartier}<br>${logement.prix} DH<br><a href="${logement.url}">Voir détails</a>`);
    });

    setTimeout(() => map.invalidateSize(), 120);
  };

  if (mapToggle) {
    mapToggle.addEventListener("click", () => {
      const isHidden = housingMap.classList.toggle("is-hidden");
      mapToggle.setAttribute("aria-expanded", isHidden ? "false" : "true");
      mapToggle.textContent = isHidden ? "Afficher la carte" : "Masquer la carte";
      if (!isHidden) {
        initMap();
      }
    });
  }
}
