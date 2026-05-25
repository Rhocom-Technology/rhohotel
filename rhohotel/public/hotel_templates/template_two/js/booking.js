let selectedRooms = {};
let roomTypesData = {};
let searchData = null;
let bookingData = null;
let roomsNeeded = 1;

const bookingAmenityIcons = {
  TV: "fa-tv",
  Air: "fa-snowflake",
  Airconditioner: "fa-snowflake",
  Bed: "fa-bed",
  Shower: "fa-shower",
  WiFi: "fa-wifi",
  Coffee: "fa-mug-hot",
  Fridge: "fa-ice-cream",
  Safe: "fa-lock",
  Desk: "fa-table",
  Table: "fa-table",
  Bath: "fa-bath",
  Phone: "fa-phone",
};

function getAmenityIcon(itemName) {
  const value = String(itemName || "");

  for (const [key, icon] of Object.entries(bookingAmenityIcons)) {
    if (value.toUpperCase().includes(key.toUpperCase())) {
      return icon;
    }
  }

  return "fa-check-circle";
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function showBookingAlert(message, type = "info") {
  const alertBox = document.getElementById("roomAvailabilityAlert");

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

  alertBox.className = `web-inline-alert show`;
  alertBox.innerHTML = `
    <i class="fa-solid fa-${icon} me-2"></i>
    ${message}
  `;

  setTimeout(() => {
    alertBox.className = "web-inline-alert";
    alertBox.innerHTML = "";
  }, 6000);
}

function callFrappeMethod(method, args = {}) {
  return new Promise((resolve, reject) => {
    if (window.frappe && frappe.call) {
      frappe.call({
        method,
        args,
        callback: function (r) {
          resolve(r.message);
        },
        error: function (err) {
          reject(err);
        },
      });
      return;
    }

    fetch(`/api/method/${method}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(args),
    })
      .then((response) => response.json())
      .then((data) => resolve(data.message))
      .catch(reject);
  });
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

  const start = new Date(checkIn);
  const end = new Date(checkOut);
  const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

  if (diff <= 0) {
    output.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-2"></i>Invalid dates`;
    return 0;
  }

  output.innerHTML = `<i class="fa-solid fa-moon me-2"></i>${diff} night${diff > 1 ? "s" : ""}`;

  return diff;
}

async function searchAvailableRooms() {
  const checkIn = document.getElementById("roomCheckIn")?.value;
  const checkOut = document.getElementById("roomCheckOut")?.value;
  const adults = parseInt(document.getElementById("roomAdults")?.value || "1", 10);
  const children = parseInt(document.getElementById("roomChildren")?.value || "0", 10);
  const numRoomsInput = document.getElementById("numRooms");

  roomsNeeded = parseInt(numRoomsInput?.value || "1", 10);

  if (!checkIn || !checkOut) {
    showBookingAlert("Please select check-in and check-out dates.", "danger");
    return;
  }

  if (new Date(checkIn) >= new Date(checkOut)) {
    showBookingAlert("Check-out date must be after check-in date.", "danger");
    return;
  }

  const button = document.getElementById("checkAvailabilityBtn");
  const resultsContainer = document.getElementById("roomAvailabilityResults");

  if (button) {
    button.disabled = true;
    button.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Searching...`;
  }

  if (resultsContainer) {
    resultsContainer.innerHTML = `
      <div class="col-12 text-center py-5">
        <i class="fa-solid fa-spinner fa-spin me-2"></i>
        Searching available rooms...
      </div>
    `;
  }

  try {
    const response = await callFrappeMethod(
      "rhohotel.search_available_rooms.search_available_rooms",
      {
        check_in_date: checkIn,
        check_out_date: checkOut,
        num_rooms: roomsNeeded,
        adults,
        children,
      }
    );

    searchData = response;
    selectedRooms = {};
    roomTypesData = {};

    if (response?.warning_no_tariff) {
      showBookingAlert(response.warning_no_tariff, "warning");
    }

    if (response?.warning_guest_mismatch) {
      showBookingAlert(response.warning_guest_mismatch, "warning");
    }

    const availableRooms = response?.available_rooms || {};
    const totalRoomTypes = Object.keys(availableRooms).length;

    if (!totalRoomTypes) {
      displayNoAvailableRooms();
      showBookingAlert("No rooms available for your selected dates.", "danger");
      return;
    }

    displayAvailableRoomTypes(response);
    showBookingAlert(`Found ${totalRoomTypes} available room type(s).`, "success");
  } catch (error) {
    console.error(error);
    displayNoAvailableRooms();
    showBookingAlert("Could not search available rooms. Please try again.", "danger");
  } finally {
    if (button) {
      button.disabled = false;
      button.innerHTML = `<i class="fa-solid fa-search me-2"></i>Check Available Rooms`;
    }
  }
}

function displayNoAvailableRooms() {
  const container = document.getElementById("roomAvailabilityResults");

  if (!container) return;

  container.innerHTML = `
    <div class="col-12">
      <div class="text-center py-5">
        <h3>No room types currently available</h3>
        <p class="web-section-text">
          No room is available for the selected dates. Please try different dates or contact the hotel.
        </p>
        <a href="/hotel/contact" class="web-btn-ghost">Contact Hotel</a>
      </div>
    </div>
  `;
}

function displayAvailableRoomTypes(data) {
  const container = document.getElementById("roomAvailabilityResults");

  if (!container) return;

  container.innerHTML = "";

  const availableRooms = data.available_rooms || {};
  const nights = data.number_of_nights || calculateNights() || 1;

  Object.entries(availableRooms).forEach(([type, details]) => {
    if (!details.available_rooms || !details.available_rooms.length) return;

    roomTypesData[type] = details;

    const safeType = slugify(type);
    const images = details.images || [];
    const amenities = details.amenities || [];
    const firstRoom = details.available_rooms[0] || {};
    const imageUrl =
      images[0]?.image ||
      "/assets/rhohotel/hotel_templates/template_two/files/room-1.jpg";

    const amenitiesHTML = amenities.length
      ? amenities
          .slice(0, 4)
          .map((amenity) => {
            const label = amenity.item || amenity.amenity || amenity.amenity_name || "Amenity";
            return `<span><i class="fa-solid ${getAmenityIcon(label)} me-1"></i>${label}</span>`;
          })
          .join("")
      : `
        <span>Comfort Stay</span>
        <span>Room Service</span>
        <span>Guest Support</span>
      `;

    const pricePerNight = Number(details.price_per_night || 0);
    const totalPrice = Number(details.total_price || pricePerNight * nights || 0);

    const card = `
      <div class="col-lg-4 col-md-6" id="room-card-${safeType}">
        <div class="web-availability-card">
          <img src="${imageUrl}" alt="${type}" onerror="this.src='/assets/rhohotel/hotel_templates/template_two/files/room-1.jpg'">

          <div class="web-availability-card-body">
            <div class="web-kicker">
              ${details.available_count || details.available_rooms.length} room(s) available
            </div>

            <h4>${type}</h4>

            <div class="web-price-line">
              ${
                pricePerNight
                  ? `From ₦${pricePerNight.toLocaleString()} / night`
                  : "Rate available on request"
              }
            </div>

            <p class="web-form-help">
              ${details.description || "A comfortable room option for a relaxing hotel stay."}
            </p>

            <div class="web-pill-list">
              ${amenitiesHTML}
            </div>

            <div class="web-summary-box mb-3">
              <div class="web-summary-row">
                <span class="web-summary-label">Capacity</span>
                <span class="web-summary-value">${firstRoom.capacity || "-"} Adult(s)</span>
              </div>

              <div class="web-summary-row">
                <span class="web-summary-label">Bed(s)</span>
                <span class="web-summary-value">${firstRoom.beds || "-"}</span>
              </div>

              <div class="web-summary-row">
                <span class="web-summary-label">Total for ${nights} night${nights > 1 ? "s" : ""}</span>
                <span class="web-summary-value">₦${totalPrice.toLocaleString()}</span>
              </div>
            </div>

            <div class="d-flex align-items-center justify-content-between gap-2 mb-3">
              <button type="button" class="web-btn-ghost px-3" data-room-minus="${type}">-</button>
              <strong id="qty-${safeType}">0</strong>
              <button type="button" class="web-btn-solid px-3" data-room-plus="${type}">+</button>
            </div>

            <button type="button" class="web-btn-primary w-100" data-room-select="${type}">
              Select Room
            </button>
          </div>
        </div>
      </div>
    `;

    container.insertAdjacentHTML("beforeend", card);
  });

  if (!container.innerHTML.trim()) {
    displayNoAvailableRooms();
    return;
  }

  bindRoomSelectionButtons();
  updateRoomSelectionSummary();
}

function bindRoomSelectionButtons() {
  document.querySelectorAll("[data-room-plus]").forEach((button) => {
    button.addEventListener("click", function () {
      updateQuantity(this.getAttribute("data-room-plus"), 1);
    });
  });

  document.querySelectorAll("[data-room-minus]").forEach((button) => {
    button.addEventListener("click", function () {
      updateQuantity(this.getAttribute("data-room-minus"), -1);
    });
  });

  document.querySelectorAll("[data-room-select]").forEach((button) => {
    button.addEventListener("click", function () {
      updateQuantity(this.getAttribute("data-room-select"), 1);
    });
  });
}

function updateQuantity(type, change) {
  const current = selectedRooms[type] || 0;
  const max = roomTypesData[type]?.available_count || roomTypesData[type]?.available_rooms?.length || 0;
  const roomsSelected = Object.values(selectedRooms).reduce((sum, qty) => sum + qty, 0);

  let newQty = current + change;

  if (newQty < 0) newQty = 0;

  if (newQty > max) {
    showBookingAlert(`Only ${max} ${type} room(s) available.`, "warning");
    return;
  }

  const totalIfAdded = roomsSelected - current + newQty;

  if (totalIfAdded > roomsNeeded) {
    showBookingAlert(`You only need ${roomsNeeded} room(s).`, "warning");
    return;
  }

  if (newQty === 0) {
    delete selectedRooms[type];
  } else {
    selectedRooms[type] = newQty;
  }

  const safeType = slugify(type);
  const qtyDisplay = document.getElementById(`qty-${safeType}`);
  const card = document.getElementById(`room-card-${safeType}`);

  if (qtyDisplay) qtyDisplay.textContent = newQty;

  if (card) {
    card.classList.toggle("selected", newQty > 0);
  }

  updateRoomSelectionSummary();
}

function updateRoomSelectionSummary() {
  const roomsSelected = Object.values(selectedRooms).reduce((sum, qty) => sum + qty, 0);
  const continueBtn = document.getElementById("continueRoomBookingBtn");

  let total = 0;
  let breakdown = "";

  Object.entries(selectedRooms).forEach(([type, qty]) => {
    const roomType = roomTypesData[type];
    const subtotal = Number(roomType?.total_price || 0) * qty;

    total += subtotal;
    breakdown += `${type} (${qty}) `;
  });

  const summaryRooms = document.getElementById("summaryRooms");
  const summaryBreakdown = document.getElementById("summaryBreakdown");
  const summaryCheckIn = document.getElementById("summaryCheckIn");
  const summaryCheckOut = document.getElementById("summaryCheckOut");
  const summaryNights = document.getElementById("summaryNights");
  const summaryTotal = document.getElementById("summaryTotal");

  if (summaryRooms) summaryRooms.textContent = `${roomsSelected} room(s)`;
  if (summaryBreakdown) summaryBreakdown.textContent = breakdown || "-";
  if (summaryCheckIn) summaryCheckIn.textContent = searchData?.check_in_date || "-";
  if (summaryCheckOut) summaryCheckOut.textContent = searchData?.check_out_date || "-";
  if (summaryNights) summaryNights.textContent = searchData?.number_of_nights || calculateNights() || "-";
  if (summaryTotal) summaryTotal.textContent = total.toLocaleString();

  if (continueBtn) {
    continueBtn.disabled = roomsSelected !== roomsNeeded;
  }
}

function continueToGuestDetails() {
  const roomsSelected = Object.values(selectedRooms).reduce((sum, qty) => sum + qty, 0);

  if (!searchData) {
    showBookingAlert("Please search available rooms first.", "danger");
    return;
  }

  if (roomsSelected !== roomsNeeded) {
    showBookingAlert(`Please select exactly ${roomsNeeded} room(s).`, "danger");
    return;
  }

  document.getElementById("roomStepOne")?.classList.remove("active");
  document.getElementById("roomStepTwo")?.classList.add("active");
  window.scrollTo(0, 0);
}

function backToRoomSelection() {
  document.getElementById("roomStepTwo")?.classList.remove("active");
  document.getElementById("roomStepOne")?.classList.add("active");
  window.scrollTo(0, 0);
}

async function handleRoomBookingSubmit(event) {
  event.preventDefault();

  const guestName = document.getElementById("roomGuestName")?.value;
  const guestEmail = document.getElementById("roomGuestEmail")?.value;
  const guestPhone = document.getElementById("roomGuestPhone")?.value;
  const paymentPreference = document.getElementById("roomPaymentMethod")?.value || "Pay online";

  if (!guestName || !guestEmail) {
    showBookingAlert("Please enter guest name and email address.", "danger");
    return;
  }

  const roomsSelected = Object.values(selectedRooms).reduce((sum, qty) => sum + qty, 0);

  if (roomsSelected !== roomsNeeded) {
    showBookingAlert(`Please select exactly ${roomsNeeded} room(s).`, "danger");
    return;
  }

  const rooms = [];
  let total = 0;

  Object.entries(selectedRooms).forEach(([type, qty]) => {
    const typeData = roomTypesData[type];

    for (let i = 0; i < qty && i < typeData.available_rooms.length; i++) {
      rooms.push(typeData.available_rooms[i].room_number);
    }

    total += Number(typeData.total_price || 0) * qty;
  });

  const submitBtn = event.target.querySelector('button[type="submit"]');

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Creating booking...`;
  }

  try {
    const response = await callFrappeMethod("rhohotel.hotel_booking.create_booking", {
      from_date: searchData.check_in_date,
      to_date: searchData.check_out_date,
      rooms: JSON.stringify(rooms),
      customer_name: guestName,
      customer_email: guestEmail,
      customer_phone: guestPhone,
    });

    if (!response?.success) {
      showBookingAlert(response?.message || "Could not create booking.", "danger");
      return;
    }

    bookingData = response;

    showBookingAlert("Booking created. Rooms are temporarily held.", "success");

    if (paymentPreference === "Pay online") {
      await createPaymentLinkAndRedirect();
    } else {
      showBookingAlert(
        `Booking created successfully. Booking Number: ${response.booking_number}`,
        "success"
      );
    }
  } catch (error) {
    console.error(error);
    showBookingAlert("Error creating booking. Please try again.", "danger");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `Book and Pay`;
    }
  }
}

async function createPaymentLinkAndRedirect() {
  if (!bookingData?.booking_number) {
    showBookingAlert("Booking number missing. Cannot proceed to payment.", "danger");
    return;
  }

  showBookingAlert("Preparing payment link...", "info");

  try {
    const response = await callFrappeMethod("rhohotel.hotel_booking.create_payment_link", {
      booking_number: bookingData.booking_number,
    });

    if (response?.success && response?.payment_url) {
      showBookingAlert("Redirecting to Paystack...", "info");

      setTimeout(() => {
        window.location.href = response.payment_url;
      }, 1200);
    } else {
      showBookingAlert(response?.message || "Could not create payment link.", "danger");
    }
  } catch (error) {
    console.error(error);
    showBookingAlert("Payment link error. Please contact the hotel.", "danger");
  }
}

function initBookingPage() {
  const checkIn = document.getElementById("roomCheckIn");
  const checkOut = document.getElementById("roomCheckOut");
  const searchBtn = document.getElementById("checkAvailabilityBtn");
  const continueBtn = document.getElementById("continueRoomBookingBtn");
  const backBtn = document.getElementById("backToRoomSearchBtn");
  const bookingForm = document.getElementById("roomBookingForm");

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

  searchBtn?.addEventListener("click", searchAvailableRooms);
  continueBtn?.addEventListener("click", continueToGuestDetails);
  backBtn?.addEventListener("click", backToRoomSelection);
  bookingForm?.addEventListener("submit", handleRoomBookingSubmit);

  if (continueBtn) {
    continueBtn.disabled = true;
  }
}

document.addEventListener("DOMContentLoaded", initBookingPage);