frappe.listview_settings['Port'] = {
    refresh(listview,frm){
        listview.page.add_inner_button("Get Port",function(){
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Contry',
                        fieldname: 'country',
                        fieldtype: 'Link',
                        options:"Country",
                        reqd:1
                    },
                    {
                        label: 'Mode',
                        fieldname: 'mode',
                        fieldtype: 'Select',
                        options:["SEA-FCL","SEA-LCL"],
                        reqd:1
                    },
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: "freightify.freightify.doctype.shipment_rate.shipment_rate.OAuth2_authentication",
                        args:{
                            doctype:"Port",
                            country:values.country,
                            mode:values.mode
                        },
                        async:true,
                        freeze:true,
                        freeze_message:"Getting all Ports",
                        callback : function(r){
                            if(r.message.function == "Failed"){
                                frappe.throw(r.message.value)                    }
                            if(r.message.function == "Success"){
                                frappe.show_alert({ message: r.message.value, indicator: "green" }, 5)
                            }
                        }
                    })
                    d.hide();
                }
            });
            d.show();
        });
    }
}