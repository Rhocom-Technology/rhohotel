document.addEventListener("DOMContentLoaded", function () {
  const sectionBackgroundOrder = [
    "web-section-bg-light",
    "web-section-bg-soft",
    "web-section-bg-secondary",
    "web-section-bg-primary",
    "web-section-bg-accent",
    "web-section-bg-soft",
    "web-section-bg-dark"
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
  if (confirm("Are you sure you want to logout?")) {
    if (window.frappe && frappe.call) {
      frappe.call({
        method: "logout",
        callback: function () {
          window.location.href = "/login";
        }
      });
    } else {
      window.location.href = "/?cmd=web_logout";
    }
  }
};