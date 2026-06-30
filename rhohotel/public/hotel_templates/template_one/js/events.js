let selectedHallRate = 0;

// Execute setup once DOM components are mounted
document.addEventListener("DOMContentLoaded", () => {
	initHallSelection();
	initEventTypeSynchronization();
	initPriceCalculationTriggers();
	initFormSubmissionPipeline();
});

// ============================
// HALL SELECTION
// ============================
function initHallSelection() {
	const hallSelect = document.getElementById("eventHall");
	if (!hallSelect) return;

	// In events.js, update your hallSelect change listener
	hallSelect.addEventListener("change", function () {
		const option = this.options[this.selectedIndex];

		// DEBUG: Add this line to your console
		console.log("Selected Option Dataset:", option.dataset);

		if (!option.value) {
			document.getElementById("hallSummary").style.display = "none";
			return;
		}

		// Force numeric conversion more safely
		const rate = parseFloat(option.dataset.rate);
		selectedHallRate = isNaN(rate) ? 0 : rate;

		console.log("Calculated selectedHallRate:", selectedHallRate); // DEBUG

		document.getElementById("hallName").textContent = option.text;
		document.getElementById("hallType").textContent = option.dataset.type || "-";
		document.getElementById("hallCapacity").textContent = option.dataset.capacity || "-";

		document.getElementById("hallRate").textContent =
			`${selectedHallRate.toLocaleString()} ${window.hotelCurrency || "NGN"} / day`;

		document.getElementById("hallSummary").style.display = "block";

		calculateEventPricing();
	});
}

// ============================
// EVENT TYPE SYNCHRONIZATION
// ============================
function initEventTypeSynchronization() {
	const typeSelect = document.getElementById("eventTypeSelect");
	if (!typeSelect) return;

	typeSelect.addEventListener("change", function() {
		const summaryType = document.getElementById("summaryEventType");
		if (summaryType) {
			summaryType.textContent = this.value || "—";
		}
	});
}

// ============================
// PRICE CALCULATION
// ============================
function initPriceCalculationTriggers() {
	const startEl = document.getElementById("eventStartDateTime");
	const endEl = document.getElementById("eventEndDateTime");

	if (startEl) startEl.addEventListener("change", calculateEventPricing);
	if (endEl) endEl.addEventListener("change", calculateEventPricing);
}

function calculateEventPricing() {
	const startEl = document.getElementById("eventStartDateTime");
	const endEl = document.getElementById("eventEndDateTime");

	if (!startEl?.value || !endEl?.value || selectedHallRate === 0) return;

	const startDate = new Date(startEl.value);
	const endDate = new Date(endEl.value);

	if (isNaN(startDate) || isNaN(endDate)) return;

	if (endDate <= startDate) {
		if(document.getElementById("totalDays")) document.getElementById("totalDays").textContent = "0";
		if(document.getElementById("totalAmount")) document.getElementById("totalAmount").textContent = "₦0";
		return;
	}

	const diffMs = endDate - startDate;
	// Calculate total days cleanly
	const totalDays = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
	const totalAmount = selectedHallRate * totalDays;

	if(document.getElementById("totalDays")) document.getElementById("totalDays").textContent = totalDays;
	if(document.getElementById("totalAmount")) document.getElementById("totalAmount").textContent = `₦${totalAmount.toLocaleString()}`;
}
// ============================
// FRAPPE CALL SYSTEM BRIDGE
// ============================
function callFrappeMethod(method, args = {}) {
	return new Promise((resolve, reject) => {
		if (window.frappe && frappe.call) {
			frappe.call({
				method,
				args,
				callback: (r) => {
					if (r.exc || r.exception) return reject(r);
					resolve(r.message);
				},
				error: reject,
			});
			return;
		}

		const csrfToken = (window.frappe && frappe.csrf_token) || window.csrf_token || document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";

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
			.then((r) => r.json())
			.then((data) => {
				if (data.exc || data.exception) return reject(data);
				resolve(data.message);
			})
			.catch(reject);
	});
}

async function getOrCreateCustomer(name, email = "", phone = "") {
	if (!name) throw new Error("Customer name required");
	return await callFrappeMethod("rhohotel.rhocom_hotel.api.customer.get_or_create_customer", { name, email, phone });
}

// ============================
// FORM SUBMISSION PIPELINE
// ============================
function initFormSubmissionPipeline() {
	const form = document.getElementById("eventBookingForm");
	if (!form) return;

	form.addEventListener("submit", async function (e) {
		e.preventDefault();

		const btn = document.getElementById("eventSubmitBtn");
		const originalBtnText = btn ? btn.innerHTML : "Book Event";

		if (btn) {
			btn.disabled = true;
			btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Submitting Hold Hold...`;
		}

		// Cache dynamic totals text values right before potential mutations
		const finalDays = document.getElementById("totalDays")?.textContent || "0";
		const finalAmount = document.getElementById("totalAmount")?.textContent || "₦0";

		try {
			const customerName = document.getElementById("eventName")?.value?.trim();
			const email = document.getElementById("eventEmail")?.value?.trim();
			const phone = document.getElementById("eventPhone")?.value?.trim();
			const eventType = document.getElementById("eventTypeSelect")?.value;
			const hall = document.getElementById("eventHall")?.value;
			const start = document.getElementById("eventStartDateTime")?.value;
			const end = document.getElementById("eventEndDateTime")?.value;

			if (!customerName || !hall || !start || !end || !eventType) {
				showAlert("Please complete all required fields.", "danger");
				if (btn) { btn.disabled = false; btn.innerHTML = originalBtnText; }
				return;
			}

			const formattedPhone = phone ? (phone.startsWith("+") ? phone : `+234${phone.replace(/^0/, "")}`) : "";

			// Step 1: Manage customer initialization sequence
			const customer = await getOrCreateCustomer(customerName, email, formattedPhone);

			// Step 2: Post reservation details payload
			const booking = await callFrappeMethod("rhohotel.rhocom_hotel.api.hall_booking.create_booking", {
				data: {
					customer_name: customerName,
					customer: customer,
					mobile_number: formattedPhone,
					hall: hall,
					event_type: eventType,
					start_datetime: start,
					end_datetime: end,
					submit: false
				}
			});

			if (!booking || !booking.name) throw new Error("Could not parse signature from booking ledger.");

			showAlert(`Success! Venue Hold Secured: ${booking.name}`, "success");

			// Step 3: Inject parameters down into digital verification success sheet
			if(document.getElementById("successReference")) document.getElementById("successReference").textContent = booking.name;
			if(document.getElementById("successName")) document.getElementById("successName").textContent = customerName;
			if(document.getElementById("successEmail")) document.getElementById("successEmail").textContent = email || "—";
			if(document.getElementById("successPhone")) document.getElementById("successPhone").textContent = formattedPhone || "—";
			if(document.getElementById("successHall")) document.getElementById("successHall").textContent = document.getElementById("eventHall").options[document.getElementById("eventHall").selectedIndex].text;
			if(document.getElementById("successEventType")) document.getElementById("successEventType").textContent = eventType;
			if(document.getElementById("successTotalDays")) document.getElementById("successTotalDays").textContent = finalDays;
			if(document.getElementById("successTotalAmount")) document.getElementById("successTotalAmount").textContent = finalAmount;

			// Switch presentation display panels smoothly
			document.getElementById("eventBookingForm").classList.add("d-none");
			document.getElementById("bookingSuccessCard").classList.remove("d-none");

		} catch (err) {
			console.error("Booking handler exception dropped:", err);
			showAlert(toUserMessage(err), "danger");
			if (btn) {
				btn.disabled = false;
				btn.innerHTML = originalBtnText;
			}
		}
	});
}

// ============================
// ALERT MESSAGING DOM EXTRACTIONS
// ============================
function showAlert(message, type = "success") {
	let alertBox = document.getElementById("bookingAlert");
	if (!alertBox) {
		alertBox = document.createElement("div");
		alertBox.id = "bookingAlert";
		alertBox.style.position = "fixed";
		alertBox.style.top = "20px";
		alertBox.style.right = "20px";
		alertBox.style.zIndex = "9999";
		document.body.appendChild(alertBox);
	}
	alertBox.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show shadow">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
	setTimeout(() => { alertBox.innerHTML = ""; }, 5000);
}

function toUserMessage(err) {
	let msg = "";
	if (err?._server_messages) {
		try {
			const parsed = JSON.parse(err._server_messages);
			msg = JSON.parse(parsed[0])?.message || parsed[0];
		} catch (e) {
			msg = err._server_messages;
		}
	}
	if (!msg && err?.exception) msg = err.exception;
	if (!msg && err?.message) msg = err.message;

	if (msg.includes("Hall") && msg.includes("not available")) return "This venue space is unavailable for those dates.";
	if (msg.includes("Conflicting Booking")) return "A scheduling block mismatch exists for that selection timeline.";

	return msg || "Submission dropped during database ledger verification pipelines.";
}
