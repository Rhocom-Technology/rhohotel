document.addEventListener("DOMContentLoaded", function () {
	const sectionBackgroundOrder = [
		"web-section-bg-light",
		"web-section-bg-soft",
		"web-section-bg-secondary",
		"web-section-bg-primary",
		"web-section-bg-accent",
		"web-section-bg-soft",
		"web-section-bg-dark",
	];

	document.querySelectorAll(".js-bg-order").forEach(function (section, index) {
		section.classList.add(sectionBackgroundOrder[index % sectionBackgroundOrder.length]);
	});

	const navbar = document.querySelector(".web-navbar");

	function handleNavbarScroll() {
		if (!navbar) return;

		if (window.scrollY > 30) {
			navbar.classList.add("web-navbar-scrolled");
		} else {
			navbar.classList.remove("web-navbar-scrolled");
		}
	}

	handleNavbarScroll();
	window.addEventListener("scroll", handleNavbarScroll);
});

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
