import re

import frappe
from frappe import _
from frappe.utils import cstr


PHONE_ALLOWED_RE = re.compile(r"^\+?[0-9][0-9\s().-]*$")


def validate_phone_number(value, label=None, required=False):
	"""Validate a practical international phone number.

	Allows a leading plus sign and common separators, then enforces the E.164
	digit length range so obviously invalid values like "123" are rejected.
	"""
	label = label or _("Phone number")
	value = cstr(value).strip()

	if not value:
		if required:
			frappe.throw(_("{0} is required.").format(label))
		return value

	digits = re.sub(r"\D", "", value)
	if not PHONE_ALLOWED_RE.match(value) or len(digits) < 7 or len(digits) > 15:
		frappe.throw(
			_("{0} must be a valid phone number with 7 to 15 digits.").format(label)
		)

	return value
