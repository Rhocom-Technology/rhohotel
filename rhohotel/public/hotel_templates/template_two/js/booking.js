function showBookingAlert(message, type = "info", targetId = "roomAvailabilityAlert") {
	const alertBox = document.getElementById(targetId);

	if (!alertBox) {
		alert(message);
		return;
	}

	const icon =
		type === "success"
			? "check-circle"
			: type === "danger"
				? "exclamation-circle"
				: type === "warning"
					? "exclamation-triangle"
					: "info-circle";

	alertBox.className = "web-inline-alert show";
	alertBox.innerHTML = `
    <i class="fa-solid fa-${icon} me-2"></i>
    ${message}
  `;

	setTimeout(() => {
		alertBox.className = "web-inline-alert";
		alertBox.innerHTML = "";
	}, 7000);
}

function calculateNights() {
	const checkInInput = document.getElementById("roomCheckIn");
	const checkOutInput = document.getElementById("roomCheckOut");
	const output = document.getElementById("roomStayOutput");

	if (!checkInInput || !checkOutInput || !output) return 0;

	const checkIn = checkInInput.value;
	const checkOut = checkOutInput.value;

	if (!checkIn || !checkOut) {
		output.innerHTML = `<i class="fa-solid fa-moon me-2"></i>Select valid dates`;
		return 0;
	}

	const start = new Date(checkIn + "T00:00:00");
	const end = new Date(checkOut + "T00:00:00");
	const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

	if (diff <= 0) {
		output.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-2"></i>Invalid dates`;
		return 0;
	}

	output.innerHTML = `<i class="fa-solid fa-moon me-2"></i>${diff} night${diff > 1 ? "s" : ""}`;

	return diff;
}

function resetRoomBookingForNow() {
	const checkAvailabilityBtn = document.getElementById("checkAvailabilityBtn");
	const continueRoomBookingBtn = document.getElementById("continueRoomBookingBtn");
	const roomBookingForm = document.getElementById("roomBookingForm");

	if (checkAvailabilityBtn) {
		checkAvailabilityBtn.addEventListener("click", function () {
			showBookingAlert(
				"Online room availability is currently being configured. Please contact the hotel to confirm available rooms.",
				"info",
			);
		});
	}

	if (continueRoomBookingBtn) {
		continueRoomBookingBtn.addEventListener("click", function () {
			showBookingAlert(
				"Room booking is currently being configured. Please contact the hotel to complete your room reservation.",
				"info",
			);
		});
	}

	if (roomBookingForm) {
		roomBookingForm.addEventListener("submit", function (event) {
			event.preventDefault();

			showBookingAlert(
				"Room booking is currently being configured. Please contact the hotel to complete your room reservation.",
				"info",
			);
		});
	}
}

function showEventAlert(message, type = "success", bookingRef = "") {
	let alertBox = document.getElementById("eventBookingAlert");
	const form = document.getElementById("eventBookingForm");

	if (!form) {
		alert(message);
		return;
	}

	if (!alertBox) {
		alertBox = document.createElement("div");
		alertBox.id = "eventBookingAlert";
		alertBox.className = "web-inline-alert mt-3";
		form.appendChild(alertBox);
	}

	const icon =
		type === "success"
			? "check-circle"
			: type === "danger"
				? "exclamation-circle"
				: type === "warning"
					? "exclamation-triangle"
					: "info-circle";

	alertBox.className = "web-inline-alert show mt-3";

	if (type === "success") {
		alertBox.style.background = "var(--web-success-soft)";
		alertBox.style.color = "var(--web-success-dark)";
		alertBox.style.border = "1px solid rgba(22, 101, 52, 0.18)";
	} else {
		alertBox.style.background = "var(--web-danger-soft)";
		alertBox.style.color = "var(--web-danger-dark)";
		alertBox.style.border = "1px solid rgba(185, 28, 28, 0.18)";
	}

	alertBox.innerHTML = `
    <div style="display: flex; gap: 12px; align-items: flex-start;">
      <div style="font-size: 1.4rem; line-height: 1;">
        <i class="fa-solid fa-${icon}"></i>
      </div>

      <div>
        <strong style="display: block; margin-bottom: 4px;">
          ${type === "success" ? "Event enquiry submitted" : "Submission failed"}
        </strong>

        <div>
          ${message}
        </div>

        ${
			bookingRef
				? `<div style="margin-top: 6px; font-size: 0.9rem;">
                Reference: <strong>${bookingRef}</strong>
              </div>`
				: ""
		}
      </div>
    </div>
  `;

	alertBox.scrollIntoView({
		behavior: "smooth",
		block: "center",
	});
}

function callFrappeMethod(method, args = {}) {
	return new Promise((resolve, reject) => {
		if (window.frappe && frappe.call) {
			frappe.call({
				method,
				args,
				callback: function (r) {
					if (r.exc || r.exception) {
						reject(r);
						return;
					}

					resolve(r.message);
				},
				error: function (err) {
					reject(err);
				},
			});

			return;
		}

		const csrfToken =
			(window.frappe && frappe.csrf_token) ||
			window.csrf_token ||
			document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") ||
			"";

		fetch(`/api/method/${method}`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": csrfToken,
				"X-Requested-With": "XMLHttpRequest",
			},
			credentials: "same-origin",
			body: JSON.stringify(args),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.exc || data.exception) {
					reject(data);
					return;
				}

				resolve(data.message);
			})
			.catch(reject);
	});
}

function resetEventBookingForNow() {
	const eventForm = document.getElementById("eventBookingForm");

	if (!eventForm) return;

	eventForm.addEventListener("submit", async function (event) {
		event.preventDefault();

		const submitButton = eventForm.querySelector('button[type="submit"]');
		const formData = new FormData(eventForm);

		const args = {
			hall: formData.get("hall"),
			guest_name: formData.get("guest_name"),
			guest_email: formData.get("guest_email"),
			guest_phone: formData.get("guest_phone"),
			event_type: formData.get("event_type"),
			event_date: formData.get("event_date"),
			start_time: formData.get("start_time"),
			end_time: formData.get("end_time"),
			estimated_guest: formData.get("estimated_guest"),
			noted: formData.get("noted"),
		};

		if (submitButton) {
			submitButton.disabled = true;
			submitButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Sending...`;
		}

		try {
			const response = await callFrappeMethod(
				"rhohotel.rhocom_hotel.api.website.submit_event_booking",
				args,
			);

			if (response && response.success) {
				showEventAlert(
					"Thank you. Your event enquiry has been received. The hotel team will contact you shortly to confirm hall availability, pricing, and setup details.",
					"success",
					response.booking,
				);

				eventForm.reset();

				eventForm.reset();
			} else {
				showEventAlert(
					response?.message || "Unable to submit event enquiry. Please try again.",
					"danger",
				);
			}
		} catch (error) {
			console.error(error);

			let message = "Unable to submit event enquiry. Please try again.";

			if (error?._server_messages) {
				try {
					const serverMessages = JSON.parse(error._server_messages);
					const firstMessage = JSON.parse(serverMessages[0]);
					message = firstMessage.message || message;
				} catch (e) {
					message = "Unable to submit event enquiry. Please try again.";
				}
			}

			showEventAlert(message, "danger");
		} finally {
			if (submitButton) {
				submitButton.disabled = false;
				submitButton.innerHTML = "Send Event Enquiry";
			}
		}
	});
}

function initBookingTabs() {
	const tabButtons = document.querySelectorAll("[data-booking-tab]");
	const panels = document.querySelectorAll("[data-booking-panel]");

	if (!tabButtons.length || !panels.length) return;

	tabButtons.forEach(function (button) {
		button.addEventListener("click", function () {
			const target = button.getAttribute("data-booking-tab");

			tabButtons.forEach(function (btn) {
				btn.classList.remove("active");
			});

			panels.forEach(function (panel) {
				panel.classList.remove("active");
			});

			button.classList.add("active");

			const activePanel = document.querySelector(`[data-booking-panel="${target}"]`);

			if (activePanel) {
				activePanel.classList.add("active");
			}
		});
	});
}

function initBookingPage() {
	initBookingTabs();

	const checkIn = document.getElementById("roomCheckIn");
	const checkOut = document.getElementById("roomCheckOut");

	if (checkIn && !checkIn.value) {
		const today = new Date();
		checkIn.valueAsDate = today;
	}

	if (checkOut && !checkOut.value) {
		const tomorrow = new Date();
		tomorrow.setDate(tomorrow.getDate() + 1);
		checkOut.valueAsDate = tomorrow;
	}

	calculateNights();

	checkIn?.addEventListener("change", calculateNights);
	checkOut?.addEventListener("change", calculateNights);

	resetRoomBookingForNow();
	resetEventBookingForNow();
}

document.addEventListener("DOMContentLoaded", initBookingPage);
