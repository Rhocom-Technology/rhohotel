const STANDARD_INSPECTION_ITEMS = [
    "Engine oil level",
    "Brake fluid level",
    "Brake pads / braking response",
    "Steering system / steering oil",
    "Coolant level",
    "Tire condition & inflation",
    "Headlights, brake lights & indicators",
    "Windshield & wipers",
    "Horn & mirrors",
    "Exterior body condition",
    "Interior condition & cleanliness",
    "Vehicle hygiene status",
    "General engine sound (idle & rev)"
]

function populate_standard_items(frm) {
    if (!frm.is_new()) return

    const has_real_items = (frm.doc.inspection_items || []).some(row => row.inspection_item)

    if (has_real_items) return

    frm.clear_table('inspection_items')

    STANDARD_INSPECTION_ITEMS.forEach(item => {
        const row = frm.add_child('inspection_items')
        row.inspection_item = item
        row.status = 'OK'
    })

    frm.refresh_field('inspection_items')
}

frappe.ui.form.on('Vehicle Safety Checklist', {
    onload(frm) {
        populate_standard_items(frm)
    },

    refresh(frm) {
        populate_standard_items(frm)

        frm.set_query('hotel_vehicle', () => ({
            filters: {
                status: ['!=', 'Disposed']
            }
        }))

        frm.set_query('driver', () => ({
            filters: {
                status: 'Active'
            }
        }))

        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Reset Standard Inspection Items'), () => {
                frappe.confirm(
                    __('This will replace the current inspection items with the standard checklist. Continue?'),
                    () => {
                        frappe.call({
                            method: 'rhohotel.rhocom_hotel.doctype.vehicle_safety_checklist.vehicle_safety_checklist.reset_standard_items',
                            args: {
                                name: frm.doc.name
                            },
                            callback() {
                                frm.reload_doc()
                            }
                        })
                    }
                )
            })
        }
    },

    hotel_vehicle(frm) {
        if (!frm.doc.hotel_vehicle) {
            frm.set_value('registration_number', null)
            frm.set_value('make_model', null)
            frm.set_value('vehicle_asset', null)
            return
        }

        frappe.db.get_doc('Hotel Vehicle', frm.doc.hotel_vehicle).then(vehicle => {
            frm.set_value('registration_number', vehicle.plate_number || null)

            const makeModel = [vehicle.make, vehicle.model]
                .filter(Boolean)
                .join(' ')

            frm.set_value('make_model', makeModel || null)
            frm.set_value('vehicle_asset', vehicle.asset || null)
        })
    }
})