
// frappe.ui.form.on('Maintenance Request', {
//     refresh: function(frm) {
//         if (!frm.doc.approved) {
//             frm.add_custom_button(__('Approve Request'), function() {
//                 // Set the approved field
//                 frm.set_value('approved', 1);
//                 frm.set_value('approval_time', frappe.datetime.now_datetime());
                
//                 // Save the document - this will trigger on_update()
//                 frm.save().then(() => {
//                     frappe.msgprint(__('Request approved successfully.'));
//                 });
//             });
//         }
//     }
// });



// frappe.ui.form.on('Maintenance Request', {
//     refresh: function(frm) {
//         if (!frm.doc.approved) {
//             frm.add_custom_button(__('Approve Request'), function() {
//                 frm.set_value('approved', 1)
//                 frm.set_value('approval_time', frappe.datetime.now_datetime())

//                 frm.save().then(() => {
//                     frappe.msgprint(__('Request approved successfully.'))
//                 })
//             })
//         }   
//     },

//     reported_by: function(frm) {
//         set_requesting_department(frm)  
//     },

//     witness_employee: function(frm) {
//         set_witness_department(frm)
//     },

//     onload: function(frm) {
//         set_requesting_department(frm)
//         set_witness_department(frm)
//     }
// })


// function set_requesting_department(frm) {
//     if (!frm.doc.reported_by) {
//         frm.set_value('requesting_department', null)
//         return
//     }

//     frappe.db.get_value(
//         'Employee',
//         frm.doc.reported_by,
//         'department',
//         function(r) {
//             if (r && r.department) {
//                 frm.set_value('requesting_department', r.department)
//             }
//         }
//     )
// }

// function set_witness_department(frm) {
//     if (!frm.doc.witness_employee) {
//         frm.set_value('witness_department', null)
//         return
//     }

//     frappe.db.get_value(
//         'Employee',
//         frm.doc.witness_employee,
//         'department',
//         function(r) {
//             if (r && r.department) {
//                 frm.set_value('witness_department', r.department)
//             }
//         }
//     )
// }







frappe.ui.form.on('Maintenance Request', {
    refresh: function(frm) {
        if (frm.doc.approved !== 'Approved') {
            frm.add_custom_button(__('Approve Request'), function() {
                frm.set_value('approved', 'Approved')
                frm.set_value('approved_by', frappe.session.user)
                frm.set_value('approved_on', frappe.datetime.now_datetime())

                frm.save().then(function() {
                    frappe.msgprint(__('Request approved successfully.'))
                })
            })
        }
    },

    reported_by: function(frm) {
        set_requesting_department(frm)
    },

    witness_employee: function(frm) {
        set_witness_department(frm)
    },

    onload: function(frm) {
        set_requesting_department(frm)
        set_witness_department(frm)
    }
})


function set_requesting_department(frm) {
    if (!frm.doc.reported_by) {
        frm.set_value('requesting_department', null)
        return
    }

    frappe.db.get_value('Employee', frm.doc.reported_by, 'department')
        .then(function(response) {
            if (response && response.message && response.message.department) {
                frm.set_value('requesting_department', response.message.department)
            }
        })
}


function set_witness_department(frm) {
    if (!frm.doc.witness_employee) {
        frm.set_value('witness_department', null)
        return
    }

    frappe.db.get_value('Employee', frm.doc.witness_employee, 'department')
        .then(function(response) {
            if (response && response.message && response.message.department) {
                frm.set_value('witness_department', response.message.department)
            }
        })
}

