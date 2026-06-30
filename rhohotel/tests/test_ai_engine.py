import sys
import types
import unittest


if "frappe" not in sys.modules:
	frappe_stub = types.ModuleType("frappe")
	frappe_stub._ = lambda text: text
	frappe_stub.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
	frappe_stub.session = types.SimpleNamespace(user="test@example.com")
	frappe_stub.get_roles = lambda user=None: []
	frappe_stub.get_all = lambda *args, **kwargs: []
	frappe_stub.log_error = lambda *args, **kwargs: None
	frappe_stub.db = types.SimpleNamespace(get_single_value=lambda *args, **kwargs: None)
	frappe_stub.cache = lambda: types.SimpleNamespace(get_value=lambda *args, **kwargs: 0, set_value=lambda *args, **kwargs: None)
	sys.modules["frappe"] = frappe_stub

if "frappe.utils" not in sys.modules:
	utils_stub = types.ModuleType("frappe.utils")
	utils_stub.today = lambda: "2026-06-30"
	utils_stub.getdate = lambda value=None: value
	utils_stub.flt = lambda value=0, *_, **__: float(value or 0)
	sys.modules["frappe.utils"] = utils_stub

from rhohotel.rhocom_hotel.api import ai_engine


class TestAIInsightPrompts(unittest.TestCase):
	def test_owner_finance_dashboard_summary_prompt_is_registered(self):
		prompt = ai_engine._INSIGHT_PROMPTS.get("owner_finance_dashboard_summary")

		self.assertIsInstance(prompt, str)
		self.assertIn("Owner Finance Dashboard", prompt)
		self.assertIn("{context}", prompt)


if __name__ == "__main__":
	unittest.main()
