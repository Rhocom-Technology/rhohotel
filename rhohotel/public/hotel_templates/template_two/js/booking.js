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

	// resetRoomBookingForNow();
	// resetEventBookingForNow();
}

document.addEventListener("DOMContentLoaded", initBookingPage);

//availability
let currentAvailability = null;

//booking state management
const bookingState = {
	search: {
		check_in_date: null,
		check_out_date: null,
		adults: 1,
		children: 0,
		number_of_rooms: 1,
		extras: "No extras",
	},

	selectedRooms: [],

	guest: {
		guest_name: "",
		guest_email: "",
		guest_phone: "",
		special_requests: "",
	},

	reservation: null,

	payment: null,
};
bookingState.selectedRooms = [];

//message helper for frappe
function showMessage(message) {
	if (typeof frappe !== "undefined") {
		frappe.msgprint(message);
	} else {
		alert(message);
	}
}

// Navigation functions

let currentStep = 1;

function goToStep(step) {
	document.querySelectorAll(".booking-step").forEach((el) => {
		el.classList.remove("active");
	});

	document.getElementById(`step${step}`).classList.add("active");

	document.querySelectorAll(".web-step").forEach((el) => {
		const num = parseInt(el.dataset.step);

		el.classList.remove("active", "completed");

		if (num < step) {
			el.classList.add("completed");
		}

		if (num === step) {
			el.classList.add("active");
		}
	});

	currentStep = step;

	const activeStep = document.getElementById(`step${step}`);

	if (activeStep) {
		const y = activeStep.getBoundingClientRect().top + window.pageYOffset - 120; // adjust offset

		window.scrollTo({
			top: y,
			behavior: "smooth",
		});
	}

	// window.scrollTo({
	// 	top: 0,
	// 	behavior: "smooth",
	// });
}

function nextStep() {
	goToStep(currentStep + 1);
}

function previousStep() {
	goToStep(currentStep - 1);
}

//rooms loading helper
function showLoading(container) {
	container.innerHTML = `
        <div class="col-12 text-center py-5">
            <div
                class="spinner-border"
                role="status"
            ></div>
        </div>
    `;
}

//api wrapper
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

document.getElementById("searchRoomsBtn").addEventListener("click", searchAvailability);

//search (check availability) function
async function searchAvailability() {
	const checkIn = document.getElementById("roomCheckIn").value;

	const checkOut = document.getElementById("roomCheckOut").value;

	const adults = parseInt(document.getElementById("roomAdults").value);

	const children = parseInt(document.getElementById("roomChildren").value);

	const rooms = parseInt(document.getElementById("numRooms").value);

	const extras = document.getElementById("roomExtras").value;

	if (!checkIn || !checkOut) {
		showMessage("Select check-in and check-out dates.");

		return;
	}

	bookingState.search = {
		check_in_date: checkIn,
		check_out_date: checkOut,
		adults,
		children,
		number_of_rooms: rooms,
		extras,
	};

	const container = document.getElementById("availableRoomsContainer");

	showLoading(container);

	try {
		const response = await apiCall("rhohotel.hotel_api.check_online_availability", {
			check_in_date: checkIn,
			check_out_date: checkOut,
			adults,
			children,
			number_of_rooms: rooms,
		});

		if (!response.success) {
			showMessage(response.message);

			return;
		}

		renderAvailableRooms(response);

		goToStep(2);
	} catch (error) {
		console.error(error);

		showMessage("Could not check room availability.");
	}
}

//room card renderer
function renderAvailableRooms(data) {
	currentAvailability = data;

	const container = document.getElementById("availableRoomsContainer");

	container.innerHTML = "";

	if (!data.room_types || !data.room_types.length) {
		container.innerHTML = `
            <div class="col-12">

                <div
                    class="alert alert-warning"
                >

                    No rooms available
                    for selected dates.

                </div>

            </div>
        `;

		return;
	}

	data.room_types.forEach((room) => {
		container.insertAdjacentHTML("beforeend", createRoomCard(room, data.nights));
	});
}

// room card html
function createRoomCard(room, nights) {
	const image = room.images && room.images.length ? room.images[0].image : "";

	return `
    <div class="col-lg-4">

        <div
            class="card shadow-sm h-100"
        >

            ${
				image
					? `
                <img
                    src="${image}"
                    class="card-img-top"
                    style="
                    height:240px;
                    object-fit:cover;
                    "
                >
                `
					: `
                <div
                    class="bg-light d-flex
                    align-items-center
                    justify-content-center"
                    style="height:240px;"
                >
                    <i
                    class="fa-solid fa-bed
                    fs-1"
                    ></i>
                </div>
                `
			}

            <div class="card-body">

                <h4>
                    ${room.room_type}
                </h4>

                <p class="small">
                    ${room.short_description || ""}
                </p>

                <div class="mb-2">

                    Capacity:
                    ${room.capacity}

                </div>

               <!-- <div class="mb-2">

                    Available:
                    ${room.available_count}

                </div> -->

                <div class="fw-bold">

                    ₦${Number(room.rate_per_night).toLocaleString()}

                    / night

                </div>

                <div class="text-muted">

                    ${nights}
                    night(s)

                </div>

                <hr>

                <label>

                    Rooms Required

                </label>

                <select class="form-select room-qty-selector" data-room-type="${room.room_type}">

                    <option value="0"> Select </option>

                    ${Array.from(
						{
							length: room.available_count,
						},
						(_, i) =>
							`
                            <option
                            value="${i + 1}">
                            ${i + 1}
                            </option>
                            `,
					).join("")}

                </select>

            </div>

        </div>

    </div>
    `;
}

//quantity change handler
document.addEventListener("change", function (e) {
	if (!e.target.classList.contains("room-qty-selector")) {
		return;
	}

	updateSelectedRooms();
});

//seleced rooms updater (builder)
function updateSelectedRooms() {
	console.log(currentAvailability);

	bookingState.selectedRooms = [];

	document.querySelectorAll(".room-qty-selector").forEach((selector) => {
		const qty = parseInt(selector.value);

		if (qty < 1) {
			return;
		}

		const card = selector.closest(".card");

		const roomType = selector.dataset.roomType;

		if (!currentAvailability?.room_types) return;

		console.log("roomType:", roomType);

		const room = currentAvailability.room_types.find((r) => r.room_type === roomType);

		console.log("found room:", room);

		if (!room) return;

		bookingState.selectedRooms.push({
			room_type: room.room_type,

			count: qty,

			rate_per_night: room.rate_per_night,

			nights: currentAvailability.nights,

			total_amount: room.rate_per_night * qty * currentAvailability.nights,
		});
	});
	console.log(bookingState.selectedRooms);
}

//proceed to summary btn handler
document.getElementById("continueToSummaryBtn").addEventListener("click", proceedToSummary);

//validate selection
function proceedToSummary() {
	if (!bookingState.selectedRooms.length) {
		showMessage("Select at least one room.");

		return;
	}

	const selectedCount = bookingState.selectedRooms.reduce((sum, item) => sum + item.count, 0);

	if (selectedCount < bookingState.search.number_of_rooms) {
		showMessage(`Please select at least ${bookingState.search.number_of_rooms} room(s).`);

		return;
	}

	buildSummaryStep();

	goToStep(3);
}

//summary renderer
function buildSummaryStep() {
	const container = document.getElementById("bookingSummaryContainer");

	let total = 0;

	const rows = bookingState.selectedRooms
		.map((room) => {
			total += room.total_amount;

			return `
                <tr>

                    <td>
                        ${room.room_type}
                    </td>

                    <td>
                        ${room.count}
                    </td>

					 <td>
                        ${currentAvailability.nights}
                    </td>

                    <td>
                        ₦${room.rate_per_night.toLocaleString()}
                    </td>

                    <td>
                        ₦${room.total_amount.toLocaleString()}
                    </td>

                </tr>
            `;
		})
		.join("");

	container.innerHTML = `

        <h2>
            Booking Summary
        </h2>

        <table
            class="
            table
            table-bordered
            "
        >

            <thead>

                <tr>

                    <th>
                        Room
                    </th>

                    <th>
                        Qty
                    </th>

					<th>
                        No. of Nights
                    </th>

                    <th>
                        Rate
                    </th>

                    <th>
                        Total
                    </th>

                </tr>

            </thead>

            <tbody>

                ${rows}

            </tbody>

        </table>

        <div class="fs-4 fw-bold">

            Total:

            ₦${total.toLocaleString()}

        </div>

        <div class="mt-4">

            <button
                type="button"
                class="web-btn-ghost"
                onclick="goToStep(2)"
            >
                Back
            </button>

            <button
                type="button"
                class="web-btn-solid"
                onclick="goToGuestStep()"
            >
                Continue
            </button>

        </div>

    `;
}

//Guest step navigation
function goToGuestStep() {
	goToStep(4);
}

//review button
document.getElementById("reviewBookingBtn").addEventListener("click", prepareReviewStep);

//guest validation
function prepareReviewStep() {
	const guest_name = document.getElementById("guestName").value.trim();

	const guest_email = document.getElementById("guestEmail").value.trim();

	const guest_phone = document.getElementById("guestPhone").value.trim();

	const special_requests = document.getElementById("specialRequests").value.trim();

	if (!guest_name) {
		showMessage("Guest name is required");

		return;
	}

	if (!guest_email) {
		showMessage("Guest email is required.");
		return;
	}

	const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

	if (!emailPattern.test(guest_email)) {
		showMessage("Enter a valid email address.");
		return;
	}

	if (!guest_phone) {
		showMessage("Phone number is required.");
		return;
	}

	const phonePattern = /^[0-9]{7,15}$/;

	if (!phonePattern.test(guest_phone)) {
		showMessage("Phone number must contain only digits and be between 7 and 15 digits.");
		return;
	}

	bookingState.guest = {
		guest_name,
		guest_email,
		guest_phone,
		special_requests,
	};

	buildReviewStep();

	goToStep(5);
}

//review builder
function buildReviewStep() {
	const container = document.getElementById("reservationReviewContainer");

	let total = 0;

	const roomsHtml = bookingState.selectedRooms
		.map((room) => {
			total += room.total_amount;

			return `
                <tr>

                    <td>
                        ${room.room_type}
                    </td>

                    <td>
                        ${room.count}
                    </td>

					 <td>
                        ${currentAvailability.nights}
                    </td>

                    <td>
                        ₦${room.total_amount.toLocaleString()}
                    </td>

                </tr>
            `;
		})
		.join("");

	container.innerHTML = `

        <div class="row">

            <div class="col-lg-10">

                <div class="card shadow-sm">

                    <div class="card-body">

                        <h2 class="mb-4">
                            Review Reservation
                        </h2>

                        <h5>
                            Guest
                        </h5>

                        <p>

                            ${bookingState.guest.guest_name}
                            <br>

                            ${bookingState.guest.guest_email}
                            <br>

                            ${bookingState.guest.guest_phone}

                        </p>

                        <hr>

                        <h5>
                            Stay Details
                        </h5>

                        <table class="table">

                            <thead>

                                <tr>

                                    <th>
                                        Room Type
                                    </th>

                                    <th>
                                        Qty
                                    </th>

									 <th>
                                        No. of Nights
                                    </th>

                                    <th>
                                        Amount
                                    </th>

                                </tr>

                            </thead>

                            <tbody>

                                ${roomsHtml}

                            </tbody>

                        </table>

                        <div
                            class="
                            fs-4
                            fw-bold
                            "
                        >

                            Total:
                            ₦${total.toLocaleString()}

                        </div>

						<div
    class="alert alert-warning mt-4"
>
    <i class="fa-solid fa-triangle-exclamation me-2"></i>

    Please review your reservation carefully.

    Once you click
    <strong>Confirm Booking</strong>,
    your reservation will be created and
    booking details can no longer be modified online.
</div>

                        <div class="mt-4">

                            <button
                                type="button"
                                class="web-btn-ghost"
                                onclick="goToStep(4)"
                            >
                                Back
                            </button>

                            <button
                                type="button"
                                id="submitReservationBtn"
                                class="web-btn-solid"
                            >
                                Confirm Booking
                            </button>

                        </div>

                    </div>

                </div>

            </div>

        </div>
    `;

	attachSubmitReservation();
}

//reservation submission handler
function attachSubmitReservation() {
	document.getElementById("submitReservationBtn").addEventListener("click", createReservation);
}

//build rooms_request helper
function getRoomsRequested() {
	return bookingState.selectedRooms.map((room) => ({
		room_type: room.room_type,

		count: room.count,
	}));
}

//create reservation
async function createReservation() {
	try {
		const btn = document.getElementById("submitReservationBtn");

		btn.disabled = true;

		btn.innerHTML = "Creating Reservation...";

		const response = await apiCall("rhohotel.hotel_api.submit_online_reservation", {
			check_in_date: bookingState.search.check_in_date,

			check_out_date: bookingState.search.check_out_date,

			adults: bookingState.search.adults,

			children: bookingState.search.children,

			guest_name: bookingState.guest.guest_name,

			guest_email: bookingState.guest.guest_email,

			guest_phone: bookingState.guest.guest_phone,

			extras: bookingState.search.extras,

			special_requests: bookingState.guest.special_requests,

			rooms_requested: JSON.stringify(getRoomsRequested()),
		});

		if (!response.success) {
			showMessage(response.message);

			btn.disabled = false;

			btn.innerHTML = "Confirm Booking";

			return;
		}

		bookingState.reservation = response;

		bookingState.reservation.reservation;

		document.getElementById("reservationNumber").value = response.reservation;

		buildPaymentStep();

		goToStep(6);
	} catch (error) {
		console.error(error);

		const btn = document.getElementById("submitReservationBtn");

		if (btn) {
			btn.disabled = false;

			btn.innerHTML = "Confirm Booking";
		}

		showMessage(error.message || "Reservation creation failed.");
	}
}

//payment builder
function buildPaymentStep() {
	const container = document.getElementById("paymentContainer");

	const reservation = bookingState.reservation;

	const summary = reservation.summary;
container.innerHTML = `
    <div class="row justify-content-center">
        <div class="col-lg-7">
            <div class="card shadow-sm border-0 rounded-4 overflow-hidden">
                <div style="height: 4px; background: linear-gradient(90deg, #1e293b, #475569);"></div>
                
                <div class="card-body p-4 p-md-5">
                    <div class="text-center mb-5">
                        <h2 class="fw-bold text-dark mb-2" style="letter-spacing: -0.5px;">Complete Your Payment</h2>
                        <p class="text-muted col-md-10 mx-auto">
                            Your booking details are securely locked in. Please complete your payment below to finalize your reservation at Serene Stay.
                        </p>
                    </div>
                    
                    <div class="row g-3 mb-4">
                        <div class="col-md-6">
                            <div class="p-3 rounded-3 border h-100 d-flex flex-column justify-content-center" style="background-color: #fafafa;">
                                <small class="text-uppercase tracking-wider text-muted fw-semibold fs-7 mb-1">Guest Details</small>
                                <div class="fw-bold text-dark fs-5">${summary.guest_name}</div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="p-3 rounded-3 border h-100 d-flex flex-column justify-content-center" style="background-color: #fafafa;">
                                <small class="text-uppercase tracking-wider text-muted fw-semibold fs-7 mb-1">Accommodation</small>
                                <div class="fw-bold text-dark fs-5">${summary.rooms_booked}</div>
                            </div>
                        </div>
                        
                        <div class="col-12">
                            <div class="p-3 rounded-3 border d-flex justify-content-between align-items-center" style="background-color: #f1f5f9;">
                                <div>
                                    <small class="text-uppercase tracking-wider text-muted fw-semibold fs-7 d-block">Total Amount</small>
                                    <span class="text-muted fs-7">All taxes & fees included</span>
                                </div>
                                <div class="fs-3 fw-bolder text-dark">
                                    ₦${Number(summary.total_amount).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="p-3 rounded-3 border border-dashed mb-5 text-center" style="background-color: #fffdec; border-color: #e2d6b5 !important;">
                        <p class="mb-0 text-dark-emphasis fs-6">
                            <strong>Need to finish this later?</strong> A secure payment link has been sent to your email. 
                            You can use it to complete your booking within the next <strong>15 minutes</strong> before it expires.
                        </p>
                    </div>

                    <div class="text-center">
                        <button type="button" id="payNowBtn" class="web-btn-solid w-100 py-3 fw-bold rounded-3 fs-5 shadow-sm transition-all">
                            Pay Now & Secure Reservation
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
`;

	attachPaymentHandler();
}

//payment button handler
function attachPaymentHandler() {
	document.getElementById("payNowBtn").addEventListener("click", startPayment);
}

//create paystack link
async function startPayment() {
	try {
		const btn = document.getElementById("payNowBtn");

		btn.disabled = true;

		btn.style.pointerEvents = "none";

		btn.innerHTML = ` <i class="fa fa-spinner fa-spin"></i> Opening Payment Gateway...`;

		const reservationName = bookingState.reservation.reservation;

		const response = await apiCall("rhohotel.hotel_api.create_reservation_payment_link", {
			reservation_name: reservationName,
		});

		if (!response.success) {
			showMessage(response.message);

			btn.disabled = false;

			btn.innerHTML = "Proceed To Payment";

			return;
		}

		sessionStorage.setItem("hotelReservation", reservationName);

		window.location.href = response.payment_url;
	} catch (error) {
		console.error(error);

		showMessage(
			"Payment could not be started. Please check your internet connection or contact support.",
		);

		const btn = document.getElementById("payNowBtn");
		if (btn) {
			btn.disabled = false;
			btn.innerHTML = "Proceed To Payment";
		}
	}
}

// function getReservationNumber() {
// 	return sessionStorage.getItem("hotelReservation");
// }

// //verify payment
// async function verifyBookingPayment() {
// 	const reservation = getReservationNumber();

// 	if (!reservation) {
// 		document.getElementById("bookingSuccessContainer").innerHTML = `
//             <div class="alert alert-danger">
//                 Reservation not found.
//             </div>
//         `;
// 		return;
// 	}

// 	try {
// 		const response = await fetch(
// 			`/api/method/rhohotel.hotel_api.verify_reservation_payment?reference=${reservation}`
// 		);

// 		const result = await response.json();
// 		const data = result.message;

// 		if (!data.success) {
// 			throw new Error(data.message);
// 		}

// 		// 🚨 THIS IS WHERE YOUR REDIRECT GOES
// 		window.location.href =
// 			`/booking-success?reservation=${data.reservation}`;

// 	} catch (error) {
// 		document.getElementById("bookingSuccessContainer").innerHTML = `
//             <div class="alert alert-danger">
//                 ${error.message}
//             </div>
//         `;
// 	}
// }

// //confirmation renderer
// function buildConfirmationPage(payment) {
// 	document.getElementById("confirmationContainer").innerHTML = `

//         <div
//             class="
//             card
//             shadow-sm
//             "
//         >

//             <div
//                 class="
//                 card-body
//                 p-5
//                 "
//             >

//                 <div
//                     class="
//                     text-center
//                     mb-4
//                     "
//                 >

//                     <i
//                         class="
//                         fa-solid
//                         fa-circle-check
//                         text-success
//                         display-3
//                         "
//                     ></i>

//                     <h2
//                         class="
//                         mt-3
//                         "
//                     >
//                         Booking Confirmed
//                     </h2>

//                 </div>

//                 <div
//                     id="
//                     receiptArea
//                     "
//                 >

//                     <table
//                         class="
//                         table
//                         "
//                     >

//                         <tr>

//                             <th>
//                                 Reservation
//                             </th>

//                             <td>
//                                 ${payment.reservation}
//                             </td>

//                         </tr>

//                         <tr>

//                             <th>
//                                 Payment Status
//                             </th>

//                             <td>
//                                 ${payment.payment_status}
//                             </td>

//                         </tr>

//                         <tr>

//                             <th>
//                                 Reservation Status
//                             </th>

//                             <td>
//                                 ${payment.reservation_status}
//                             </td>

//                         </tr>

//                     </table>

//                 </div>

//                 <div
//                     class="
//                     mt-4
//                     "
//                 >

//                     <button
//                         class="
//                         web-btn-solid
//                         "
//                         onclick="
//                         printReceipt()
//                         "
//                     >
//                         Print Receipt
//                     </button>

//                 </div>

//             </div>

//         </div>

//     `;
// }

// //print receipt
// function printReceipt() {
// 	const receipt = document.getElementById("receiptArea").innerHTML;

// 	const win = window.open("", "_blank");

// 	win.document.write(`
//         <html>
//         <head>
//             <title>
//                 Receipt
//             </title>
//         </head>
//         <body>

//             ${receipt}

//         </body>
//         </html>
//     `);

// 	win.document.close();

// 	win.print();
// }
window.addEventListener("pageshow", function () {
	const btn = document.getElementById("payNowBtn");

	if (btn) {
		btn.disabled = false;
		btn.style.pointerEvents = "";
		btn.innerHTML = "Proceed To Payment";
	}
});
