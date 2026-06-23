"""
ai_engine.py — AI assistant engine for hotel operations.

Public whitelisted endpoints:
- get_ai_config()       Returns non-sensitive provider info for the frontend UI.
- chat()                Main chatbot endpoint with role-gated tool calling.
- generate_insight()    Page-level AI insight generation (context passed directly, no tool calling).

Security:
- Write-intent and prompt-injection patterns are blocked before any LLM call.
- Tool access is role-gated; lower-privilege roles cannot call financial/sensitive tools.
- All tool functions use Frappe ORM without ignore_permissions.
- The OpenAI API key is never returned to the frontend under any role.
"""

import frappe
import json
import re
import time

import requests as _http

from frappe.utils import today
from rhohotel.rhocom_hotel.api import ai_tools


# ── Safety layer ──────────────────────────────────────────────────────────────

_BLOCKED = re.compile(
	r"""
	\bDELETE\s+FROM\b
	|\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|TRIGGER|PROCEDURE|COLUMN)\b
	|\bTRUNCATE\b
	|\bUPDATE\s+\S+\s+SET\b
	|\bINSERT\s+INTO\b
	|\bALTER\s+(TABLE|DATABASE|SCHEMA)\b
	|\bCREATE\s+(TABLE|DATABASE|INDEX|SCHEMA)\b
	|\bEXEC(?:UTE)?\s*\(
	|frappe\.db\.(set_value|delete|sql_ddl|drop|rename_table|commit)
	|frappe\.(delete_doc|rename_doc)
	|ignore_permissions\s*=\s*True
	|IGNORE\s+PREVIOUS\s+INSTRUCTIONS?
	|YOU\s+ARE\s+NOW\s+(A|AN)\s
	|ACT\s+AS\s+(A|AN)\s
	|DISREGARD\s+(ALL|PREVIOUS|YOUR)
	|FORGET\s+(ALL|EVERYTHING|YOUR)
	|NEW\s+PERSONA
	|JAILBREAK
	|DAN\s+MODE
	""",
	re.IGNORECASE | re.VERBOSE,
)


def _is_safe(text: str) -> bool:
	return not _BLOCKED.search(text or "")


# ── Tool registry ──────────────────────────────────────────────────────────────

_ALL_TOOLS = {
	"get_occupancy_summary": {
		"fn": ai_tools.get_occupancy_summary,
		"description": "Get current hotel room occupancy counts (occupied, vacant, maintenance) and occupancy percentage.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_revenue_summary": {
		"fn": ai_tools.get_revenue_summary,
		"description": "Get hotel revenue summary for a date: total invoiced and total payments collected.",
		"parameters": {
			"type": "object",
			"properties": {
				"date": {"type": "string", "description": "Date in YYYY-MM-DD format. Defaults to today."}
			},
			"required": [],
		},
	},
	"get_inhouse_guests": {
		"fn": ai_tools.get_inhouse_guests,
		"description": "List guests currently checked in with room number, check-in/out dates, and outstanding balances.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max guests to return. Default 20."}
			},
			"required": [],
		},
	},
	"get_reservations": {
		"fn": ai_tools.get_reservations,
		"description": "List hotel reservations filtered by status (Hold, Confirmed, Checked In, Cancelled, No Show) and/or date.",
		"parameters": {
			"type": "object",
			"properties": {
				"status": {"type": "string", "description": "Reservation status filter."},
				"date": {"type": "string", "description": "Check-in date filter in YYYY-MM-DD."},
				"limit": {"type": "integer", "description": "Max results."},
			},
			"required": [],
		},
	},
	"get_overdue_checkouts": {
		"fn": ai_tools.get_overdue_checkouts,
		"description": "List guests past their expected checkout time who have not yet checked out.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_guest_profile": {
		"fn": ai_tools.get_guest_profile,
		"description": "Retrieve detailed profile for a specific hotel guest by their guest document ID.",
		"parameters": {
			"type": "object",
			"properties": {
				"guest_name": {"type": "string", "description": "The Hotel Guest document name/ID."}
			},
			"required": ["guest_name"],
		},
	},
	"get_outstanding_invoices": {
		"fn": ai_tools.get_outstanding_invoices,
		"description": "List unpaid or overdue sales invoices with amounts and due dates.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max invoices to return."}
			},
			"required": [],
		},
	},
	"get_housekeeping_summary": {
		"fn": ai_tools.get_housekeeping_summary,
		"description": "Get housekeeping task counts by status (Pending, Assigned, In Progress, Completed) and completion rate.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_maintenance_summary": {
		"fn": ai_tools.get_maintenance_summary,
		"description": "Get maintenance task counts: open, urgent, completed today, and open requests.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_pos_summary": {
		"fn": ai_tools.get_pos_summary,
		"description": "Get POS gross sales and invoice count for a specific date.",
		"parameters": {
			"type": "object",
			"properties": {
				"date": {"type": "string", "description": "Date in YYYY-MM-DD format. Defaults to today."}
			},
			"required": [],
		},
	},
	"get_payment_summary": {
		"fn": ai_tools.get_payment_summary,
		"description": "Get payment collection breakdown by payment method for a specific date.",
		"parameters": {
			"type": "object",
			"properties": {
				"date": {"type": "string", "description": "Date in YYYY-MM-DD format. Defaults to today."}
			},
			"required": [],
		},
	},
	"search_guests": {
		"fn": ai_tools.search_guests,
		"description": "Search for hotel guests by name, phone number, or email address.",
		"parameters": {
			"type": "object",
			"properties": {
				"query": {"type": "string", "description": "Search term (min 2 chars)."},
				"limit": {"type": "integer", "description": "Max results."},
			},
			"required": ["query"],
		},
	},
	"get_guest_payment_total": {
		"fn": ai_tools.get_guest_payment_total,
		"description": "Get the total amount a specific guest has paid so far (from submitted Payment Entries and POS paid amounts).",
		"parameters": {
			"type": "object",
			"properties": {
				"guest_query": {"type": "string", "description": "Guest name/ID/customer name to match."},
				"include_pos": {
					"type": "boolean",
					"description": "Whether to include submitted POS invoice paid amounts. Defaults to true.",
				},
			},
			"required": ["guest_query"],
		},
	},
	"get_billing_dashboard_summary": {
		"fn": ai_tools.get_billing_dashboard_summary,
		"description": "Get a hotel-wide billing snapshot: total outstanding invoices, overdue balance, and unallocated payments.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_corporate_overdue_accounts": {
		"fn": ai_tools.get_corporate_overdue_accounts,
		"description": "List corporate customers with the highest overdue invoice balances, ranked by amount.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max accounts to return. Default 10."}
			},
			"required": [],
		},
	},
	"get_today_arrivals": {
		"fn": ai_tools.get_today_arrivals,
		"description": "List hotel reservations expected to arrive today.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max results. Default 20."}
			},
			"required": [],
		},
	},
	"get_today_departures": {
		"fn": ai_tools.get_today_departures,
		"description": "List hotel reservations expected to depart today.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max results. Default 20."}
			},
			"required": [],
		},
	},
	"get_dirty_vacant_rooms": {
		"fn": ai_tools.get_dirty_vacant_rooms,
		"description": "List vacant rooms with an open housekeeping task — rooms currently blocking revenue.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_maintenance_blocked_rooms": {
		"fn": ai_tools.get_maintenance_blocked_rooms,
		"description": "List rooms with occupancy status Maintenance — currently out of service.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_hall_events_today": {
		"fn": ai_tools.get_hall_events_today,
		"description": "List hall bookings that are active or starting today.",
		"parameters": {
			"type": "object",
			"properties": {
				"limit": {"type": "integer", "description": "Max events to return. Default 10."}
			},
			"required": [],
		},
	},
	"get_shift_coverage_summary": {
		"fn": ai_tools.get_shift_coverage_summary,
		"description": "Get the count of active shift assignments for today, grouped by department.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
	"get_vip_guests": {
		"fn": ai_tools.get_vip_guests,
		"description": "List VIP and Gold loyalty-tier guests currently in-house, including who is checking out today. Use this whenever the user asks about VIP, Gold, Platinum, or premium guests.",
		"parameters": {"type": "object", "properties": {}, "required": []},
	},
}

# Role → allowed tool names (cascading: higher roles inherit all lower-role tools)
_ROLE_TOOLS = {
	"System Manager": list(_ALL_TOOLS),
	"Hotel Manager": list(_ALL_TOOLS),
	"Front Desk Manager": [
		"get_occupancy_summary", "get_revenue_summary", "get_inhouse_guests",
		"get_reservations", "get_overdue_checkouts", "get_guest_profile",
		"get_outstanding_invoices", "get_housekeeping_summary",
		"get_maintenance_summary", "get_pos_summary", "get_payment_summary",
		"search_guests", "get_guest_payment_total",
		"get_billing_dashboard_summary", "get_corporate_overdue_accounts",
		"get_today_arrivals", "get_today_departures",
		"get_dirty_vacant_rooms", "get_maintenance_blocked_rooms",
		"get_hall_events_today", "get_shift_coverage_summary",
		"get_vip_guests",
	],
	"Hotel Receptionist": [
		"get_occupancy_summary", "get_inhouse_guests", "get_reservations",
		"get_overdue_checkouts", "get_guest_profile", "search_guests", "get_guest_payment_total",
		"get_today_arrivals", "get_today_departures", "get_dirty_vacant_rooms",
		"get_hall_events_today", "get_vip_guests",
	],
	"Housekeeping Supervisor": [
		"get_occupancy_summary", "get_housekeeping_summary", "get_dirty_vacant_rooms",
	],
	"POS User": [
		"get_pos_summary", "get_payment_summary", "get_occupancy_summary",
	],
}
_DEFAULT_TOOLS = ["get_occupancy_summary"]


def _get_allowed_tools(roles: list) -> dict:
	allowed = set(_DEFAULT_TOOLS)
	for role in roles:
		if role in _ROLE_TOOLS:
			allowed.update(_ROLE_TOOLS[role])
	return {k: v for k, v in _ALL_TOOLS.items() if k in allowed}


def _build_tools_schema(allowed_tools: dict) -> list:
	return [
		{
			"type": "function",
			"function": {
				"name": name,
				"description": defn["description"],
				"parameters": defn["parameters"],
			},
		}
		for name, defn in allowed_tools.items()
	]


def _execute_tool(name: str, args: dict, allowed_tools: dict):
	if name not in allowed_tools:
		return {"error": f"Tool '{name}' is not available for your role."}
	try:
		return allowed_tools[name]["fn"](**(args or {})) or {}
	except TypeError as e:
		frappe.log_error(f"AI tool call {name}({args}): {e}", "AI Tool Error")
		return {"error": f"Invalid arguments for '{name}'."}
	except Exception as e:
		frappe.log_error(f"AI tool runtime {name}: {e}", "AI Tool Error")
		return {"error": str(e)}


# ── Settings ───────────────────────────────────────────────────────────────────

def _get_settings() -> dict:
	"""Read AI Settings using Frappe's document cache (1 query per request instead of 7)."""
	from frappe.utils.password import get_decrypted_password

	doc = frappe.get_cached_doc("AI Settings")
	provider = doc.provider or "Ollama"
	enabled = bool(doc.enabled)
	temperature = float(doc.temperature or 0.3)
	max_tokens = int(doc.max_tokens or 600)
	ollama_base_url = (doc.ollama_base_url or "http://localhost:11434").rstrip("/")
	ollama_model = doc.ollama_model or "llama3.1:8b"
	openai_model = doc.openai_model or "gpt-4o-mini"

	openai_api_key = ""
	if provider == "OpenAI":
		try:
			openai_api_key = (
				get_decrypted_password("AI Settings", "AI Settings", "openai_api_key", raise_exception=False)
				or ""
			)
		except Exception:
			pass

	return {
		"provider": provider,
		"enabled": enabled,
		"temperature": temperature,
		"max_tokens": max_tokens,
		"ollama_base_url": ollama_base_url,
		"ollama_model": ollama_model,
		"openai_model": openai_model,
		"openai_api_key": openai_api_key,
		"model": ollama_model if provider == "Ollama" else openai_model,
	}


# ── Provider calls ─────────────────────────────────────────────────────────────

def _call_ollama(messages: list, tools, settings: dict) -> dict:
	payload = {
		"model": settings["ollama_model"],
		"messages": messages,
		"stream": False,
		"options": {"temperature": settings["temperature"]},
	}
	if tools:
		payload["tools"] = tools
	resp = _http.post(f"{settings['ollama_base_url']}/api/chat", json=payload, timeout=60)
	resp.raise_for_status()
	return resp.json()


def _call_openai(messages: list, tools, settings: dict):
	try:
		import openai
	except ImportError:
		frappe.throw("OpenAI library not installed. Run: bench pip install openai")

	client = openai.OpenAI(api_key=settings["openai_api_key"], timeout=60.0)
	kwargs = {
		"model": settings["openai_model"],
		"messages": messages,
		"temperature": settings["temperature"],
		"max_tokens": settings["max_tokens"],
	}
	if tools:
		kwargs["tools"] = tools
		kwargs["tool_choice"] = "auto"
	return client.chat.completions.create(**kwargs)


# ── Tool-calling loop ──────────────────────────────────────────────────────────

_MAX_ROUNDS = 5


def _run_loop(messages: list, allowed_tools: dict, tools_schema: list, settings: dict) -> str:
	provider = settings["provider"]

	for _ in range(_MAX_ROUNDS):
		if provider == "Ollama":
			raw = _call_ollama(messages, tools_schema or None, settings)
			msg = raw.get("message", {})
			tool_calls = msg.get("tool_calls") or []
			content = (msg.get("content") or "").strip()

			if not tool_calls:
				return content

			messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
			for tc in tool_calls:
				fn = tc.get("function", {})
				result = _execute_tool(fn.get("name", ""), fn.get("arguments") or {}, allowed_tools)
				messages.append({"role": "tool", "content": json.dumps(result, default=str)})

		else:  # OpenAI
			raw = _call_openai(messages, tools_schema or None, settings)
			choice = raw.choices[0]
			msg = choice.message
			tool_calls = msg.tool_calls or []
			content = (msg.content or "").strip()

			if choice.finish_reason != "tool_calls" or not tool_calls:
				return content

			messages.append({
				"role": "assistant",
				"content": content or None,
				"tool_calls": [
					{
						"id": tc.id,
						"type": "function",
						"function": {"name": tc.function.name, "arguments": tc.function.arguments},
					}
					for tc in tool_calls
				],
			})
			for tc in tool_calls:
				try:
					args = json.loads(tc.function.arguments or "{}")
				except json.JSONDecodeError:
					args = {}
				result = _execute_tool(tc.function.name, args, allowed_tools)
				messages.append({
					"role": "tool",
					"tool_call_id": tc.id,
					"content": json.dumps(result, default=str),
				})

	return "I was unable to complete the request after multiple attempts. Please try rephrasing your question."


def _call_simple(messages: list, settings: dict) -> str:
	"""Single LLM call without tool calling (used by generate_insight)."""
	if settings["provider"] == "Ollama":
		raw = _call_ollama(messages, None, settings)
		return (raw.get("message", {}).get("content") or "").strip()
	else:
		raw = _call_openai(messages, None, settings)
		return (raw.choices[0].message.content or "").strip()


# ── Public module aliases (stable API for cross-module use) ────────────────────
get_settings = _get_settings
call_simple = _call_simple
is_safe = _is_safe


# ── System prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(user: str, roles: list, allowed_tools: dict) -> str:
	role_label = next(
		(r for r in ["System Manager", "Hotel Manager", "Front Desk Manager",
		             "Hotel Receptionist", "Housekeeping Supervisor", "POS User"]
		 if r in roles),
		"Staff",
	)
	tool_lines = "\n".join(
		f"- {name}: {defn['description']}" for name, defn in allowed_tools.items()
	)
	return (
		f"You are the Hotel AI Assistant — a professional, concise assistant for hotel operations staff.\n\n"
		f"Current User: {user}\n"
		f"Access Level: {role_label}\n"
		f"Today's Date: {today()}\n\n"
		f"Available Tools (ONLY call these):\n{tool_lines}\n\n"
		f"RULES:\n"
		f"1. Only answer questions about hotel operations: rooms, guests, reservations, billing, "
		f"housekeeping, maintenance, POS, and related topics.\n"
		f"2. Politely decline unrelated questions and redirect to hotel topics.\n"
		f"3. Use tools to retrieve real-time data — never fabricate numbers or guest details.\n"
		f"4. Be concise and professional. Use \u20a6 for Nigerian Naira amounts.\n"
		f"5. If a tool returns an error, acknowledge it clearly.\n"
		f"6. Never attempt to modify, delete, or update any data."
	)


# ── Insight prompt templates ───────────────────────────────────────────────────

_INSIGHT_PROMPTS = {
	"room_view_briefing": (
		"You are a hotel front desk AI. Based on this hotel status data, write a concise 2-3 sentence "
		"operational briefing for the front desk team. Be specific with numbers. "
		"Lead with overdue checkouts or urgent issues first. "
		"Then mention any VIP, Gold, or Platinum guests by name — both in-house and arriving — "
		"and note their room number and tier. If there are no VIP guests, skip that.\n\n"
		"Hotel Status:\n{context}\n\nBriefing:"
	),
	"night_audit_summary": (
		"You are a hotel night auditor AI. Based on this audit data, write a professional 3-4 sentence "
		"narrative summary for the end-of-day report. Cover revenue performance, occupancy, and flag "
		"critical items. Use \u20a6 for currency.\n\n"
		"Audit Data:\n{context}\n\nNarrative:"
	),
	"guest_profile_summary": (
		"You are a hotel guest intelligence AI. Based on this guest profile, write a 2-3 sentence "
		"professional insight covering: their value to the hotel, loyalty/visit patterns, and one "
		"personalised recommendation for the front desk team.\n\n"
		"Guest Profile:\n{context}\n\nInsight:"
	),
	"billing_risk_summary": (
		"You are a hotel finance AI. Based on this billing data, write a 2-3 sentence actionable "
		"collection priority summary for the billing team. Flag the most urgent risk, name amounts "
		"precisely, and end with one specific next action. Use \u20a6 for currency.\n\n"
		"Billing Data:\n{context}\n\nSummary:"
	),
	"corporate_bill_summary": (
		"You are a hotel finance AI. Based on this corporate invoice, write a 2-sentence status "
		"summary: state the payment position, flag any overdue risk, and recommend the single most "
		"important next step. Use \u20a6 for currency.\n\n"
		"Invoice Data:\n{context}\n\nSummary:"
	),
	"housekeeping_dispatch_summary": (
		"You are a hotel housekeeping AI. Based on these task counts and room status figures, write a "
		"2-3 sentence dispatch priority plan for the housekeeping supervisor. "
		"Lead with revenue-blocking dirty-vacant rooms, then arrivals needing a clean, then in-progress tasks.\n\n"
		"Housekeeping Status:\n{context}\n\nDispatch Plan:"
	),
	"maintenance_triage_summary": (
		"You are a hotel maintenance AI. Based on these figures, write a 2-sentence triage summary: "
		"rank the most urgent items, flag any revenue-blocking room faults, and suggest the first action. "
		"Be specific with numbers.\n\n"
		"Maintenance Data:\n{context}\n\nTriage:"
	),
	"daily_manager_briefing": (
		"You are a hotel operations AI. Based on this end-of-day snapshot, write a 3-4 sentence "
		"shift handover briefing for the duty manager. Cover: (1) occupancy and overdue checkouts, "
		"(2) financial watchpoints, (3) housekeeping and maintenance risks, "
		"(4) one priority action for the next shift. Use \u20a6 for currency. Be specific.\n\n"
		"Operations Snapshot:\n{context}\n\nBriefing:"
	),
	"reservation_quality_review": (
		"You are a hotel reservations AI. Review this reservation for completeness and risk. "
		"Write 2-3 sentences covering missing or unusual details, billing concerns, and one "
		"recommended action before check-in. If everything looks correct, say so clearly.\n\n"
		"Reservation:\n{context}\n\nReview:"
	),
	"pos_shift_close_summary": (
		"You are a hotel POS AI. Based on this shift-close data, write a 2-sentence summary: "
		"explain any cash/card variance, flag unusual patterns, and state whether the close appears "
		"normal or needs follow-up. Use \u20a6 for currency.\n\n"
		"POS Shift Data:\n{context}\n\nSummary:"
	),
	"hall_event_summary": (
		"You are a hotel events AI. Based on this hall booking or event dashboard data, write a "
		"2-3 sentence operational summary: highlight today's active events, revenue and payment status, "
		"and one item that needs attention. Use \u20a6 for currency.\n\n"
		"Event Data:\n{context}\n\nSummary:"
	),
	"report_narrative": (
		"You are a hotel reporting AI. Based on this report data, write a 2-3 sentence management "
		"narrative: describe what changed, what matters most, and one forward-looking action. "
		"Use \u20a6 for currency. Be specific with numbers.\n\n"
		"Report Data:\n{context}\n\nNarrative:"
	),
}


# ── Rate limiting ──────────────────────────────────────────────────────────────

_CHAT_RATE_LIMIT = 20  # max chat requests per user per minute


def _check_rate_limit(user: str) -> bool:
	"""Returns True if the request is allowed; False if the user exceeded 20 req/min."""
	key = f"ai_chat_rate:{user}:{int(time.time()) // 60}"
	count = frappe.cache().get_value(key) or 0
	if count >= _CHAT_RATE_LIMIT:
		return False
	frappe.cache().set_value(key, count + 1, expires_in_sec=120)
	return True


# ── Public API methods ─────────────────────────────────────────────────────────

@frappe.whitelist()
def get_ai_config():
	"""Return non-sensitive AI configuration for the frontend UI. Safe for all logged-in users."""
	try:
		provider = frappe.db.get_single_value("AI Settings", "provider") or "Ollama"
		enabled = bool(frappe.db.get_single_value("AI Settings", "enabled"))
		if provider == "Ollama":
			model = frappe.db.get_single_value("AI Settings", "ollama_model") or "llama3.1:8b"
		else:
			model = frappe.db.get_single_value("AI Settings", "openai_model") or "gpt-4o-mini"
		return {"enabled": enabled, "provider": provider, "model": model}
	except Exception as e:
		frappe.log_error(f"get_ai_config: {e}", "AI Config Error")
		return {"enabled": False, "provider": "", "model": ""}


@frappe.whitelist()
def chat(message: str, history: str = "[]"):
	"""
	Main AI chatbot endpoint.

	Args:
		message: The user's message (capped at 500 chars).
		history: JSON-encoded list of previous {role, content} dicts (last 10 kept).

	Returns:
		{"answer": str}
	"""
	if not message or not isinstance(message, str):
		return {"answer": "Please provide a message."}

	message = message.strip()[:500]

	# Rate limit — 20 requests per user per minute
	if not _check_rate_limit(frappe.session.user):
		return {"answer": "You're sending messages too quickly. Please wait a moment and try again."}

	# Safety check — runs before any LLM call
	if not _is_safe(message):
		frappe.log_error(
			f"AI safety block | user={frappe.session.user} | msg={message[:200]}",
			"AI Security Block",
		)
		return {
			"answer": (
				"I can only assist with hotel operations questions. "
				"Your message was blocked by the security policy. "
				"If you believe this is an error, contact your administrator."
			)
		}

	settings = _get_settings()
	if not settings.get("enabled"):
		return {"answer": "The AI assistant is not enabled. Contact your administrator."}

	# Parse and sanitise history
	try:
		history_list = json.loads(history) if history else []
		if not isinstance(history_list, list):
			history_list = []
	except (json.JSONDecodeError, TypeError):
		history_list = []
	history_list = history_list[-10:]

	# Role-gated tools
	roles = frappe.get_roles(frappe.session.user)
	allowed_tools = _get_allowed_tools(roles)
	tools_schema = _build_tools_schema(allowed_tools)

	# Build messages
	system_prompt = _build_system_prompt(frappe.session.user, roles, allowed_tools)
	messages = [{"role": "system", "content": system_prompt}]
	for h in history_list:
		if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content"):
			messages.append({"role": h["role"], "content": str(h["content"])})
	messages.append({"role": "user", "content": message})

	try:
		answer = _run_loop(messages, allowed_tools, tools_schema, settings)
		return {"answer": answer or "I couldn't generate a response. Please try again."}
	except _http.exceptions.ConnectionError:
		return {"answer": "Unable to reach the Ollama service. Check AI Settings in Hotel Setup."}
	except _http.exceptions.Timeout:
		return {"answer": "The AI service timed out. Please try again."}
	except Exception as e:
		frappe.log_error(f"AI chat error: {e}", "AI Chat Error")
		return {"answer": "An unexpected error occurred. Please try again or contact the administrator."}


@frappe.whitelist()
def generate_insight(context_type: str, context_data: str = "{}"):
	"""
	Generate a page-level AI insight. Context data is passed directly — no tool calling.

	Args:
		context_type: One of: room_view_briefing, night_audit_summary, guest_profile_summary
		context_data: JSON string of the page's current data snapshot.

	Returns:
		{"summary": str}
	"""
	if not _is_safe(context_type) or not _is_safe(str(context_data)):
		return {"summary": "Request blocked by security policy."}

	settings = _get_settings()
	if not settings.get("enabled"):
		return {"summary": "AI assistant is not configured. Contact your administrator."}

	prompt_template = _INSIGHT_PROMPTS.get(context_type)
	if not prompt_template:
		return {"summary": f"Unknown insight type: {context_type}"}

	try:
		ctx = json.loads(context_data) if isinstance(context_data, str) else (context_data or {})
	except (json.JSONDecodeError, TypeError):
		ctx = {}

	prompt = prompt_template.format(context=json.dumps(ctx, indent=2, default=str))

	# Resolve the hotel's default currency symbol so the LLM never falls back to $.
	try:
		currency_code = frappe.get_cached_doc("System Settings").default_currency or "NGN"
		currency_symbol = (
			frappe.get_cached_doc("Currency", currency_code).symbol or currency_code
		)
	except Exception:
		currency_symbol = "\u20a6"  # fallback: ₦

	messages = [
		{
			"role": "system",
			"content": (
				f"You are a hotel operations AI assistant. "
				f"Always use {currency_symbol} (never $ or USD) for all monetary amounts."
			),
		},
		{"role": "user", "content": prompt},
	]

	try:
		insight_settings = {**settings, "max_tokens": max(settings["max_tokens"], 400)}
		summary = _call_simple(messages, insight_settings)
		return {"summary": summary or "No insight generated."}
	except _http.exceptions.ConnectionError:
		return {"summary": "Unable to reach the Ollama service. Check AI Settings in Hotel Setup."}
	except _http.exceptions.Timeout:
		return {"summary": "The AI service timed out. Please try again."}
	except Exception as e:
		frappe.log_error(f"AI generate_insight error: {e}", "AI Insight Error")
		return {"summary": "Could not generate insight at this time."}
