// =========================================================================
// GLOBAL SETUP & WORKSPACE STATE CONFIGURATION
// =========================================================================
let currentAvailability = null;

const bookingState = {
	search: {
		check_in_date: null,
		check_out_date: null,
		adults: 2,
		children: 0,
		number_of_rooms: 1,
		extras: "No extras",
	},
	selectedRooms: {
		executive: { room_type: "Executive Royal Suite", count: 0, rate: 75000 },
		presidential: { room_type: "Imperial Presidential", count: 0, rate: 150000 }
	},
	guest: {
		guest_name: "",
		guest_email: "",
		guest_phone: "",
		special_requests: "",
	},
	reservation: null,
};

// Custom Helper: Message handler with native Frappe fallback matching project rules
function showMessage(message) {
	if (typeof frappe !== "undefined") {
		frappe.msgprint(message);
	} else {
		alert(message);
	}
}

// Custom Helper: Unified Async Frappe Core Request Routing
async function apiCall(method, args = {}) {
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
			"X-Frappe-CSRF-Token":
				window.csrf_token ||
				document.querySelector('meta[name="csrf-token"]')?.content ||
				"",
		},
		body: JSON.stringify(args),
	});

	const result = await response.json();
	if (result.exc) {
		throw new Error(result.exc);
	}
	return result.message;
}

// =========================================================================
// STEP 1: INITIAL DATE INPUT VALIDATION & NIGHT MATH
// =========================================================================
document.addEventListener("DOMContentLoaded", function () {
	const checkinInput = document.getElementById("input_checkin");
	const checkoutInput = document.getElementById("input_checkout");

	if (checkinInput && checkoutInput) {
		const today = new Date().toISOString().split("T")[0];
		checkinInput.min = today;
		checkoutInput.min = today;

		// Set initial baseline defaults safely if empty
		if (!checkinInput.value) checkinInput.value = today;
		if (!checkoutInput.value) {
			const tomorrow = new Date();
			tomorrow.setDate(tomorrow.getDate() + 1);
			checkoutInput.value = tomorrow.toISOString().split("T")[0];
		}
		calculateNights();

		checkinInput.addEventListener("change", function () {
			checkoutInput.min = checkinInput.value;
			if (checkoutInput.value && checkoutInput.value < checkinInput.value) {
				checkoutInput.value = "";
			}
			calculateNights();
		});

		checkoutInput.addEventListener("change", calculateNights);
	}
});

function calculateNights() {
	const checkinInput = document.getElementById("input_checkin");
	const checkoutInput = document.getElementById("input_checkout");
	const nightsInput = document.getElementById("input_nights");

	if (!checkinInput || !checkoutInput) return 0;
	if (!checkinInput.value || !checkoutInput.value) {
		if (nightsInput) nightsInput.value = "";
		return 0;
	}

	const start = new Date(checkinInput.value + "T00:00:00");
	const end = new Date(checkoutInput.value + "T00:00:00");
	const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

	if (diff <= 0) {
		if (nightsInput) nightsInput.value = "";
		return 0;
	}

	if (nightsInput) nightsInput.value = diff;
	return diff;
}

// Increment/Decrement helpers for the step 1 form buttons
function incrementValue(id) {
	const input = document.getElementById(id);
	if (input) {
		input.value = parseInt(input.value, 10) + 1;
		if (id === 'adultsCount' || id === 'childrenCount') {
			validateInputField(input, id === 'adultsCount' ? 1 : 0);
		}
	}
}

function decrementValue(id) {
	const input = document.getElementById(id);
	if (input) {
		const min = parseInt(input.getAttribute('min'), 10) || 0;
		const current = parseInt(input.value, 10);
		if (current > min) {
			input.value = current - 1;
			if (id === 'adultsCount' || id === 'childrenCount') {
				validateInputField(input, id === 'adultsCount' ? 1 : 0);
			}
		}
	}
}

function validateInputField(input, minVal) {
	let val = parseInt(input.value, 10);
	if (isNaN(val) || val < minVal) {
		input.value = minVal;
	}
}

// =========================================================================
// STEP 2: AVAILABILITY ENGINE & DYNAMIC LOOP RENDERING
// =========================================================================
// =========================================================================
// STEP 2: AVAILABILITY ENGINE & DYNAMIC LOOP RENDERING
// =========================================================================
async function searchAvailability() {
	// Grab using your actual layout IDs
	const checkIn = document.getElementById("input_checkin").value;
	const checkOut = document.getElementById("input_checkout").value;
	const adults = parseInt(document.getElementById("adultsCount")?.value || 2, 10);
	const children = parseInt(document.getElementById("childrenCount")?.value || 0, 10);
	const rooms = parseInt(document.getElementById("input_rooms")?.value || 1, 10);

	if (!checkIn || !checkOut) {
		showMessage("Please select valid check-in and check-out dates.");
		return;
	}

	// Update operational application state parameters
	bookingState.search = {
		check_in_date: checkIn,
		check_out_date: checkOut,
		adults,
		children,
		number_of_rooms: rooms,
		extras: "No extras"
	};
	bookingState.selectedRooms = {};

	const totalNights = calculateNights();

	// Sync step 2 tracking header badges
	const summaryDates = document.getElementById("summaryDatesLabel");
	const summaryNights = document.getElementById("summaryNightsLabel");
	const summaryComposition = document.getElementById("summaryCompositionLabel");

	if (summaryDates) summaryDates.innerHTML = `<i class="bi bi-calendar3 me-1 text-accent-theme"></i> ${checkIn} — ${checkOut}`;
	if (summaryNights) summaryNights.innerText = `${totalNights} ${totalNights === 1 ? "Night" : "Nights"}`;
	if (summaryComposition) summaryComposition.innerHTML = `<i class="bi bi-people-fill me-1 text-accent-theme"></i> ${adults} Adults, ${children} Children`;

	const submitBtn = document.querySelector("#roomBookingTab button[type='submit']");
	const originalHtml = submitBtn ? submitBtn.innerHTML : "";

	if (submitBtn) {
		submitBtn.disabled = true;
		submitBtn.innerHTML = `<div class="spinner-border spinner-border-sm text-light me-2"></div> Verification In Progress...`;
	}

	try {
		// Fire transaction payload direct to your live Frappe API method
		const response = await apiCall("rhohotel.hotel_api.check_online_availability", {
			check_in_date: checkIn,
			check_out_date: checkOut,
			adults,
			children,
			number_of_rooms: rooms,
		});

		if (submitBtn) {
			submitBtn.disabled = false;
			submitBtn.innerHTML = originalHtml;
		}

		if (!response.success) {
			showMessage(response.message);
			return;
		}

		currentAvailability = response;

		const container = document.getElementById("availableRoomsContainer");
		const fallbackAlert = document.getElementById("noRoomsFallbackAlert");

		if (!container) return;
		container.innerHTML = ""; // Empty dynamic allocation grid

		// CRITICAL CORRECTION: Frappe uses 'room_types' array, not 'available_rooms'
		if (!response.room_types || response.room_types.length === 0) {
			fallbackAlert?.classList.remove("d-none");
			recalculateGlobalCartTotals();
		} else {
			fallbackAlert?.classList.add("d-none");

			// Loop seamlessly over room types returned by the backend database
			response.room_types.forEach(room => {
				const dynamicSlug = room.room_type.toLowerCase().replace(/[^a-z0-9]/g, "_");

				// Match state variables safely to actual properties returned from Frappe
				const ratePerNight = room.rate_per_night || room.rate || 0;

				bookingState.selectedRooms[dynamicSlug] = {
					room_type: room.room_type,
					count: 0,
					rate: ratePerNight
				};

				// Pull layout image from first image in the returned list, or fallback to unsplash placeholders
				const roomImage = (room.images && room.images.length > 0) ? room.images[0].image :
					(room.room_type.includes("Imperial")
						? "https://images.unsplash.com/photo-1590490360182-c33d57733427?q=80&w=600&auto=format&fit=crop"
						: "https://images.unsplash.com/photo-1618773928121-c32242e63f39?q=80&w=600&auto=format&fit=crop");

				const premiumBadgeHtml = room.room_type.toLowerCase().includes("imperial") || ratePerNight > 100000
					? `<span class="badge bg-warning text-dark position-absolute top-0 start-0 m-3 text-uppercase fw-bold tracking-wider" style="font-size:0.6rem; z-index: 2;">Premium Option</span>`
					: "";

				const roomCardHtml = `
          <div class="col-lg-6">
            <div class="card h-100 border rounded-2 shadow-sm overflow-hidden bg-white">
              <div class="row g-0 h-100">
                <div class="col-sm-5 bg-dark position-relative min-h-200" style="background: url('${roomImage}') center/cover no-repeat;">
                  ${premiumBadgeHtml}
                </div>
                <div class="col-sm-7 p-4 d-flex flex-column justify-content-between">
                  <div>
                    <div class="d-flex justify-content-between align-items-start mb-1">
                      <h5 class="fw-black text-dark text-uppercase m-0 tracking-tight" style="font-size: 0.95rem;">${room.room_type}</h5>
                      <span class="fw-black text-accent-theme h6 m-0" style="font-size: 0.9rem;">₦${Number(ratePerNight).toLocaleString()}<span class="text-muted fw-normal small" style="font-size: 0.65rem;">/Nt</span></span>
                    </div>
                    <p class="text-muted small mb-3" style="font-size: 0.75rem; line-height: 1.4;">${room.short_description || room.description || 'Refined layouts featuring elegant furniture settings, modern entertainment sets, and elite room fixtures.'}</p>
                    <div class="d-flex gap-3 text-muted mb-4" style="font-size: 0.72rem;">
                      <span><i class="bi bi-person-fill text-accent-theme"></i> Max ${room.capacity || 2} Guests</span>
                      <span><i class="bi bi-door-open-fill text-accent-theme"></i> ${room.available_count || 1} Available</span>
                    </div>
                  </div>
                  <div class="d-flex align-items-center justify-content-between border-top pt-3">
                    <span class="text-muted small fw-bold text-uppercase" style="font-size: 0.65rem;">Select Rooms</span>
                    <div class="input-group input-group-sm" style="max-width: 110px;">
                      <button class="btn btn-outline-secondary" type="button" onclick="adjustSelectedRoomCount('${dynamicSlug}', -1)">-</button>
                      <input type="number" class="form-control text-center fw-bold room-qty-selector" id="qty_${dynamicSlug}" value="0" min="0" max="${room.available_count || 5}" readonly>
                      <button class="btn btn-outline-secondary" type="button" onclick="adjustSelectedRoomCount('${dynamicSlug}', 1)">+</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
				container.insertAdjacentHTML("beforeend", roomCardHtml);
			});
			recalculateGlobalCartTotals();
		}

		// Swap workspace containers smoothly
		document.getElementById("booking-form-workspace").classList.add("d-none");
		document.getElementById("booking-results-workspace").classList.remove("d-none");

	} catch (error) {
		console.error(error);
		if (submitBtn) {
			submitBtn.disabled = false;
			submitBtn.innerHTML = originalHtml;
		}
		showMessage("Could not pull live inventory logs from server cluster.");
	}
}

// =========================================================================
// QUANTITY MANAGEMENT & SELECTION CARD CONTROLS
// =========================================================================
function adjustSelectedRoomCount(type, delta) {
	const input = document.getElementById(`qty_${type}`);
	if (!input) return;

	let currentCount = parseInt(input.value, 10) || 0;
	let newCount = currentCount + delta;

	if (newCount < 0) newCount = 0;
	if (newCount > 10) newCount = 10; // Upper limit boundary guard

	input.value = newCount;
	bookingState.selectedRooms[type].count = newCount;

	recalculateGlobalCartTotals();
}

function recalculateGlobalCartTotals() {
	const totalNights = calculateNights() || 1;
	const targetRoomsGoal = bookingState.search.number_of_rooms || 1;

	let chosenCount = 0;
	let accumulatedCost = 0;

	Object.keys(bookingState.selectedRooms).forEach(key => {
		const item = bookingState.selectedRooms[key];
		chosenCount += item.count;
		accumulatedCost += (item.count * item.rate * totalNights);
	});

	// Update layout anchors
	const roomsLabel = document.getElementById("stickyTotalRoomsLabel");
	const costLabel = document.getElementById("stickyTotalCostLabel");
	const actionBtn = document.getElementById("stickyBookBtn");

	if (roomsLabel) roomsLabel.innerText = `${chosenCount} ${chosenCount === 1 ? "Room Selected" : "Rooms Selected"}`;
	if (costLabel) costLabel.innerText = `₦${accumulatedCost.toLocaleString()}`;

	// Balance authorization pathways check
	if (chosenCount === targetRoomsGoal) {
		if (actionBtn) actionBtn.removeAttribute("disabled");
	} else {
		if (actionBtn) actionBtn.setAttribute("disabled", "true");
	}
}

// =========================================================================
// STEP 3: GUEST MANIFEST FORM PREPARATION
// =========================================================================
function proceedToSummary() {
	document.getElementById("booking-results-workspace").classList.add("d-none");
	document.getElementById("booking-verification-workspace").classList.remove("d-none");

	const checkIn = document.getElementById("input_checkin").value;
	const checkOut = document.getElementById("input_checkout").value;
	const costText = document.getElementById("stickyTotalCostLabel")?.innerText || "₦0.00";

	// Sync state data to form layouts
	const step3Dates = document.getElementById("step3DatesLabel");
	if (step3Dates) step3Dates.innerText = `${checkIn} to ${checkOut}`;

	const chosenProfiles = [];
	Object.keys(bookingState.selectedRooms).forEach(key => {
		const item = bookingState.selectedRooms[key];
		if (item.count > 0) chosenProfiles.push(`${item.count}x ${item.room_type}`);
	});

	const step3Rooms = document.getElementById("step3SelectedRoomsLabel");
	if (step3Rooms) step3Rooms.innerText = chosenProfiles.join(", ");

	// Populate dynamic editable profile details copies
	if (document.getElementById("step3AdultsCount")) document.getElementById("step3AdultsCount").value = bookingState.search.adults;
	if (document.getElementById("step3ChildrenCount")) document.getElementById("step3ChildrenCount").value = bookingState.search.children;

	if (document.getElementById("step3BaseTotalDisplay")) document.getElementById("step3BaseTotalDisplay").innerText = costText;
	if (document.getElementById("step3GrandTotalDisplay")) document.getElementById("step3GrandTotalDisplay").innerText = costText;

	window.scrollTo({
		top: document.getElementById("booking-engine-core")?.offsetTop - 20 || 0,
		behavior: "smooth",
	});
}

// =========================================================================
// STEP 4 & 5: VALIDATE GUEST AND PROCESS RESERVATION HOLD
// =========================================================================
function getRoomsRequestedArray() {
	const arr = [];
	Object.keys(bookingState.selectedRooms).forEach(key => {
		const item = bookingState.selectedRooms[key];
		if (item.count > 0) {
			arr.push({ room_type: item.room_type, count: item.count });
		}
	});
	return arr;
}

async function prepareAndSubmitReservation(wantsImmediatePayment = false) {
	const guest_name = document.getElementById("guestFullName")?.value.trim();
	const guest_email = document.getElementById("guestEmail")?.value.trim();
	const guest_phone = document.getElementById("guestPhone")?.value.trim();
	const special_requests = document.getElementById("guestNotes")?.value.trim() || "";

	if (!guest_name || !guest_email || !guest_phone) {
		showMessage("Please fill all required primary guest contact fields.");
		return;
	}

	// Capture updated guest counts from step 3 adjustments if changed
	const finalAdults = parseInt(document.getElementById("step3AdultsCount")?.value || bookingState.search.adults, 10);
	const finalChildren = parseInt(document.getElementById("step3ChildrenCount")?.value || bookingState.search.children, 10);

	bookingState.guest = { guest_name, guest_email, guest_phone, special_requests };

	try {
		const response = await apiCall("rhohotel.hotel_api.submit_online_reservation", {
			check_in_date: bookingState.search.check_in_date,
			check_out_date: bookingState.search.check_out_date,
			adults: finalAdults,
			children: finalChildren,
			guest_name: bookingState.guest.guest_name,
			guest_email: bookingState.guest.guest_email,
			guest_phone: bookingState.guest.guest_phone,
			extras: bookingState.search.extras,
			special_requests: bookingState.guest.special_requests,
			rooms_requested: JSON.stringify(getRoomsRequestedArray()),
		});

		if (!response.success) {
			showMessage(response.message);
			return;
		}

		bookingState.reservation = response;

		if (wantsImmediatePayment) {
			// Direct routing link out to paystack gateway pipeline
			await launchPaystackGateway(response.reservation);
		} else {
			// Build and showcase receipt manifest container as a standard local hold
			renderFinalReceiptVoucher("Hold / Unpaid");
		}

	} catch (error) {
		console.error(error);
		showMessage(error.message || "Reservation transmission failed.");
	}
}

async function launchPaystackGateway(reservationName) {
	try {
		const response = await apiCall("rhohotel.hotel_api.create_reservation_payment_link", {
			reservation_name: reservationName,
		});

		if (!response.success) {
			showMessage(response.message);
			return;
		}

		sessionStorage.setItem("hotelReservation", reservationName);
		window.location.href = response.payment_url; // Seamless outbound payment redirect
	} catch (error) {
		console.error(error);
		showMessage("Failed to construct external Paystack transactional gateway routing safely.");
	}
}

// =========================================================================
// STEP 6: RECEIPT PROCESSING & INLINE VOUCHER RENDER OPERATIONS
// =========================================================================
function renderFinalReceiptVoucher(statusText) {
	// 1. Hide the guest contact verification form pane
	const verificationPane = document.getElementById("booking-verification-workspace");
	if (verificationPane) {
		verificationPane.classList.add("d-none");
	}

	// 2. Unmask your beautiful inline confirmation layout container
	const confirmationPane = document.getElementById("booking-confirmation-workspace");
	if (confirmationPane) {
		confirmationPane.classList.remove("d-none");
	} else {
		console.error("Critical Layout Error: 'booking-confirmation-workspace' container missing from DOM.");
		showMessage("Reservation processed successfully, but the confirmation screen node could not be found.");
		return;
	}

	const res = bookingState.reservation;
	const summary = res.summary;

	// 3. Map values directly onto your printable receipt targets
	if (document.getElementById("manifestTokenString")) document.getElementById("manifestTokenString").innerText = res.reservation;
	if (document.getElementById("receiptGuestName")) document.getElementById("receiptGuestName").innerText = summary.guest_name;
	if (document.getElementById("receiptGuestEmail")) document.getElementById("receiptGuestEmail").innerText = bookingState.guest.guest_email;
	if (document.getElementById("receiptGuestPhone")) document.getElementById("receiptGuestPhone").innerText = bookingState.guest.guest_phone;

	if (document.getElementById("receiptCheckInDate")) document.getElementById("receiptCheckInDate").innerText = bookingState.search.check_in_date;
	if (document.getElementById("receiptCheckOutDate")) document.getElementById("receiptCheckOutDate").innerText = bookingState.search.check_out_date;
	if (document.getElementById("receiptNightsCount")) document.getElementById("receiptNightsCount").innerText = `${summary.nights} Night(s)`;
	if (document.getElementById("receiptComposition")) document.getElementById("receiptComposition").innerText = `${summary.adults} Adults, ${summary.children} Children`;
	if (document.getElementById("receiptNotesProfile")) document.getElementById("receiptNotesProfile").innerText = summary.special_requests || "None";

	if (document.getElementById("receiptRoomsProfile")) document.getElementById("receiptRoomsProfile").innerText = summary.rooms_booked;
	if (document.getElementById("receiptBaseAmountLine")) document.getElementById("receiptBaseAmountLine").innerText = "₦" + Number(summary.total_amount).toLocaleString();
	if (document.getElementById("receiptFinalAmount")) document.getElementById("receiptFinalAmount").innerText = "₦" + Number(summary.total_amount).toLocaleString();

	// 4. Update the visual Status Badge styling based on selection criteria
	const statusBadge = document.getElementById("receiptStatusBadge");
	const alertBanner = document.getElementById("bootstrapHoldAlert");

	if (statusBadge) {
		statusBadge.innerText = statusText;
		if (statusText.includes("Paid")) {
			statusBadge.className = "badge bg-success text-white mt-2 px-3 py-2 text-uppercase";
		} else {
			statusBadge.className = "badge bg-warning text-dark mt-2 px-3 py-2 text-uppercase";
		}
	}

	if (alertBanner) {
		if (statusText.includes("Hold")) {
			alertBanner.classList.remove("d-none"); // Show payment guidelines if it's a pay-later hold
		} else {
			alertBanner.classList.add("d-none");
		}
	}

	// 5. Smooth scroll up to the top of the booking platform core matrix
	const coreAnchor = document.getElementById("booking-engine-core");
	if (coreAnchor) {
		window.scrollTo({ top: coreAnchor.offsetTop - 20, behavior: "smooth" });
	}
}

function printReceipt() {
	window.print();
}

// =========================================================================
// HTML LAYOUT COMPATIBILITY ROUTERS (MATCHING YOUR FORM ATTRIBUTES)
// =========================================================================
function handleSearchSubmitAndSwap() {
	searchAvailability();
}

function executeRoomBookingHoldTransition() {
	proceedToSummary();
}

function processPaystackEngineGateway() {
	prepareAndSubmitReservation(true); // True triggers Paystack loop
}

function processPayLaterHoldRequest() {
	prepareAndSubmitReservation(false); // False keeps it local as a Hold
}

function revertToRoomSelectionGrid() {
	document.getElementById("booking-verification-workspace").classList.add("d-none");
	document.getElementById("booking-results-workspace").classList.remove("d-none");
}

function revertToSearchCriteria() {
	document.getElementById("booking-results-workspace").classList.add("d-none");
	document.getElementById("booking-form-workspace").classList.remove("d-none");
}
