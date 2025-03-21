# Copyright (c) 2024, Freightify and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document

#-------FOR CONSOLIDATED SO------------------------------
import frappe.utils

from frappe.model.mapper import get_mapped_doc


class FreightifyShipment(Document):
	def before_submit(self):
		update_shipped_qty_in_so(method="before_submit",self=self)
		
	def before_cancel(self):
		update_shipped_qty_in_so(method="before_cancel",self=self)


def update_shipped_qty_in_so(method,self):
	if self.items:
		so_obj={}
		for shipment in self.items:
			if shipment.custom_sales_order and shipment.custom_sales_order not in so_obj.keys():
				so_obj[shipment.custom_sales_order]=[]
				so_obj[shipment.custom_sales_order].append(shipment)
			elif shipment.custom_sales_order and shipment.custom_sales_order  in so_obj.keys():
				so_obj[shipment.custom_sales_order].append(shipment)
		if so_obj:
			for key,value in so_obj.items():
				so_count=0
				total_shipped_qty=0
				so_doc=frappe.get_doc("Sales Order",key)
				for order in so_doc.items:
					if so_doc and so_doc.items:
						for shipment in value:
							if shipment.item_code == order.item_code:
								if method in ["before_submit"]:
									shipped_qty=order.custom_shipped_qty + shipment.qty
									if shipped_qty > order.qty:
										frappe.throw(f"Shipped Qty is <b>Exceeding</b> its <b>Order Qty</b> for item <b>{order.item_name}</b> in Sales Order <b>{key}</b>")
									order.custom_shipped_qty=shipped_qty
								if method in ["before_cancel"]:
									shipped_qty=order.custom_shipped_qty - shipment.qty
									order.custom_shipped_qty=shipped_qty
								so_count +=1
								total_shipped_qty +=shipped_qty
								break
				if so_count>0:
					total_shipped_percentage = (total_shipped_qty/so_doc.total_qty)*100
					so_doc.custom_total_shipped_qty=total_shipped_qty
					so_doc.custom_per_shipped=total_shipped_percentage
					so_doc.save(ignore_permissions=True)
			frappe.db.commit()
	
@frappe.whitelist()
def make_freightify_shipment(source_name, target_doc=None, ignore_permissions=False):
    def update_item(source, target, source_parent):
        target.qty = source.qty -  source.custom_shipped_qty
        target.item_code = source.item_code
        target.item_name = source.item_name
        target.uom = source.uom
        target.rate = source.rate
        target.amount = source.amount
        target.custom_shipped_qty = source.custom_shipped_qty
    doclist = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Freightify Shipment",
            },
            "Sales Order Item": {
                "doctype": "Sales Order Item",
                "postprocess": update_item,
                "condition": lambda doc: doc.qty > doc.custom_shipped_qty,
            },
        },
        target_doc,
        ignore_permissions=ignore_permissions,
    )
    return doclist

@frappe.whitelist()
def check_shipment_shedule_and_rate(doc,doctype):
	self=json.loads(doc)
	self=frappe._dict(self)
	if not frappe.db.exists(doctype,{"reference_doctype":"Freightify Shipment","reference_name":self.name,"docstatus":["!=",2]}):
		return {"function":"Success"}
	else:
		values=frappe.db.get_value(doctype,{"reference_doctype":"Freightify Shipment","reference_name":self.name},["name"])
		return {"function":"Failed","value":f"{doctype} <b>{values} already present</b> for this Shipment <b>{self.name}</b>"}
	
@frappe.whitelist()
def get_item_detail(item_code):
	item_details=frappe.db.get_value("Item",item_code,['item_name','stock_uom'],as_dict=True)
	if item_details :
		return {"function":"Success",'value':item_details}
	else:
		return {"function":"Failed",'value':f"<b>Item Name and UOM</b> not found for Item Code <b>{item_code}</b>"}

@frappe.whitelist()
def consolidate_shipment_item(table,doctype):
    table=json.loads(table)
    consolidate_item_list=[]
    for item in table:
        item=frappe._dict(item)
        if item.is_selected==1 and len(item.charges_json)>0:
            for charge in json.loads(item.charges_json):
                charge=frappe._dict(charge)
                charges_list=charge.rate_type_base_charges
                if len(charges_list)>0:
                    for charge in charges_list:
                        charge=frappe._dict(charge)
                        consolidate_item_obj=frappe._dict({})
                        # if not frappe.db.exists("Item",{"item_code":charge.charge_code,"is_stock_item":0,"disabled":0}):
                        #     create_item(charge)
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