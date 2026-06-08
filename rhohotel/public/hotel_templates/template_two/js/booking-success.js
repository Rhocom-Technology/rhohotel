function getReservationNumber() {
	const params = new URLSearchParams(window.location.search);

	return params.get("reservation") || params.get("reference") || params.get("trxref");
}

document.addEventListener("DOMContentLoaded", verifyBookingPayment);

async function verifyBookingPayment() {
	const reservation = getReservationNumber();
	const container = document.getElementById("bookingSuccessContainer");

	if (!container) return;

	if (!reservation) {
		showError(container, "Reservation not found.");
		return;
	}

	try {
		const response = await fetch(
			`/api/method/rhohotel.hotel_api.verify_reservation_payment?reference=${reservation}`,
		);

		const result = await response.json();
		const data = result.message;

		if (!data.success) {
			showError(container, data.message);
			return;
		}

		showSuccess(container, data);
	} catch (error) {
		showError(container, "Unable to verify payment. Please try again.");
	}
}

function printReceipt() {
	const receiptEl = document.getElementById("receiptArea");

	if (!receiptEl) return;

	const receipt = receiptEl.innerHTML;

	const win = window.open("", "_blank");

	win.document.write(`
        <html>
        <head><title>Receipt</title></head>
        <body>${receipt}</body>
        </html>
    `);

	win.document.close();
	win.print();
}

function showSuccess(container, data) {
    container.innerHTML = `
    <div class="web-confirmation-page">

        <div class="web-success-banner">
            <i class="fa-solid fa-circle-check"></i>
            <h2>Booking Confirmed</h2>
            <p>Your reservation has been successfully processed</p>
        </div>

        <div id="receiptArea" class="web-receipt">

            <div class="web-receipt-header">

                <div class="web-hotel-branding">

                    <img
                        src="${window.HOTEL.logo || "/assets/rhohotel/logo.png"}"
                        alt="Hotel Logo"
                        onerror="this.src='/assets/rhohotel/logo.png'"
                    />

                    <div>
                        <h2>${window.HOTEL.name}</h2>
                        <p>${window.HOTEL.email}</p>
                        <p>${window.HOTEL.phone}</p>
                        <small>${window.HOTEL.address || ""}</small>
                    </div>

                </div>

            </div>

            <div class="web-receipt-body">

                <h3 class="web-receipt-title">
                    Reservation Receipt
                </h3>

                <!-- Reservation Details -->
                <div class="web-receipt-section">

                    <h4 class="web-section-title">
                        Reservation Details
                    </h4>

                    <div class="web-receipt-row">
                        <strong>Reservation Number</strong>
                        <span>${data.reservation || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Booking Status</strong>
                        <span>${data.reservation_status || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Payment Status</strong>
                        <span>${data.payment_status || "-"}</span>
                    </div>

                </div>

                <!-- Guest Information -->
                <div class="web-receipt-section">

                    <h4 class="web-section-title">
                        Guest Information
                    </h4>

                    <div class="web-receipt-row">
                        <strong>Guest Name</strong>
                        <span>${data.guest_name || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Email Address</strong>
                        <span>${data.guest_email || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Phone Number</strong>
                        <span>${data.guest_phone || "-"}</span>
                    </div>

                </div>

                <!-- Stay Details -->
                <div class="web-receipt-section">

                    <h4 class="web-section-title">
                        Stay Details
                    </h4>

                    <div class="web-receipt-row">
                        <strong>Check-in Date</strong>
                        <span>${data.check_in_date || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Check-out Date</strong>
                        <span>${data.check_out_date || "-"}</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Number of Nights</strong>
                        <span>${data.number_of_nights || 0}</span>
                    </div>

                </div>

                <!-- Room Reservation -->
                <div class="web-receipt-section">

                    <h4 class="web-section-title">
                        Room Reservation
                    </h4>

                    <div class="web-receipt-row">
                        <strong>Room Type</strong>
                       <span>
${data.room_type_summary
    ? Object.entries(data.room_type_summary)
        .map(([type, count]) => `
            <div>${count} × ${type}</div>
        `)
        .join("")
    : "-"}
</span>
                    </div>

                    <div class="web-receipt-row">
                        <strong>Rooms Reserved</strong>
                        <span>${data.number_of_rooms || 1}</span>
                    </div>

                </div>

                <!-- Payment Summary -->
                <div class="web-receipt-section">

                    <h4 class="web-section-title">
                        Payment Summary
                    </h4>

                    <div class="web-receipt-row">
                        <strong>Subtotal</strong>
                        <span>₦${Number(data.subtotal || 0).toLocaleString()}</span>
                    </div>

                    ${
                        Number(data.discount_amount || 0) > 0
                        ? `
                        <div class="web-receipt-row">
                            <strong>Discount</strong>
                            <span>₦${Number(data.discount_amount).toLocaleString()}</span>
                        </div>
                        `
                        : ""
                    }

                    <div class="web-receipt-row web-total-row">
                        <strong>Total Paid</strong>
                        <span>₦${Number(data.total_amount || 0).toLocaleString()}</span>
                    </div>

                </div>

                <div class="web-receipt-footer">
                    <p>Thank you for choosing ${window.HOTEL.name}.</p>
                    <small>Please present this receipt during check-in.</small>
                </div>

            </div>

        </div>

        <div class="web-actions">

            <button
                class="web-btn-outline"
                onclick="window.print()"
            >
                Print Receipt
            </button>

            <button
                class="web-btn-solid"
                onclick="window.location.href='/'"
            >
                Back Home
            </button>

        </div>

    </div>
    `;
}



function showError(container, message) {
	container.innerHTML = `
        <div class="card shadow-sm border-danger">
            <div class="card-body text-center">

                <i class="fa-solid fa-triangle-exclamation text-danger display-3"></i>

                <h2 class="mt-3">Payment Failed</h2>

                <p>${message}</p>

                <hr>

                <p>
                    Please contact the hotel for assistance:
                </p>

                <p>
                    📞 <strong>+234 XXX XXX XXXX</strong><br>
                    📧 <strong>support@yourhotel.com</strong>
                </p>

            </div>
        </div>
    `;
}

function printReceipt() {
	window.print();
}
