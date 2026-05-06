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
    const file = input.files && input.files[0];
    if (file && selectedMediaName) {
      selectedMediaName.textContent = `Fichier sélectionné : ${file.name}`;
    }
  });
});

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
