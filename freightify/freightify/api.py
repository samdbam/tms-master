import frappe,json
import requests
from requests.auth import HTTPBasicAuth

@frappe.whitelist()
def make_shipment(source_name,target_doc = None , ignore_permissions =False):
    from frappe.model.mapper import get_mapped_doc
    doctype = frappe.flags.args.doctype
    target_doc = get_mapped_doc("Sales Order",source_name,
        {
            "Schedule and Rate Detail": {
                "doctype": "Schedule and Rate Detail",
            },
            "Sales Order Item": {
                "doctype": "Sales Order Item",
            },
            "Sales Order": {
                "doctype": doctype,
                "field_map":{
                    "custom_shipping_type":"shipping_type",
                    "custom_origin":"origin",
                    "custom_destination":"destination",
                    "custom_departure_date":"departure_date",
                    "custom_duration":"duration",
                    "custom_reference_doctype":"reference_doctype",
                    "custom_reference_name":"   reference_name",
                    "company":"   company"
                }
            },
        },
        target_doc,
        ignore_permissions=ignore_permissions,
    )
    shipped_count=0
    deleted_row=[]
    for order in target_doc.items:
        if order.qty > order.custom_shipped_qty:
            shipped_qty= order.custom_shipped_qty if order.custom_shipped_qty  else 0
            order.qty = order.qty - shipped_qty
            shipped_count +=1
        else:
            del_obj=frappe._dict({
                "idx":order.idx,
                "item_code":order.item_code
            })
            deleted_row.append(del_obj)
    for row in deleted_row:
        for order in target_doc.items:
            if row.idx==order.idx and row.item_code==order.item_code:
                target_doc.items.remove(order)
    if shipped_count > 0:
        return target_doc
    else:
        frappe.throw(f"All items are shipped in Sales Order <b>{source_name}</b>")

@frappe.whitelist()
def before_submit_sales_order(doc,method=None):
    if doc.items:
        for order in doc.items:
            order.custom_sales_order = doc.name
  
#------------------------CREATE ITEM FOR QUOTATION SALES ORDER----------------------------------------
@frappe.whitelist()
def consolidate_item(table,doctype):
    table=json.loads(table)
    consolidate_item_list=[]
    for item in table:
        item=frappe._dict(item)
        if item.__checked==1 and len(item.charges_json)>0:
            for charge in json.loads(item.charges_json):
                charge=frappe._dict(charge)
                charges_list=charge.rate_type_base_charges
                if len(charges_list)>0:
                    for charge in charges_list:
                        charge=frappe._dict(charge)
                        consolidate_item_obj=frappe._dict({})
                        if not frappe.db.exists("Item",{"item_code":charge.charge_code,"is_stock_item":0,"disabled":0}):
                            create_item(charge)
                        consolidate_item_obj["item_code"]=charge.charge_code
                        consolidate_item_obj["item_name"]=charge.charge_name
                        consolidate_item_obj["description"]=charge.charge_name
                        consolidate_item_obj["uom"]="Nos"
                        consolidate_item_obj["stock_uom"]="Nos"
                        consolidate_item_obj["qty"]=charge.qty
                        if doctype in ["Quotation","Sales Order","Freightify Shipment"]:
                            consolidate_item_obj["rate"]=charge.sell_rate_usd
                            consolidate_item_obj["amount"]=charge.sell_amount_usd
                        if doctype in ["Purchase Order","Request for Quotation","Supplier Quotation"]:
                            consolidate_item_obj["rate"]=charge.buy_rate_usd
                            consolidate_item_obj["amount"]=charge.buy_amount_usd
                        # consolidate_item_obj["buying_rate"]=charge.buy_rate_usd
                        # consolidate_item_obj["buying_amount"]=charge.buy_amount_usd
                        # consolidate_item_obj["selling_rate"]=charge.sell_rate_usd
                        # consolidate_item_obj["selling_amount"]=charge.sell_amount_usd
                        consolidate_item_obj["ref_name"]=item.rate_id
                        consolidate_item_list.append(consolidate_item_obj)
    if consolidate_item_list:
        return {"function":"Success","value":consolidate_item_list}
    else:
        return {"function":"Failed","value":f"Charges are <b>not available</b>"}

def create_item(charge):
	item_doc=frappe.new_doc("Item")
	item_doc.item_code=charge.charge_code
	item_doc.item_name=charge.charge_name
	item_doc.item_group="Services"
	item_doc.stock_uom="Nos"
	item_doc.description=charge.charge_name
	item_doc.is_stock_item=0
	item_doc.disabled=0
	conversion_factor_row=item_doc.append("uoms",{})
	conversion_factor_row.uom="Nos"
	conversion_factor_row.conversion_factor=1
	item_doc.insert()
	frappe.db.commit()


