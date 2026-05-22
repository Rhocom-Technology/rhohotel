frappe.ui.form.on('Vehicle Mileage Log', {

    refresh(frm) {

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

        frm.set_query('supervisor', () => ({
            filters: {
                status: 'Active'
            }
        }))
    },

    hotel_vehicle(frm) {

        if (!frm.doc.hotel_vehicle) {

            frm.set_value('plate_number', null)
            frm.set_value('asset', null)

            return
        }

        frappe.db.get_doc(
            'Hotel Vehicle',
            frm.doc.hotel_vehicle
        ).then(vehicle => {

            frm.set_value(
                'plate_number',
                vehicle.plate_number || null
            )

            frm.set_value(
                'asset',
                vehicle.asset || null
            )
        })
    },

    odometer_start(frm) {
        calculate_trip_km(frm)
    },

    odometer_stop(frm) {
        calculate_trip_km(frm)
    }
})


function calculate_trip_km(frm) {

    const start = frm.doc.odometer_start || 0
    const stop = frm.doc.odometer_stop || 0

    if (stop >= start) {
        frm.set_value(
            'km_this_trip',
            stop - start
        )
    }
}