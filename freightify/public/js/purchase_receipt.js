frappe.ui.form.on("Schedule and Rate Detail",{
    form_render(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frm.set_df_property("custom_schedule_and_rate", "options", d.schedule, frm.doc.name, "schedule_html", d.name)
        frm.set_df_property("custom_schedule_and_rate", "options", d.charge, frm.doc.name, "charge_html", d.name)
        frm.refresh_field("custom_schedule_and_rate")
    },
})