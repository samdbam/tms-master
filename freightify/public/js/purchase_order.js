frappe.ui.form.on("Purchase Order", {
    refresh(frm){
        frm.set_df_property('custom_schedule_and_rate', 'cannot_add_rows', true);
        frm.fields_dict['custom_schedule_and_rate'].grid.wrapper.find('.grid-remove-rows').hide();
        frm.refresh_field("custom_schedule_and_rate")
        if(!frm.is_new() && frm.doc.docstatus == 0){
            frm.add_custom_button(("Shipment Rate"), function(){
                frappe.new_doc("Shipment Rate",{
                    "reference_doctype":frm.doc.doctype,
                    "reference_name":frm.doc.name,
                    "company":frm.doc.company
                })
            },__("Create"))
        }
    },
    custom_get_item(frm){
        if(frm.doc.custom_schedule_and_rate){
            var selected = 0
            check_selected=check_shedule_and_rate(frm,selected)
            if(check_selected==0){
                frappe.throw("<b>Need to Select any one Schedule and Rate Item</b>")
            }
            else{
                frm.set_value("items",[])
                frm.refresh_field("items")
                var schdeule_rate_table=frm.doc.custom_schedule_and_rate
                frm.call({
                    method: "freightify.freightify.api.consolidate_item",
                    args: {
                        table:schdeule_rate_table,
                        doctype:"Purchase Order"
                    },
                    freeze:true,    
                    freeze_message:"Getting Items",
                    async:true,
                }).then(r => {
                    if(r.message.function=="Failed"){
                        frappe.throw(r.message.value)
                    }
                    if(r.message.function=="Success"){
                        for(let consolidate of r.message.value){
                            var row=cur_frm.add_child("items")
                            row.item_code=consolidate.item_code
                            row.item_name=consolidate.item_name
                            row.description=consolidate.description
                            row.custom_schedule_and_rate_ref=consolidate.ref_name
                            row.qty=consolidate.qty
                            row.uom=consolidate.uom
                            row.uom=consolidate.uom
                            row.conversion_factor=1
                            row.stock_uom=consolidate.stock_uom
                            row.rate=consolidate.rate
                            row.custom_shipment_rate=consolidate.rate
                            row.amount=consolidate.amount
                        }
                        frm.refresh_field("items")
                        for(let rate of frm.doc.custom_schedule_and_rate){
                            if(rate.__checked){
                                rate.is_selected = 1
                            }
                            else if(!rate.__checked && rate.is_selected == 1){
                                rate.is_selected = 0
                            }
                        }
                        frm.refresh_field("custom_schedule_and_rate")
                    }
                })
            }
        }
    },
    custom_fetch_items(frm){
        if(frm.doc.custom_schedule_and_rate){
            var selected = 0
            check_selected=check_shedule_and_rate(frm,selected)
            if(check_selected==0){
                frappe.throw("<b>Need to Select any one Schedule and Rate Item</b>")
            }
            else{
                get_checked_item(frm)
            }
        }
    },
})
frappe.ui.form.on('Purchase Order Item',{
    before_items_remove(frm,cdt,cdn) {
        var d = locals[cdt][cdn]
        var deleted_row = frappe.get_doc(cdt, cdn);
        if(deleted_row.custom_schedule_and_rate_ref){
            var to_have = []
            for(let item of frm.doc.items){
                if(item.custom_schedule_and_rate_ref != deleted_row.custom_schedule_and_rate_ref){
                    to_have.push(item)
                }
            }
            frm.set_value("items",to_have)
            frm.refresh_field("items")
            for(let rate of frm.doc.custom_schedule_and_rate){
                if(rate.rate_id == deleted_row.custom_schedule_and_rate_ref){
                    rate.__checked = 0
                    rate.is_selected = 0
                }
            }
            frm.refresh_field("custom_schedule_and_rate")
        }
	},
})
frappe.ui.form.on("Schedule and Rate Detail",{
    form_render(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frm.set_df_property("custom_schedule_and_rate", "options", d.schedule, frm.doc.name, "schedule_html", d.name)
        frm.set_df_property("custom_schedule_and_rate", "options", d.charge, frm.doc.name, "charge_html", d.name)
        frm.refresh_field("custom_schedule_and_rate")
    },
})
function check_shedule_and_rate(frm,selected){
    for(let rate of frm.doc.custom_schedule_and_rate){
        if(rate.__checked==1){
            selected = selected + 1
        }
    }
    return selected
}
function get_checked_item(frm){
    let checked_item_list=[]
    for(let rate of frm.doc.custom_schedule_and_rate){
        if(rate.__checked==1){
            checked_item_list.push(rate.rate_id)
        }
    }
    if(checked_item_list){
        let present = 0
        for(let item of frm.doc.items){
            if(checked_item_list.includes(item.custom_schedule_and_rate_ref)){
                item.__checked = 1
                present = present + 1
            }
            else{
                item.__checked = 0
            }
        }
        frm.refresh_field("items")
        if(present == 0){
            frappe.throw("<b>There is no Item is Mapped</b>")
        }
    }
}