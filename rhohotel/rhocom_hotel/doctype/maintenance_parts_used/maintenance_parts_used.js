// frappe.ui.form.on('Maintenance Parts Used', {
//     item_code(frm, cdt, cdn) {
//         set_available_qty(frm, cdt, cdn)
//     },

//     warehouse(frm, cdt, cdn) {
//         set_available_qty(frm, cdt, cdn)
//     }
// })


// function set_available_qty(frm, cdt, cdn) {
//     const row = locals[cdt][cdn]

//     if (!row.item_code || !row.warehouse) {
//         frappe.model.set_value(cdt, cdn, 'available_qty', 0)
//         return
//     }

//     frappe.db.get_value(
//         'Bin',
//         {
//             item_code: row.item_code,
//             warehouse: row.warehouse
//         },
//         'actual_qty'
//     ).then(function(response) {
//         const qty = (
//             response &&
//             response.message &&
//             response.message.actual_qty
//         ) || 0

//         frappe.model.set_value(cdt, cdn, 'available_qty', qty)
//     })
// }


frappe.ui.form.on('Maintenance Parts Used', {
    item_code(frm, cdt, cdn) {
        update_available_qty(cdt, cdn)
    },

    warehouse(frm, cdt, cdn) {
        update_available_qty(cdt, cdn)
    }
})


function update_available_qty(cdt, cdn) {
    const row = locals[cdt][cdn]

    if (!row.item_code || !row.warehouse) {
        frappe.model.set_value(cdt, cdn, 'available_qty', 0)
        return
    }

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Bin',
            filters: {
                item_code: row.item_code,
                warehouse: row.warehouse
            },
            fieldname: 'actual_qty'
        },
        callback: function(r) {
            let qty = 0

            if (
                r.message &&
                r.message.actual_qty !== undefined
            ) {
                qty = r.message.actual_qty
            }

            frappe.model.set_value(
                cdt,
                cdn,
                'available_qty',
                qty
            )
        }
    })
}