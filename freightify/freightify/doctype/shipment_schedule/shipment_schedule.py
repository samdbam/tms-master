# Copyright (c) 2024, Freightify and contributors
# For license information, please see license.txt

import frappe,json
import requests
from requests.auth import HTTPBasicAuth
from frappe.model.document import Document


class ShipmentSchedule(Document):
	pass


#-----------------------------------------OAUTH2 Authentication------------------------------
@frappe.whitelist()
def OAuth2_authentication(doc):
	self=json.loads(doc)
	self=frappe._dict(self)
	oauth2_url = "https://api.freightify.com/oauth2/token"
	payload = {
		'username': 'test40@freightify.com',
		'password': 'Asfgh@%4!23',
		'grant_type': 'password',
		'scope': ''
	}
	# Define the basic authentication credentials
	username = "ea52ca40-c9f1-11ec-8a52-f1d06bcd2b53"
	password = "rfaGLwBkPjL4PVEpG15Uh1B13opbXE0LMWKMukrY"
	try :
		# Send the POST request
		oauth2_response = requests.post(oauth2_url, data=payload, auth=HTTPBasicAuth(username, password))
		# Check the oauth2_response
		if oauth2_response.status_code == 200:
			bearer=oauth2_response.json()['access_token']
			if self.doctype in ["Purchase Invoice","Sales Invoice"]:
				final_data=get_price(bearer,self)
			if self.doctype in ["Shipment Schedule"]:
				final_data=get_schedules(bearer,self)
			return {"function":"Success","value":final_data}
			
		else:
			frappe.log_error("Error:", oauth2_response.status_code, oauth2_response.text)
	except Exception as e :
		frappe.log_error("Error during Oauth token getting",frappe.get_traceback())
		return {"function":"Failed","values":'Error during Oauth token getting'}

#-----------------------------------------GET PRICES-----------------------------------------------
@frappe.whitelist()
def get_price(bearer,self):
	# Define the URL and parameters
	price_url = "https://api.freightify.com/v3/prices"
	params = {
		'origin': self.origin,
		'destination': self.destination,
		'departureDate': self.departure_date,
		'containers': '1X20GPX25000XKG',
		'mode': 'FCL',
		'originType': 'PORT',
		'destinationType': 'PORT'
	}
	# Define the Bearer token and additional headers
	bearer_token=bearer
	# Define headers
	headers = {
		'Authorization': f'Bearer {bearer_token}',
		'X-api-key': 'ep4kXpuz6d860bZbChjoq7CpzLwpikRY4pLhSghK'
	}
	try:
		# Send the GET request
		response = requests.get(price_url, headers=headers, params=params)
		# Check the response
		if response.status_code == 200:
			return response.json()
		else:
			frappe.log_error("Error:", response.status_code, response.text)
	except Exception as e:
		frappe.log_error("Error during Price getting",frappe.get_traceback())
		return {"function":"Failed","values":'Error during price getting'}

#-----------------------------------------GET SCHEDULES-----------------------------------------------
@frappe.whitelist()
def get_schedules(bearer,self):
	frappe.log_error("get schedule called:")
	url = "https://api.freightify.com/v1/schedules"
	params = {
		'origin': self.origin,
		'destination': self.destination,
		'departureDate': self.departure_date,
		'duration': str(self.duration)
	}
	# Define the Bearer token for authentication
	bearer_token=bearer
	# Define custom headers
	headers = {
		'X-api-key': 'ep4kXpuz6d860bZbChjoq7CpzLwpikRY4pLhSghK',
		'Authorization': f'Bearer {bearer_token}'
	}
	try:
		# Send the GET request
		response = requests.get(url, headers=headers, params=params)
		# Check the response status
		if response.status_code == 200:
			# Convert the JSON response to a Python dictionary
			data = response.json()
			return data
		else:
			frappe.log_error("Error:", response.status_code, response.text)
	except Exception as e:
		frappe.log_error("Error during Schedule getting",frappe.get_traceback())
		return {"function":"Failed","values":'Error during price getting'}
	

#-----------------------------------------QUOTATION AND SALES ORDER-------------------------------------------
@frappe.whitelist()
def make_quotation_sales_order(source_name,target_doc = None , ignore_permissions =False):
	from frappe.model.mapper import get_mapped_doc
	doctype = frappe.flags.args.doctype
	target_doc = get_mapped_doc("Shipment Schedule",source_name,
		{
			"Schedule and Rate Detail": {
				"doctype": "Schedule and Rate Detail",
			},
			"Shipment Schedule": {
                "doctype": doctype,
                "field_map": {
					"shipping_type": "custom_shipping_type",
                    "origin": "custom_origin",
                    "departure_date": "custom_departure_date",
                    "destination": "custom_destination",
                    "duration": "custom_duration",
                    "doctype": "custom_reference_doctype",
                    "name": "custom_reference_name"
                },
            },
		},
		target_doc,
		ignore_permissions=ignore_permissions,
	)
	return target_doc

#----------------------------------------FREIGHTIFY SHIPMENT-------------------------------
@frappe.whitelist()
def make_shipment(source_name,target_doc = None , ignore_permissions =False):
	from frappe.model.mapper import get_mapped_doc
	doctype = frappe.flags.args.doctype
	target_doc = get_mapped_doc("Shipment Schedule",source_name,
		{
			"Schedule and Rate Detail": {
				"doctype": "Schedule and Rate Detail",
			},
			"Shipment Schedule": {
                "doctype": doctype,
                "field_map": {
					"shipping_type": "shipping_type",
                    "origin": "origin",
                    "departure_date": "departure_date",
                    "destination": "destination",
                    "duration": "duration",
                    "doctype": "reference_doctype",
                    "name": "reference_name"
                },
            },
		},
		target_doc,
		ignore_permissions=ignore_permissions,
	)
	return target_doc

@frappe.whitelist()
def check_shedule_and_rate(doc,doctype):
	self=json.loads(doc)
	self=frappe._dict(self)
	if not frappe.db.exists(doctype,{"shipment_schedule":self.name,"docstatus":["!=",2]}):
		return {"function":"Success"}
	else:
		values=frappe.db.exists(doctype,{"shipment_schedule":self.name,"docstatus":["!=",2]},["name"])
		return {"function":"Failed","value":f"{doctype} <b>{values} already present</b> for this Schedule <b>{self.name}</b>"}

  