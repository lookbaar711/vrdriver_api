from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from function.checktokenexpire import check_token_expire_backend
from function.getmemberinfo import *
from function.api import *
from bson.objectid import ObjectId
from bson.json_util import loads , dumps
from datetime import datetime , date , timedelta
import sys
import json
import random
import string
import re
import os
from modules.login import get_random_token
from modules.upload_image import *

def car_type_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		car_type = db.car_type.find()

		if car_type is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			car_type_object = dumps(car_type)
			car_type_json = json.loads(car_type_object)

			car_type_list = []

			for i in range(len(car_type_json)):
				car_brand = db.car_brand.find({
												"car_type_id": car_type_json[i]['_id']['$oid'],
												"brand_status": "1"
											})
				if car_brand is None:
					detail = "-"
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_brand_object = dumps(car_brand)
					car_brand_json = json.loads(car_brand_object)
					detail = ""

					for j in range(len(car_brand_json)):
						if j == 0:
							detail = car_brand_json[j]['brand_name']
						else:
							detail = detail+" , "+car_brand_json[j]['brand_name']

				car_type_list.append({"id" : car_type_json[i]['_id']['$oid'],"type": car_type_json[i]['car_type_name_th'],"detail": detail})

			result = {
						"status" : True,
						"msg" : "Get car type success.",
						"data" : car_type_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "car_type_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def car_brand_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type_id = "car_type_id" in params

	if isset_accept and isset_content_type and isset_app_version and isset_car_type_id:
		car_brand = db.car_brand.find({
										"car_type_id": params['car_type_id'],
										"brand_status": "1"
									})
		car_brand_list = []

		if car_brand is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			car_brand_object = dumps(car_brand)
			car_brand_json = json.loads(car_brand_object)

			car_brand_list = []

			for i in range(len(car_brand_json)):
				car_brand_list.append({"id" : car_brand_json[i]['_id']['$oid'],"name": car_brand_json[i]['brand_name'],"car_type_id": car_brand_json[i]['car_type_id']})

		result = {
					"status" : True,
					"msg" : "Get car brand success.",
					"data" : car_brand_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "car_brand_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_car_brand(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type_id = "car_type_id" in params
	isset_brand_name = "brand_name" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_type_id and isset_brand_name:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"car_type_id": params['car_type_id'],
						"brand_name": params['brand_name'].strip(),
						"brand_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.car_brand.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add car brand success."
						}
			else:
				result = {
						"status" : False,
						"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_car_brand"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_car_brand(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_brand_id = "brand_id" in params
	isset_brand_name = "brand_name" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_brand_id and isset_brand_name:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['brand_id']) }
			value_param = {
							"$set":
								{
									"brand_name": params['brand_name'].strip(),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.car_brand.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit car brand success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_car_brand"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_car_brand(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_brand_id = "brand_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_brand_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['brand_id']) }
			value_param = {
							"$set":
								{
									"brand_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.car_brand.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete car brand success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_car_brand"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_outside_inspection(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type_code = "car_type_code" in params

	if isset_accept and isset_content_type and isset_app_version and isset_car_type_code:
		outside_inspection = db.outside_inspection.find({"car_type_code": params['car_type_code']})
		
		if outside_inspection is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			outside_inspection_object = dumps(outside_inspection)
			outside_inspection_json = json.loads(outside_inspection_object)

			outside_inspection_list = []

			for i in range(len(outside_inspection_json)):
				part_list = []
				for j in range(len(outside_inspection_json[i]['part'])):
					part_list.append({
						"part_name_en": outside_inspection_json[i]['part'][j]['part_name_en'],
						"part_name_th": outside_inspection_json[i]['part'][j]['part_name_th']
					})

				outside_inspection_list.append({
					"id" : outside_inspection_json[i]['_id']['$oid'],
					"car_type_code": outside_inspection_json[i]['car_type_code'],
					"point_name_en": outside_inspection_json[i]['point_name_en'],
					"point_name_th": outside_inspection_json[i]['point_name_th'],
					"part": part_list
				})

			result = {
						"status" : True,
						"msg" : "Get outside inspection success.",
						"data" : outside_inspection_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_outside_inspection"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_outside_inspection(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data = "data" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			for i in range(len(params['data'])):
				# update data
				where_param = { "_id": ObjectId(params['data'][i]['id']) }

				if len(params['data'][i]['part']) == 0:
					value_param = {
								"$set":
									{
										"point_name_en": params['data'][i]['point_name_en'].strip(),
										"point_name_th": params['data'][i]['point_name_th'].strip(),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				else:
					part_list = []
					for j in range(len(params['data'][i]['part'])):
						part_list.append({
							"part_code": str(j),
							"part_name_en": params['data'][i]['part'][j]['part_name_en'].strip(),
							"part_name_th": params['data'][i]['part'][j]['part_name_th'].strip()
						})

					value_param = {
								"$set":
									{
										"point_name_en": params['data'][i]['point_name_en'].strip(),
										"point_name_th": params['data'][i]['point_name_th'].strip(),
										"part": part_list,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				if db.outside_inspection.update(where_param , value_param):
					check_update = "1"
				else:
					check_update = "0"
					data_id = params['data'][i]['id']
					break

			if check_update == "1":
				result = {
							"status" : True,
							"msg" : "Edit outside inspection success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_outside_inspection"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_inspection_before_use(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		inspection_before_use = db.inspection_before_use.find()
		
		if inspection_before_use is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			inspection_before_use_object = dumps(inspection_before_use)
			inspection_before_use_json = json.loads(inspection_before_use_object)

			inspection_before_use_list = []

			for i in range(len(inspection_before_use_json)):
				if inspection_before_use_json[i]['check_status'] == "1":
					check_status_text = "เปิดใช้งาน"
				else:
					check_status_text = "ปิดใช้งาน"

				inspection_before_use_list.append({
					"id" : inspection_before_use_json[i]['_id']['$oid'],
					"check_name_en": inspection_before_use_json[i]['check_name_en'],
					"check_name_th": inspection_before_use_json[i]['check_name_th'],
					"check_status": inspection_before_use_json[i]['check_status'],
					"check_status_text": check_status_text
				})

			result = {
						"status" : True,
						"msg" : "Get inspection before use success.",
						"data" : inspection_before_use_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_inspection_before_use"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_inspection_before_use(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_check_name_en = "check_name_en" in params
	isset_check_name_th = "check_name_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_check_name_en and isset_check_name_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"check_name_en": params['check_name_en'].strip(),
						"check_name_th": params['check_name_th'].strip(),
						"check_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.inspection_before_use.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add inspection before use success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_inspection_before_use"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_inspection_before_use(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_check_id = "check_id" in params
	isset_check_name_en = "check_name_en" in params
	isset_check_name_th = "check_name_th" in params
	isset_check_status = "check_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_check_id and isset_check_name_en and isset_check_name_th and isset_check_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			inspection_before_use = db.inspection_before_use.find_one({"_id": ObjectId(params['check_id'])})
		
			if inspection_before_use is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				inspection_before_use_object = dumps(inspection_before_use)
				inspection_before_use_json = json.loads(inspection_before_use_object)

				if params['check_status'] is None:
					check_status = inspection_before_use_json['check_status']
				elif params['check_status'] == "0":
					check_status = "0"
				else:
					check_status = "1"

				# update data
				where_param = { "_id": ObjectId(params['check_id']) }
				value_param = {
								"$set":
									{
										"check_name_en": params['check_name_en'].strip(),
										"check_name_th": params['check_name_th'].strip(),
										"check_status": check_status,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				if db.inspection_before_use.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit inspection before use success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_inspection_before_use"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_inspection_before_use(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_check_id = "check_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_check_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['check_id']) }
			value_param = {
							"$set":
								{
									"check_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.inspection_before_use.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete inspection before use success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_inspection_before_use"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def driver_level_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		driver_level = db.driver_level.find({"level_status": "1"})
		driver_level_list = []

		if driver_level is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			driver_level_object = dumps(driver_level)
			driver_level_json = json.loads(driver_level_object)

			for i in range(len(driver_level_json)):
				driver_level_list.append({
					"id" : driver_level_json[i]['_id']['$oid'],
					"name_en": driver_level_json[i]['level_name_en'],
					"name_th": driver_level_json[i]['level_name_th'],
					"detail_en": driver_level_json[i]['level_detail_en'],
					"detail_th": driver_level_json[i]['level_detail_th'],
					"priority": int(driver_level_json[i]['level_priority']),
					"image": driver_level_json[i]['level_image']
				})

		result = {
					"status" : True,
					"msg" : "Get driver level success.",
					"data" : driver_level_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "driver_level_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_driver_level(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_level_name_en = "level_name_en" in params
	isset_level_name_th = "level_name_th" in params
	isset_level_detail_en = "level_detail_en" in params
	isset_level_detail_th = "level_detail_th" in params
	isset_level_priority = "level_priority" in params
	isset_level_image = "level_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_level_name_en and isset_level_name_th and isset_level_detail_en and isset_level_detail_th and isset_level_priority and isset_level_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				level_priority = int(params['level_priority'])
				check_level_priority = True
			except ValueError:
				check_level_priority = False

			check_level_name_en = db.driver_level.find({"level_name_en": params['level_name_en'].strip() , "level_status": "1"}).count()
			check_level_name_th = db.driver_level.find({"level_name_th": params['level_name_th'].strip() , "level_status": "1"}).count()

			if check_level_name_en > 0:
				result = {
							"status" : False,
							"msg" : "Level name (EN) has been used."
						}
			elif check_level_name_th > 0:
				result = {
							"status" : False,
							"msg" : "Level name (TH) has been used."
						}
			elif not check_level_priority:
				result = { 
							"status" : False,
							"msg" : "Level priority is not a number."
						}
			else:
				if params['level_image'] is None:
					image_name = None
				else:
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_driver_level_image(params['level_image'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				data = { 
							"level_name_en": params['level_name_en'].strip(),
							"level_name_th": params['level_name_th'].strip(),
							"level_detail_en": params['level_detail_en'].strip(),
							"level_detail_th": params['level_detail_th'].strip(),
							"level_priority": int(params['level_priority']),
							"level_image": image_name,
							"level_status": "1",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.driver_level.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add driver level success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_driver_level"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_level(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_level_id = "level_id" in params
	isset_level_name_en = "level_name_en" in params
	isset_level_name_th = "level_name_th" in params
	isset_level_detail_en = "level_detail_en" in params
	isset_level_detail_th = "level_detail_th" in params
	isset_level_priority = "level_priority" in params
	isset_level_status = "level_status" in params
	isset_level_image = "level_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_level_id and isset_level_name_en and isset_level_name_th and isset_level_detail_en and isset_level_detail_th and isset_level_priority and isset_level_status and isset_level_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				level_priority = int(params['level_priority'])
				check_level_priority = True
			except ValueError:
				check_level_priority = False

			check_level_name_en = db.driver_level.find({
														"_id": {"$ne": ObjectId(params['level_id'])},
														"level_name_en": params['level_name_en'].strip(),
														"level_status": "1"
													}).count()

			check_level_name_th = db.driver_level.find({
														"_id": {"$ne": ObjectId(params['level_id'])},
														"level_name_th": params['level_name_th'].strip(),
														"level_status": "1"
													}).count()
			if check_level_name_en > 0:
				result = {
							"status" : False,
							"msg" : "Level name (EN) has been used."
						}
			elif check_level_name_th > 0:
				result = {
							"status" : False,
							"msg" : "Level name (TH) has been used."
						}
			elif not check_level_priority:
				result = { 
							"status" : False,
							"msg" : "Level priority is not a number."
						}
			else:
				driver_level = db.driver_level.find_one({
															"_id": ObjectId(params['level_id'])
														})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)

				if params['level_image'] is None:
					image_name = driver_level_json['level_image']
				else:
					#เช็ค path และลบรูปเก่า
					if driver_level_json['level_image'] is not None:
						if os.path.exists("static/images/driver_level/"+driver_level_json['level_image']):
							os.remove("static/images/driver_level/"+driver_level_json['level_image'])

					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_driver_level_image(params['level_image'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				if params['level_status'] is None:
					level_status = driver_level_json['level_status']
				elif params['level_status'] == "0":
					level_status = "0"
				else:
					level_status = "1"

				# update data
				where_param = { "_id": ObjectId(params['level_id']) }
				value_param = {
								"$set":
									{
										"level_name_en": params['level_name_en'].strip(),
										"level_name_th": params['level_name_th'].strip(),
										"level_detail_en": params['level_detail_en'].strip(),
										"level_detail_th": params['level_detail_th'].strip(),
										"level_priority": int(params['level_priority']),
										"level_image": image_name,
										"level_status": level_status,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.driver_level.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver level success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_driver_level"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_driver_level(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_level_id = "level_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_level_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['level_id']) }
			value_param = {
							"$set":
								{
									"level_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.driver_level.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete driver level success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_driver_level"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def payment_channel_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		payment_channel = db.payment_channel.find()
		payment_channel_list = []

		if payment_channel is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			payment_channel_object = dumps(payment_channel)
			payment_channel_json = json.loads(payment_channel_object)

			payment_channel_list = []

			for i in range(len(payment_channel_json)):
				if payment_channel_json[i]['account_status'] == "1":
					account_status_show = "เปิดใช้งาน"
				else:
					account_status_show = "ปิดใช้งาน"

				payment_channel_list.append({"id" : payment_channel_json[i]['_id']['$oid'],"account_name": payment_channel_json[i]['account_name'],"account_number": payment_channel_json[i]['account_number'],"bank_name_en": payment_channel_json[i]['bank_name_en'],"bank_name_th": payment_channel_json[i]['bank_name_th'],"bank_logo": payment_channel_json[i]['bank_logo'],"account_status": payment_channel_json[i]['account_status'],"account_status_show": account_status_show})

		result = {
					"status" : True,
					"msg" : "Get payment channel success.",
					"data" : payment_channel_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "payment_channel_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_payment_channel(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_account_name = "account_name" in params
	isset_account_number = "account_number" in params
	isset_bank_name_en = "bank_name_en" in params
	isset_bank_name_th = "bank_name_th" in params
	isset_account_status = "account_status" in params
	isset_bank_logo = "bank_logo" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_account_name and isset_account_number and isset_bank_name_en and isset_bank_name_th and isset_account_status and isset_bank_logo:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_account = db.payment_channel.find({"account_name": params['account_name'].strip() , "account_number": params['account_number'].strip()}).count()

			if check_account > 0:
				result = {
							"status" : False,
							"msg" : "Account has been used."
						}
			else:
				if params['bank_logo'] is None:
					image_name = None
				else:
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_bank_logo(params['bank_logo'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				if params['account_status'] == "0":
					account_status = "0"
				else:
					account_status = "1"

				data = { 
							"account_name": params['account_name'].strip(),
							"account_number": params['account_number'].strip(),
							"bank_name_en": params['bank_name_en'].strip(),
							"bank_name_th": params['bank_name_th'].strip(),
							"bank_logo": image_name,
							"account_status": account_status,
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.payment_channel.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add payment channel success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_payment_channel"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_payment_channel(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_account_id = "account_id" in params
	isset_account_name = "account_name" in params
	isset_account_number = "account_number" in params
	isset_bank_name_en = "bank_name_en" in params
	isset_bank_name_th = "bank_name_th" in params
	isset_account_status = "account_status" in params
	isset_bank_logo = "bank_logo" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_account_id and isset_account_name and isset_account_number and isset_bank_name_en and isset_bank_name_th and isset_account_status and isset_bank_logo:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_account = db.payment_channel.find({
													"_id": {"$ne": ObjectId(params['account_id'])},
													"account_name": params['account_name'].strip(),
													"account_number": params['account_number'].strip()
												}).count()

			if check_account > 0:
				result = {
							"status" : False,
							"msg" : "Account has been used."
						}
			else:
				payment_channel = db.payment_channel.find_one({"_id": ObjectId(params['account_id'])})

				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				payment_channel_object = dumps(payment_channel)
				payment_channel_json = json.loads(payment_channel_object)

				#ถ้าไม่มีการแก้ไขรูป profile (bank_logo เป็น null) ไม่ต้องอัพเดตรูป  
				if params['bank_logo'] is None:
					image_name = payment_channel_json['bank_logo']
				else:
					#เช็ค path และลบรูปเก่า
					if payment_channel_json['bank_logo'] is not None:
						if os.path.exists("static/images/bank/"+payment_channel_json['bank_logo']):
							os.remove("static/images/bank/"+payment_channel_json['bank_logo'])
		
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_bank_logo(params['bank_logo'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				if params['account_status'] is None:
					account_status = payment_channel_json['account_status']
				elif params['account_status'] == "0":
					account_status = "0"
				else:
					account_status = "1"

				# update data
				where_param = { "_id": ObjectId(params['account_id']) }
				value_param = {
								"$set":
									{
										"account_name": params['account_name'].strip(),
										"account_number": params['account_number'].strip(),
										"bank_name_en": params['bank_name_en'].strip(),
										"bank_name_th": params['bank_name_th'].strip(),
										"bank_logo": image_name,
										"account_status": account_status,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.payment_channel.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit payment channel success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_payment_channel"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_payment_channel(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_account_id = "account_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_account_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#update data
			where_param = { "_id": ObjectId(params['account_id']) }
			value_param = {
							"$set":
								{
									"account_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.payment_channel.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete payment channel success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_payment_channel"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_emergency_call(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		emergency_call = db.emergency_call.find_one()
		
		if emergency_call is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			emergency_call_object = dumps(emergency_call)
			emergency_call_json = json.loads(emergency_call_object)

			result = {
						"status" : True,
						"msg" : "Get emergency call success.",
						"emergency_call_id" : emergency_call_json['_id']['$oid'],
						"call_customer_admin" : emergency_call_json['call_customer_admin'],
						"call_driver_admin" : emergency_call_json['call_driver_admin']
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_emergency_call"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_emergency_call(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_emergency_call_id = "emergency_call_id" in params
	isset_call_customer_admin = "call_customer_admin" in params
	isset_call_driver_admin = "call_driver_admin" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_emergency_call_id and isset_call_customer_admin and isset_call_driver_admin:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#update data
			where_param = { "_id": ObjectId(params['emergency_call_id']) }
			value_param = {
							"$set":
								{
									"call_customer_admin": params['call_customer_admin'].strip(),
									"call_driver_admin": params['call_driver_admin'].strip(),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.emergency_call.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit emergency call success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_emergency_call"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def region_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		region = db.region.find()

		if region is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			region_object = dumps(region)
			region_json = json.loads(region_object)

			region_list = []

			for i in range(len(region_json)):
				region_list.append({"id" : region_json[i]['_id']['$oid'],"region_code": region_json[i]['region_code'],"region_name_en": region_json[i]['region_name_en'],"region_name_th": region_json[i]['region_name_th']})

			result = {
						"status" : True,
						"msg" : "Get region success.",
						"data" : region_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "region_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def province_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		province = db.province.find({"province_status": "1"})

		if province is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			province_object = dumps(province)
			province_json = json.loads(province_object)

			province_list = []

			for i in range(len(province_json)):
				province_list.append({"id" : province_json[i]['_id']['$oid'],"province_code": province_json[i]['province_code'],"province_en": province_json[i]['province_en'],"province_th": province_json[i]['province_th'],"region_code": province_json[i]['region_code'],"region_name": province_json[i]['region_name']})

			result = {
						"status" : True,
						"msg" : "Get province success.",
						"data" : province_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "province_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_province(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_province_code = "province_code" in params
	isset_province_en = "province_en" in params
	isset_province_th = "province_th" in params
	isset_region_code = "region_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_province_code and isset_province_en and isset_province_th and isset_region_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_province = db.province.find({
												"$or": [
														{"province_code": params['province_code'].strip()},
														{"province_en": params['province_en'].strip()},
														{"province_th": params['province_th'].strip()}
												]}).count()

			if check_province > 0:
				result = {
							"status" : False,
							"msg" : "Province has been used."
						}
			else:
				region = db.region.find_one({"region_code": params['region_code'].strip()})
				if region is None:
					result = { 
								"status" : False,
								"msg" : "Region not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					region_object = dumps(region)
					region_json = json.loads(region_object)

					data = { 
								"province_code": params['province_code'].strip(),
								"province_en": params['province_en'].strip(),
								"province_th": params['province_th'].strip(),
								"region_code": params['region_code'].strip(),
								"region_name": region_json['region_name_th'],
								"province_status": "1",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

				if db.province.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add province success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_province"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_province(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_province_id = "province_id" in params
	isset_province_code = "province_code" in params
	isset_province_en = "province_en" in params
	isset_province_th = "province_th" in params
	isset_region_code = "region_code" in params
	isset_province_status = "province_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_province_id and isset_province_code and isset_province_en and isset_province_th and isset_region_code and isset_province_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_province = db.province.find({
												"$or": [
													{"province_code": params['province_code'].strip()},
													{"province_en": params['province_en'].strip()},
													{"province_th": params['province_th'].strip()}
												],
												"$and": [
													{"_id": {"$ne": ObjectId(params['province_id'])}}
												]}).count()

			if check_province > 0:
				result = {
							"status" : False,
							"msg" : "Province has been used."
						}
			else:
				province = db.province.find_one({"_id": ObjectId(params['province_id'])})
				region = db.region.find_one({"region_code": params['region_code']})

				if province is None:
					result = { 
								"status" : False,
								"msg" : "Province not found."
							}
				elif region is None:
					result = { 
								"status" : False,
								"msg" : "Region not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					province_object = dumps(province)
					province_json = json.loads(province_object)
					region_object = dumps(region)
					region_json = json.loads(region_object)

					if params['province_status'] is None:
						province_status = province_json['province_status']
					elif params['province_status'] == "0":
						province_status = "0"
					else:
						province_status = "1"

					# update data
					where_param = { "_id": ObjectId(params['province_id']) }
					value_param = {
									"$set":
										{
											"province_code": params['province_code'].strip(),
											"province_en": params['province_en'].strip(),
											"province_th": params['province_th'].strip(),
											"region_code": params['region_code'].strip(),
											"region_name": region_json['region_name_th'],
											"province_status": province_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.province.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit province success."
								}
					else:
						result = {
									"status" : False,
									"msg" : "Data update failed."
								}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_province"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_province(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_province_id = "province_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_province_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['province_id']) }
			value_param = {
							"$set":
								{
									"province_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.province.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete province success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_province"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def district_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_province_code = "province_code" in params

	if isset_accept and isset_content_type and isset_app_version and isset_province_code:
		if params['province_code'] is None:
			district = db.district.find({"district_status": "1"})
		else:
			district = db.district.find({
											"province_code": params['province_code'],
											"district_status": "1"
										})

		if district is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			district_object = dumps(district)
			district_json = json.loads(district_object)

			district_list = []

			for i in range(len(district_json)):
				district_list.append({"id" : district_json[i]['_id']['$oid'],"district_code": district_json[i]['district_code'],"district_en": district_json[i]['district_en'],"district_th": district_json[i]['district_th'],"province_name": district_json[i]['province_name']})

			result = {
						"status" : True,
						"msg" : "Get district success.",
						"data" : district_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "district_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_district_code = "district_code" in params
	isset_district_en = "district_en" in params
	isset_district_th = "district_th" in params
	isset_province_code = "province_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_district_code and isset_district_en and isset_district_th and isset_province_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_district = db.district.find({
												"$or": [
														{"district_code": params['district_code'].strip()},
														{"district_en": params['district_en'].strip()},
														{"district_th": params['district_th'].strip()}
												]}).count()

			if check_district > 0:
				result = {
							"status" : False,
							"msg" : "District has been used."
						}
			else:
				province = db.province.find_one({"province_code": params['province_code']})
				if province is None:
					result = { 
								"status" : False,
								"msg" : "Province not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					province_object = dumps(province)
					province_json = json.loads(province_object)

					data = { 
								"district_code": params['district_code'].strip(),
								"district_en": params['district_en'].strip(),
								"district_th": params['district_th'].strip(),
								"province_code": params['province_code'].strip(),
								"province_name": province_json['province_th'],
								"district_status": "1",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

				if db.district.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add district success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_district_id = "district_id" in params
	isset_district_code = "district_code" in params
	isset_district_en = "district_en" in params
	isset_district_th = "district_th" in params
	isset_province_code = "province_code" in params
	isset_district_status = "district_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_district_id and isset_district_code and isset_district_en and isset_district_th and isset_province_code and isset_district_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_district = db.district.find({
												"$or": [
													{"district_code": params['district_code'].strip()},
													{"district_en": params['district_en'].strip()},
													{"district_th": params['district_th'].strip()}
												],
												"$and": [
													{"_id": {"$ne": ObjectId(params['district_id'])}}
												]}).count()

			if check_district > 0:
				result = {
							"status" : False,
							"msg" : "District has been used."
						}
			else:
				district = db.district.find_one({"_id": ObjectId(params['district_id'])})
				province = db.province.find_one({"province_code": params['province_code']})
				
				if district is None:
					result = { 
								"status" : False,
								"msg" : "District not found."
							}
				elif province is None:
					result = { 
								"status" : False,
								"msg" : "Province not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					district_object = dumps(district)
					district_json = json.loads(district_object)
					province_object = dumps(province)
					province_json = json.loads(province_object)

					if params['district_status'] is None:
						district_status = district_json['district_status']
					elif params['district_status'] == "0":
						district_status = "0"
					else:
						district_status = "1"

					# update data
					where_param = { "_id": ObjectId(params['district_id']) }
					value_param = {
									"$set":
										{
											"district_code": params['district_code'].strip(),
											"district_en": params['district_en'].strip(),
											"district_th": params['district_th'].strip(),
											"province_code": params['province_code'].strip(),
											"province_name": province_json['province_th'],
											"district_status": district_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.district.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit district success."
								}
					else:
						result = {
									"status" : False,
									"msg" : "Data update failed."
								}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_district_id = "district_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_district_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['district_id']) }
			value_param = {
							"$set":
								{
									"district_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.district.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete district success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def sub_district_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_district_code = "district_code" in params

	if isset_accept and isset_content_type and isset_app_version and isset_district_code:
		if params['district_code'] is None:
			sub_district = db.sub_district.find({"sub_district_status": "1"})
		else:
			sub_district = db.sub_district.find({
											"district_code": params['district_code'],
											"sub_district_status": "1"
										})

		if sub_district is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			sub_district_object = dumps(sub_district)
			sub_district_json = json.loads(sub_district_object)

			sub_district_list = []

			for i in range(len(sub_district_json)):
				sub_district_list.append({"sub_district_id" : sub_district_json[i]['_id']['$oid'],"sub_district_code": sub_district_json[i]['sub_district_code'],"sub_district_en": sub_district_json[i]['sub_district_en'],"sub_district_th": sub_district_json[i]['sub_district_th'],"postcode": sub_district_json[i]['postcode'],"district_code": sub_district_json[i]['district_code'],"district_en": sub_district_json[i]['district_en'],"district_th": sub_district_json[i]['district_th'],"province_code": sub_district_json[i]['province_code'],"province_en": sub_district_json[i]['province_en'],"province_th": sub_district_json[i]['province_th']})

			result = {
						"status" : True,
						"msg" : "Get sub-district success.",
						"data" : sub_district_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "sub_district_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_sub_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_sub_district_code = "sub_district_code" in params
	isset_sub_district_en = "sub_district_en" in params
	isset_sub_district_th = "sub_district_th" in params
	isset_postcode = "postcode" in params
	isset_district_code = "district_code" in params
	isset_province_code = "province_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_sub_district_code and isset_sub_district_en and isset_sub_district_th and isset_postcode and isset_district_code and isset_province_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_sub_district = db.sub_district.find({"sub_district_code": params['sub_district_code']}).count()

			if check_sub_district > 0:
				result = {
							"status" : False,
							"msg" : "Sub-district has been used."
						}
			else:
				district = db.district.find_one({"district_code": params['district_code'].strip()})
				province = db.province.find_one({"province_code": params['province_code'].strip()})

				if district is None:
					result = { 
								"status" : False,
								"msg" : "District not found."
							}
				elif province is None:
					result = { 
								"status" : False,
								"msg" : "Province not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					district_object = dumps(district)
					district_json = json.loads(district_object)

					province_object = dumps(province)
					province_json = json.loads(province_object)

					data = { 
								"sub_district_code": params['sub_district_code'].strip(),
								"sub_district_en": params['sub_district_en'].strip(),
								"sub_district_th": params['sub_district_th'].strip(),
								"postcode": params['postcode'].strip(),
								"district_code": params['district_code'].strip(),
								"district_en": district_json['district_en'],
								"district_th": district_json['district_th'],
								"province_code": params['province_code'].strip(),
								"province_en": province_json['province_en'],
								"province_th": province_json['province_th'],
								"sub_district_status": "1",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

				if db.sub_district.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add sub-district success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_sub_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_sub_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_sub_district_id = "sub_district_id" in params
	isset_sub_district_code = "sub_district_code" in params
	isset_sub_district_en = "sub_district_en" in params
	isset_sub_district_th = "sub_district_th" in params
	isset_postcode = "postcode" in params
	isset_district_code = "district_code" in params
	isset_province_code = "province_code" in params
	isset_sub_district_status = "sub_district_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_sub_district_id and isset_sub_district_code and isset_sub_district_en and isset_sub_district_th and isset_postcode and isset_district_code and isset_province_code and isset_sub_district_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_sub_district = db.sub_district.find({
														"sub_district_code": params['sub_district_code'].strip(),
														"$and": [
															{"_id": {"$ne": ObjectId(params['sub_district_id'])}}
														]}).count()

			if check_sub_district > 0:
				result = {
							"status" : False,
							"msg" : "Sub-district has been used."
						}
			else:
				sub_district = db.sub_district.find_one({"_id": ObjectId(params['sub_district_id'])})
				district = db.district.find_one({"district_code": params['district_code'].strip()})
				province = db.province.find_one({"province_code": params['province_code'].strip()})

				if district is None:
					result = { 
								"status" : False,
								"msg" : "Sub-district not found."
							}
				elif district is None:
					result = { 
								"status" : False,
								"msg" : "District not found."
							}
				elif province is None:
					result = { 
								"status" : False,
								"msg" : "Province not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					sub_district_object = dumps(sub_district)
					sub_district_json = json.loads(sub_district_object)

					district_object = dumps(district)
					district_json = json.loads(district_object)

					province_object = dumps(province)
					province_json = json.loads(province_object)

					if params['sub_district_status'] is None:
						sub_district_status = sub_district_json['sub_district_status']
					elif params['sub_district_status'] == "0":
						sub_district_status = "0"
					else:
						sub_district_status = "1"

					# update data
					where_param = { "_id": ObjectId(params['sub_district_id']) }
					value_param = {
									"$set":
										{
											"sub_district_code": params['sub_district_code'].strip(),
											"sub_district_en": params['sub_district_en'].strip(),
											"sub_district_th": params['sub_district_th'].strip(),
											"postcode": params['postcode'].strip(),
											"district_code": params['district_code'].strip(),
											"district_en": district_json['district_en'],
											"district_th": district_json['district_th'],
											"province_code": params['province_code'].strip(),
											"province_en": province_json['province_en'],
											"province_th": province_json['province_th'],
											"sub_district_status": sub_district_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.sub_district.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit sub-district success."
								}
					else:
						result = {
									"status" : False,
									"msg" : "Data update failed."
								}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_sub_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_sub_district(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_sub_district_id = "sub_district_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_sub_district_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['sub_district_id']) }
			value_param = {
							"$set":
								{
									"sub_district_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.sub_district.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete sub-district success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_sub_district"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_address_info_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_postcode = "postcode" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_postcode:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
			
			postcode = db.postcode.find({
											"postcode": params['postcode'],
											"postcode_status": "1"
										})

			if postcode is None:
				result = { 
							"status" : False,
							"msg" : "Data not found." 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				postcode_object = dumps(postcode)
				postcode_json = json.loads(postcode_object)

				address_info_list = []

				for i in range(len(postcode_json)):
					sub_district_name = postcode_json[i]['sub_district_th']
					district_name = postcode_json[i]['district_th']
					province_name = postcode_json[i]['province_th']

					address_info_list.append({
						"postcode": postcode_json[i]['postcode'],
						"sub_district_code": postcode_json[i]['sub_district_code'],
						"sub_district_name": sub_district_name,
						"district_code": postcode_json[i]['district_code'],
						"district_name": district_name,
						"province_code": postcode_json[i]['province_code'],
						"province_name": province_name
					})

				result = {
							"status" : True,
							"msg" : "Get address info success.", 
							"data" : address_info_list
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_address_info"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def text_list(request):
	# เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		with open('static/language/mobile_customer.json', 'r', encoding='utf-8') as json_file:
			data_customer = json.load(json_file)
	
		with open('static/language/mobile_driver.json', 'r', encoding='utf-8') as json_file:
			data_driver = json.load(json_file)
	
		with open('static/language/web_frontend.json', 'r', encoding='utf-8') as json_file:
			data_web = json.load(json_file)

		text_list = []

		for key_customer in data_customer['language_data'].keys():
			text_list.append({"user_type" : "customer","text_code" : key_customer,"text_en": data_customer['language_data'][key_customer]['EN'],"text_th": data_customer['language_data'][key_customer]['TH']})

		for key_driver in data_driver['language_data'].keys():
			text_list.append({"user_type" : "driver","text_code" : key_driver,"text_en": data_driver['language_data'][key_driver]['EN'],"text_th": data_driver['language_data'][key_driver]['TH']})

		for key_web in data_web['language_data'].keys():
			text_list.append({"user_type" : "web","text_code" : key_web,"text_en": data_web['language_data'][key_web]['EN'],"text_th": data_web['language_data'][key_web]['TH']})

		result = { 
				"status" : True,
				"msg" : "Get text success.",
				"data" : text_list
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "text_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result
	
def add_text(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params
	isset_text_code = "text_code" in params
	isset_text_en = "text_en" in params
	isset_text_th = "text_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_user_type and isset_text_code and isset_text_en and isset_text_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			if params['user_type'] == "customer":
				with open('static/language/mobile_customer.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			elif params['user_type'] == "driver":
				with open('static/language/mobile_driver.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			else:
				with open('static/language/web_frontend.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)

			#ถ้าเจอ text_code ใน language_data จะไม่สามารถเพิ่มข้อมูลได้
			if params['text_code'] in data['language_data']:
				result = {
							"status" : False,
							"msg" : "Text code has been used."
						}
			else:
				text_dict = {
					params['text_code']: {
						"TH": params['text_th'],
						"EN": params['text_en']
					}
				}

				#เพิ่ม text ใหม่ใส่ language_data
				data['language_data'].update(text_dict) 

				language_all = {
					"language_list" : data['language_list'],
					"language_data" : data['language_data']
				}

				try:
					if params['user_type'] == "customer":
						with open('static/language/mobile_customer.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					elif params['user_type'] == "driver":
						with open('static/language/mobile_driver.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					else:
						with open('static/language/web_frontend.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)

					result = {
								"status" : True,
								"msg" : "Add text success."
							}
				except:
					result = {
								"status" : False,
								"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_text"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_text(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params
	isset_text_code = "text_code" in params
	isset_text_en = "text_en" in params
	isset_text_th = "text_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_user_type and isset_text_code and isset_text_en and isset_text_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			if params['user_type'] == "customer":
				with open('static/language/mobile_customer.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			elif params['user_type'] == "driver":
				with open('static/language/mobile_driver.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			else:
				with open('static/language/web_frontend.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)

			#ถ้าเจอ text_code ใน language_data ถึงจะแก้ไขได้
			if params['text_code'] in data['language_data']:
				#แก้ไขข้อมูล
				data['language_data'][params['text_code']]['TH'] = params['text_th']
				data['language_data'][params['text_code']]['EN'] = params['text_en']

				language_all = {
					"language_list" : data['language_list'],
					"language_data" : data['language_data']
				}

				try:
					if params['user_type'] == "customer":
						with open('static/language/mobile_customer.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					elif params['user_type'] == "driver":
						with open('static/language/mobile_customer.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					else:
						with open('static/language/web_frontend.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)

					result = {
								"status" : True,
								"msg" : "Edit text success."
							}
				except:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
			else:
				result = {
							"status" : False,
							"msg" : "Text code not found."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_text"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_text(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params
	isset_text_code = "text_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_user_type and isset_text_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			if params['user_type'] == "customer":
				with open('static/language/mobile_customer.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			elif params['user_type'] == "driver":
				with open('static/language/mobile_driver.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)
			else:
				with open('static/language/web_frontend.json', 'r', encoding='utf-8') as json_file:
					data = json.load(json_file)

			#ถ้าเจอ text_code ใน language_data ถึงจะลบได้
			if params['text_code'] in data['language_data']:
				#ลบข้อมูล
				del data['language_data'][params['text_code']]

				language_all = {
					"language_list" : data['language_list'],
					"language_data" : data['language_data']
				}

				try:
					if params['user_type'] == "customer":
						with open('static/language/mobile_customer.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					elif params['user_type'] == "driver":
						with open('static/language/mobile_customer.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)
					else:
						with open('static/language/web_frontend.json','w', encoding='utf8') as f: 
							json.dump(language_all, f, indent=2, ensure_ascii=False)

					result = {
								"status" : True,
								"msg" : "Delete text success."
							}
				except:
					result = {
								"status" : False,
								"msg" : "Delete text failed."
							}
			else:
				result = {
							"status" : False,
							"msg" : "Text code not found."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_text"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def communication_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		communication = db.communication.find()

		if communication is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			communication_object = dumps(communication)
			communication_json = json.loads(communication_object)

			communication_list = []

			for i in range(len(communication_json)):
				communication_list.append({"id" : communication_json[i]['_id']['$oid'],"lang_name_en": communication_json[i]['lang_name_en'],"lang_name_th": communication_json[i]['lang_name_th'],"lang_code": communication_json[i]['lang_code'],"flag_image": communication_json[i]['flag_image']})

			result = {
						"status" : True,
						"msg" : "Get communication success.",
						"data" : communication_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "communication_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_communication(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_communication_id = "communication_id" in params
	isset_lang_name_en = "lang_name_en" in params
	isset_lang_name_th = "lang_name_th" in params
	isset_lang_code = "lang_code" in params
	isset_flag_image = "flag_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_communication_id and isset_lang_name_en and isset_lang_name_th and isset_lang_code and isset_flag_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_lang_name = db.communication.find({
				"$or": [
					{"lang_name_en": params['lang_name_en'].strip()},
					{"lang_name_th": params['lang_name_th'].strip()}
				],
				"$and": [
					{"_id": {"$ne": ObjectId(params['communication_id'])}}
				]}).count()

			if check_lang_name > 0:
				result = {
							"status" : False,
							"msg" : "Communication has been used."
						}
			else:
				#ถ้าไม่มีการแก้ไขรูป flag (flag_image เป็น null) ไม่ต้องอัพเดตรูป  
				if params['flag_image'] is None:
					image_name = "flag_"+params['lang_code']+".png"
				else:
					#เช็ค path และลบรูปเก่า
					if os.path.exists("static/images/flag/flag_"+params['lang_code']+".png"):
						os.remove("static/images/flag/flag_"+params['lang_code']+".png")
		
					check_upload_image = upload_flag_image(params['flag_image'], "flag_"+params['lang_code'])

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				# update data
				where_param = { "_id": ObjectId(params['communication_id']) }
				value_param = {
								"$set":
									{
										"lang_name_en": params['lang_name_en'].strip(),
										"lang_name_th": params['lang_name_th'].strip(),
										"flag_image": image_name,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.communication.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit communication success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_communication"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_contact_us_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		contact_us = db.contact_us.find_one()
		
		if contact_us is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			contact_us_object = dumps(contact_us)
			contact_us_json = json.loads(contact_us_object)

			result = {
						"status" : True,
						"msg" : "Get contact us success.",
						"contact_id" : contact_us_json['_id']['$oid'],
						"contact_address_en" : contact_us_json['contact_address_en'],
						"contact_address_th" : contact_us_json['contact_address_th'],
						"contact_email" : contact_us_json['contact_email'],
						"contact_tel" : contact_us_json['contact_tel']
					}

	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_contact_us_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_contact_us(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_contact_id = "contact_id" in params
	isset_contact_address_en = "contact_address_en" in params
	isset_contact_address_th = "contact_address_th" in params
	isset_contact_email = "contact_email" in params
	isset_contact_tel = "contact_tel" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_contact_id and isset_contact_address_en and isset_contact_address_th and isset_contact_email and isset_contact_tel:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['contact_id']) }
			value_param = {
							"$set":
								{
									"contact_address_en": params['contact_address_en'].strip(),
									"contact_address_th": params['contact_address_th'].strip(),
									"contact_email": params['contact_email'].strip(),
									"contact_tel": params['contact_tel'].strip(),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.contact_us.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit contact us success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_contact_us"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def contact_topic_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		contact_topic = db.contact_topic.find({"topic_status": "1"})

		if contact_topic is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			contact_topic_object = dumps(contact_topic)
			contact_topic_json = json.loads(contact_topic_object)

			contact_topic_list = []

			for i in range(len(contact_topic_json)):
				if contact_topic_json[i]['topic_status'] == "1":
					topic_status_text = "เปิดใช้งาน"
				else:
					topic_status_text = "ปิดใช้งาน"

				contact_topic_list.append({
					"id" : contact_topic_json[i]['_id']['$oid'],
					"topic_en": contact_topic_json[i]['topic_en'],
					"topic_th": contact_topic_json[i]['topic_th'],
					"topic_status": contact_topic_json[i]['topic_status'],
					"topic_status_text": topic_status_text
				})

		result = {
					"status" : True,
					"msg" : "Get contact topic success.",
					"data" : contact_topic_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "contact_topic_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_contact_topic(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_topic_en = "topic_en" in params
	isset_topic_th = "topic_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_topic_en and isset_topic_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"topic_en": params['topic_en'].strip(),
						"topic_th": params['topic_th'].strip(),
						"topic_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.contact_topic.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add contact topic success."
						}
			else:
				result = {
						"status" : False,
						"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_contact_topic"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_contact_topic(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_topic_id = "topic_id" in params
	isset_topic_en = "topic_en" in params
	isset_topic_th = "topic_th" in params
	isset_topic_status = "topic_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_topic_id and isset_topic_en and isset_topic_th and isset_topic_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			contact_topic = db.contact_topic.find_one({"_id": ObjectId(params['topic_id'])})
			
			if contact_topic is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				contact_topic_object = dumps(contact_topic)
				contact_topic_json = json.loads(contact_topic_object)

				if params['topic_status'] is None:
					topic_status = contact_topic_json['topic_status']
				elif params['topic_status'] == "0":
					topic_status = "0"
				else:
					topic_status = "1"


			# update data
			where_param = { "_id": ObjectId(params['topic_id']) }
			value_param = {
							"$set":
								{
									"topic_en": params['topic_en'].strip(),
									"topic_th": params['topic_th'].strip(),
									"topic_status": topic_status,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.contact_topic.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit contact topic success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_contact_topic"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_contact_topic(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_topic_id = "topic_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_topic_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['topic_id']) }
			value_param = {
							"$set":
								{
									"topic_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.contact_topic.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete contact topic success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_contact_topic"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def service_rating_question_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		service_rating_question = db.service_rating_question.find()

		if service_rating_question is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			service_rating_question_object = dumps(service_rating_question)
			service_rating_question_json = json.loads(service_rating_question_object)

			service_rating_question_list = []

			for i in range(len(service_rating_question_json)):
				service_rating_question_list.append({"id" : service_rating_question_json[i]['_id']['$oid'],"question_en": service_rating_question_json[i]['question_en'],"question_th": service_rating_question_json[i]['question_th']})

		result = {
					"status" : True,
					"msg" : "Get service rating question success.",
					"data" : service_rating_question_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "service_rating_question_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_service_rating_question(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_question_id = "question_id" in params
	isset_question_en = "question_en" in params
	isset_question_th = "question_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_question_id and isset_question_en and isset_question_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['question_id']) }
			value_param = {
							"$set":
								{
									"question_en": params['question_en'].strip(),
									"question_th": params['question_th'].strip(),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.service_rating_question.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit service rating question success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_service_rating_question"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def service_area_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		service_area = db.service_area.find()

		if service_area is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			service_area_object = dumps(service_area)
			service_area_json = json.loads(service_area_object)

			service_area_list = []

			for i in range(len(service_area_json)):
				service_area_list.append({"id" : service_area_json[i]['_id']['$oid'],"name_en": service_area_json[i]['service_area_name_en'],"name_th": service_area_json[i]['service_area_name_th']})

			result = {
						"status" : True,
						"msg" : "Get service area success.",
						"data" : service_area_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "service_area_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_service_area(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_area_name_en = "service_area_name_en" in params
	isset_area_name_th = "service_area_name_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_area_name_en and isset_area_name_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_area_name = db.service_area.find({"$or": [{"service_area_name_en": params['service_area_name_en'].strip()},{"service_area_name_th": params['service_area_name_th'].strip()}]}).count()

			if check_area_name > 0:
				result = {
							"status" : False,
							"msg" : "Service area has been used."
						}
			else:
				data = { 
							"service_area_name_en": params['service_area_name_en'].strip(),
							"service_area_name_th": params['service_area_name_th'].strip(),
							"service_area_status": "1",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.service_area.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add service area success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_service_area"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_service_area(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_area_id = "service_area_id" in params
	isset_area_name_en = "service_area_name_en" in params
	isset_area_name_th = "service_area_name_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_area_id and isset_area_name_en and isset_area_name_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_area_name = db.service_area.find({
				"$or": [
					{"service_area_name_en": params['service_area_name_en'].strip()},
					{"service_area_name_th": params['service_area_name_th'].strip()}
				],
				"$and": [
					{"_id": {"$ne": ObjectId(params['service_area_id'])}}
				]}).count()

			if check_area_name > 0:
				result = {
							"status" : False,
							"msg" : "Service area has been used."
						}
			else:
				# update data
				where_param = { "_id": ObjectId(params['service_area_id']) }
				value_param = {
								"$set":
									{
										"service_area_name_en": params['service_area_name_en'].strip(),
										"service_area_name_th": params['service_area_name_th'].strip(),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.service_area.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit service area success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_service_area"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_specification_policy_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_user_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			specification = db.specification.find_one({"user_type": params['user_type']})
			
			if specification is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				specification_object = dumps(specification)
				specification_json = json.loads(specification_object)

				result = {
							"status" : True,
							"msg" : "Get specification and policy success.",
							"user_type" : specification_json['user_type'],
							"specification_en" : specification_json['specification_en'],
							"specification_th" : specification_json['specification_th'],
							"policy_en" : specification_json['policy_en'],
							"policy_th" : specification_json['policy_th']
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_specification_policy_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_specification_policy(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params
	isset_specification_en = "specification_en" in params
	isset_specification_th = "specification_th" in params
	isset_policy_en = "policy_en" in params
	isset_policy_th = "policy_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_user_type and isset_specification_en and isset_specification_th and isset_policy_en and isset_policy_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "user_type": params['user_type'] }
			value_param = {
							"$set":
								{
									"specification_en": params['specification_en'].strip(),
									"specification_th": params['specification_th'].strip(),
									"policy_en": params['policy_en'].strip(),
									"policy_th": params['policy_th'].strip(),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.specification.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit specification and policy success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_specification_policy"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def car_engine_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		car_engine = db.car_engine.find()

		if car_engine is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			car_engine_object = dumps(car_engine)
			car_engine_json = json.loads(car_engine_object)

			car_engine_list = []

			for i in range(len(car_engine_json)):
				if car_engine_json[i]['car_engine_status'] == "1":
					car_engine_status_text = "เปิดใช้งาน"
				else:
					car_engine_status_text = "ปิดใช้งาน"

				car_engine_list.append({
					"id" : car_engine_json[i]['_id']['$oid'],
					"car_engine_en": car_engine_json[i]['car_engine_en'],
					"car_engine_th": car_engine_json[i]['car_engine_th'],
					"car_engine_status": car_engine_json[i]['car_engine_status'],
					"car_engine_status_text": car_engine_status_text
				})

		result = {
					"status" : True,
					"msg" : "Get car engine success.",
					"data" : car_engine_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "car_engine_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_car_engine(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_engine_en = "car_engine_en" in params
	isset_car_engine_th = "car_engine_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_engine_en and isset_car_engine_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"car_engine_en": params['car_engine_en'].strip(),
						"car_engine_th": params['car_engine_th'].strip(),
						"car_engine_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.car_engine.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add car engine success."
						}
			else:
				result = {
						"status" : False,
						"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_car_engine"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_car_engine(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_engine_id = "car_engine_id" in params
	isset_car_engine_en = "car_engine_en" in params
	isset_car_engine_th = "car_engine_th" in params
	isset_car_engine_status = "car_engine_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_engine_id and isset_car_engine_en and isset_car_engine_th and isset_car_engine_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			car_engine = db.car_engine.find_one({"_id": ObjectId(params['car_engine_id'])})
			
			if car_engine is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_engine_object = dumps(car_engine)
				car_engine_json = json.loads(car_engine_object)

				if params['car_engine_status'] is None:
					car_engine_status = car_engine_json['car_engine_status']
				elif params['car_engine_status'] == "0":
					car_engine_status = "0"
				else:
					car_engine_status = "1"


			# update data
			where_param = { "_id": ObjectId(params['car_engine_id']) }
			value_param = {
							"$set":
								{
									"car_engine_en": params['car_engine_en'].strip(),
									"car_engine_th": params['car_engine_th'].strip(),
									"car_engine_status": car_engine_status,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.car_engine.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit car engine success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_car_engine"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_vat_rate_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			vat = db.vat_rate.find_one()
			
			if vat is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				vat_object = dumps(vat)
				vat_json = json.loads(vat_object)

				result = {
							"status" : True,
							"msg" : "Get vat rate success.",
							"vat_rate" : vat_json['vat_rate']
						}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_vat_rate_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_vat_rate(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_vat_rate = "vat_rate" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_vat_rate:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
			
			try:
				vat_rate = float(params['vat_rate'])
				check_vat_rate = True
			except ValueError:
				check_vat_rate = False

			if not check_vat_rate:
				result = { 
						"status" : False,
						"msg" : "Vat rate is not a number."
					}
			else:
				# update data
				where_param = { "vat_rate": {"$gt" : 0} }
				value_param = {
								"$set":
									{
										"vat_rate": vat_rate,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.vat_rate.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit vat rate success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
		else:
			result = { 
				"status" : False,
				"error_code" : 401,
				"msg" : "Unauthorized."
			}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_vat_rate"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def request_driver_remark_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		remark = db.request_driver_remark.find()

		if remark is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			remark_object = dumps(remark)
			remark_json = json.loads(remark_object)

			remark_list = []

			for i in range(len(remark_json)):
				if remark_json[i]['remark_status'] == "1":
					remark_status_text = "เปิดใช้งาน"
				else:
					remark_status_text = "ปิดใช้งาน"

				remark_list.append({
					"id" : remark_json[i]['_id']['$oid'],
					"remark_en": remark_json[i]['remark_en'],
					"remark_th": remark_json[i]['remark_th'],
					"remark_status": remark_json[i]['remark_status'],
					"remark_status_text": remark_status_text
				})

		result = {
					"status" : True,
					"msg" : "Get request driver remark success.",
					"data" : remark_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "request_driver_remark_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_request_driver_remark(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_remark_en = "remark_en" in params
	isset_remark_th = "remark_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_remark_en and isset_remark_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"remark_en": params['remark_en'].strip(),
						"remark_th": params['remark_th'].strip(),
						"remark_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.request_driver_remark.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add request driver remark success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_request_driver_remark"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_request_driver_remark(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_remark_id = "remark_id" in params
	isset_remark_en = "remark_en" in params
	isset_remark_th = "remark_th" in params
	isset_remark_status = "remark_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_remark_id and isset_remark_en and isset_remark_th and isset_remark_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			remark = db.request_driver_remark.find_one({"_id": ObjectId(params['remark_id'])})
			
			if remark is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				remark_object = dumps(remark)
				remark_json = json.loads(remark_object)

				if params['remark_status'] is None:
					remark_status = remark_json['remark_status']
				elif params['remark_status'] == "0":
					remark_status = "0"
				else:
					remark_status = "1"


			# update data
			where_param = { "_id": ObjectId(params['remark_id']) }
			value_param = {
							"$set":
								{
									"remark_en": params['remark_en'].strip(),
									"remark_th": params['remark_th'].strip(),
									"remark_status": remark_status,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.request_driver_remark.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit request driver remark success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_request_driver_remark"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

#add -- add special skill
def special_skill_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		special_skill = db.special_skill.find()

		if special_skill is not None:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			special_skill_object = dumps(special_skill)
			special_skill_json = json.loads(special_skill_object)

			special_skill_list = []

			for i in range(len(special_skill_json)):
				if special_skill_json[i]['skill_status'] == "1":
					skill_status_text = "เปิดใช้งาน"
				else:
					skill_status_text = "ปิดใช้งาน"

				special_skill_list.append({
					"id" : special_skill_json[i]['_id']['$oid'],
					"skill_en": special_skill_json[i]['skill_en'],
					"skill_th": special_skill_json[i]['skill_th'],
					"skill_status": special_skill_json[i]['skill_status'],
					"skill_status_text": skill_status_text
				})

		result = {
					"status" : True,
					"msg" : "Get special skill success.",
					"data" : special_skill_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "special_skill_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_special_skill(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_skill_en = "skill_en" in params
	isset_skill_th = "skill_th" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_skill_en and isset_skill_th:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			data = { 
						"skill_en": params['skill_en'].strip(),
						"skill_th": params['skill_th'].strip(),
						"skill_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.special_skill.insert_one(data):
				result = {
							"status" : True,
							"msg" : "Add special skill success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "add_special_skill"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_special_skill(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_skill_id = "skill_id" in params
	isset_skill_en = "skill_en" in params
	isset_skill_th = "skill_th" in params
	isset_skill_status = "skill_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_skill_id and isset_skill_en and isset_skill_th and isset_skill_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			special_skill = db.special_skill.find_one({"_id": ObjectId(params['skill_id'])})
			
			if special_skill is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				special_skill_object = dumps(special_skill)
				special_skill_json = json.loads(special_skill_object)

				if params['skill_status'] is None:
					skill_status = special_skill_json['skill_status']
				elif params['skill_status'] == "0":
					skill_status = "0"
				else:
					skill_status = "1"

			# update data
			where_param = { "_id": ObjectId(params['skill_id']) }
			value_param = {
							"$set":
								{
									"skill_en": params['skill_en'].strip(),
									"skill_th": params['skill_th'].strip(),
									"skill_status": skill_status,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.special_skill.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Edit special skill success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "edit_special_skill"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_special_skill(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_skill_id = "skill_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_skill_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['skill_id']) }
			value_param = {
							"$set":
								{
									"skill_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.special_skill.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete special skill success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : "Unauthorized."
					}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "delete_special_skill"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result