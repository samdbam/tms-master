// Copyright (c) 2024, Freightify and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shipment Schedule", {
    refresh(frm){
        if(frm.doc.docstatus==1){
            frm.add_custom_button(("Quotation"), function(){
                frappe.model.open_mapped_doc({
                    method:"freightify.freightify.doctype.shipment_schedule.shipment_schedule.make_quotation_sales_order",
                    frm:frm,
                    args:{
                        doctype:"Quotation"
                    },
                })
            },__("Create"))
            frm.add_custom_button(("Order"), function(){
                frappe.model.open_mapped_doc({
                    method:"freightify.freightify.doctype.shipment_schedule.shipment_schedule.make_quotation_sales_order",
                    frm:frm,
                    args:{
                        doctype:"Sales Order"
                    },
                })
            },__("Create"))
            frm.add_custom_button(("Shipment"), function(){
                if(frm.doc.reference_doctype != "Freightify Shipment"){
                    check_existing(frm,doctype="Freightify Shipment")
                }
                else{
                    frappe.throw(`Shipment <b>${frm.doc.reference_name}</b> is <b>Already Created</b> for this Schedule </b>${frm.doc.name}</b>`)
                }
            },__("Create"))
        }
    },
	get_schedules(frm){
        frm.set_value("schedule",[])
        frm.refresh_field("schedule")
        if(frm.doc.origin && frm.doc.destination && frm.doc.departure_date && frm.doc.duration){
            frm.call({
                method: "freightify.freightify.doctype.shipment_schedule.shipment_schedule.OAuth2_authentication",
                args: {
                    doc:frm.doc,
                },
                async:true,
                freeze:true,
                freeze_message:"Getting Schedules",
            }).then(r => {
                console.log("OAuth2_authentication",r);
                if(r.message.function=="Failed"){
                    frappe.throw(r.message.values)
                }
                if(r.message.function=="Success"){
                    console.log("schedules",r.message.value)
                    if(r.message.value && Object.keys(r.message.value).length  >0){
                        var schedule_list=r.message.value
                        for(let schedule of schedule_list){
                            var detail = schedule.scheduleDetails[0]
                            var schedule_row =cur_frm.add_child("schedule")
                            schedule_row.function="Schedule"
                            //From Location
                            schedule_row.departure_date=detail.fromLocation.departure
                            schedule_row.from_location=detail.fromLocation.portName
                            schedule_row.vgm_cutoff=""
                            schedule_row.port_cutoff=""
                            schedule_row.service=detail.serviceCode
                            schedule_row.vessel=detail.transport.vessel.name
                            schedule_row.voyage_ref=detail.transport.voyageNumber
                            //To Location
                            schedule_row.arrival_date=detail.toLocation.arrival
                            schedule_row.to_location=detail.toLocation.portName
                        }
                        frm.refresh_field("schedule")
                    }
                    else{
                        frappe.throw(`<b>Shedules are not available.</b>`)
                    }
                }
            })
        }
    },
});
function check_existing(frm,doctype){
    frm.call({
        method: "freightify.freightify.doctype.shipment_schedule.shipment_schedule.check_shedule_and_rate",
        args: {
            doc:frm.doc,
            doctype:doctype
        },
        freeze:true,
        freeze_message:"Check Existing",
        async:true,
    }).then(r => {
        if(r.message.function=="Success"){
            frappe.model.open_mapped_doc({
                method:"freightify.freightify.doctype.shipment_schedule.shipment_schedule.make_shipment",
                frm:frm,
                args:{
                    doctype:"Freightify Shipment"
                },
            })
        }
        if(r.message.function=="Failed"){
            frappe.throw(r.message.value)
        }
    })
}
frappe.ui.form.on("Schedule and Rate Detail", {
	schedule_add(frm,cdt,cdn) {
        var d = locals[cdt][cdn]
        if(frm.doc.doctype=="Shipment Schedule"){
            d.function="Schedule"
        }
        frm.refresh_field("schedule")
	},
});