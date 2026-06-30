//on scroll effect
window.addEventListener("scroll", function () {
	const navbar = document.getElementById("heroNavbar");
	if (window.scrollY > 10) {
		navbar.classList.add("scrolled");
	} else {
		navbar.classList.remove("scrolled");
	}
});


//toggler for navbar
function openMenu() {
	document.getElementById("mobileMenu").classList.add("active");
}

function closeMenu() {
	document.getElementById("mobileMenu").classList.remove("active");
}

// Global Client Scroll Navigation Actions
function scrollToTop() {
	window.scrollTo({
		top: 0,
		behavior: "smooth" /* Delivers smooth scroll back to header viewports */,
	});
}

document.addEventListener("DOMContentLoaded", function () {
	// 1. Get and normalize current path (removes trailing slashes, index.html reference, and converts to lowercase)
	let currentPath = window.location.pathname.toLowerCase();
	if (currentPath.endsWith("/")) currentPath += "index.html";
	if (currentPath === "") currentPath = "index.html";

	// Helper function to extract just the file/clean name (e.g., "/spa.html" -> "spa")
	const getCleanFilename = (path) => {
		const segments = path.split("/");
		const lastSegment = segments[segments.length - 1] || "index.html";
		return lastSegment.replace(".html", "");
	};

	const currentCleanName = getCleanFilename(currentPath);

	// 2. Target all link variants across both layouts
	const allLinks = document.querySelectorAll(
		"#heroNavbar .nav-link, #heroNavbar .dropdown-item, #mobileMenu a",
	);
	let matchFound = false;

	allLinks.forEach((link) => {
		const href = link.getAttribute("href");
		if (!href || href === "#") return;

		const linkCleanName = getCleanFilename(href.toLowerCase());

		// Check if current clean filename matches link destination
		if (currentCleanName === linkCleanName) {
			link.classList.add("active");
			matchFound = true;

			// Handle Bootstrap Dropdown parent highlighting
			if (link.classList.contains("dropdown-item")) {
				const parentDropdown = link.closest(".dropdown");
				if (parentDropdown) {
					const dropdownToggle =
						parentDropdown.querySelector(".dropdown-toggle");
					if (dropdownToggle) dropdownToggle.classList.add("active");
				}
			}
		} else {
			link.classList.remove("active");
		}
	});

	// 3. Fallback to Home if root path didn't capture a match
	if (
		!matchFound &&
		(currentCleanName === "index" || currentCleanName === "")
	) {
		const homeLinks = document.querySelectorAll('a[href="index.html"]');
		homeLinks.forEach((el) => el.classList.add("active"));
	}
});

// Switcher Logic for Single Page Booking Portal tabs
function switchBookingTab(profile) {
	const roomsTab = document.getElementById("roomBookingTab");
	const eventsTab = document.getElementById("eventBookingTab");
	const roomsBtn = document.getElementById("roomToggleBtn");
	const eventsBtn = document.getElementById("eventToggleBtn");

	if (profile === "rooms") {
		roomsTab.classList.remove("d-none");
		eventsTab.classList.add("d-none");
		roomsBtn.classList.add("active");
		eventsBtn.classList.remove("active");
	} else {
		eventsTab.classList.remove("d-none");
		roomsTab.classList.add("d-none");
		eventsBtn.classList.add("active");
		roomsBtn.classList.remove("active");
	}
}

window.hotelLogout = function () {
	const modalEl = document.getElementById("logoutModal");

	if (!modalEl) {
		console.error("logoutModal not found");
		return;
	}

	const modal = new bootstrap.Modal(modalEl);
	modal.show();
};

document.getElementById("confirmLogoutBtn").addEventListener("click", async function () {
	const btn = this;

	btn.disabled = true;

	btn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Signing Out...
        `;

	try {
		await fetch("/api/method/logout", {
			method: "GET",
			credentials: "same-origin",
		});
	} catch (e) {
		console.error(e);
	}

	window.location.replace("/login");
});


