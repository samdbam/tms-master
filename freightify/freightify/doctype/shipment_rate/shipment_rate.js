// Copyright (c) 2024, Freightify and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shipment Rate", {
	refresh(frm){
        // frm.previous_idx = 0
        // if(frm.doc.doctype == "Shipment Rate"){
        //     // $("[class='btn btn-xs btn-secondary grid-add-row']").remove()
        //     // $("[class='btn btn-xs btn-danger grid-remove-rows']").remove()
        // }
        $("[data-fieldname='rate']").click(function (event) {
            $("[class='btn btn-xs btn-danger grid-remove-rows']").remove()
            // var rate_table=frm.doc.rate
            // var function_name = "selecting"
            // shipment_rate_item(frm,rate_table,function_name)	
        })
        if(frm.doc.docstatus == 1){
            setTimeout(() => {
                frm.add_custom_button(("Request for Quotation"), function(){
                    frappe.model.open_mapped_doc({
                        method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_quotation_sales_order",
                        frm:frm,
                        args:{
                            doctype:"Request for Quotation"
                        },
                    })
                },__("Create"))
                frm.add_custom_button(("Supplier Quotation"), function(){
                    frappe.model.open_mapped_doc({
                        method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_quotation_sales_order",
                        frm:frm,
                        args:{
                            doctype:"Supplier Quotation"
                        },
                    })
                },__("Create"))
                frm.add_custom_button(("Purchase Order"), function(){
                    frappe.model.open_mapped_doc({
                        method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_quotation_sales_order",
                        frm:frm,
                        args:{
                            doctype:"Purchase Order"
                        },
                    })
                },__("Create"))
                frm.add_custom_button(("Quotation"), function(){
                    frappe.model.open_mapped_doc({
                        method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_quotation_sales_order",
                        frm:frm,
                        args:{
                            doctype:"Quotation"
                        },
                    })
                },__("Create"))
                frm.add_custom_button(("Sales Order"), function(){
                    frappe.model.open_mapped_doc({
                        method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_quotation_sales_order",
                        frm:frm,
                        args:{
                            doctype:"Sales Order"
                        },
                    })
                },__("Create"))
                frm.add_custom_button(("Shipment"), function(){
                    if(!frm.doc.reference_doctype){
                        check_existing(frm,doctype="Freightify Shipment")
                    }
                    else if(frm.doc.reference_doctype != "Freightify Shipment"){
                        check_existing(frm,doctype="Freightify Shipment")
                    }
                    else{
                        frappe.throw(`Forwarding Shipment <b>${frm.doc.reference_name}</b> is <b>Already Created</b> for this Shipment Rate <b>${frm.doc.name}</b>`)
                    }
                },__("Create"))
            }, 1000);
        }
    },
    mode(frm){
        // frm.set_value("container_qty","")
        // frm.set_value("container_type","")
        frm.set_value("weight","")
        frm.set_value("volume","")
        // frm.set_value("weight_unit","")
        frm.set_value("containers","")
        frm.set_value("dimensions","")
        frm.set_value("has_dimensions",0)
        frm.refresh_fields()
    },
    has_dimensions(frm){
        frm.set_value("volume","")
        frm.set_value("weight","")
        frm.set_value("dimensions","")
        frm.refresh_fields()
    },
	get_rates(frm){
        frm.set_value("rate",[])
        frm.refresh_field("items")
        frm.set_value("items",[])
        frm.refresh_field("rate")
        var message = check_all_fields_filled(frm)
        // console.log("message",message);
        if (message.function =="Failed"){
            frappe.throw(message.value)
        }
        if(frm.doc.origin && frm.doc.destination && frm.doc.departure_date){
            frm.call({
                method: "freightify.freightify.doctype.shipment_rate.shipment_rate.OAuth2_authentication",
                args: {
                    doc:frm.doc,
                },
                async:true,
                freeze:true,
                freeze_message:"Getting Rates",
            }).then(r => {
                console.log("price",r.message);
                
                if(r.message.function=="Failed"){
                    frappe.throw(r.message.value)
                }
                if(r.message.function=="Success"){
                    // frappe.throw("Test")
                    if(r.message.value){
                        for(let item of r.message.value){
                            var row=cur_frm.add_child("rate")
                            row.port_of_origin=item.port_of_origin
                            row.port_of_destination=item.port_of_destination
                            row.carrier_name=item.carrier_name
                            row.carrier_code=item.carrier_code
                            row.transit_time=item.transit_time
                            row.service_type=item.service_type
                            row.rate_id=item.rate_id
                            row.sailing_date=item.sailing_date
                            row.buy_rate=item.buy_rate
                            row.sell_rate=item.sell_rate
                            row.effective_from=item.effective_from
                            row.effective_to=item.effective_to
                            row.incoterm=item.incoterm
                            row.cargo_type=item.cargo_type
                            row.commodity=item.commodity
                            row.remarks=item.remarks
                            row.inclusions=item.inclusions
                            row.terms_and_conditions=""
                            row.schedule_json=JSON.stringify(item.schedule_json)
                            row.schedule=item.schedule
                            row.charges_json=JSON.stringify(item.charges_json)
                            row.charge=item.charge
                            // row.charge_html item.charge
                        }
                        frm.refresh_field("rate")
                        frm.save()
                    }
                    else{
                        frappe.throw(`<b>Shedules and Rates are not available.</b>`)
                    }
                }
            })
        }
    },
    // get_item(frm){
    //     var rate_table=frm.doc.rate
    //     var function_name = "fetching"
    //     shipment_rate_item(frm,rate_table,function_name)
    // },
    container_qty(frm){
        set_containers(frm)
    },
    weight(frm){
        set_containers(frm)
    },
    container_type(frm){
        set_containers(frm)
    },
    weight_unit(frm){
        set_containers(frm)
    },
});

frappe.ui.form.on("Schedule and Rate Detail", {
	rate_add(frm,cdt,cdn) {
        var d = locals[cdt][cdn]
        if(frm.doc.doctype=="Shipment Rate"){
            d.function="Rate"
        }
        frm.refresh_field("rate")
	},
    form_render(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frm.set_df_property("rate", "options", d.schedule, frm.doc.name, "schedule_html", d.name)
        frm.set_df_property("rate", "options", d.charge, frm.doc.name, "charge_html", d.name)
        frm.refresh_field("rate")
    },
});
frappe.ui.form.on("Schedule and Rate Item", {
	before_items_remove(frm,cdt,cdn) {
        var d = locals[cdt][cdn]
        var deleted_row = frappe.get_doc(cdt, cdn);
        if(frm.doc.rate){
            for(let item of frm.doc.rate){
                if(item.name==deleted_row.ref_name){
                    item.is_selected=0
                    frm.set_value("is_selected",0)
                    frm.refresh_field("is_selected")
                    break
                }
            }
            frm.set_value("items",[])
            frm.refresh_field("items")
            frm.save()
        }
	},
});

function check_all_fields_filled(frm){
    if (frm.doc.mode == "FCL" && (!frm.doc.origin_service_mode || !frm.doc.destination_service_mode || !frm.doc.container_qty || !frm.doc.container_type || !frm.doc.weight || !frm.doc.weight_unit)){
        return {"function":"Failed","value":"<b>Need to set Service Codes or Container Qty or Container Type or Weight or Weight Unit</b>"}
    }
    if(frm.doc.mode == "LCL" && !(frm.doc.dimensions || (frm.doc.weight && frm.doc.weight_unit && frm.doc.volume && frm.doc.volume_unit))){
        return {"function":"Failed","value":"<b>Need to set Dimensions or Weight, Volume and their units</b>"}
    }
    return {"function":"Success"}
}
function check_existing(frm,doctype){
    frm.call({
        method: "freightify.freightify.doctype.shipment_rate.shipment_rate.check_shedule_and_rate",
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
                method:"freightify.freightify.doctype.shipment_rate.shipment_rate.make_shipment",
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

function set_containers(frm){
    let qty = frm.doc.container_qty ? frm.doc.container_qty : "";
    let weight = frm.doc.weight ? frm.doc.weight : "";
    let container_type = frm.doc.container_type ? frm.doc.container_type : "";
    let weight_unit = frm.doc.weight_unit ? frm.doc.weight_unit : "";
    let containers= String(qty) +"X"+ String(container_type) +"X"+ String(weight) +"X" + String(weight_unit)
    frm.set_value("containers",containers)
    frm.refresh_field("containers")
}

function shipment_rate_item(frm,rate_table,function_name){
	if(rate_table.length>0){
        var selected = 0
		for(var item of rate_table){
            if(item.__checked == 0 && item.is_selected==1){
                item.is_selected=0
            }
			if(item.__checked==1){
                selected = selected + 1
                if(function_name=="selecting"){
                    if(!frm.previous_idx){
                        frm.previous_idx = item.idx
                        cur_frm.fields_dict.rate.grid.data[frm.previous_idx-1].is_selected = 1
                    }else{
                        if(item.idx!=frm.previous_idx){
                            cur_frm.fields_dict.rate.grid.data[frm.previous_idx-1].__checked = 0
                            cur_frm.fields_dict.rate.grid.data[frm.previous_idx-1].is_selected = 0
                            cur_frm.fields_dict.rate.grid.data[item.idx-1].is_selected = 1
                            frm.previous_idx = item.idx
                        }
                    }
                    frm.set_value("is_selected",1)
                    frm.refresh_field("is_selected")
                }
                if(function_name=="fetching"){
                    if(JSON.parse(item.charges_json).length >0){
                        let charge_list=JSON.parse(item.charges_json)
                        frm.call({
                            method: "freightify.freightify.doctype.shipment_rate.shipment_rate.consolidate_item",
                            args: {
                                item:item
                            },
                            freeze:true,
                            freeze_message:"Getting Items",
                            async:true,
                        }).then(r => {
                            if(r.message){
                                for(let item of r.message){
                                    var row=cur_frm.add_child("items")
                                    row.item_code=item.item_code
                                    row.item_name=item.item_name
                                    row.description=item.description
                                    row.ref_name=item.ref_name
                                    row.qty=item.qty
                                    row.uom=item.uom
                                    row.stock_uom=item.stock_uom
                                    row.rate=item.rate
                                    row.buying_rate=item.buying_rate
                                    row.selling_rate=item.selling_rate
                                    row.amount=item.amount
                                    row.buying_amount=item.buying_amount
                                    row.selling_amount=item.selling_amount
                                }
                                frm.save()
                            }
                        })
                    }
                }
			}
		}
        frm.refresh_field("rate")
        if(selected==0){
            frm.set_value("is_selected",0)
            frm.refresh_field("is_selected")
        }
	}
}
