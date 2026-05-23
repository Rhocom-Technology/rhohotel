"""
Hotel Booking Validations - Additional safety checks
Ensures rooms are still available before holding and before charging payment
"""

import frappe
from frappe.utils import getdate, nowdate
from datetime import datetime
from .shared_utilities import parse_date
from rhohotel.rhocom_hotel.utils.room_availability import (
    check_checkin_conflict,
)


@frappe.whitelist()
def validate_rooms_still_available(
    rooms_list, check_in_date, check_out_date, current_booking_number=None
):
    """
    RE-VALIDATE that selected rooms are still available.
    Called before creating or validating a temporary booking.
    
    Args:
        rooms_list (str or list): Room numbers to validate
        check_in_date (str): Check-in date (YYYY-MM-DD)
        check_out_date (str): Check-out date (YYYY-MM-DD)
        current_booking_number (str, optional): 
            Booking number that owns the hold. Prevents self-conflict.

    Returns:
        dict: Validation result with unavailable rooms list
    """
    try:
        import json
        if isinstance(rooms_list, str):
            try:
                rooms_list = json.loads(rooms_list)
            except json.JSONDecodeError:
                raise frappe.ValidationError("Invalid rooms format")
        
        if not isinstance(rooms_list, list) or len(rooms_list) == 0:
            raise frappe.ValidationError("No rooms to validate")
        
        # Parse dates
        check_in_str, check_in = parse_date(check_in_date, "check_in_date")
        check_out_str, check_out = parse_date(check_out_date, "check_out_date")
        
        unavailable_rooms = []
        
        for room_number in rooms_list:
            # Check if room exists
            room = frappe.db.get_value(
                "Hotel Room",
                room_number,
                ["name", "room_type", "status", "operational_status", 
                 "booking_status", "hold_expires_at", "current_booking_number"],
                as_dict=True
            )
            
            if not room:
                unavailable_rooms.append({
                    "room_number": room_number,
                    "reason": "Room does not exist"
                })
                continue
            
            # ---------------------
            # 1. Operational status
            # ---------------------
            if room.get("operational_status") != "In Service":
                unavailable_rooms.append({
                    "room_number": room_number,
                    "reason": "Room is out of service"
                })
                continue
            
            # ---------------------
            # 2. Hold status check
            # ---------------------
            if room.get("booking_status") == "Held":
                hold_expires = room.get("hold_expires_at")
                held_by = room.get("current_booking_number")
                
                # Ignore self holds
                if held_by and current_booking_number and held_by == current_booking_number:
                    pass
                else:
                    if hold_expires and datetime.fromisoformat(str(hold_expires)) > datetime.now():
                        unavailable_rooms.append({
                            "room_number": room_number,
                            "reason": "Room is currently held by another booking"
                        })
                        continue
            
            # ----------------------------
            # 3. Active Check-Ins (live)
            # ----------------------------
            if check_checkin_conflict(room_number, check_in_str, check_out_str):
                unavailable_rooms.append({
                    "room_number": room_number,
                    "reason": "Room currently occupied (active check-in)"
                })
                continue
        
        return {
            "success": len(unavailable_rooms) == 0,
            "unavailable_rooms": unavailable_rooms,
            "total_rooms_checked": len(rooms_list),
            "valid_rooms_count": len(rooms_list) - len(unavailable_rooms),
            "message": f"{len(rooms_list) - len(unavailable_rooms)}/{len(rooms_list)} rooms validated"
        }
    
    except frappe.ValidationError as e:
        frappe.throw(str(e))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Room Validation Error")
        frappe.throw(f"Error validating rooms: {str(e)}")


@frappe.whitelist()
def check_room_hold_conflict(room_numbers, start_holding_time=None):
    """
    Check if any rooms have conflicting holds or bookings.
    """
    try:
        import json
        if isinstance(room_numbers, str):
            try:
                room_numbers = json.loads(room_numbers)
            except json.JSONDecodeError:
                raise frappe.ValidationError("Invalid rooms format")
        
        current_time = start_holding_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conflicts = []
        
        for room_number in room_numbers:
            held_by = frappe.db.get_value(
                "Hotel Room",
                room_number,
                ["booking_status", "current_booking_number", "hold_expires_at"]
            )
            
            if held_by:
                booking_status, booking_number, hold_expires = held_by
                
                if booking_status == "Held" and hold_expires:
                    hold_time = datetime.fromisoformat(str(hold_expires))
                    if hold_time > datetime.fromisoformat(current_time):
                        conflicts.append({
                            "room_number": room_number,
                            "held_by": booking_number,
                            "expires_at": hold_expires
                        })
        
        return {
            "success": len(conflicts) == 0,
            "conflicts": conflicts,
            "message": f"No conflicts found" if len(conflicts) == 0 else f"{len(conflicts)} room(s) have conflicts"
        }
    
    except Exception as e:
        frappe.log_error(f"Error checking hold conflicts: {str(e)}")
        return {
            "success": False,
            "conflicts": [],
            "message": f"Error: {str(e)}"
        }
