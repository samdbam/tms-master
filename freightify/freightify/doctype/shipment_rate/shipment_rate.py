# Copyright (c) 2024, Freightify and contributors
# For license information, please see license.txt

import frappe,json
import requests
from requests.auth import HTTPBasicAuth
from frappe.model.document import Document


class ShipmentRate(Document):
	def before_submit(self):
		if self.reference_doctype and self.reference_name:
			doc=frappe.get_doc(self.reference_doctype,self.reference_name)
			if self.reference_doctype == "Freightify Shipment":
				doc.shipping_type=self.shipping_type
				doc.origin=self.origin
				doc.destination=self.destination
				doc.departure_date=self.departure_date
				doc.duration=self.duration
				doc.schedule_and_rate=self.rate
				doc.reference_doctype="Shipment Rate"
				doc.reference_name=self.name
				doc.update({"schedule_and_rate":self.rate})
				doc.save(ignore_permissions=True)
			else:
				if not doc.custom_reference_doctype and not doc.custom_reference_name:
					doc.custom_shipping_type=self.shipping_type
					doc.custom_origin=self.origin
					doc.custom_destination=self.destination
					doc.custom_departure_date=self.departure_date
					doc.custom_duration=self.duration
					doc.custom_schedule_and_rate=self.rate
					doc.custom_reference_doctype="Shipment Rate"
					doc.custom_reference_name=self.name
					doc.update({"custom_schedule_and_rate":self.rate})
					doc.save(ignore_permissions=True)

#-----------------------------------------OAUTH2 Authentication------------------------------
@frappe.whitelist()
def OAuth2_authentication(doc=None,doctype=None,country=None,mode=None):
	if doc:
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
		frappe.log_error("oauth2_response",oauth2_response)
		if oauth2_response.status_code == 200:
			bearer=oauth2_response.json()['access_token']
			if doctype in ["Carrier","Container Type","Port"] :
				final_data = get_all_documents(bearer,doctype,country=country,mode=mode)
				if final_data["function"] == "Success":
					message = create_documents_long_jobs(data=final_data["value"],doctype=doctype)
					return message
				else:
					return final_data
			if self.doctype in ["Shipment Rate"]:
				final_data=get_price(bearer,self)
			if self.doctype in ["Shipment Schedule"]:
				final_data=get_schedules(bearer,self)
			if self.doctype in ["Freightify Shipment"]:
				final_tracking_data = frappe._dict({})
				for track in self.container:
					track = frappe._dict(track)
					making_freightify_shipment(self,track,final_tracking_data,bearer)
				if final_tracking_data:
					return {"function":"Success","value":final_tracking_data}
				else:
					return {"function":"Failed","value":"<b>Schedules and Rates are not available</b>"}
			if final_data:
				final_data=frappe._dict(final_data)
				# return {"function":"Success","value":final_data}
				if len(final_data.offers)>0:
					final_list=[]
					for data in final_data.offers:
						making_shipment_rate(final_list=final_list,data=data,final_data=final_data)
					return {"function":"Success","value":final_list}
				else:
					return {"function":"Failed","value":"<b>Schedules and Rates are not available</b>"}
			else:
				return {"function":"Failed","value":"<b>Schedules and Rates are not available</b>"}
		else:
			frappe.log_error("Error during Oauth token getting",frappe.get_traceback())
			return {"function":"Failed","value":'Error during Oauth token getting'}
	except Exception as e :
		frappe.log_error("Error during Oauth token getting",frappe.get_traceback())
		return {"function":"Failed","value":'Error during Oauth token getting'}

@frappe.whitelist()
def making_freightify_shipment(self,track,final_tracking_data,bearer):
	if track.container_no not in final_tracking_data.keys():
		tracking_data=get_tracking_data(bearer,self,containerId=track.container_no,sealine=track.carrier)
		if tracking_data:
			frappe.log_error("tracking data",tracking_data)
			# return {"function":"Success","value":tracking_data}
			if "locations" in tracking_data.keys():
				tracking_data = frappe._dict(tracking_data)
				tracking_result = create_tracking_table(data=tracking_data)
				final_tracking_data[track.container_no] = tracking_result
			else:
				tracking_result = create_empty_table(data="Tracking Status")
				final_tracking_data[track.container_no] = tracking_result
		else:
			tracking_result = create_empty_table(data="Tracking Status")
			final_tracking_data[track.container_no] = tracking_result

@frappe.whitelist()
def making_shipment_rate(final_list,data,final_data):
	final_obj=frappe._dict({})
	final_obj["port_of_origin"]=data["productOffer"]["originPort"]
	final_obj["port_of_destination"]=data["productOffer"]["destinationPort"]
	final_obj["carrier_name"]=data["productOffer"]["carrierName"]
	final_obj["carrier_code"]=data["productOffer"]["carrierScac"]
	final_obj["transit_time"]=data["productPrice"]["transitTimeInDays"]
	final_obj["service_type"]=data["productPrice"]["serviceType"]
	final_obj["rate_id"]=data["freightifyId"]
	final_obj["sailing_date"]=data["productPrice"]["sailingDate"]
	final_obj["buy_rate"]=data["productPrice"]["totalUSDAmount"]["BUY"]
	final_obj["sell_rate"]=data["productPrice"]["totalUSDAmount"]["SELL"]
	final_obj["effective_from"]=data["productPrice"]["validFrom"]
	final_obj["effective_to"]=data["productPrice"]["validTo"]
	final_obj["incoterm"]="-"
	final_obj["cargo_type"]=data["productPrice"]["cargoType"]
	final_obj["commodity"]=data["productPrice"]["commodity"]
	final_obj["remarks"]=data["productPrice"]["commodity"]
	final_obj["inclusions"]=data["productPrice"]["commodity"]
	line_schedules=consolidate_schedules(schedules=data["productPrice"],data=final_data)
	final_obj["schedule_json"]=line_schedules[0]
	final_obj["schedule"]=line_schedules[1]
	line_charges=consolidate_charges(charges=data["productPrice"]["charges"])
	final_obj["charges_json"]=line_charges[0]
	final_obj["charge"]=line_charges[1]
	final_list.append(final_obj)
#----------------------------------------GET CARRIERS,CONTAINER TYPE----------------------------------------------
@frappe.whitelist()
def get_all_documents(bearer,doctype,country=None,mode=None):
	# Define the URL and parameters
	if doctype == "Carrier":
		api_url = "https://api.freightify.com/v1/carriers"
		params = {
			'isTrackingAvailable': "null",
		}
	if doctype == "Container Type":
		api_url = "https://api.freightify.com/v1/load-types"
		params = {}
	
	if doctype == "Port":
		api_url = "https://api.freightify.com/v1/sea-ports"
		country_code = frappe.db.get_value("Country",country,["code"]).upper()
		params = {
			'countryCode': country_code,
			'mode':mode,
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
		response = requests.get(api_url, headers=headers, params=params)
		# Check the response
		if response.status_code == 200:
			return {"function":"Success","value":response.json()}
		else:
			frappe.log_error("Error:", [response.status_code, response.text])
			return {"function":"Failed","value":f'Error during {doctype} getting'}
	except Exception as e:
		frappe.log_error(f"Error during {doctype} getting",frappe.get_traceback())
		return {"function":"Failed","value":f'Error during {doctype} getting'}
	
@frappe.whitelist()
def create_documents_long_jobs(data,doctype):
	try:
		if data:
			for item in data:
				if doctype == "Carrier":
					if not frappe.db.exists("Carrier",{"carrier_code":item["scacCode"],"carrier_name":item["scacName"]}):
						create_carrier_document(item)
				if doctype == "Container Type":
					if not frappe.db.exists("Container Type",{"code":item["code"],"iso_code":item["isoCode"]}):
						create_container_type_document(item)
				if doctype == "Port":
					if not frappe.db.exists("Port",{"code":item["unLoCode"]}) and item["unLoCode"]:
						try:
							frappe.enqueue("freightify.freightify.doctype.shipment_rate.shipment_rate.create_port_document",queue="long",param=item)
						except Exception as e:
							return {"function":"Failed","value":"Port Creating Long Job Failed"}
			frappe.db.commit()
			return {"function":'Success','value':f'All {doctype}s are fetched Successfully'}
	except Exception as e:
		return {"function":"Failed","value":f"<b>Create {doctype} Function Failed</b>"}
	
@frappe.whitelist()	
def create_carrier_document(item):
	carrier_doc = frappe.new_doc('Carrier')
	carrier_doc.carrier_code = item["scacCode"]
	carrier_doc.carrier_name = item["scacName"]
	carrier_doc.insert(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_links=True, # ignore Link validation in the document
		ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
		ignore_mandatory=True # insert even if mandatory fields are not set
	)

@frappe.whitelist()
def create_container_type_document(item):
	container_type_doc = frappe.new_doc('Container Type')
	container_type_doc.code = item["code"]
	container_type_doc.iso_code = item["isoCode"]
	container_type_doc.description = item["description"]
	container_type_doc.minkgs = item["minKGS"]
	container_type_doc.mincbm = item["minCBM"]
	container_type_doc.insert(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_links=True, # ignore Link validation in the document
		ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
		ignore_mandatory=True # insert even if mandatory fields are not set
	)

@frappe.whitelist()
def create_port_document(param):
	item = param
	port_doc = frappe.new_doc('Port')
	port_doc.port_code=item['unLoCode']
	port_doc.port_name=item['siteName']
	port_doc.city_name=item['cityName']
	port_doc.type=item['type']
	port_doc.location=item['location']
	port_doc.country_name=item['countryName']
	port_doc.country_code=item['countryCode']
	port_doc.region_name=item['regionName']
	port_doc.region_code=item['regionCode']
	port_doc.latitude=item['latitude']
	port_doc.longitude=item['longitude']
	port_doc.insert(
		ignore_permissions=True, # ignore write permissions during insert
		ignore_links=True, # ignore Link validation in the document
		ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
		ignore_mandatory=True # insert even if mandatory fields are not set
	)


#-----------------------------------------GET PRICES-----------------------------------------------
@frappe.whitelist()
def get_price(bearer,self):
	# Define the URL and parameters
	price_url = "https://api.freightify.com/v3/prices"
	params = {
		'origin': self.origin,
		'destination': self.destination,
		'departureDate': self.departure_date,
		'mode': self.mode,
		'originType': self.origin_type,
		'destinationType': self.destination_type
	}
	if self.mode == "FCL":
		params["containers"]=self.containers
		params["originServiceMode"]=self.origin_service_mode
		params["destinationServiceMode"]=self.destination_service_mode
	if self.mode == "LCL":
		if self.dimensions :
			params["dimensions"]=self.dimensions
		if self.weight and self.weight_unit:
			params["totalWeight"]=f"{self.weight}X{self.weight_unit}"
		if self.volume and self.volume_unit:
			params["totalVolume"]=f"{self.volume}X{self.volume_unit}"
		
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
			frappe.log_error("Error:", [response.status_code, response.text])
	except Exception as e:
		frappe.log_error("Error during Price getting",frappe.get_traceback())
		return {"function":"Failed","value":'Error during price getting'}
	
#----------------------------------------GET TRACKING STATUS--------------------------------------
@frappe.whitelist()
def get_tracking_data(bearer,self,containerId,sealine):
	# Define the URL and parameters
	tracking_status_url = f"https://api.freightify.com/v1/track/container/{containerId}"
	params = {
		'sealine': sealine,
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
		response = requests.get(tracking_status_url, headers=headers, params=params)
		# Check the response
		if response.status_code == 200:
			return response.json()
		else:
			frappe.log_error("Error:", [response.status_code, response.text])
	except Exception as e:
		frappe.log_error("Error during Tracking Status getting",frappe.get_traceback())
		return {"function":"Failed","value":'Error during Tracking Status getting'}

#-----------------------------------------GET SCHEDULES-----------------------------------------------
@frappe.whitelist()
def get_schedules(bearer,self):
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
			frappe.log_error("Error:", [response.status_code, response.text])
	except Exception as e:
		frappe.log_error("Error during Schedule getting",frappe.get_traceback())
		return {"function":"Failed","value":'Error during Schedules getting'}
	
#---------------------------CONSOLIDATE TRACKING AND STATUS---------------------------------
@frappe.whitelist()
def create_tracking_table(data):
	eta = convert_date(date_str=data.container["sailingInfo"][-1]["date"])
	departure = convert_date(date_str=data.container["sailingInfo"][0]["date"])
	created_on = convert_date(date_str=frappe.utils.today())
	schedule_list = data.schedule.keys()
	point_of_loading = [item for item in schedule_list if "Pol" in item]
	point_of_discharge = [item for item in schedule_list if "Pod" in item]
	pol = ""
	pod = ""
	if point_of_loading:
		for loading in point_of_loading:
			if pol == "":
				pol += data.locations[data.schedule[loading]["location"]-1]["name"]
			else:
				pol = pol + "," + data.locations[data.schedule[loading]["location"]-1]["name"]
	if point_of_discharge:
		for discharge in point_of_discharge:
			if pod == "":
				pod += data.locations[data.schedule[discharge]["location"]-1]["name"]
			else:
				pod = pod + "," + data.locations[data.schedule[discharge]["location"]-1]["name"]
	
	style = "style='border-collapse: collapse; border: 1px solid black; padding:10px;'"
	content = f"""
	<div class="card" style="border: 1px solid #ccc; border-radius: 8px; padding:15px;margin:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
		<div class="card-body">
			<div style=" border-radius: 10px; width:100%; margin:auto;  padding: 15px; text-align: left;float:right; display:flex;">
				<div style="margin:auto;">
					<p class='text_muted'>Container Number</p>
					<strong><p>{data.container["number"]}</p></strong>
				</div>
				<div style="margin:auto;">
					<p class='text_muted'>POL</p>
					<strong><p>{pol}</p></strong>
				</div>
				<div style="margin:auto;">
					<p class='text_muted'>POD</p>
					<strong><p>{pod}</p></strong>
				</div>
				<div style="margin:auto;">
					<p class='text_muted'>ETA</p>
					<strong><p>{eta}</p></strong>
				</div>
				<div style="margin:auto;">
					<p class='text_muted'>Departure Date</p>
					<strong><p>{departure}</p></strong>
				</div>
			</div>
			<h5><strong>MILESTONE</strong></h5>
			<div style=" border-radius: 10px;text-align: center;">
				<table {style}>
					<thead {style}>
						<tr {style}>
							<th {style}>Milestones</th>
							<th {style}>Location</th>
							<th {style}>Vessel Name</th>
							<th {style}>Planned Date</th>
							<th {style}>Actual Date</th>
						</tr>
					</thead>
					<tbody>
	"""
	for item in data.container["sailingInfo"]:
		item = frappe._dict(item)
		if item.vessel:
			vessel = data.vessels[(item.vessel)-1]["name"]
		else:
			vessel = "-"
		formatted_date = convert_date(date_str=item.date)
		content += f"""
				<tr {style}>
					<td {style}><strong>{item.description}</strong></td>
					<td {style}><strong>{data.locations[(item.location)-1]["name"]},{data.locations[(item.location)-1]["country"]}</strong></td>
					<td {style}><strong>{vessel}</strong></td>
					<td {style}><strong>{formatted_date}</strong></td>
					<td {style}><strong>{formatted_date}</strong></td>
				</tr>
		"""
	content += "</table></div>"
	content += f"""
				<div style=" border-radius: 10px; width:100%; margin:auto;  padding: 15px;justify-content:space-between; text-align: left;float:right; display:flex;">
					<div style="margin:auto;">
						<p class='text_muted'>Created On</p>
						<strong><p>{created_on}</p></strong>
					</div>
					<div style="margin:auto;">
						<p class='text_muted'>Created By</p>
						<strong><p>{frappe.session.user}</p></strong>
					</div>
				</div>
				</div></div>
				"""
	return content

#----------------------------CONSOLIDATE CHARGES--------------------------------------------

@frappe.whitelist()
def consolidate_charges(charges):
	charges_list=[]
	for charge in charges:
		charges_obj=frappe._dict({})
		if charges_list:
			charge_present=0
			for present in charges_list:
				if present.rate_type_code == charge["rateTypeCode"]:
					charge_code_present=0
					for value in present.rate_type_base_charges:
						if value.charge_code == charge["chargeCode"]:
							if charge["rateType"] == "BUY":
								value["buy_rate_usd"]=charge["rateUsd"]
								value["buy_amount_usd"]=charge["amountUsd"]
							if charge["rateType"] == "SELL":
								value["sell_rate_usd"]=charge["rateUsd"]
								value["sell_amount_usd"]=charge["amountUsd"]
								if "rate_type_code_total" in present.keys():
									present["rate_type_code_total"] +=charge["amountUsd"]
								else:
									present["rate_type_code_total"] =charge["amountUsd"]
							charge_code_present += 1
							break
					if charge_code_present==0:
						charge_code_obj=rate_type_base_charges_obj(charge,present=present)
						present.rate_type_base_charges.append(charge_code_obj)
					charge_present += 1
					break
			if charge_present == 0:
				create_charge_obj(charges_list=charges_list,charges_obj=charges_obj,charge=charge)
		else:
			create_charge_obj(charges_list=charges_list,charges_obj=charges_obj,charge=charge)
	if charges_list:
		final_div=""
		for table in charges_list:
			content=""
			message= create_charges_table(content=content,table=table)
			final_div +=message
		return [charges_list , final_div]
	

@frappe.whitelist()
def create_charge_obj(charges_list,charges_obj,charge):
	charges_obj["rate_type_code"]=charge["rateTypeCode"]
	charges_obj["rate_currency"]=charge["rateCurrency"]
	if charge["rateType"] == "SELL":
		charges_obj["rate_type_code_total"] =charge["amountUsd"]
	charges_obj["rate_type_base_charges"]=[]
	charge_code_obj=rate_type_base_charges_obj(charge)
	charges_obj["rate_type_base_charges"].append(charge_code_obj)
	charges_list.append(charges_obj)

@frappe.whitelist()
def rate_type_base_charges_obj(charge,present=None):
	charge_code_obj=frappe._dict({})
	charge_code_obj["charge_code"]=charge["chargeCode"]
	charge_code_obj["charge_name"]=charge["aggregatedChargeCode"]
	charge_code_obj["rate_currency"]=charge["rateCurrency"]
	charge_code_obj["rate_basis"]=charge["rateBasis"]
	charge_code_obj["container_type"]=charge["containerType"]
	charge_code_obj["qty"]=charge["qty"]
	charge_code_obj["rate_type"]=charge["rateType"]
	if charge["rateType"] == "BUY":
		charge_code_obj["buy_rate_usd"]=charge["rateUsd"]
		charge_code_obj["buy_amount_usd"]=charge["amountUsd"]
	if charge["rateType"] == "SELL":
		charge_code_obj["sell_rate_usd"]=charge["rateUsd"]
		charge_code_obj["sell_amount_usd"]=charge["amountUsd"]
		if "rate_type_code_total" in present.keys():
			present["rate_type_code_total"] +=charge["amountUsd"]
		else:
			present["rate_type_code_total"] =charge["amountUsd"]
	return charge_code_obj

@frappe.whitelist()
def create_charges_table(content,table):
	style = "style='border-collapse: collapse; border: 1px solid black;width:100%; padding:5px;'"
	content = f"""
		<div class="card" style="border: 1px solid #ccc; border-radius: 8px; padding: 15px;margin:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
			<div class="card-body">
				<div style='display: flex;justify-content: space-between;'>
					<div><b>{table.rate_type_code}</b></div>
					<div text-align: right; margin-right:5px;'>Sub Total <span><strong>{table.rate_currency}</strong></span> <span>{table.rate_type_code_total}</span></div>
				</div>
				<table {style}>
					<thead {style}>
						<tr {style}>
							<th {style}>Charges</th>
							<th {style}>Basis</th>
							<th {style}>Equipment Type</th>
							<th {style}>Quantity</th>
							<th {style}>Buying Currency</th>
							<th {style}>Buy Rate</th>
							<th {style}>Buy Amount</th>
							<th {style}>Selling Currency</th>
							<th {style}>Sell Rate</th>
							<th {style}>Sell Amount</th>
						</tr>
					</thead>
					<tbody>
	"""
	for item in table.rate_type_base_charges:
		content += f"""
			<tr {style}>
				<td {style}>{item.charge_name}</td>
				<td {style}>{item.rate_basis.replace("_", " ")}</td>
				<td {style}>{item.container_type}</td>
				<td {style}>{item.qty}</td>
				<td {style}>{item.rate_currency}</td>
				<td {style}>{item.buy_rate_usd}</td>
				<td {style}>{item.buy_amount_usd}</td>
				<td {style}>{item.rate_currency}</td>
				<td {style}>{item.sell_rate_usd}</td>
				<td {style}>{item.sell_amount_usd}</td>
			</tr>
		"""
	content += """
					</tbody>
				</table>
			</div>
		</div>
	"""
	return content

#------------------------------CONSOLIDATE SCHEDULES--------------------------------------------------
def consolidate_schedules(schedules,data):
	if len(schedules["routeScheduleIds"])>0:
		schedule_list=[]
		presented_schedule_id_list = []
		for schedule in schedules["routeScheduleIds"]:
			if not schedule_list or schedule not in presented_schedule_id_list :
				schedule_obj=frappe._dict({})
				schedule_details=data["schedules"][schedule]["scheduleDetails"]
				schedule_obj["transit_time"]=data["schedules"][schedule]["transitTime"]
				schedule_obj["origin"]=data["schedules"][schedule]["fromLocation"]["unLocCode"]
				schedule_obj["start_date"]=data["schedules"][schedule]["fromLocation"]["departure"]
				schedule_obj["destination"]=data["schedules"][schedule]["toLocation"]["unLocCode"]
				schedule_obj["end_date"]=data["schedules"][schedule]["toLocation"]["arrival"]
				schedule_obj["route"]=[]	
				if len(schedule_details):
					for detail in schedule_details:
						detail_obj=frappe._dict({})
						detail_obj["departure"]=detail["fromLocation"]["departure"]
						detail_obj["departure_port"]=detail["fromLocation"]["unLocCode"]
						detail_obj["arrival"]=detail["toLocation"]["arrival"]
						detail_obj["arrival_port"]=detail["toLocation"]["unLocCode"]
						detail_obj["service"]=detail["serviceCode"]
						detail_obj["vessel"]=detail["transport"]["vessel"]["name"]
						detail_obj["voyage_number"]=detail["transport"]["voyageNumber"]
						schedule_obj["route"].append(detail_obj)
				schedule_list.append(schedule_obj)
				presented_schedule_id_list.append(schedule)
		if schedule_list:
			if schedule_list:
				final_div=""
				for table in schedule_list:
					content=""
					message= create_schedule_table(content=content,table=table)
					final_div +=message
				return [schedule_list , final_div]

	else:
		schedule_list = []
		final_div=create_empty_table(data="Schedules")
		return [schedule_list , final_div]

@frappe.whitelist()
def create_empty_table(data):
	content = f"""
		<div class="card" style="border: 1px solid #ccc; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
			<div class="card-body">
				<h4>{data} Not Found</h4>
			</div>
		</div>
	"""
	return content

from datetime import datetime
def convert_date(date_str):
	# Define possible input formats
	input_formats = [
		'%Y-%m-%d %H:%M:%S',
		'%Y-%m-%dT%H:%M:%S.%f',
		'%Y-%m-%d'
	]
	# Try to parse the date string using the defined formats
	given_format =""
	for fmt in input_formats:
		try:
			date_obj = datetime.strptime(date_str, fmt)
			given_format =fmt
			break
		except ValueError:
			continue
	else:
		raise ValueError(f"Date format of '{date_str}' is not supported.")

	# Define the output format
	if given_format == '%Y-%m-%d' :
		output_format = '%d %b %Y\n%a'
	else:
		output_format = '%d %b %Y\n%H:%M\n%a'
	# Convert to the desired format
	return date_obj.strftime(output_format)

@frappe.whitelist()
def create_schedule_table(content,table):
	#Start Date
	start_date=table.start_date
	formatted_start_date = convert_date(table.start_date)
	#End Date
	end_date=table.end_date
	formatted_end_date = convert_date(table.end_date)
	style = "style='border-collapse: collapse; border: 1px solid black;'"
	content = f"""
	<div class="card" style="border: 1px solid #ccc; border-radius: 8px; padding:15px;margin:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
		<div class="card-body">
			<div style=" border-radius: 10px; width:100%; margin:auto;  padding: 15px; text-align: center;">
				<div style=" border-radius: 10px;  padding: 3px; text-align: center;">
					<input style="float: left;" type="checkbox" name="select_schedule" value="{table.voyage_number}">
					<p><strong>{table.origin} TO {table.destination} - {table.transit_time}</strong></p>
				</div>
				<div style="display: flex; justify-content: space-between;">
					<strong><span>{table.origin}</span></strong>
					<strong><span>{table.destination}</span></strong>
				</div>
				<div style="display: flex; justify-content: space-between;">
					<strong><span>{formatted_start_date}</span></strong>
					<strong><span>{formatted_end_date}</span></strong>
				</div>
			</div>
			<div style=" border-radius: 10px;text-align: center;">
				<table style="width: 100%; border: none;">
	"""
	for item in table.route:
		if item.arrival:
			date_str = item.arrival
			port_name = item.arrival_port
		if item.departure:
			date_str = item.departure
			port_name = item.departure_port
		formatted_date = convert_date(date_str)
		content += f"""
				<tr>
					<td><strong>{formatted_date}</strong></td>
					<td style="border-left: 1px dotted grey;"><strong>{port_name}<br>Service<br>Vessel<br>Voyage Ref</strong></td>					
					<td><br>{item.service}<br>{item.vessel}<br>{item.voyage_number}</td>
				</tr>
		"""
	content += "</table></div></div></div>"
	return content

#-----------------------------------------QUOTATION AND SALES ORDER-------------------------------------------
@frappe.whitelist()
def make_quotation_sales_order(source_name, target_doc=None, ignore_permissions=False):
    from frappe.model.mapper import get_mapped_doc
    doctype = frappe.flags.args.doctype
    mapping = {
        "Schedule and Rate Detail": {
            "doctype": "Schedule and Rate Detail",
        },
        "Shipment Rate": {
            "doctype": doctype,
            "field_map": {
                "shipping_type": "custom_shipping_type",
                "origin": "custom_origin",
                "departure_date": "custom_departure_date",
                "destination": "custom_destination",
                "duration": "custom_duration",
                "origin_service_mode": "custom_origin_service_mode",
                "destination_service_mode": "custom_destination_service_mode",
                "doctype": "custom_reference_doctype",
                "name": "custom_reference_name"
            },
        },
    }

    target_doc = get_mapped_doc("Shipment Rate", source_name, mapping, target_doc, ignore_permissions=ignore_permissions)
    return target_doc
#----------------------FREIGHTIFY SHIPMENT---------------------------------------
@frappe.whitelist()
def make_shipment(source_name,target_doc = None , ignore_permissions =False):
	from frappe.model.mapper import get_mapped_doc
	doctype = frappe.flags.args.doctype
	target_doc = get_mapped_doc("Shipment Rate",source_name,
		{
			"Schedule and Rate Detail": {
				"doctype": "Schedule and Rate Detail",
			},
			"Schedule and Rate Item": {
				"doctype": "Sales Order Item",
				"field_map":{
					"selling_rate":"rate",
					"selling_amount":"amount"
				}
			},
			"Shipment Rate": {
                "doctype": doctype,
                "field_map": {
					"shipping_type": "shipping_type",
                    "origin": "origin",
                    "departure_date": "departure_date",
                    "destination": "destination",
                    "duration": "duration",
                    "origin_service_mode": "origin_service_mode",
                    "destination_service_mode": "destination_service_mode",
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
	if not frappe.db.exists(doctype,{"reference_name":self.name,"docstatus":["!=",2]}):
		return {"function":"Success"}
	else:
		values=frappe.db.exists(doctype,{"reference_name":self.name,"docstatus":["!=",2]},["name"])
		return {"function":"Failed","value":f"Forwarding Shipment <b>{values} already present</b> for this Rate <b>{self.name}</b>"}


#----------------------------------CREATE ITEM-----------------------------------------------
@frappe.whitelist()
def consolidate_item(item):
	item=frappe._dict(json.loads(item))
	if len(item.charges_json)>0:
		consolidate_item_list=[]
		for charge in json.loads(item.charges_json):
			charges_list=charge["rate_type_base_charges"]
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
					consolidate_item_obj["rate"]=charge.sell_rate_usd
					consolidate_item_obj["amount"]=charge.sell_amount_usd
					consolidate_item_obj["buying_rate"]=charge.buy_rate_usd
					consolidate_item_obj["buying_amount"]=charge.buy_amount_usd
					consolidate_item_obj["selling_rate"]=charge.sell_rate_usd
					consolidate_item_obj["selling_amount"]=charge.sell_amount_usd
					consolidate_item_obj["ref_name"]=item.name
					consolidate_item_list.append(consolidate_item_obj)
		if consolidate_item_list:
			return consolidate_item_list


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