from connections.connect_mongo import db
from bson.objectid import ObjectId
from bson.json_util import loads , dumps
from datetime import datetime , date , timedelta
import sys
import json

def check_request_status(request_id):
	request_driver = db.request_driver.find_one({"_id": ObjectId(request_id)})

	if request_driver is None:
		return None
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		if request_driver_json['driver_list_id'] is None:
			request_status = {
				"all_driver" : 0,
				"count_reject" : 0,
				"count_cancel" : 0,
				"count_accept" : 0,
				"count_pending" : 0
			}

			return request_status
		else:
			driver_list = db.driver_list.find_one({"_id": ObjectId(request_driver_json['driver_list_id'])})
			# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			driver_list_object = dumps(driver_list)
			driver_list_json = json.loads(driver_list_object)

			all_driver = len(driver_list_json['driver_list'])
			count_reject = 0
			count_cancel = 0
			count_accept = 0
			count_pending = 0

			if len(driver_list_json['driver_list']) > 0:
				for i in range(len(driver_list_json['driver_list'])):
					if driver_list_json['driver_list'][i]['driver_request_status'] == "4":
						count_reject += 1
					elif driver_list_json['driver_list'][i]['driver_request_status'] == "3" or driver_list_json['driver_list'][i]['driver_request_status'] == "2":
						count_cancel += 1
					elif driver_list_json['driver_list'][i]['driver_request_status'] == "1":
						count_accept += 1
					else:
						count_pending += 1

				request_status = {
					"all_driver" : all_driver,
					"count_reject" : count_reject,
					"count_cancel" : count_cancel,
					"count_accept" : count_accept,
					"count_pending" : count_pending
				}

				return request_status
			else:
				return None




		

