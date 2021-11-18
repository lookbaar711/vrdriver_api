from connections.connect_mongo import db
from bson.objectid import ObjectId
from bson.json_util import loads , dumps
from datetime import datetime , date , timedelta
import sys
import json

def get_api_message(function_name , message_code , message_lang=None):
	api_message = db.api_message.find_one({
											"function_name": function_name,
											"message_code": message_code
										})

	if api_message is None:
		if message_lang is None:
			message_lang = "en"

		if message_lang == "en":
			message_text = "Get message "+message_code+" failed."
		else:
			message_text = "ดึงข้อความ "+message_code+" ไม่สำเร็จ"

		return message_text
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		api_message_object = dumps(api_message)
		api_message_json = json.loads(api_message_object)

		#set default message_lang
		if message_lang is None:
			message_lang = "en"

		if message_lang == "en":
			message_text = api_message_json['message_text_en']
		else:
			message_text = api_message_json['message_text_th']

		return message_text

def set_api_log(user_type , user_id , function_name , headers , parameters_get , parameters_post , result):

	if function_name == "get_driver_register" or function_name == "province_list" or function_name == "district_list" or function_name == "sub_district_list" or function_name == "text_list":
		data_result = None
	else:
		data_result = result
	
	if headers.has_key("Authorization"):
		data_headers = {
							"Content-Type": headers['Content-Type'],
							"Accept": headers['Accept'],
							"Authorization": headers['Authorization']
						}
	else:
		data_headers = {
							"Content-Type": headers['Content-Type'],
							"Accept": headers['Accept']
						}

	data = { 
				"user_type": user_type,
				"user_id": user_id,
				"function_name": function_name,
				"headers": data_headers,
				"parameters_get": parameters_get,
				"parameters_post": parameters_post,
				"result_status": str(result['status']),
				"result_message": result['msg'],
				"result": data_result,
				"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			}

	try:
		db.api_log.insert_one(data)
		response = "True"
	except:
		response = "False"	

	return response

def set_cronjob_log(user_type , function_name , result):
	data = { 
				"user_type": user_type,
				"user_id": None,
				"function_name": function_name,
				"headers": None,
				"parameters_get": None,
				"parameters_post": None,
				"result_status": str(result['status']),
				"result_message": result['msg'],
				"result": result,
				"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			}

	try:
		db.api_log.insert_one(data)
		response = "True"
	except:
		response = "False"	

	return response

	