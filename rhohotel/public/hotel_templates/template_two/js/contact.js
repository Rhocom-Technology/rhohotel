function showContactAlert(message, type = "success") {
  let alertBox = document.getElementById("contactFormAlert");

  if (!alertBox) {
    const form = document.getElementById("contactForm");

    alertBox = document.createElement("div");
    alertBox.id = "contactFormAlert";
    alertBox.className = "web-inline-alert mt-3";

    form.appendChild(alertBox);
  }

  alertBox.className = "web-inline-alert show mt-3";

  if (type === "success") {
    alertBox.style.background = "var(--web-success-soft)";
    alertBox.style.color = "var(--web-success-dark)";
  } else {
    alertBox.style.background = "var(--web-danger-soft)";
    alertBox.style.color = "var(--web-danger-dark)";
  }

  alertBox.innerHTML = message;
}

function callContactMethod(args) {
  return new Promise((resolve, reject) => {
    const method = "rhohotel.rhocom_hotel.api.website.submit_contact_message";

    if (window.frappe && frappe.call) {
      frappe.call({
        method: method,
        args: args,
        callback: function (r) {
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

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contactForm");

  if (!form) return;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);

    const args = {
      full_name: formData.get("full_name"),
      email: formData.get("email"),
      phone: formData.get("phone"),
      enquiry_type: formData.get("enquiry_type"),
      message: formData.get("message"),
    };

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin me-2"></i>Sending...';
    }

    try {
      const response = await callContactMethod(args);

      if (response && response.success) {
        showContactAlert(
          "Message sent successfully. The hotel team will get back to you.",
          "success"
        );
        form.reset();
      } else {
        showContactAlert(
          response?.message || "Unable to send message. Please try again.",
          "danger"
        );
      }
    } catch (error) {
      console.error(error);

      let errorMessage = "Unable to send message. Please try again.";

      if (error?._server_messages) {
        try {
          const serverMessages = JSON.parse(error._server_messages);
          const firstMessage = JSON.parse(serverMessages[0]);
          errorMessage = firstMessage.message || errorMessage;
        } catch (e) {
          errorMessage = "Unable to send message. Please try again.";
        }
      }

      if (error?.exception && error.exception.includes("CSRFTokenError")) {
        errorMessage =
          "Security token error. Please refresh the page and try again.";
      }

      showContactAlert(errorMessage, "danger");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = "Send Message";
      }
    }
  });
});