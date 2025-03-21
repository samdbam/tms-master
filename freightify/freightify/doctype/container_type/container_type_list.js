frappe.listview_settings['Container Type'] = {
    refresh(listview,frm){
        listview.page.add_inner_button("Get Container Type",function(){
            console.log("button clicked")
            frappe.call({
                method: "freightify.freightify.doctype.shipment_rate.shipment_rate.OAuth2_authentication",
                args:{
                    doctype:"Container Type"
                },
                async:true,
                freeze:true,
                freeze_message:"Getting all Container Types",
                callback : function(r){
                    console.log("container_type",r.message);
                    if(r.message.function == "Failed"){
                        frappe.throw(r.message.value)                    }
                    if(r.message.function == "Success"){
                        frappe.show_alert({ message: r.message.value, indicator: "green" }, 5)
                    }
                }
            })
        });
    }
}