# Copyright (c) 2024, Freightify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ConsolidatedShipment(Document):
	def before_save(self):
		if self.shipment:
			for ship in self.shipment:
				if not ship.shipment_id :
					shipment_docname = create_freightify_shipment(self,ship)
					if shipment_docname:
						ship.shipment_id = shipment_docname
			
	"""
	def before_submit(self):
		error_count = 0
		error_message = "Need to Submit Freightify Shipment "
		if self.shipment:
			for ship in self.shipment:
				if ship.shipment_id :
					if frappe.db.exists("Freightify Shipment",{"name":ship.shipment_id,"docstatus":0}):
						if error_count > 0 :
							error_message += f",<b>{ship.shipment_id}</b>"
						else:
							error_message += f"<b>{ship.shipment_id}</b>"
						error_count += 1
		if error_count > 0 :
			frappe.throw(error_message)

	def before_cancel(self):
		if self.shipment:
			for ship in self.shipment:
				if ship.shipment_id :
					shipment_doc = frappe.get_doc("Freightify Shipment",ship.shipment_id)
					if shipment_doc.docstatus == 1 :
						shipment_doc.docstatus = 2
						shipment_doc.save(ignore_permissions=True)
			frappe.db.commit()
	"""
					
	def on_update(self):
		delete_shipment_doc(self)

@frappe.whitelist()
def delete_shipment_doc(self):
	if self.docstatus == 0 :
		old_shipment_list = []
		old_doc = self.get_doc_before_save()
		if old_doc:
			if old_doc.shipment:
				for old in old_doc.shipment:
					if old.shipment_id:
						old_shipment_list.append(old.shipment_id)
		if self.shipment:
			for ship in self.shipment:
				if ship.shipment_id in old_shipment_list:
					old_shipment_list.remove(ship.shipment_id)
		if old_shipment_list:
			for docname in old_shipment_list:
				frappe.delete_doc("Freightify Shipment",docname)



@frappe.whitelist()
def create_freightify_shipment(self,ship):
	freightify_shipment_doc = frappe.new_doc("Freightify Shipment")
	freightify_shipment_doc.shipping_type = "Ocean Import"
	freightify_shipment_doc.consolidated_shipment_ref = self.name
	if ship.consignee:
		freightify_shipment_doc.oversea_agent = ship.consignee
	if ship.consignor:
		freightify_shipment_doc.forwarding_agent = ship.consignor
	if ship.origin:
		freightify_shipment_doc.port_of_loading = ship.origin
	if ship.destination:
		freightify_shipment_doc.port_of_discharge = ship.destination
	if ship.etd:
		freightify_shipment_doc.etd = ship.etd
	if ship.eta:
		freightify_shipment_doc.place_of_delivery_eta = ship.eta
	if ship.house_bill:
		row = freightify_shipment_doc.append("hbl",{})
		row.hbl_no =ship.house_bill
	freightify_shipment_doc.insert(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_links=True, # ignore Link validation in the document
		ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
		ignore_mandatory=True # insert even if mandatory fields are not set
	)
	frappe.db.commit()
	return freightify_shipment_doc.name


@frappe.whitelist()
def get_agent_address_contact(doctype,docname):
	address = get_address(doctype,docname)
	contact = get_contact(doctype,docname)
	return [address,contact]
	

@frappe.whitelist()
def get_address(doctype,docname):
	address = frappe.db.sql(f"""
			SELECT
				A.name,A.address_line1,A.city,A.state,A.country,A.pincode
			FROM
				`tabAddress` A
			INNER JOIN
				`tabDynamic Link` DL
			ON
				A.name = DL.parent
			WHERE
				DL.link_doctype = %s
			AND
				DL.link_name = %s
	""",(doctype,docname),as_dict=1)
	address_value = ""
	if address:
		address_value = get_address_contact_value(obj=address[0])
	return address_value

@frappe.whitelist()
def get_contact(doctype,docname):
	contact = frappe.db.sql(f"""
			SELECT
				C.email_id,C.phone
			FROM
				`tabContact` C
			INNER JOIN
				`tabDynamic Link` DL
			ON
				C.name = DL.parent
			WHERE
				DL.link_doctype = %s
			AND
				DL.link_name = %s
	""",(doctype,docname),as_dict=1)
	contact_value = ""
	if contact :
		contact_value = get_address_contact_value(obj=contact[0])
	return contact_value



@frappe.whitelist()
def get_address_contact_value(obj):
	address_contact_value = ""
	for key,value in obj.items():
		address_contact_value += str(value) + "\n"
	return address_contact_value