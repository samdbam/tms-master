// Copyright (c) 2024, Freightify and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consolidated Shipment", {
	refresh(frm) {
        set_container_mode(frm)
	},
    transport(frm){
        set_container_mode(frm)
    },
    selling_agent_name(frm){
        if(frm.doc.selling_agent_name){
            let value = get_address_contact(frm,id=frm.doc.selling_agent_name)
            frm.set_value("selling_agent_address",value[0])
            frm.set_value("selling_agent_contact",value[1])
            frm.refresh_fields()
        }
    },
    receiving_agent_name(frm){
        if(frm.doc.receiving_agent_name){
            let value = get_address_contact(frm,id=frm.doc.receiving_agent_name)
            frm.set_value("receiving_agent_address",value[0])
            frm.set_value("receiving_agent_contact",value[1])
            frm.refresh_fields()
        }
    }
});

function get_address_contact(frm,id){
    var result = frappe.call({
        method:"freightify.freightify.doctype.consolidated_shipment.consolidated_shipment.get_agent_address_contact",
        args: {
            doctype: "Customer",
            docname: id
        },
        async:false,
        callback: function(r){
            return r.message
        }
    })
    return result.responseJSON.message
}


function set_container_mode(frm){
    if(frm.doc.transport){
        frm.set_query("container_mode",  function() {
            return {
                filters:{
                    transport_type:frm.doc.transport
                }
            }    
        });
    }
}
