let selectedHallRate = 0;

// ============================
// HALL SELECTION
// ============================
const hallSelect = document.getElementById("eventHall");

if (hallSelect) {
	hallSelect.addEventListener("change", function () {
		const option = this.options[this.selectedIndex];
		if (!option.value) return;

		selectedHallRate = Number(option.dataset.rate || 0);

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
// PRICE CALCULATION
// ============================
function calculateEventPricing() {
	const startEl = document.getElementById("eventStartDateTime");
	const endEl = document.getElementById("eventEndDateTime");

	if (!startEl?.value || !endEl?.value) return;

	const startDate = new Date(startEl.value);
	const endDate = new Date(endEl.value);

	if (isNaN(startDate) || isNaN(endDate)) return;

	if (endDate <= startDate) {
		document.getElementById("totalDays").textContent = "0";
		document.getElementById("totalAmount").textContent = "0";
		return;
	}

	const diffMs = endDate - startDate;
	const totalDays = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));

	const totalAmount = selectedHallRate * totalDays;

	document.getElementById("ratePerDay").textContent = selectedHallRate.toLocaleString();
	document.getElementById("totalDays").textContent = totalDays;
	document.getElementById("totalAmount").textContent = totalAmount.toLocaleString();
}

document.getElementById("eventStartDateTime")?.addEventListener("change", calculateEventPricing);
document.getElementById("eventEndDateTime")?.addEventListener("change", calculateEventPricing);

// ============================
// FRAPPE CALL WRAPPER
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
			.then((r) => r.json())
			.then((data) => {
				if (data.exc || data.exception) return reject(data);
				resolve(data.message);
			})
			.catch(reject);
	});
}

// ============================
//get or create customer o
//============================
async function getOrCreateCustomer(name, email = "", phone = "") {
	if (!name) throw new Error("Customer name required");

	try {
		const existing = await callFrappeMethod("frappe.client.get_value", {
			doctype: "Customer",
			filters: { customer_name: name },
			fieldname: "name",
		});

		const existingName = existing?.name || existing?.message?.name;

		if (existingName) {
			return existingName;
		}

		const customer = await callFrappeMethod("frappe.client.insert", {
			doc: {
				doctype: "Customer",
				customer_name: name,
				customer_type: "Individual",
				customer_group: "Individual",
				territory: "All Territories",
				email_id: email || "",
				mobile_no: phone || "",
			},
		});

		return customer?.name || customer?.message?.name;
	} catch (err) {
		console.error("Customer create/check failed:", err);

		const serverMsg = err?._server_messages || err?.exception || err?.message || "";
		const error = new Error(serverMsg || "Customer creation failed");
		error.original = err;

		throw error;
	}
}

// ============================
// FORM SUBMISSION
// ============================
document.getElementById("eventBookingForm")?.addEventListener("submit", async function (e) {
	e.preventDefault();

	const btn = this.querySelector("button[type='submit']");
	if (btn) {
		btn.disabled = true;
		btn.textContent = "Booking...";
	}

	// ============================
	// ✅ SNAPSHOT FIX (IMPORTANT)
	// ============================
	const finalTotalDays = document.getElementById("totalDays").textContent;
	const finalTotalAmount = document.getElementById("totalAmount").textContent;

	try {
		const customerName = document.getElementById("eventName")?.value?.trim();
		const email = document.getElementById("eventEmail")?.value?.trim();
		const hall = document.getElementById("eventHall")?.value;
		const start = document.getElementById("eventStartDateTime")?.value;
		const end = document.getElementById("eventEndDateTime")?.value;
		const phone = document.getElementById("eventPhone")?.value?.trim();
		const eventType = document.getElementById("eventTypeSelect")?.value;

		if (!customerName || !hall || !start || !end) {
			showAlert("Please fill in all required fields.", "danger");
			return;
		}

		if (!eventType) {
			showAlert("Please select an event type.", "danger");
			return;
		}

		if (new Date(end) <= new Date(start)) {
			showAlert("End date must be after start date.", "danger");
			return;
		}

		const formattedPhone = phone
			? phone.startsWith("+")
				? phone
				: `+234${phone.replace(/^0/, "")}`
			: "";

		const customer = await getOrCreateCustomer(customerName, email, phone);

		const booking = await callFrappeMethod(
			"rhohotel.rhocom_hotel.api.hall_booking.create_booking",
			{
				data: {
					customer_name: customerName,
					customer,
					mobile_number: formattedPhone || "",
					hall,
					event_type: eventType,
					start_datetime: start,
					end_datetime: end,
					submit: true,
				},
			}
		);

		if (!booking?.name) throw new Error("Invalid response from server");

		showAlert(`Booking successful! Reference: ${booking.name}`, "success");

		// ============================
		// SUCCESS UI (FIXED)
		// ============================
		document.getElementById("successReference").textContent = booking.name;
		document.getElementById("successHall").textContent =
			document.getElementById("eventHall").selectedOptions[0].text;

		document.getElementById("successEventType").textContent = eventType;
		document.getElementById("successName").textContent = customerName;
		document.getElementById("successEmail").textContent = email || "-";
		document.getElementById("successPhone").textContent = formattedPhone || "-";

		// ✅ FIX: use snapshot (NOT reset DOM)
		document.getElementById("successTotalDays").textContent = finalTotalDays;

		document.getElementById("successTotalAmount").textContent =
			Number(finalTotalAmount.replace(/,/g, ""))?.toLocaleString?.() || finalTotalAmount;

		document.getElementById("bookingSuccessCard").classList.remove("d-none");
		document.getElementById("eventBookingForm").style.display = "none";

		this.reset();

		document.getElementById("hallSummary").style.display = "none";
		selectedHallRate = 0;

		document.getElementById("ratePerDay").textContent = "-";
		document.getElementById("totalDays").textContent = "0";
		document.getElementById("totalAmount").textContent = "0";

	} catch (err) {
		console.error("Booking error:", err);
		const msg = toUserMessage(err);
		showAlert(msg, "danger");
	} finally {
		if (btn) {
			btn.disabled = false;
			btn.textContent = "Book Event";
		}
	}
});

// ============================
// ALERT SYSTEM
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

	setTimeout(() => (alertBox.innerHTML = ""), 5000);
}

// ============================
// ERROR HANDLER
// ============================
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

	return msg || "Something went wrong. Please try again.";
}