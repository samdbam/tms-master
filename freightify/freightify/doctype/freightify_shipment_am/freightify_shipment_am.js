// Copyright (c) 2024, Freightify and contributors
// For license information, please see license.txt

frappe.ui.form.on("Freightify Shipment Am", {
	refresh(frm) {
        frm.set_df_property('schedule_and_rate', 'cannot_add_rows', true);
        frm.fields_dict['schedule_and_rate'].grid.wrapper.find('.grid-remove-rows').hide();
        frm.refresh_field("schedule_and_rate")
        // Show buttons only when pos view is active
		if (cint(frm.doc.docstatus == 0) && frm.page.current_view_name !== "pos" && !frm.doc.is_return) {
            frm.add_custom_button(
                __("Sales Order"),
                function () {
                    erpnext.utils.map_current_doc({
                        method: "freightify.freightify.doctype.freightify_shipment_am.freightify_shipment_am.make_freightify_shipment_am",
                        source_doctype: "Sales Order",
                        target: frm,
                        setters: {
                            customer: frm.doc.customer || undefined,    
                        },
                        get_query_filters: {
                            docstatus: 1,
                            status: ["not in", ["Closed", "On Hold"]],
                            custom_per_shipped: ["<", 99.99],
                            per_billed: ["<", 99.99],
                            company: frm.doc.company,
                        },
                    });
                },
                __("Get Items From")
            );
		}
        if(!frm.is_new()){
            if(frm.doc.docstatus == 1){
                frm.set_df_property('items', 'cannot_add_rows', true);
                frm.fields_dict['items'].grid.wrapper.find('.grid-remove-rows').hide();
                frm.add_custom_button(("Project"), function(){
                    frappe.new_doc("Project",{"project_name":frm.doc.name})
                },__("Create"))
            }
            // frm.add_custom_button(("Shipment Schedule"), function(){
            //     if(!frm.doc.shipment_rate){
            //         check_existing(frm,doctype="Shipment Schedule")
            //     }
            //     else{
            //         frappe.throw(`Shipment Schedule <b>${frm.doc.shipment_schedule}</b> is <b>Already Created</b> for this Shipment</b>${frm.doc.name}</b>`)
            //     }
            // },__("Create"))
            frm.add_custom_button(("Shipment Rate"), function(){
                if(!frm.doc.reference_doctype && !frm.doc.reference_name){
                    check_existing(frm,doctype="Shipment Rate")
                }
                else{
                    frappe.throw(`Shipment Rate <b>${frm.doc.reference_name}</b> is <b>Already Created</b> for this Shipment</b>${frm.doc.name}</b>`)
                }
            },__("Create"))
        }
	},
    get_item(frm){
        if(frm.doc.schedule_and_rate){
            var selected = 0
            check_selected=check_shedule_and_rate(frm,selected)
            if(check_selected==0){
                frappe.throw("<b>Need to Select any one Schedule and Rate Item</b>")
            }
            else{
                frm.set_value("items",[])
                frm.refresh_field("items")
                var schdeule_rate_table=frm.doc.schedule_and_rate
                frm.call({
                    method: "freightify.freightify.api.consolidate_item",
                    args: {
                        table:schdeule_rate_table,
                        doctype:"Freightify Shipment Am"
                    },
                    freeze:true,    
                    freeze_message:"Getting Items",
                    async:true,
                }).then(r => {
                    if(r.message.function=="Failed"){
                        frappe.throw(r.message.value)
                    }
                    if(r.message.function=="Success"){
                        add_items_in_table(frm,item_list = r.message.value)
                        for(let rate of frm.doc.schedule_and_rate){
                            if(rate.__checked){
                                rate.is_selected = 1
                            }
                            else if(!rate.__checked && rate.is_selected == 1){
                                rate.is_selected = 0
                            }
                        }
                        frm.refresh_field("schedule_and_rate")
                        frm.save()
                    }
                })
            }
        }
    },
    fetch_items(frm){
        if(frm.doc.schedule_and_rate){
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
    track(frm){
        if(frm.doc.container){
            for(let item of frm.doc.container){
                if(!item.container_no || !item.carrier){
                    frappe.throw(`<b>Container No</b> or <b>Carrier not present </b> in Row <b>${item.idx}</b>`)
                }
            }
            frm.call({
                method: "freightify.freightify.doctype.shipment_rate.shipment_rate.OAuth2_authentication",
                args: {
                    doc:frm.doc,
                },
                async:true,
                freeze:true,
                freeze_message:"Tracking Status",
            }).then(r => {
                console.log("track",r.message);
                
                if(r.message.function=="Failed"){
                    frappe.show_alert({ message: `${r.message.value}`, indicator: "red" }, 5)
                }
                if(r.message.function=="Success"){
                    // frappe.throw("Test")
                    frappe.show_alert({ message: `<b>Track and Trace Successfully fetched</b>`, indicator: "green" }, 5)
                    for(let status of frm.doc.container){
                        status.tracking_json =  JSON.stringify(r.message.value)
                    }
                    frm.refresh_field("container")
                    frm.dirty()
                    frm.save()
                }
            })
        }
    },
});
frappe.ui.form.on('Sales Order Item',{
    item_code(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if(d.item_code && (!d.item_name || !d.uom || !d.conversion_factor)){
            frm.call({
                method: "freightify.freightify.doctype.freightify_shipment_am.freightify_shipment_am.get_item_detail",
                args: {
                    item_code:d.item_code,
                },
                async:true,
            }).then(r => {
                if(r.message.function=="Failed"){
                    frappe.show_alert({ message: `${r.message.value}`, indicator: "red" }, 5)
                }
                if(r.message.function=="Success"){
                    d.item_name=r.message.value.item_name
                    d.uom=r.message.value.stock_uom
                    d.conversion_factor=1
                }
                frm.refresh_field("items")
                
            })

        }
    },
    qty(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        d.amount = d.rate * d.qty
        frm.refresh_field("items") 
    },
    rate(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        d.amount = d.rate * d.qty 
        frm.refresh_field("items") 
    },
    before_items_remove(frm,cdt,cdn) {
        var d = locals[cdt][cdn]
        if(d.custom_schedule_and_rate_ref){
            for(let rate of frm.doc.schedule_and_rate){
                if(rate.rate_id == d.custom_schedule_and_rate_ref){
                    rate.__checked = 0
                    rate.is_selected = 0
                }
            }
            frm.refresh_field("schedule_and_rate")
            var selected = 0
            check_selected=check_shedule_and_rate_is_selected(frm,selected)
            if(check_selected==0){
                frm.set_value("items",[])
                frm.refresh_field("items")
                // frm.save()
            }
            else{
                frm.set_value("items",[])
                frm.refresh_field("items")
                var schdeule_rate_table=frm.doc.schedule_and_rate
                frm.call({
                    method: "freightify.freightify.doctype.freightify_shipment_am.freightify_shipment_am.consolidate_shipment_item",
                    args: {
                        table:schdeule_rate_table,
                        doctype:"Freightify Shipment Am"
                    },
                    async:true,
                }).then(r => {
                    if(r.message.function=="Failed"){
                        frappe.throw(r.message.value)
                    }
                    if(r.message.function=="Success"){
                        add_items_in_table(frm,item_list = r.message.value)
                        // frm.save()
                    }
                })
            }
        }
	},
})
frappe.ui.form.on("Schedule and Rate Detail",{
    form_render(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frm.set_df_property("schedule_and_rate", "options", d.schedule, frm.doc.name, "schedule_html", d.name)
        frm.set_df_property("schedule_and_rate", "options", d.charge, frm.doc.name, "charge_html", d.name)
        frm.refresh_field("schedule_and_rate")
    },
})
frappe.ui.form.on("Freightify Container",{
    form_render(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        var tracking_json = JSON.parse(d.tracking_json)
        var tracking_status = tracking_json[d.container_no]
        frm.set_df_property("container", "options", tracking_status, frm.doc.name, "tracking_html", d.name)
        frm.refresh_field("container")
    },
})
function check_existing(frm,doctype){
    frm.call({
        method: "freightify.freightify.doctype.freightify_shipment_am.freightify_shipment_am.check_shipment_shedule_and_rate",
        args: {
            doc:frm.doc,
            doctype:doctype
        },
        freeze:true,
        freeze_message:"Check Existing",
        async:true,
    }).then(r => {
        if(r.message.function=="Success"){
            frappe.new_doc(doctype,{
                "reference_doctype":frm.doc.doctype,
                "reference_name":frm.doc.name,
                "company":frm.doc.company,
                "shipping_type":frm.doc.shipping_type
            })
        }
        if(r.message.function=="Failed"){
            frappe.throw(r.message.value)
        }
    })
}
function check_shedule_and_rate(frm,selected){
    for(let rate of frm.doc.schedule_and_rate){
        if(rate.__checked==1){
            selected = selected + 1
        }
    }
    return selected
}
function check_shedule_and_rate_is_selected(frm,selected){
    for(let rate of frm.doc.schedule_and_rate){
        if(rate.is_selected==1){
            selected = selected + 1
        }
    }
    return selected
}
function get_checked_item(frm){
    let checked_item_list=[]
    for(let rate of frm.doc.schedule_and_rate){
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

function add_items_in_table(frm,item_list){
    if(item_list){
        for(let consolidate of item_list){
            var row=cur_frm.add_child("items")
            row.item_code=consolidate.item_code
            row.item_name=consolidate.item_name
            row.description=consolidate.description
            row.custom_schedule_and_rate_ref=consolidate.ref_name
            row.qty=consolidate.qty
            row.uom=consolidate.uom
            row.stock_uom=consolidate.stock_uom
            row.conversion_factor=1
            row.rate=consolidate.rate
            row.custom_shipment_rate=consolidate.rate
            row.amount=consolidate.amount
        }
        frm.refresh_field("items")
    }
}