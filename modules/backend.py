from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from function.notification import send_push_message
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
import hashlib
import re
import os
from flask import render_template
from flask_mail import Mail, Message
from modules.login import get_random_token
from modules.upload_image import *
from modules.send_email import send_email

def package_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_package_model = "package_model" in params
	isset_package_type = "package_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_package_model and isset_package_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:		

				# package = db.package.find()

				# if package is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	package_object = dumps(package)
				# 	package_json = json.loads(package_object)

				# 	for i in range(len(package_json)):
						
				# 		package_price_text = str(package_json[i]['package_price']) 

				# 		# update data
				# 		where_param = { "_id": ObjectId(package_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"package_price_text": package_price_text
				# 							}
				# 					}

				# 		db.package.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = {}

				#package_code , package_name , package_price
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "package_code": {"$regex": params['search_text']} },
												{ "package_name_en": {"$regex": params['search_text']} },
												{ "package_name_th": {"$regex": params['search_text']} },
												{ "package_price_text": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['package_model'] == "normal" or params['package_model'] == "special":
					add_params = {"package_model" : params['package_model']}
					where_param.update(add_params)

				if params['package_type'] == "hour" or params['package_type'] == "time":
					add_params = {"package_type" : params['package_type']}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# package_code = package_code
					# package_name = package_name_th
					# package_model = package_model
					# package_type = package_type
					# package_price = package_price
					# package_status_show = package_status

					if params['sort_name'] == "package_name":
						sort_name = "package_name_th"
					elif params['sort_name'] == "package_status_show":
						sort_name = "package_status"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				package = db.package.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.package.find(where_param).count()

				if package is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					package_list = []

					for i in range(len(package_json)):
						if package_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if package_json[i]['package_type'] == "hour":
							package_type = "รายชั่วโมง"
						else:
							package_type = "รายครั้ง"

						if package_json[i]['package_status'] == "1":
							package_status_show = "เปิดใช้งาน"
						else:
							package_status_show = "ปิดใช้งาน"

						package_list.append({
							"package_id" : package_json[i]['_id']['$oid'],
							"package_code": package_json[i]['package_code'],
							"package_name": package_json[i]['package_name_th'],
							"package_model": package_model,
							"package_type": package_type,
							"package_price": float(package_json[i]['package_price']),
							"package_status": package_json[i]['package_status'],
							"package_status_show": package_status_show
						})

				result = {
							"status" : True,
							"msg" : "Get package list success.",
							"data" : package_list,
							"total_data" : total_data
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
	function_name = "package_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_form(request):
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

			driver_level = db.driver_level.find({"level_status": "1"})
			communication = db.communication.find()
			
			if driver_level is None:
				result = { 
							"status" : False,
							"msg" : "Driver level not found."
						}
			elif communication is None:
				result = { 
							"status" : False,
							"msg" : "Communication not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)
				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)

				driver_level_list = []
				communication_list = []

				package_model_list = [
										{"code": "normal","name": "Normal"},
										{"code": "special","name": "Special"}
									]

				package_type_list = [
										{"code": "hour","name": "รายชั่วโมง"},
										{"code": "time","name": "รายครั้ง"}
									]

				service_time_list = [
										{"code": "allday","name": "All day"},
										{"code": "weekday","name": "Weekday"},
										{"code": "weekend","name": "Weekend"}
									]

				package_status_list = [
										{"code": "0","name": "ปิดใช้งาน"},
										{"code": "1","name": "เปิดใช้งาน"}
									]

				for i in range(len(driver_level_json)):
					driver_level_list.append({
						"id" : driver_level_json[i]['_id']['$oid'],
						"name": driver_level_json[i]['level_name_th']
					})

				for j in range(len(communication_json)):
					communication_list.append({
						"id" : communication_json[j]['_id']['$oid'],
						"lang_name": communication_json[j]['lang_name_th']
					})

				vat_rate = get_vat_rate()

				result = {
							"status" : True,
							"msg" : "Get package form success.",
							"package_model" : package_model_list,
							"package_type" : package_type_list,
							"service_time" : service_time_list,
							"driver_level" : driver_level_list,
							"package_status" : package_status_list,
							"communication" : communication_list,
							"vat_rate" : vat_rate
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
	function_name = "get_package_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_company(request):
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

			company = db.company.find({"company_status": "1"})
			
			if company is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				company_list = []

				for i in range(len(company_json)):
					company_list.append({
						"id" : company_json[i]['_id']['$oid'],
						"name": company_json[i]['company_name']
					})
			
				result = {
							"status" : True,
							"msg" : "Get package company success.",
							"company" : company_list
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
	function_name = "get_package_company"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_detail_backend(package_id,request):
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

			package = db.package.find_one({"_id": ObjectId(package_id)})
			if package is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_object = dumps(package)
				package_json = json.loads(package_object)

				if package_json['package_status'] == "1":
					package_status_show = "เปิดใช้งาน"
				else:
					package_status_show = "ปิดใช้งาน"


				special_company = []
				
				#ถ้า special_company ไม่ใช่ array เปล่า
				if len(package_json['special_company']) > 0:
					company_in = []

					for i in range(len(package_json['special_company'])):
						company_in.append(ObjectId(package_json['special_company'][i]))

					company = db.company.find({"_id" : {"$in" : company_in}})

					if company is not None or company.count() > 0:
						# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						company_object = dumps(company)
						company_json = json.loads(company_object)

						special_company = []

						for j in range(len(company_json)):
							special_company.append({
								"value" : company_json[j]['_id']['$oid'],
								"label": company_json[j]['company_name']
							})

				data = {
							"package_id": package_json['_id']['$oid'],
							"package_code": package_json['package_code'],
							"package_name_en": package_json['package_name_en'],
							"package_name_th": package_json['package_name_th'],
							"package_detail_en": package_json['package_detail_en'],
							"package_detail_th": package_json['package_detail_th'],
							"package_condition_en": package_json['package_condition_en'],
							"package_condition_th": package_json['package_condition_th'],
							"package_model": package_json['package_model'],
							"package_type": package_json['package_type'],
							"hour_amount": package_json['hour_amount'],
							"time_amount": package_json['time_amount'],
							"package_price": float(package_json['package_price']),
							"package_price_not_vat": package_json['package_price_not_vat'],
							"package_price_vat": package_json['package_price_vat'],
							"vat_rate": package_json['vat_rate'],
							"total_usage_date": package_json['total_usage_date'],
							"special_company": special_company,
							"service_time": package_json['service_time'],
							"driver_level": package_json['driver_level'],
							"communication": package_json['communication'],
							"normal_paid_rate": float(package_json['normal_paid_rate']),
							"normal_received_rate": float(package_json['normal_received_rate']),
							"overtime_paid_rate": float(package_json['overtime_paid_rate']),
							"overtime_received_rate": float(package_json['overtime_received_rate']),
							"package_status": package_json['package_status'],
							"package_status_show": package_status_show,
							"package_image": package_json['package_image']
						}

				result = {
							"status" : True,
							"msg" : "Get package detail success.",
							"data" : data
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
	function_name = "get_package_detail_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_package(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_name_en = "package_name_en" in params
	isset_package_name_th = "package_name_th" in params
	isset_package_detail_en = "package_detail_en" in params
	isset_package_detail_th = "package_detail_th" in params
	isset_package_condition_en = "package_condition_en" in params
	isset_package_condition_th = "package_condition_th" in params
	isset_package_model = "package_model" in params
	isset_package_type = "package_type" in params
	isset_hour_amount = "hour_amount" in params
	isset_time_amount = "time_amount" in params
	isset_package_price = "package_price" in params
	isset_total_usage_date = "total_usage_date" in params
	isset_special_company = "special_company" in params
	isset_service_time = "service_time" in params
	isset_driver_level = "driver_level" in params
	isset_communication = "communication" in params
	isset_normal_paid_rate = "normal_paid_rate" in params
	isset_normal_received_rate = "normal_received_rate" in params
	isset_overtime_paid_rate = "overtime_paid_rate" in params
	isset_overtime_received_rate = "overtime_received_rate" in params
	isset_package_status = "package_status" in params
	isset_package_image = "package_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_name_en and isset_package_name_th and isset_package_detail_en and isset_package_detail_th and isset_package_condition_en and isset_package_condition_en and isset_package_model and isset_package_type and isset_hour_amount and isset_time_amount and isset_package_price and isset_total_usage_date and isset_special_company and isset_service_time and isset_driver_level and isset_communication and isset_normal_paid_rate and isset_normal_received_rate and isset_overtime_paid_rate and isset_overtime_received_rate and isset_package_status and isset_package_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['package_name_en']=="" or params['package_name_en'] is None:
				validate.append({"error_param" : "package_name","msg" : "Package name (EN) is required."})
			elif params['package_name_th']=="" or params['package_name_th'] is None:
				validate.append({"error_param" : "package_name","msg" : "Package name (TH) is required."})
			else:
				#check already package name
				check_package_name_en = db.package.find({
														"package_name_en": params['package_name_en']
													}).count()

				check_package_name_th = db.package.find({
														"package_name_th": params['package_name_th']
													}).count()
				if check_package_name_en > 0:
					validate.append({"error_param" : "package_name_en","msg" : "Package name (EN) has been used."})
				if check_package_name_th > 0:
					validate.append({"error_param" : "package_name_th","msg" : "Package name (TH) has been used."})

			if params['package_model']=="" or params['package_model'] is None:
				validate.append({"error_param" : "package_model","msg" : "Package model is required."})
			elif params['package_model']!="normal" and params['package_model']!="special":
				validate.append({"error_param" : "package_model","msg" : "Package model value is not normal and special."})
			if params['package_type']=="" or params['package_type'] is None:
				validate.append({"error_param" : "package_type","msg" : "Package type is required."})
			elif params['package_type']!="hour" and params['package_type']!="time":
				validate.append({"error_param" : "package_model","msg" : "Package type value is not hour and time."})
			if params['package_type']=="hour" and (params['hour_amount']=="" or params['hour_amount'] is None):
				validate.append({"error_param" : "hour_amount","msg" : "Hour amount is required."})
			elif params['package_type']=="hour" and (params['hour_amount']!="" and params['hour_amount'] is not None):
				try:
					hour_amount = int(params['hour_amount'])
				except ValueError:
					validate.append({"error_param" : "hour_amount","msg" : "Hour amount is not a number."})

			if params['package_type']=="time" and (params['time_amount']=="" or params['time_amount'] is None):
				validate.append({"error_param" : "time_amount","msg" : "Time amount is required."})
			elif params['package_type']=="time" and (params['time_amount']!="" and params['time_amount'] is not None):
				try:
					time_amount = int(params['time_amount'])
				except ValueError:
					validate.append({"error_param" : "time_amount","msg" : "Time amount is not a number."})

			if params['package_price']=="" or params['package_price'] is None:
				validate.append({"error_param" : "package_price","msg" : "Package price is required."})
			else:
				check_int = isinstance(params['package_price'], int)
				check_float = isinstance(params['package_price'], float)

				if check_int or check_float:
					package_price = round(float(params['package_price']) , 2)
				else:
					validate.append({"error_param" : "package_price","msg" : "Package price is not a number."})

			if params['total_usage_date']=="" or params['total_usage_date'] is None:
				validate.append({"error_param" : "total_usage_date","msg" : "Total usage date is required."})
			else:
				try:
					total_usage_date = int(params['total_usage_date'])
				except ValueError:
					validate.append({"error_param" : "total_usage_date","msg" : "Total usage date is not a number."})

			if params['package_model']=="special" and (params['special_company']=="" or params['special_company'] is None):
				validate.append({"error_param" : "special_company","msg" : "Special company is required."})
			elif params['package_model']=="special" and (params['special_company']!="" and params['special_company'] is not None):
				if len(params['special_company']) == 0:
					validate.append({"error_param" : "special_company","msg" : "Special company value is undefined."})

			if params['service_time']=="" or params['service_time'] is None:
				validate.append({"error_param" : "service_time","msg" : "Service time is required."})
			elif params['service_time']!="allday" and params['service_time']!="weekday" and params['service_time']!="weekend":
				validate.append({"error_param" : "service_time","msg" : "Service time value is not allday , weekday and weekend."})

			if params['driver_level']=="" or params['driver_level'] is None:
				validate.append({"error_param" : "driver_level","msg" : "Driver level is required."})
			if params['communication']=="" or params['communication'] is None:
				validate.append({"error_param" : "communication","msg" : "Communication is required."})
			elif params['communication']!="" and params['communication'] is not None:
				if len(params['communication']) == 0:
					validate.append({"error_param" : "communication","msg" : "Communication value is undefined."})

			if params['normal_paid_rate']=="" or params['normal_paid_rate'] is None:
				validate.append({"error_param" : "normal_paid_rate","msg" : "Normal paid rate is required."})
			else:
				check_int = isinstance(params['normal_paid_rate'], int)
				check_float = isinstance(params['normal_paid_rate'], float)

				if check_int or check_float:
					normal_paid_rate = float(params['normal_paid_rate'])
				else:
					validate.append({"error_param" : "normal_paid_rate","msg" : "Normal paid rate is not a number."})
			if params['normal_received_rate']=="" or params['normal_received_rate'] is None:
				validate.append({"error_param" : "normal_received_rate","msg" : "Normal received rate is required."})
			else:
				check_int = isinstance(params['normal_received_rate'], int)
				check_float = isinstance(params['normal_received_rate'], float)

				if check_int or check_float:
					normal_received_rate = float(params['normal_received_rate'])
				else:
					validate.append({"error_param" : "normal_received_rate","msg" : "Normal received rate is not a number."})
			if params['overtime_paid_rate']=="" or params['overtime_paid_rate'] is None:
				validate.append({"error_param" : "overtime_paid_rate","msg" : "Overtime paid rate is required."})
			else:
				check_int = isinstance(params['overtime_paid_rate'], int)
				check_float = isinstance(params['overtime_paid_rate'], float)

				if check_int or check_float:
					overtime_paid_rate = float(params['overtime_paid_rate'])
				else:
					validate.append({"error_param" : "overtime_paid_rate","msg" : "Overtime paid rate is not a number."})
			if params['overtime_received_rate']=="" or params['overtime_received_rate'] is None:
				validate.append({"error_param" : "overtime_received_rate","msg" : "Overtime received rate is required."})
			else:
				check_int = isinstance(params['overtime_received_rate'], int)
				check_float = isinstance(params['overtime_received_rate'], float)

				if check_int or check_float:
					overtime_received_rate = float(params['overtime_received_rate'])
				else:
					validate.append({"error_param" : "overtime_received_rate","msg" : "Overtime received rate is not a number."})
			#set communication_en & communication_th
			communication_in = []
			for i in range(len(params['communication'])):
				communication_in.append(ObjectId(params['communication'][i]))

			communication = db.communication.find({"_id" : {"$in" : communication_in}})

			if communication is None or communication.count() == 0:
				validate.append({"error_param" : "communication","msg" : "Please check your communication value."})
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)

				communication_list = []

				communication_en = ""
				communication_th = ""

				for i in range(len(communication_json)):
					if i == 0:
						communication_en = communication_json[i]['lang_name_en']
						communication_th = communication_json[i]['lang_name_th']
					else:
						communication_en = communication_en+" , "+communication_json[i]['lang_name_en']
						communication_th = communication_th+" , "+communication_json[i]['lang_name_th']

			


			#ถ้า validate ผ่าน
			if len(validate) == 0:
				if params['package_image'] is None:
					image_name = None
				else:
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_package_image(params['package_image'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				special_company_list = []

				if params['package_model'] == "special":
					for i in range(len(params['special_company'])):
						special_company_list.append(params['special_company'][i]['value'])

				if params['package_type'] == "time":
					hour_amount = None
					time_amount = int(params['time_amount'])
				else:
					hour_amount = int(params['hour_amount'])
					time_amount = None

				if params['package_status'] == "0":
					package_status = "0"
				else:
					package_status = "1"

				#ดึง package_code ล่าสุดจาก tb package แล้วเอามา +1
				package = db.package.find_one(sort=[("package_code", -1)])
				pid = 1

				if package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					pid = int(package_json["package_code"][1:8])+1

				package_code = "P"+"%07d" % pid

				if params['package_detail_en']=="" or params['package_detail_en'] is None:
					package_detail_en = ""
				else:
					package_detail_en = params['package_detail_en']
				if params['package_detail_th']=="" or params['package_detail_th'] is None:
					package_detail_th = ""
				else:
					package_detail_th = params['package_detail_th']

				if params['package_condition_en']=="" or params['package_condition_en'] is None:
					package_condition_en = ""
				else:
					package_condition_en = params['package_condition_en']
				if params['package_condition_th']=="" or params['package_condition_th'] is None:
					package_condition_th = ""
				else:
					package_condition_th = params['package_condition_th']

				vat_rate = get_vat_rate()
				package_price_vat = round(((package_price * vat_rate) / 100) , 2)
				package_price_not_vat = round(package_price - package_price_vat , 2)
				package_price_text = str(package_price)

				data = { 
							"package_code": package_code,
							"package_name_en": params['package_name_en'],
							"package_name_th": params['package_name_th'],
							"package_detail_en": package_detail_en,
							"package_detail_th": package_detail_th,
							"package_condition_en": package_condition_en,
							"package_condition_th": package_condition_th,
							"package_model": params['package_model'],
							"package_type": params['package_type'],
							"hour_amount": hour_amount,
							"time_amount": time_amount,
							"package_price": package_price,
							"package_price_text": package_price_text,
							"package_price_not_vat": package_price_not_vat,
							"package_price_vat": package_price_vat,
							"vat_rate": vat_rate,
							"total_usage_date": total_usage_date,
							"special_company": special_company_list,
							"service_time": params['service_time'],
							"driver_level": params['driver_level'],
							"communication": params['communication'],
							"communication_en": communication_en,
							"communication_th": communication_th,
							"normal_paid_rate": normal_paid_rate,
							"normal_received_rate": normal_received_rate,
							"overtime_paid_rate": overtime_paid_rate,
							"overtime_received_rate": overtime_received_rate,
							"package_image": image_name,
							"package_status": package_status,
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.package.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add package success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
							}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "add_package"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_package(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params
	isset_package_name_en = "package_name_en" in params
	isset_package_name_th = "package_name_th" in params
	isset_package_detail_en = "package_detail_en" in params
	isset_package_detail_th = "package_detail_th" in params
	isset_package_condition_en = "package_condition_en" in params
	isset_package_condition_th = "package_condition_th" in params
	isset_package_model = "package_model" in params
	isset_package_type = "package_type" in params
	isset_hour_amount = "hour_amount" in params
	isset_time_amount = "time_amount" in params
	isset_package_price = "package_price" in params
	isset_total_usage_date = "total_usage_date" in params
	isset_special_company = "special_company" in params
	isset_service_time = "service_time" in params
	isset_driver_level = "driver_level" in params
	isset_communication = "communication" in params
	isset_normal_paid_rate = "normal_paid_rate" in params
	isset_normal_received_rate = "normal_received_rate" in params
	isset_overtime_paid_rate = "overtime_paid_rate" in params
	isset_overtime_received_rate = "overtime_received_rate" in params
	isset_package_status = "package_status" in params
	isset_package_image = "package_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id and isset_package_name_en and isset_package_name_th and isset_package_detail_en and isset_package_detail_th and isset_package_condition_en and isset_package_condition_th and isset_package_model and isset_package_type and isset_hour_amount and isset_time_amount and isset_package_price and isset_total_usage_date and isset_special_company and isset_service_time and isset_driver_level and isset_communication and isset_normal_paid_rate and isset_normal_received_rate and isset_overtime_paid_rate and isset_overtime_received_rate and isset_package_status and isset_package_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['package_name_en']=="" or params['package_name_en'] is None:
				validate.append({"error_param" : "package_name_en","msg" : "Package name (EN) is required."})
			elif params['package_name_th']=="" or params['package_name_th'] is None:
				validate.append({"error_param" : "package_name_th","msg" : "Package name (EN) is required."})
			else:
				#check already package name
				check_package_name_en = db.package.find({
														"_id": {"$ne": ObjectId(params['package_id'])},
														"package_name_en": params['package_name_en']
													}).count()

				check_package_name_th = db.package.find({
														"_id": {"$ne": ObjectId(params['package_id'])},
														"package_name_th": params['package_name_th']
													}).count()
				if check_package_name_en > 0:
					validate.append({"error_param" : "package_name_en","msg" : "Package name (EN) has been used."})
				if check_package_name_th > 0:
					validate.append({"error_param" : "package_name_th","msg" : "Package name (TH) has been used."})

			if params['package_model']=="" or params['package_model'] is None:
				validate.append({"error_param" : "package_model","msg" : "Package model is required."})
			elif params['package_model']!="normal" and params['package_model']!="special":
				validate.append({"error_param" : "package_model","msg" : "Package model value is not normal and special."})
			if params['package_type']=="" or params['package_type'] is None:
				validate.append({"error_param" : "package_type","msg" : "Package type is required."})
			elif params['package_type']!="hour" and params['package_type']!="time":
				validate.append({"error_param" : "package_model","msg" : "Package type value is not hour and time."})
			if params['package_type']=="hour" and (params['hour_amount']=="" or params['hour_amount'] is None):
				validate.append({"error_param" : "hour_amount","msg" : "Hour amount is required."})
			elif params['package_type']=="hour" and (params['hour_amount']!="" and params['hour_amount'] is not None):
				try:
					hour_amount = int(params['hour_amount'])
				except ValueError:
					validate.append({"error_param" : "hour_amount","msg" : "Hour amount is not a number."})

			if params['package_type']=="time" and (params['time_amount']=="" or params['time_amount'] is None):
				validate.append({"error_param" : "time_amount","msg" : "Time amount is required."})
			elif params['package_type']=="time" and (params['time_amount']!="" and params['time_amount'] is not None):
				try:
					time_amount = int(params['time_amount'])
				except ValueError:
					validate.append({"error_param" : "time_amount","msg" : "Time amount is not a number."})

			if params['package_price']=="" or params['package_price'] is None:
				validate.append({"error_param" : "package_price","msg" : "Package price is required."})
			else:
				check_int = isinstance(params['package_price'], int)
				check_float = isinstance(params['package_price'], float)

				if check_int or check_float:
					package_price = round(float(params['package_price']) , 2)
				else:
					validate.append({"error_param" : "package_price","msg" : "Package price is not a number."})
			if params['total_usage_date']=="" or params['total_usage_date'] is None:
				validate.append({"error_param" : "total_usage_date","msg" : "Total usage date is required."})
			else:
				try:
					total_usage_date = int(params['total_usage_date'])
				except ValueError:
					validate.append({"error_param" : "total_usage_date","msg" : "Total usage date is not a number."})

			if params['package_model']=="special" and (params['special_company']=="" or params['special_company'] is None):
				validate.append({"error_param" : "special_company","msg" : "Special company is required."})
			elif params['package_model']=="special" and (params['special_company']!="" and params['special_company'] is not None):
				if len(params['special_company']) == 0:
					validate.append({"error_param" : "special_company","msg" : "Special company value is undefined."})

			if params['service_time']=="" or params['service_time'] is None:
				validate.append({"error_param" : "service_time","msg" : "Service time is required."})
			elif params['service_time']!="allday" and params['service_time']!="weekday" and params['service_time']!="weekend":
				validate.append({"error_param" : "service_time","msg" : "Service time value is not allday , weekday and weekend."})

			if params['driver_level']=="" or params['driver_level'] is None:
				validate.append({"error_param" : "driver_level","msg" : "Driver level is required."})
			if params['communication']=="" or params['communication'] is None:
				validate.append({"error_param" : "communication","msg" : "Communication is required."})
			elif params['communication']!="" and params['communication'] is not None:
				if len(params['communication']) == 0:
					validate.append({"error_param" : "communication","msg" : "Communication value is undefined."})

			if params['normal_paid_rate']=="" or params['normal_paid_rate'] is None:
				validate.append({"error_param" : "normal_paid_rate","msg" : "Normal paid rate is required."})
			else:
				check_int = isinstance(params['normal_paid_rate'], int)
				check_float = isinstance(params['normal_paid_rate'], float)

				if check_int or check_float:
					normal_paid_rate = float(params['normal_paid_rate'])
				else:
					validate.append({"error_param" : "normal_paid_rate","msg" : "Normal paid rate is not a number."})
			if params['normal_received_rate']=="" or params['normal_received_rate'] is None:
				validate.append({"error_param" : "normal_received_rate","msg" : "Normal received rate is required."})
			else:
				check_int = isinstance(params['normal_received_rate'], int)
				check_float = isinstance(params['normal_received_rate'], float)

				if check_int or check_float:
					normal_received_rate = float(params['normal_received_rate'])
				else:
					validate.append({"error_param" : "normal_received_rate","msg" : "Normal received rate is not a number."})
			if params['overtime_paid_rate']=="" or params['overtime_paid_rate'] is None:
				validate.append({"error_param" : "overtime_paid_rate","msg" : "Overtime paid rate is required."})
			else:
				check_int = isinstance(params['overtime_paid_rate'], int)
				check_float = isinstance(params['overtime_paid_rate'], float)

				if check_int or check_float:
					overtime_paid_rate = float(params['overtime_paid_rate'])
				else:
					validate.append({"error_param" : "overtime_paid_rate","msg" : "Overtime paid rate is not a number."})
			if params['overtime_received_rate']=="" or params['overtime_received_rate'] is None:
				validate.append({"error_param" : "overtime_received_rate","msg" : "Overtime received rate is required."})
			else:
				check_int = isinstance(params['overtime_received_rate'], int)
				check_float = isinstance(params['overtime_received_rate'], float)

				if check_int or check_float:
					overtime_received_rate = float(params['overtime_received_rate'])
				else:
					validate.append({"error_param" : "overtime_received_rate","msg" : "Overtime received rate is not a number."})

			#set communication_en & communication_th
			communication_in = []
			for i in range(len(params['communication'])):
				communication_in.append(ObjectId(params['communication'][i]))

			communication = db.communication.find({"_id" : {"$in" : communication_in}})

			if communication is None or communication.count() == 0:
				validate.append({"error_param" : "communication","msg" : "Please check your communication value."})
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)

				communication_list = []

				communication_en = ""
				communication_th = ""

				for i in range(len(communication_json)):
					if i == 0:
						communication_en = communication_json[i]['lang_name_en']
						communication_th = communication_json[i]['lang_name_th']
					else:
						communication_en = communication_en+" , "+communication_json[i]['lang_name_en']
						communication_th = communication_th+" , "+communication_json[i]['lang_name_th']

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				package = db.package.find_one({
												"_id": ObjectId(params['package_id'])
											})
				if package is None:
					result = { 
								"status" : False,
								"msg" : "Package not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					#ถ้าไม่มีการแก้ไขรูป profile (profile_image เป็น null) ไม่ต้องอัพเดตรูป  
					if params['package_image'] is None:
						image_name = package_json['package_image']
					else:
						#เช็ค path และลบรูปเก่า
						if package_json['package_image'] is not None:
							if os.path.exists("static/images/package/"+package_json['package_image']):
								os.remove("static/images/package/"+package_json['package_image'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_package_image(params['package_image'], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

					special_company_list = []

					if params['package_model'] == "special":
						for i in range(len(params['special_company'])):
							special_company_list.append(params['special_company'][i]['value'])

					if params['package_type'] == "time":
						hour_amount = None
						time_amount = int(params['time_amount'])
					else:
						hour_amount = int(params['hour_amount'])
						time_amount = None


					if params['package_status'] is None:
						package_status = package_json['package_status']
					elif params['package_status'] == "0":
						package_status = "0"
					else:
						package_status = "1"

					if params['package_detail_en']=="" or params['package_detail_en'] is None:
						package_detail_en = ""
					else:
						package_detail_en = params['package_detail_en']
					if params['package_detail_th']=="" or params['package_detail_th'] is None:
						package_detail_th = ""
					else:
						package_detail_th = params['package_detail_th']

					if params['package_condition_en']=="" or params['package_condition_en'] is None:
						package_condition_en = ""
					else:
						package_condition_en = params['package_condition_en']
					if params['package_condition_th']=="" or params['package_condition_th'] is None:
						package_condition_th = ""
					else:
						package_condition_th = params['package_condition_th']

					vat_rate = get_vat_rate()
					package_price_vat = round(((package_price * vat_rate) / 100) , 2)
					package_price_not_vat = round(package_price - package_price_vat , 2)
					package_price_text = str(package_price)

					# update data
					where_param = { "_id": ObjectId(params['package_id']) }
					value_param = {
									"$set":
										{
											"package_name_en": params['package_name_en'],
											"package_name_th": params['package_name_th'],
											"package_detail_en": package_detail_en,
											"package_detail_th": package_detail_th,
											"package_condition_en": package_condition_en,
											"package_condition_th": package_condition_th,
											"package_model": params['package_model'],
											"package_type": params['package_type'],
											"hour_amount": hour_amount,
											"time_amount": time_amount,
											"package_price": package_price,
											"package_price_text": package_price_text,
											"package_price_not_vat": package_price_not_vat,
											"package_price_vat": package_price_vat,
											"vat_rate": vat_rate,
											"total_usage_date": total_usage_date,
											"special_company": special_company_list,
											"service_time": params['service_time'],
											"driver_level": params['driver_level'],
											"communication": params['communication'],
											"communication_en": communication_en,
											"communication_th": communication_th,
											"normal_paid_rate": normal_paid_rate,
											"normal_received_rate": normal_received_rate,
											"overtime_paid_rate": overtime_paid_rate,
											"overtime_received_rate": overtime_received_rate,
											"package_status": package_status,
											"package_image": image_name,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.package.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit package success."
								}
					else:
						result = {
									"status" : False,
									"msg" : "Data update failed."
								}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "edit_package"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_package(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['package_id']) }
			value_param = {
							"$set":
								{
									"package_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.package.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Delete package success."
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
	function_name = "delete_package"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_register_channel = "register_channel" in params
	isset_company_status = "company_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_register_channel and isset_company_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				# company = db.company.find()

				# if company is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	company_object = dumps(company)
				# 	company_json = json.loads(company_object)

				# 	for i in range(len(company_json)):
				# 		if company_json[i]['os_type'] == "ios" or company_json[i]['os_type'] == "android":
				# 			register_channel = "app"
				# 		else:
				# 			register_channel = "web"

				# 		# update data
				# 		where_param = { "_id": ObjectId(company_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"register_channel": register_channel
				# 							}
				# 					}

				# 		db.company.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = {}

				#company_tax_id , company_name , company_tel
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "company_tax_id": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "company_tel": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['company_status'] == "":
					add_params = {"company_status" : {"$in" : ["1","2","3","4"]}}
					where_param.update(add_params)
				else:
					add_params = {"company_status": params['company_status']}
					where_param.update(add_params)

				if params['register_channel'] == "web":
					add_params = {"os_type" : "web"}
					where_param.update(add_params)
				elif params['register_channel'] == "app":
					add_params = {"os_type" : {"$in" : ["ios","android"]}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# company_name = company_name
					# company_tax_id = company_tax_id
					# company_tel = company_tel
					# register_channel_show = register_channel
					# company_status_show = company_status

					if params['sort_name'] == "register_channel_show":
						sort_name = "register_channel"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				company = db.company_history.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.company_history.find(where_param).count()

				if company is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)

					company_list = []

					for i in range(len(company_json)):
						if company_json[i]['os_type'] == "ios" or company_json[i]['os_type'] == "android":
							register_channel = "app"
							register_channel_show = "ผ่าน App"
						else:
							register_channel = "web"
							register_channel_show = "ผ่านเว็บไซต์"

						if company_json[i]['company_status'] == "4":
							company_status_show = "ปิดใช้งาน"
						elif company_json[i]['company_status'] == "3":
							company_status_show = "ไม่อนุมัติ"
						elif company_json[i]['company_status'] == "2":
							company_status_show = "รออนุมัติ"
						elif company_json[i]['company_status'] == "1":
							company_status_show = "เปิดใช้งาน"

						company_list.append({
							"id" : company_json[i]['_id']['$oid'],
							"company_id" : company_json[i]['company_id'],
							"company_name": company_json[i]['company_name'],
							"company_tax_id": company_json[i]['company_tax_id'],
							"company_tel": company_json[i]['company_tel'],
							"register_channel": register_channel,
							"register_channel_show": register_channel_show,
							"company_status": company_json[i]['company_status'],
							"company_status_show": company_status_show
						})

				result = {
							"status" : True,
							"msg" : "Get company list success.",
							"data" : company_list,
							"total_data" : total_data
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
	function_name = "company_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_form(request):
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

			register_channel_list = [
										{"code": "app","name": "ผ่าน App"},
										{"code": "web","name": "ผ่านเว็บไซต์"}
									]

			status_list = [
							{"code": "1","name": "เปิดใช้งาน"},
							{"code": "2","name": "รออนุมัติ"},
							{"code": "3","name": "ไม่อนุมัติ"},
							{"code": "4","name": "ปิดใช้งาน"}
						]

			result = {
						"status" : True,
						"msg" : "Get company form success.",
						"register_channel" : register_channel_list,
						"status" : status_list
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
	function_name = "get_company_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_info_backend(company_history_id,request):
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

			company = db.company_history.find_one({"_id": ObjectId(company_history_id)})

			if company is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)

				if company_json['os_type'] == "ios" or company_json['os_type'] == "android":
					register_channel = "app"
					register_channel_show = "ผ่าน App"
				else:
					register_channel = "web"
					register_channel_show = "ผ่านเว็บไซต์"

				if company_json['company_status'] == "4":
					company_status_show = "ปิดใช้งาน"
				elif company_json['company_status'] == "3":
					company_status_show = "ไม่อนุมัติ"
				elif company_json['company_status'] == "2":
					company_status_show = "รออนุมัติ"
				elif company_json['company_status'] == "1":
					company_status_show = "เปิดใช้งาน"

				data = {
							"id": company_json['_id']['$oid'],
							"company_id": company_json['company_id'],
							"company_name": company_json['company_name'],
							"company_tax_id": company_json['company_tax_id'],
							"company_email": company_json['company_email'],
							"company_tel": company_json['company_tel'],

							"company_address": company_json['company_address'],
							"company_postcode": company_json['company_postcode'],
							"company_province": company_json['company_province_th'],
							"company_province_code": company_json['company_province_code'],
							"company_district": company_json['company_district_th'],
							"company_district_code": company_json['company_district_code'],
							"company_sub_district": company_json['company_sub_district_th'],
							"company_sub_district_code": company_json['company_sub_district_code'],

							"billing_date": company_json['billing_date'],
							"billing_receiver_firstname": company_json['billing_receiver_firstname'],
							"billing_receiver_lastname": company_json['billing_receiver_lastname'],
							"billing_receiver_email": company_json['billing_receiver_email'],
							"billing_receiver_tel": company_json['billing_receiver_tel'],
							"same_company_address": company_json['same_company_address'],

							"billing_address": company_json['billing_address'],
							"billing_postcode": company_json['billing_postcode'],
							"billing_province": company_json['billing_province_th'],
							"billing_province_code": company_json['billing_province_code'],
							"billing_district": company_json['billing_district_th'],
							"billing_district_code": company_json['billing_district_code'],
							"billing_sub_district": company_json['billing_sub_district_th'],
							"billing_sub_district_code": company_json['billing_sub_district_code'],

							"vat_registration_doc": company_json['vat_registration_doc'],
							"vat_registration_doc_type": company_json['vat_registration_doc_type'],
							"vat_registration_doc_name": company_json['vat_registration_doc_name'],
							"company_certificate_doc": company_json['company_certificate_doc'],
							"company_certificate_doc_type": company_json['company_certificate_doc_type'],
							"company_certificate_doc_name": company_json['company_certificate_doc_name'],
							"company_logo": company_json['company_logo'],
							"register_channel": register_channel,
							"register_channel_show": register_channel_show,
							"company_status": company_json['company_status'],
							"company_status_show": company_status_show
						}

				result = {
							"status" : True,
							"msg" : "Get company info success.",
							"data" : data
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
	function_name = "get_company_info_backend"
	request_headers = request.headers
	params_get = {"company_history_id" : company_history_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

# def edit_company_backend(request):
# 	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_accept = "Accept" in request.headers
# 	isset_content_type = "Content-Type" in request.headers
# 	isset_token = "Authorization" in request.headers
# 	admin_id = None

# 	params = json.loads(request.data)

# 	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_app_version = "app_version" in params
# 	isset_id = "id" in params
# 	isset_company_status = "company_status" in params

# 	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_id and isset_company_status:
# 		#เช็ค token ว่า expire แล้วหรือยัง
# 		token = request.headers['Authorization']
# 		check_token = check_token_expire_backend(token)

# 		if check_token:
# 			admin_info = get_admin_info(token)
# 			admin_id = admin_info['_id']['$oid']
# 			company_status_text = str(params['company_status'])

# 			#ถ้า company_status = '3' แสดงว่าไม่อนุมัติ
# 			if company_status_text == "3":
# 				company_status = "0"
# 				company_history_status = "3"
# 			#ถ้า company_status = '2' แสดงว่ารออนุมัติ หรือ company_status = '1' แสดงว่าอนุมัติ หรือ company_status = '4' แสดงว่าปิดใช้งาน ให้อัพเดตเป็นสถานะเดิม
# 			else:
# 				company_status = company_status_text
# 				company_history_status = company_status_text

# 			company = db.company_history.find_one({"_id": ObjectId(params['id'])})

# 			if company is None:
# 				result = { 
# 							"status" : False,
# 							"msg" : "Data not found."
# 						}
# 			else:
# 				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 				company_object = dumps(company)
# 				company_json = json.loads(company_object)
# 				company_id = company_json['company_id']

# 				comp = db.company.find_one({"_id": ObjectId(company_id)})
# 				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 				comp_object = dumps(comp)
# 				comp_json = json.loads(comp_object)
# 				approved_at = comp_json['approved_at']

# 				#ถ้า company_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
# 				if company_status == "1" and approved_at is None:
# 					# update data to tb member
# 					where_param = { "company_id": company_id }
# 					value_param = {
# 										"$set":
# 											{
# 												"member_status": "1",
# 												"company_status": company_status,
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 												"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}
# 				else:
# 					if company_status == "1":
# 						member_status = "1"
# 					else:
# 						member_status = "0"

# 					# update data to tb member
# 					where_param = { "company_id": company_id }
# 					value_param = {
# 										"$set":
# 											{
# 												"member_status": member_status,
# 												"company_status": company_status,
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}

# 				db.member.update(where_param , value_param)

# 				#ถ้า company_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
# 				if company_status == "1" and approved_at is None:
# 					# update data to tb company
# 					where_param = { "_id": ObjectId(company_id) }
# 					value_param = {
# 									"$set":
# 										{
# 											"company_status": company_status,
# 											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 											"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 										}
# 								}
# 				else:
# 					# update data to tb company
# 					where_param = { "_id": ObjectId(company_id) }
# 					value_param = {
# 									"$set":
# 										{
# 											"company_status": company_status,
# 											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 										}
# 								}

# 				if db.company.update(where_param , value_param):
# 					#ถ้า company_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
# 					if company_status == "1" and approved_at is None:
# 						# update data to tb company_history
# 						where_param = { "_id": ObjectId(params['id']) }
# 						value_param = {
# 										"$set":
# 											{
# 												"company_status": company_history_status,
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 												"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}
# 					else:
# 						# update data to tb company_history
# 						where_param = { "_id": ObjectId(params['id']) }
# 						value_param = {
# 										"$set":
# 											{
# 												"company_status": company_history_status,
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}

# 					if db.company_history.update(where_param , value_param):
# 						member = db.member.find_one({"company_id": company_id})
# 						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 						member_object = dumps(member)
# 						member_json = json.loads(member_object)
# 						member_email = member_json['member_email']

# 						#ถ้า company_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
# 						if company_status == "1" and approved_at is None:
# 							#send email
# 							android_link = "https://play.google.com/store"
# 							ios_link = "https://www.apple.com/th/ios/app-store/"
								
# 							email_type = "approve_company"
# 							subject = "VR Driver : อนุมัติสมาชิกนิติบุคคลเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
# 							to_email = member_email.lower()
# 							template_html = "approve_company.html"
# 							data_detail = { "android_link" : android_link , "ios_link" : ios_link }

# 							data_email = { 
# 											"email_type": email_type,
# 											"data": data_detail,
# 											"subject": subject,
# 											"to_email": to_email,
# 											"template_html": template_html,
# 											"send_status": "0",
# 											"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 										}
# 							db.queue_email.insert_one(data_email)

# 							#ถ้า noti_key ไม่ใช่ null แสดงว่า user ใช้งานบน app ให้เตะ user นั้นออกจากระบบ
# 							if member_json['noti_key'] is not None:
# 								# ส่ง noti หา noti_key ค่าเก่า
# 								send_noti_key = member_json['noti_key']
# 								send_noti_title = "There are other users logged in."
# 								send_noti_message = "Please login again later."
# 								send_noti_data = { "action" : "logout" }
# 								send_noti_badge = 1

# 								try:
# 									send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
# 									send_status = True
# 								except:
# 									send_status = False	

# 							#update member_token เป็น null เพื่อเตะ user ที่ใช้งานอยู่ออกจากระบบ
# 							where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
# 							value_param = {
# 											"$set":
# 												{
# 													"member_token": None,
# 													"noti_key": None,
# 													"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 												}
# 										}

# 							db.member.update(where_param , value_param)
# 						elif company_status == "3":
# 							#send email
# 							web_link = "https://play.google.com/store"

# 							email_type = "not_approve_company"
# 							subject = "VR Driver : ไม่อนุมัติสมัครสมาชิกนิติบุคคล"
# 							to_email = member_email.lower()
# 							template_html = "not_approve_company.html"
# 							data_detail = { "web_link" : web_link }

# 							data_email = { 
# 											"email_type": email_type,
# 											"data": data_detail,
# 											"subject": subject,
# 											"to_email": to_email,
# 											"template_html": template_html,
# 											"send_status": "0",
# 											"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 										}
# 							db.queue_email.insert_one(data_email)
# 						else:
# 							#ถ้า noti_key ไม่ใช่ null แสดงว่า user ใช้งานบน app ให้เตะ user นั้นออกจากระบบ
# 							if member_json['noti_key'] is not None:
# 								# ส่ง noti หา noti_key ค่าเก่า
# 								send_noti_key = member_json['noti_key']
# 								send_noti_title = "There are other users logged in."
# 								send_noti_message = "Please login again later."
# 								send_noti_data = { "action" : "logout" }
# 								send_noti_badge = 1

# 								try:
# 									send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
# 									send_status = True
# 								except:
# 									send_status = False	

# 							#update member_token เป็น null เพื่อเตะ user ที่ใช้งานอยู่ออกจากระบบ
# 							where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
# 							value_param = {
# 											"$set":
# 												{
# 													"member_token": None,
# 													"noti_key": None,
# 													"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 												}
# 										}

# 							db.member.update(where_param , value_param)

# 						result = {
# 									"status" : True,
# 									"msg" : "Edit company success."
# 								}
# 					else:
# 						result = {
# 									"status" : False,
# 									"msg" : "Company history update failed."
# 								}
# 				else:
# 					result = {
# 								"status" : False,
# 								"msg" : "Company update failed."
# 							}
# 		else:
# 			result = { 
# 				"status" : False,
# 				"error_code" : 401,
# 				"msg" : "Unauthorized."
# 			}
# 	else:
# 		result = { 
# 					"status" : False,
# 					"msg" : "Please check your parameters."
# 				}

# 	#set log detail
# 	user_type = "admin"
# 	function_name = "edit_company_backend"
# 	request_headers = request.headers
# 	params_get = None
# 	params_post = params
# 	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

# 	return result

#edit
def edit_company_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_id = "id" in params
	isset_company_name = "company_name" in params
	isset_company_tax_id = "company_tax_id" in params
	isset_company_email = "company_email" in params
	isset_company_tel = "company_tel" in params
	isset_company_address = "company_address" in params
	isset_company_postcode = "company_postcode" in params
	isset_company_province_code = "company_province_code" in params
	isset_company_district_code = "company_district_code" in params
	isset_company_sub_district_code = "company_sub_district_code" in params
	isset_billing_date = "billing_date" in params
	isset_billing_receiver_firstname = "billing_receiver_firstname" in params
	isset_billing_receiver_lastname = "billing_receiver_lastname" in params
	isset_billing_receiver_email = "billing_receiver_email" in params
	isset_billing_receiver_tel = "billing_receiver_tel" in params
	isset_same_company_address = "same_company_address" in params
	isset_billing_address = "billing_address" in params
	isset_billing_postcode = "billing_postcode" in params
	isset_billing_province_code = "billing_province_code" in params
	isset_billing_district_code = "billing_district_code" in params
	isset_billing_sub_district_code = "billing_sub_district_code" in params
	isset_company_status = "company_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_id and isset_company_name and isset_company_tax_id and isset_company_email and isset_company_tel and isset_company_address and isset_company_postcode and isset_company_province_code and isset_company_district_code and isset_company_sub_district_code and isset_billing_date and isset_billing_receiver_firstname and isset_billing_receiver_lastname and isset_billing_receiver_email and isset_billing_receiver_tel and isset_same_company_address and isset_billing_address and isset_billing_postcode and isset_billing_province_code and isset_billing_district_code and isset_billing_sub_district_code and isset_company_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
			company_status_text = str(params['company_status'])

			#ถ้า company_status = '3' แสดงว่าไม่อนุมัติ
			if company_status_text == "3":
				company_status = "0"
				company_history_status = "3"
			#ถ้า company_status = '2' แสดงว่ารออนุมัติ หรือ company_status = '1' แสดงว่าอนุมัติ หรือ company_status = '4' แสดงว่าปิดใช้งาน ให้อัพเดตเป็นสถานะเดิม
			else:
				company_status = company_status_text
				company_history_status = company_status_text

			company = db.company_history.find_one({"_id": ObjectId(params['id'])})

			if company is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				company_id = company_json['company_id']

				comp = db.company.find_one({"_id": ObjectId(company_id)})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				comp_object = dumps(comp)
				comp_json = json.loads(comp_object)
				comp_status = comp_json['company_status']
				approved_at = comp_json['approved_at']

				validate = []

				same_company_address = str(params['same_company_address'])

				#check required
				if params['company_name']=="" or params['company_name'] is None:
					validate.append({"error_param" : "company_name","msg" : "Company name is required."}) 
				if params['company_tax_id']=="" or params['company_tax_id'] is None:
					validate.append({"error_param" : "company_tax_id","msg" : "Company tax id is required."}) 
				if params['company_email']=="" or params['company_email'] is None:
					validate.append({"error_param" : "company_email","msg" : "Company e-mail is required."}) 
				if params['company_tel']=="" or params['company_tel'] is None:
					validate.append({"error_param" : "company_tel","msg" : "Company tel is required."}) 

				if params['company_address']=="" or params['company_address'] is None:
					validate.append({"error_param" : "company_address","msg" : "Company address is required."}) 
				if params['company_postcode']=="" or params['company_postcode'] is None:
					validate.append({"error_param" : "company_postcode","msg" : "Company postcode is required."}) 
				if params['company_province_code']=="" or params['company_province_code'] is None:
					validate.append({"error_param" : "company_province_code","msg" : "Company province is required."}) 
				if params['company_district_code']=="" or params['company_district_code'] is None:
					validate.append({"error_param" : "company_district_code","msg" : "Company district is required."}) 
				if params['company_sub_district_code']=="" or params['company_sub_district_code'] is None:
					validate.append({"error_param" : "company_sub_district_code","msg" : "Company sub-district is required."}) 
				
				if params['billing_date']=="" or params['billing_date'] is None:
					validate.append({"error_param" : "billing_date","msg" : "Billing date is required."}) 
				if params['billing_receiver_firstname']=="" or params['billing_receiver_firstname'] is None:
					validate.append({"error_param" : "billing_receiver_firstname","msg" : "Billing receiver firstname is required."}) 
				if params['billing_receiver_lastname']=="" or params['billing_receiver_lastname'] is None:
					validate.append({"error_param" : "billing_receiver_lastname","msg" : "Billing receiver lastname is required."}) 
				if params['billing_receiver_email']=="" or params['billing_receiver_email'] is None:
					validate.append({"error_param" : "billing_receiver_email","msg" : "Billing receiver email is required."}) 
				if params['billing_receiver_tel']=="" or params['billing_receiver_tel'] is None:
					validate.append({"error_param" : "billing_receiver_tel","msg" : "Billing receiver tel is required."}) 

				if same_company_address=="0" and (params['billing_address']=="" or params['billing_address'] is None):
					validate.append({"error_param" : "billing_address","msg" : "Billing address is required."}) 
				if same_company_address=="0" and (params['billing_postcode']=="" or params['billing_postcode'] is None):
					validate.append({"error_param" : "billing_postcode","msg" : "Billing postcode is required."}) 
				if same_company_address=="0" and (params['billing_province_code']=="" or params['billing_province_code'] is None):
					validate.append({"error_param" : "billing_province","msg" : "Billing province is required."}) 
				if same_company_address=="0" and (params['billing_district_code']=="" or params['billing_district_code'] is None):
					validate.append({"error_param" : "billing_district_code","msg" : "Billing district is required."}) 
				if same_company_address=="0" and (params['billing_sub_district_code']=="" or params['billing_sub_district_code'] is None):
					validate.append({"error_param" : "billing_sub_district_code","msg" : "Billing sub-district is required."}) 

				#check already company name
				if params['company_name']!="" and params['company_name'] is not None:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_company_name = db.company.find({
													"_id": {"$ne": ObjectId(company_id)},
													"company_name": params['company_name'].strip(),
													"company_status": "1"
												}).count()
					if check_company_name > 0:
						validate.append({"error_param" : "company_name","msg" : "Company name has been used."}) 

				#check already tax id
				if params['company_tax_id']!="" and params['company_tax_id'] is not None:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_company_tax_id = db.company.find({
													"_id": {"$ne": ObjectId(company_id)},
													"company_tax_id": params['company_tax_id'].strip(),
													"company_status": "1"
												}).count()
					if check_company_tax_id > 0:
						validate.append({"error_param" : "company_tax_id","msg" : "Company tax id has been used."}) 

				#check already company email
				if params['company_email']!="" and params['company_email'] is not None:
					#check email format
					pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
					regex = re.compile(pattern)
					check_format_email = regex.findall(params['company_email'])

					if len(check_format_email) > 0:
						#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
						check_email = db.company.find({
														"_id": {"$ne": ObjectId(company_id)},
														"company_email": params['company_email'].strip().lower(),
														"company_status": "1"
													}).count()
						if check_email > 0:
							validate.append({"error_param" : "company_email","msg" : "Company e-mail has been used."}) 
					else:
						validate.append({"error_param" : "company_email","msg" : "Invalid email format."})

				#check company tel format
				if params['company_tel']!="" and params['company_tel'] is not None:
					tel = params['company_tel'].replace("-", "")
					count_tel = len(tel)

					try:
						data_company_tel = int(params['company_tel'])
						check_data_company_tel = True
					except ValueError:
						check_data_company_tel = False

					if ((count_tel < 9) or (count_tel > 10) or (not check_data_company_tel)):
						validate.append({"error_param" : "company_tel","msg" : "Invalid company tel format."}) 

				#check billing tel format
				if params['billing_receiver_tel']!="" and params['billing_receiver_tel'] is not None:
					tel = params['billing_receiver_tel'].replace("-", "")
					count_tel = len(tel)

					try:
						data_billing_receiver_tel = int(params['billing_receiver_tel'])
						check_data_billing_receiver_tel = True
					except ValueError:
						check_data_billing_receiver_tel = False

					if ((count_tel < 9) or (count_tel > 10) or (not check_data_billing_receiver_tel)):
						validate.append({"error_param" : "billing_receiver_tel","msg" : "Invalid billing tel format."}) 

				#check company postcode format
				if params['company_postcode']!="" and params['company_postcode'] is not None:
					count_postcode = len(params['company_postcode'])

					if count_postcode != 5:
						validate.append({"error_param" : "company_postcode","msg" : "Invalid company postcode format."}) 
				
				#check billing postcode format
				if same_company_address=="0" and (params['billing_postcode']!="" and params['billing_postcode'] is not None):
					count_postcode = len(params['billing_postcode'])

					if count_postcode != 5:
						validate.append({"error_param" : "billing_postcode","msg" : "Invalid billing postcode format."}) 


				#set company_province_en & company_province_th
				province = db.province.find_one({"province_code" : params['company_province_code']})

				if province is None:
					validate.append({"error_param" : "company_province_code","msg" : "Please check your company province code value."}) 
				else:
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					province_object = dumps(province)
					province_json = json.loads(province_object)

					company_province_en = province_json['province_en']
					company_province_th = province_json['province_th']

				#set company_district_en & company_district_th
				district = db.district.find_one({"district_code" : params['company_district_code']})

				if district is None:
					validate.append({"error_param" : "company_district_code","msg" : "Please check your company district code value."}) 
				else:
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					district_object = dumps(district)
					district_json = json.loads(district_object)

					company_district_en = district_json['district_en']
					company_district_th = district_json['district_th']

				#set company_sub_district_en & company_sub_district_th
				sub_district = db.sub_district.find_one({"sub_district_code" : params['company_sub_district_code']})

				if sub_district is None:
					validate.append({"error_param" : "company_sub_district_code","msg" : "Please check your company sub-district code value."}) 
				else:
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					sub_district_object = dumps(sub_district)
					sub_district_json = json.loads(sub_district_object)

					company_sub_district_en = sub_district_json['sub_district_en']
					company_sub_district_th = sub_district_json['sub_district_th']

				
				#ถ้า validate ผ่าน
				if len(validate) == 0:
					#ถ้า company_history_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
					if company_history_status == "1" and approved_at is None:
						# update data to tb member
						where_param = { "company_id": company_id }
						value_param = {
											"$set":
												{
													"member_status": "1",
													"company_status": company_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}
					else:
						if company_status == "1":
							member_status = "1"
						else:
							member_status = "0"

						# update data to tb member
						where_param = { "company_id": company_id }
						value_param = {
											"$set":
												{
													"member_status": member_status,
													"company_status": company_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

					db.member.update(where_param , value_param)

					#คนละที่อยู่
					if same_company_address=="0":
						billing_address = params['billing_address']
						billing_postcode = params['billing_postcode']

						#set billing_province_en & billing_province_th
						billing_province = db.province.find_one({"province_code" : params['billing_province_code']})

						if billing_province is None:
							validate.append({"error_param" : "billing_province_code","msg" : "Please check your billing province code value."}) 
						else:
							# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							billing_province_object = dumps(billing_province)
							billing_province_json = json.loads(billing_province_object)

							billing_province_en = billing_province_json['province_en']
							billing_province_th = billing_province_json['province_th']
							billing_province_code = billing_province_json['province_code']

						#set billing_district_en & billing_district_th
						billing_district = db.district.find_one({"district_code" : params['billing_district_code']})

						if billing_district is None:
							validate.append({"error_param" : "billing_district_code","msg" : "Please check your billing district code value."}) 
						else:
							# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							billing_district_object = dumps(billing_district)
							billing_district_json = json.loads(billing_district_object)

							billing_district_en = billing_district_json['district_en']
							billing_district_th = billing_district_json['district_th']
							billing_district_code = billing_district_json['district_code']

						#set billing_sub_district_en & billing_sub_district_th
						billing_sub_district = db.sub_district.find_one({"sub_district_code" : params['billing_sub_district_code']})

						if billing_sub_district is None:
							validate.append({"error_param" : "billing_sub_district_code","msg" : "Please check your billing sub-district code value."}) 
						else:
							# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							billing_sub_district_object = dumps(billing_sub_district)
							billing_sub_district_json = json.loads(billing_sub_district_object)

							billing_sub_district_en = billing_sub_district_json['sub_district_en']
							billing_sub_district_th = billing_sub_district_json['sub_district_th']
							billing_sub_district_code = billing_sub_district_json['sub_district_code']
					#ที่อยู่เดียวกัน
					else:
						billing_address = params['company_address']
						billing_postcode = params['company_postcode']

						billing_province_en = company_province_en
						billing_province_th = company_province_th
						billing_province_code = params['company_province_code']
						billing_district_en = company_district_en
						billing_district_th = company_district_th
						billing_district_code = params['company_district_code']
						billing_sub_district_en = company_sub_district_en
						billing_sub_district_th = company_sub_district_th
						billing_sub_district_code = params['company_sub_district_code']

					#ถ้า company_history_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
					if company_history_status == "1" and approved_at is None:
						# update data to tb company
						where_param = { "_id": ObjectId(company_id) }
						value_param = {
										"$set":
											{
												"company_name": params['company_name'].strip(),
												"company_tax_id": params['company_tax_id'].strip(),
												"company_email": params['company_email'].strip().lower(),
												"company_tel": params['company_tel'].strip(),
												
												"company_address": params['company_address'].strip(),
												"company_postcode": params['company_postcode'].strip(),
												"company_province_en": company_province_en,
												"company_province_th": company_province_th, 
												"company_province_code": params['company_province_code'],
												"company_district_en": company_district_en,
												"company_district_th": company_district_th, 
												"company_district_code": params['company_district_code'],
												"company_sub_district_en": company_sub_district_en,
												"company_sub_district_th": company_sub_district_th,
												"company_sub_district_code": params['company_sub_district_code'],
												
												"billing_date": params['billing_date'],
												"billing_receiver_firstname": params['billing_receiver_firstname'].strip(),
												"billing_receiver_lastname": params['billing_receiver_lastname'].strip(),
												"billing_receiver_email": params['billing_receiver_email'].strip().lower(),
												"billing_receiver_tel": params['billing_receiver_tel'].strip(),
											
												"same_company_address": same_company_address,
												"billing_address": billing_address.strip(),
												"billing_postcode": billing_postcode.strip(),
												"billing_province_en": billing_province_en,
												"billing_province_th": billing_province_th, 
												"billing_province_code": billing_province_code,
												"billing_district_en": billing_district_en,
												"billing_district_th": billing_district_th, 
												"billing_district_code": billing_district_code,
												"billing_sub_district_en": billing_sub_district_en,
												"billing_sub_district_th": billing_sub_district_th,
												"billing_sub_district_code": billing_sub_district_code,

												"company_status": company_status,
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}
					else:
						#สามารถแก้ไขข้อมูลบริษัทได้เฉพาะ company_history_status = '1' เท่านั้น
						if company_history_status == "1":
							# update data to tb company
							where_param = { "_id": ObjectId(company_id) }
							value_param = {
											"$set":
												{
													"company_name": params['company_name'].strip(),
													"company_tax_id": params['company_tax_id'].strip(),
													"company_email": params['company_email'].strip().lower(),
													"company_tel": params['company_tel'].strip(),
													
													"company_address": params['company_address'].strip(),
													"company_postcode": params['company_postcode'].strip(),
													"company_province_en": company_province_en,
													"company_province_th": company_province_th, 
													"company_province_code": params['company_province_code'],
													"company_district_en": company_district_en,
													"company_district_th": company_district_th, 
													"company_district_code": params['company_district_code'],
													"company_sub_district_en": company_sub_district_en,
													"company_sub_district_th": company_sub_district_th,
													"company_sub_district_code": params['company_sub_district_code'],
													
													"billing_date": params['billing_date'],
													"billing_receiver_firstname": params['billing_receiver_firstname'].strip(),
													"billing_receiver_lastname": params['billing_receiver_lastname'].strip(),
													"billing_receiver_email": params['billing_receiver_email'].strip().lower(),
													"billing_receiver_tel": params['billing_receiver_tel'].strip(),
												
													"same_company_address": same_company_address,
													"billing_address": billing_address.strip(),
													"billing_postcode": billing_postcode.strip(),
													"billing_province_en": billing_province_en,
													"billing_province_th": billing_province_th, 
													"billing_province_code": billing_province_code,
													"billing_district_en": billing_district_en,
													"billing_district_th": billing_district_th, 
													"billing_district_code": billing_district_code,
													"billing_sub_district_en": billing_sub_district_en,
													"billing_sub_district_th": billing_sub_district_th,
													"billing_sub_district_code": billing_sub_district_code,

													"company_status": company_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}
						else:
							# update data to tb company
							where_param = { "_id": ObjectId(company_id) }
							value_param = {
											"$set":
												{
													"company_status": company_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

					if db.company.update(where_param , value_param):
						#ถ้า company_history_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
						if company_history_status == "1" and approved_at is None:
							# update data to tb company_history
							where_param = { "_id": ObjectId(params['id']) }
							value_param = {
											"$set":
												{
													"company_name": params['company_name'].strip(),
													"company_tax_id": params['company_tax_id'].strip(),
													"company_email": params['company_email'].strip().lower(),
													"company_tel": params['company_tel'].strip(),
													
													"company_address": params['company_address'].strip(),
													"company_postcode": params['company_postcode'].strip(),
													"company_province_en": company_province_en,
													"company_province_th": company_province_th, 
													"company_province_code": params['company_province_code'],
													"company_district_en": company_district_en,
													"company_district_th": company_district_th, 
													"company_district_code": params['company_district_code'],
													"company_sub_district_en": company_sub_district_en,
													"company_sub_district_th": company_sub_district_th,
													"company_sub_district_code": params['company_sub_district_code'],
													
													"billing_date": params['billing_date'],
													"billing_receiver_firstname": params['billing_receiver_firstname'].strip(),
													"billing_receiver_lastname": params['billing_receiver_lastname'].strip(),
													"billing_receiver_email": params['billing_receiver_email'].strip().lower(),
													"billing_receiver_tel": params['billing_receiver_tel'].strip(),
												
													"same_company_address": same_company_address,
													"billing_address": billing_address.strip(),
													"billing_postcode": billing_postcode.strip(),
													"billing_province_en": billing_province_en,
													"billing_province_th": billing_province_th, 
													"billing_province_code": billing_province_code,
													"billing_district_en": billing_district_en,
													"billing_district_th": billing_district_th, 
													"billing_district_code": billing_district_code,
													"billing_sub_district_en": billing_sub_district_en,
													"billing_sub_district_th": billing_sub_district_th,
													"billing_sub_district_code": billing_sub_district_code,

													"company_status": company_history_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}
						#ถ้า company_status = '3' แสดงว่าไม่อนุมัติ และยังไม่เคยอนุมัติ
						elif company_history_status == "3" and approved_at is None:
							# update data to tb company_history
							where_param = { "_id": ObjectId(params['id']) }
							value_param = {
											"$set":
												{
													"company_status": company_history_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}
						else:
							#สามารถแก้ไขข้อมูลบริษัทได้เฉพาะ company_history_status = '1' เท่านั้น
							if company_history_status == "1":
								# update data to tb company_history
								where_param = { "_id": ObjectId(params['id']) }
								value_param = {
												"$set":
													{
														"company_name": params['company_name'].strip(),
														"company_tax_id": params['company_tax_id'].strip(),
														"company_email": params['company_email'].strip().lower(),
														"company_tel": params['company_tel'].strip(),
														
														"company_address": params['company_address'].strip(),
														"company_postcode": params['company_postcode'].strip(),
														"company_province_en": company_province_en,
														"company_province_th": company_province_th, 
														"company_province_code": params['company_province_code'],
														"company_district_en": company_district_en,
														"company_district_th": company_district_th, 
														"company_district_code": params['company_district_code'],
														"company_sub_district_en": company_sub_district_en,
														"company_sub_district_th": company_sub_district_th,
														"company_sub_district_code": params['company_sub_district_code'],
														
														"billing_date": params['billing_date'],
														"billing_receiver_firstname": params['billing_receiver_firstname'].strip(),
														"billing_receiver_lastname": params['billing_receiver_lastname'].strip(),
														"billing_receiver_email": params['billing_receiver_email'].strip().lower(),
														"billing_receiver_tel": params['billing_receiver_tel'].strip(),
													
														"same_company_address": same_company_address,
														"billing_address": billing_address.strip(),
														"billing_postcode": billing_postcode.strip(),
														"billing_province_en": billing_province_en,
														"billing_province_th": billing_province_th, 
														"billing_province_code": billing_province_code,
														"billing_district_en": billing_district_en,
														"billing_district_th": billing_district_th, 
														"billing_district_code": billing_district_code,
														"billing_sub_district_en": billing_sub_district_en,
														"billing_sub_district_th": billing_sub_district_th,
														"billing_sub_district_code": billing_sub_district_code,

														"company_status": company_history_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
							else:
								# update data to tb company_history
								where_param = { "_id": ObjectId(params['id']) }
								value_param = {
												"$set":
													{
														"company_status": company_history_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

						if db.company_history.update(where_param , value_param):
							member = db.member.find_one({"company_id": company_id})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							member_object = dumps(member)
							member_json = json.loads(member_object)
							member_email = member_json['member_email']

							#ถ้า company_history_status = '1' แสดงว่าอนุมัติ และยังไม่เคยอนุมัติ
							if company_history_status == "1" and approved_at is None:
								#send email
								android_link = "https://play.google.com/store"
								ios_link = "https://www.apple.com/th/ios/app-store/"
									
								email_type = "approve_company"
								subject = "VR Driver : อนุมัติสมาชิกนิติบุคคลเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
								to_email = member_email.lower()
								template_html = "approve_company.html"
								data_detail = { "android_link" : android_link , "ios_link" : ios_link }

								data_email = { 
												"email_type": email_type,
												"data": data_detail,
												"subject": subject,
												"to_email": to_email,
												"template_html": template_html,
												"send_status": "0",
												"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
								db.queue_email.insert_one(data_email)

								#ถ้า noti_key ไม่ใช่ null แสดงว่า user ใช้งานบน app ให้เตะ user นั้นออกจากระบบ
								if member_json['noti_key'] is not None:
									# ส่ง noti หา noti_key ค่าเก่า
									send_noti_key = member_json['noti_key']
									send_noti_title = "There are other users logged in."
									send_noti_message = "Please login again later."
									send_noti_data = { "action" : "logout" }
									send_noti_badge = 1

									try:
										send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
										send_status = True
									except:
										send_status = False	

								#update member_token เป็น null เพื่อเตะ user ที่ใช้งานอยู่ออกจากระบบ
								where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
								value_param = {
												"$set":
													{
														"member_token": None,
														"noti_key": None,
														"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								db.member.update(where_param , value_param)
							#ถ้า company_history_status = '3' แสดงว่าไม่อนุมัติ และยังไม่เคยอนุมัติ
							elif company_history_status == "3" and approved_at is None:
								#send email
								web_link = "https://play.google.com/store"

								email_type = "not_approve_company"
								subject = "VR Driver : ไม่อนุมัติสมัครสมาชิกนิติบุคคล"
								to_email = member_email.lower()
								template_html = "not_approve_company.html"
								data_detail = { "web_link" : web_link }

								data_email = { 
												"email_type": email_type,
												"data": data_detail,
												"subject": subject,
												"to_email": to_email,
												"template_html": template_html,
												"send_status": "0",
												"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
								db.queue_email.insert_one(data_email)
							else:
								#ถ้า company_status ปัจจุบันไม่เท่ากับ company_history_status ที่ส่งเข้ามา ให้เตะ user ที่กำลัง login ออกจากระบบ
								if comp_status != company_history_status:
									#ถ้า noti_key ไม่ใช่ null แสดงว่า user ใช้งานบน app ให้เตะ user นั้นออกจากระบบ
									if member_json['noti_key'] is not None:
										# ส่ง noti หา noti_key ค่าเก่า
										send_noti_key = member_json['noti_key']
										send_noti_title = "There are other users logged in."
										send_noti_message = "Please login again later."
										send_noti_data = { "action" : "logout" }
										send_noti_badge = 1

										try:
											send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
											send_status = True
										except:
											send_status = False	

									#update member_token เป็น null เพื่อเตะ user ที่ใช้งานอยู่ออกจากระบบ
									where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
									value_param = {
													"$set":
														{
															"member_token": None,
															"noti_key": None,
															"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}

									db.member.update(where_param , value_param)

							result = {
										"status" : True,
										"msg" : "Edit company success."
									}
						else:
							result = {
										"status" : False,
										"msg" : "Company history update failed."
									}
					else:
						result = {
									"status" : False,
									"msg" : "Company update failed." 
								}
				else:
					result = {
								"status" : False,
								"msg" : "Please check your parameters value.", 
								"error_list" : validate
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
	function_name = "edit_company_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def driver_register_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_register_date = "register_date" in params
	isset_member_status = "member_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_register_date and isset_member_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:

				# member = db.member.find()

				# if member is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	member_object = dumps(member)
				# 	member_json = json.loads(member_object)

				# 	for i in range(len(member_json)):
						
				# 		member_name_en = member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']
				# 		member_name_th = member_json[i]['member_firstname_th']+" "+member_json[i]['member_lastname_th']
				# 		register_date_int = int(datetime.strptime(member_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				# 		# update data
				# 		where_param = { "_id": ObjectId(member_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"member_name_en": member_name_en,
				# 								"member_name_th": member_name_th,
				# 								"register_date_int": register_date_int
				# 							}
				# 					}

				# 		db.member.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}



				where_param = { "member_type" : "driver" }

				#member_fullname , member_tel
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "member_firstname_en": {"$regex": params['search_text']} },
												{ "member_lastname_en": {"$regex": params['search_text']} },
												{ "member_firstname_th": {"$regex": params['search_text']} },
												{ "member_lastname_th": {"$regex": params['search_text']} },
												{ "member_tel": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['member_status'] == "0" or params['member_status'] == "2":
					add_params = {"member_status" : params['member_status']}
					where_param.update(add_params)
				else:
					add_params = {"member_status" : {"$in" : ["0","2"]}}
					where_param.update(add_params)

				if params['register_date'] != "":
					register_date_int = int(datetime.strptime(params['register_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"register_date_int" : register_date_int}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# member_fullname = member_name
					# member_tel = member_tel
					# register_date = created_at
					# register_status_show = member_status

					if params['sort_name'] == "member_fullname":
						sort_name = "member_name_th"
					elif params['sort_name'] == "register_date":
						sort_name = "created_at"
					elif params['sort_name'] == "register_status_show":
						sort_name = "member_status"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				driver = db.member.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.member.find(where_param).count()

				if driver is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					driver_object = dumps(driver)
					driver_json = json.loads(driver_object)

					driver_register_list = []

					for i in range(len(driver_json)):
						if driver_json[i]['member_status'] == "2":
							register_status_show = "ไม่อนุมัติ"
						else:
							register_status_show = "รออนุมัติ"

						approved_by_name = None
						if driver_json[i]['member_status'] != "0":
							approved_by_name = driver_json[i]['approved_by_name'] 

						register_date = datetime.strptime(driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

						driver_register_list.append({
							"member_id" : driver_json[i]['_id']['$oid'],
							"member_fullname": driver_json[i]['member_firstname_th']+" "+driver_json[i]['member_lastname_th'],
							"member_tel": driver_json[i]['member_tel'],
							"member_status": driver_json[i]['member_status'],
							"register_status_show": register_status_show,
							"register_date": register_date,
							"approved_by_name": approved_by_name
						})

				result = {
							"status" : True,
							"msg" : "Get driver register list success.",
							"data" : driver_register_list,
							"total_data" : total_data
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
	function_name = "driver_register_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_driver_register_form(request):
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

			driver_level = db.driver_level.find({"level_status": "1"})
			driver_level_list = []

			if driver_level is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)

				for i in range(len(driver_level_json)):
					driver_level_list.append({
						"id" : driver_level_json[i]['_id']['$oid'],
						"name": driver_level_json[i]['level_name_th']
					})

			driver_status_list = [
							{"code": "0","name": "รออนุมัติ"},
							{"code": "1","name": "อนุมัติ"},
							{"code": "2","name": "ไม่อนุมัติ"}
						]

			result = {
						"status" : True,
						"msg" : "Get driver register form success.",
						"driver_level" : driver_level_list,
						"driver_status" : driver_status_list
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
	function_name = "get_driver_register_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def get_driver_detail(member_id,request):
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

			driver = db.member.find_one({"_id": ObjectId(member_id), "member_type" : "driver"})
			if driver is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_object = dumps(driver)
				driver_json = json.loads(driver_object)	

				#ถ้า driver_level ไม่ใช่ null ให้ดึง driver_level_th มาแสดง 
				driver_level_text = None

				if driver_json['driver_level'] is not None:
					driver_level = db.driver_level.find_one({"_id": ObjectId(driver_json['driver_level'])})
					
					if driver_level is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						driver_level_object = dumps(driver_level)
						driver_level_json = json.loads(driver_level_object)

						driver_level_text = driver_level_json["level_name_th"]

				if driver_json['member_status'] == "4":
					register_status_show = "พักการให้บริการชั่วคราว"
				elif driver_json['member_status'] == "3":
					register_status_show = "พักการให้บริการ"
				elif driver_json['member_status'] == "2":
					register_status_show = "ไม่อนุมัติ"
				elif driver_json['member_status'] == "1":
					register_status_show = "อนุมัติ"
				else:
					register_status_show = "รอตรวจสอบ"

				member_birthday = None
				driver_license_expire = None
				break_start_date = None
				break_end_date = None
				register_date = None

				if driver_json['member_birthday'] is not None:
					member_birthday = datetime.strptime(driver_json['member_birthday'], '%Y-%m-%d').strftime('%d/%m/%Y')

				if driver_json['driver_license_expire'] is not None:
					driver_license_expire = datetime.strptime(driver_json['driver_license_expire'], '%Y-%m-%d').strftime('%d/%m/%Y')
				
				if driver_json['break_start_date'] is not None:
					break_start_date = datetime.strptime(driver_json['break_start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				
				if driver_json['break_end_date'] is not None:
					break_end_date = datetime.strptime(driver_json['break_end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				
				if driver_json['created_at'] is not None:
					register_date = datetime.strptime(driver_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

				if driver_json['driver_rating'] is not None:
					driver_rating = round(float(driver_json['driver_rating']) , 1)
				else:
					driver_rating = float("0")

				data = {
							"member_id": driver_json['_id']['$oid'],
							"member_code": driver_json['member_code'],
							"member_username": driver_json['member_username'],
							"member_firstname_en": driver_json['member_firstname_en'],
							"member_lastname_en": driver_json['member_lastname_en'],
							"member_firstname_th": driver_json['member_firstname_th'],
							"member_lastname_th": driver_json['member_lastname_th'],
							"member_email": driver_json['member_email'],
							"member_tel": driver_json['member_tel'],

							"member_birthday": member_birthday,
							"member_gender": driver_json['member_gender'],
							"driver_license_expire": driver_license_expire,
							"driver_license_no": driver_json['driver_license_no'],

							"car_type": driver_json['car_type'],
							"car_type_text": driver_json['car_type_th'],
							"car_gear": driver_json['car_gear'],
							"car_gear_text": driver_json['car_gear_th'],
							"service_area": driver_json['service_area'],
							"service_area_text": driver_json['service_area_th'],
							"communication": driver_json['communication'],
							"communication_text": driver_json['communication_th'],
							"workday": driver_json['workday'],
							"workday_text": driver_json['workday_th'],
							"special_skill": driver_json['special_skill'],
							"special_skill_text": driver_json['special_skill_th'],

							"driver_level": driver_json['driver_level'],
							"driver_level_text": driver_level_text,
							"driver_rating": driver_rating,
							"profile_image": driver_json['profile_image'],
							"member_lang": driver_json['member_lang'],
							"member_status": driver_json['member_status'],
							"register_status_show": register_status_show,
							"break_start_date": break_start_date,
							"break_end_date": break_end_date,

							"register_date": register_date,
							"os_type": driver_json['os_type']
						}

				result = {
							"status" : True,
							"msg" : "Get driver detail success.",
							"data" : data
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
	function_name = "get_driver_detail"
	request_headers = request.headers
	params_get = {"member_id" : member_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_register(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_driver_level_id = "driver_level_id" in params
	isset_member_status = "member_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_driver_level_id and isset_member_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
			member_info = get_member_info_by_id(params['member_id'])

			validate = []

			if params['member_status'] == "1" and params['driver_level_id'] is None and params['driver_level_id'] == "":
				validate.append({"error_param" : "driver_level_id","msg" : "Please check your driver level."})

				result = {
							"status" : False,
							"msg" : "Please check your driver level.",
							"error_list" : validate
						}
			#member_status = 0 , 1 , 2 and driver_level_id != None
			else:
				if params['driver_level_id'] is None:
					driver_level = None
					driver_level_priority = 0
					driver_level_text = None
				else:
					driver_level = params['driver_level_id']

					dl = db.driver_level.find_one({"_id": ObjectId(params['driver_level_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					dl_object = dumps(dl)
					dl_json = json.loads(dl_object)
					driver_level_priority = int(dl_json['level_priority'])
					driver_level_text = dl_json['level_name_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"driver_level": driver_level,
										"driver_level_text": driver_level_text,
										"driver_level_priority": driver_level_priority,
										"member_status": params['member_status'],
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"approved_by_id": admin_info['_id']['$oid'],
										"approved_by_name": admin_info['admin_firstname']+" "+admin_info['admin_lastname']
									}
							}

				if db.member.update(where_param , value_param):
					if params['member_status'] == "1":
						#send email
						android_link = "https://play.google.com/store"
						ios_link = "https://www.apple.com/th/ios/app-store/"
							
						email_type = "approve_driver"
						subject = "VR Driver : อนุมัติสมาชิกคนขับเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
						to_email = member_info['member_email'].lower()
						template_html = "approve_driver.html"
						data_detail = { "android_link" : android_link , "ios_link" : ios_link }

						data_email = { 
										"email_type": email_type,
										"data": data_detail,
										"subject": subject,
										"to_email": to_email,
										"template_html": template_html,
										"send_status": "0",
										"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
						db.queue_email.insert_one(data_email)
						
					elif params['member_status'] == "2":
						#send email
						android_link = "https://play.google.com/store"
						ios_link = "https://www.apple.com/th/ios/app-store/"
							
						email_type = "not_approve_driver"
						subject = "VR Driver : ไม่อนุมัติสมาชิกคนขับเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
						to_email = member_info['member_email'].lower()
						template_html = "not_approve_driver.html"
						data_detail = { "android_link" : android_link , "ios_link" : ios_link }

						data_email = { 
										"email_type": email_type,
										"data": data_detail,
										"subject": subject,
										"to_email": to_email,
										"template_html": template_html,
										"send_status": "0",
										"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
						db.queue_email.insert_one(data_email)

					result = {
								"status" : True,
								"msg" : "Edit driver register success."
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
	function_name = "edit_driver_register"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def driver_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_driver_level = "driver_level" in params
	isset_register_date = "register_date" in params
	isset_member_status = "member_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_driver_level and isset_register_date and isset_member_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:

				# member = db.member.find({"member_type" : "driver"})

				# if member is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	member_object = dumps(member)
				# 	member_json = json.loads(member_object)

				# 	for i in range(len(member_json)):
						
				# 		member_name_en = member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']
				# 		member_name_th = member_json[i]['member_firstname_th']+" "+member_json[i]['member_lastname_th']
				# 		register_date_int = int(datetime.strptime(member_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				# 		driver_level_text = None

				# 		if member_json[i]['driver_level'] is not None:
				# 			driver_level = db.driver_level.find_one({"_id": ObjectId(member_json[i]['driver_level'])})
				# 			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 			driver_level_object = dumps(driver_level)
				# 			driver_level_json = json.loads(driver_level_object)
				# 			driver_level_text = driver_level_json["level_name_th"]

				# 		# update data
				# 		where_param = { "_id": ObjectId(member_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"driver_level_text": driver_level_text
				# 							}
				# 					}

				# 		db.member.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = { "member_type" : "driver" }

				#member_code , member_fullname , member_tel
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "member_code": {"$regex": params['search_text']} },
												{ "member_firstname_en": {"$regex": params['search_text']} },
												{ "member_lastname_en": {"$regex": params['search_text']} },
												{ "member_firstname_th": {"$regex": params['search_text']} },
												{ "member_lastname_th": {"$regex": params['search_text']} },
												{ "member_tel": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['member_status'] == "1" or params['member_status'] == "3" or params['member_status'] == "4":
					add_params = {"member_status" : params['member_status']}
					where_param.update(add_params)
				else:
					add_params = {"member_status" : {"$in" : ["1","3","4"]}}
					where_param.update(add_params)

				if params['register_date'] != "":
					register_date_int = int(datetime.strptime(params['register_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"register_date_int" : register_date_int}
					where_param.update(add_params)

				if params['driver_level'] != "":
					add_params = {"driver_level" : params['driver_level']}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# member_code = member_code
					# member_fullname = member_name
					# member_tel = member_tel
					# driver_level_text = driver_level_text
					# register_status_show = member_status

					if params['sort_name'] == "member_fullname":
						sort_name = "member_name_th"
					elif params['sort_name'] == "register_status_show":
						sort_name = "member_status"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				driver = db.member.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.member.find(where_param).count()

				if driver is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					driver_object = dumps(driver)
					driver_json = json.loads(driver_object)

					driver_list = []

					for i in range(len(driver_json)):
						if driver_json[i]['member_status'] == "4":
							register_status_show = "พักการให้บริการชั่วคราว"
						elif driver_json[i]['member_status'] == "3":
							register_status_show = "พักการให้บริการ"
						else:
							register_status_show = "พร้อมให้บริการ"

						approved_by_name = None
						if driver_json[i]['member_status'] != "0":
							approved_by_name = driver_json[i]['approved_by_name'] 

						register_date = datetime.strptime(driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

						driver_list.append({
							"member_id" : driver_json[i]['_id']['$oid'],
							"member_code": driver_json[i]['member_code'],
							"member_fullname": driver_json[i]['member_firstname_th']+" "+driver_json[i]['member_lastname_th'],
							"driver_level_text": driver_json[i]['driver_level_text'],
							"member_tel": driver_json[i]['member_tel'],
							"member_status": driver_json[i]['member_status'],
							"register_status_show": register_status_show,
							"register_date": register_date,
							"approved_by_name": approved_by_name 
						})

				result = {
							"status" : True,
							"msg" : "Get driver list success.",
							"data" : driver_list,
							"total_data" : total_data
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
	function_name = "driver_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def get_driver_form(request):
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

			car_type = db.car_type.find()
			car_gear = db.car_gear.find()
			service_area = db.service_area.find()
			communication = db.communication.find()
			workday = db.workday.find()
			driver_level = db.driver_level.find({"level_status": "1"})
			special_skill = db.special_skill.find({"skill_status": "1"})

			if car_type is None or car_gear is None or service_area is None or communication is None or workday is None or driver_level is None or special_skill is None:
				result = { 
							"status" : False,
							"msg" : "Please check your master data in database."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				car_gear_object = dumps(car_gear)
				car_gear_json = json.loads(car_gear_object)

				service_area_object = dumps(service_area)
				service_area_json = json.loads(service_area_object)

				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)

				workday_object = dumps(workday)
				workday_json = json.loads(workday_object)

				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)

				special_skill_object = dumps(special_skill)
				special_skill_json = json.loads(special_skill_object)

				car_type_list = []
				car_gear_list = []
				service_area_list = []
				communication_list = []
				workday_list = []
				driver_level_list = []
				special_skill_list = []

				for i in range(len(car_type_json)):
					car_type_list.append({
						"car_type_id": car_type_json[i]['_id']['$oid'],
						"car_type_name": car_type_json[i]['car_type_name_th'],
						"status": ""
					})

				for i in range(len(car_gear_json)):
					car_gear_list.append({
						"car_gear_id": car_gear_json[i]['_id']['$oid'],
						"car_gear_name": car_gear_json[i]['car_gear_th'],
						"status": ""
					})

				for j in range(len(service_area_json)):
					service_area_list.append({
						"service_area_id": service_area_json[j]['_id']['$oid'],
						"service_area_name": service_area_json[j]['service_area_name_th'],
						"is_bangkok": service_area_json[j]['is_bangkok'],
						"all_bangkok": service_area_json[j]['all_bangkok'],
						"status": ""
					})

				for k in range(len(communication_json)):
					communication_list.append({
						"communication_id": communication_json[k]['_id']['$oid'],
						"lang_name": communication_json[k]['lang_name_th'],
						"lang_code": communication_json[k]['lang_code'],
						"flag_image": communication_json[k]['flag_image'],
						"status": ""
					})

				for l in range(len(workday_json)):
					workday_list.append({
						"workday_id": workday_json[l]['_id']['$oid'],
						"short_name": workday_json[l]['short_name_th'],
						"status": ""
					})

				for m in range(len(driver_level_json)):
					driver_level_list.append({
						"id": driver_level_json[m]['_id']['$oid'],
						"name": driver_level_json[m]['level_name_th'],
						"status": ""
					})

				for n in range(len(special_skill_json)):
					special_skill_list.append({
						"special_skill_id": special_skill_json[n]['_id']['$oid'],
						"special_skill_name": special_skill_json[n]['skill_th'],
						"status": ""
					})

				driver_status_list = [
								{"code": "1","name": "พร้อมให้บริการ"},
								{"code": "3","name": "พักการให้บริการ"},
								{"code": "4","name": "พักการให้บริการชั่วคราว"}
							]

				all_driver_status_list = [
								{"code": "0","name": "รออนุมัติ"},
								{"code": "1","name": "อนุมัติ / พร้อมให้บริการ"},
								{"code": "2","name": "ไม่อนุมัติ"},
								{"code": "3","name": "พักการให้บริการ"},
								{"code": "4","name": "พักการให้บริการชั่วคราว"}
							]

				gender_list = [
								{"code": "male","name": "ชาย"},
								{"code": "female","name": "หญิง"}
							]

				result = {
							"status" : True,
							"msg" : "Get driver form success.",
							"driver_level" : driver_level_list,
							"gender" : gender_list,
							"driver_status" : driver_status_list,
							"all_driver_status" : all_driver_status_list,
							"car_type" : car_type_list,
							"car_gear" : car_gear_list,
							"service_area" : service_area_list,
							"communication" : communication_list,
							"workday" : workday_list,
							"special_skill" : special_skill_list
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
	function_name = "get_driver_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def add_driver(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_username = "member_username" in params
	isset_member_firstname_en = "member_firstname_en" in params
	isset_member_lastname_en = "member_lastname_en" in params
	isset_member_firstname_th = "member_firstname_th" in params
	isset_member_lastname_th = "member_lastname_th" in params
	isset_member_email = "member_email" in params
	isset_member_tel = "member_tel" in params
	isset_member_birthday = "member_birthday" in params
	isset_member_gender = "member_gender" in params
	isset_driver_license_expire = "driver_license_expire" in params
	isset_driver_license_no = "driver_license_no" in params
	isset_driver_level_id = "driver_level_id" in params
	isset_member_status = "member_status" in params
	isset_break_start_date = "break_start_date" in params
	isset_break_end_date = "break_end_date" in params
	isset_profile_image = "profile_image" in params
	isset_member_lang = "member_lang" in params
	isset_os_type = "os_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_username and isset_member_firstname_en and isset_member_lastname_en and isset_member_firstname_th and isset_member_lastname_th and isset_member_email and isset_member_tel and isset_member_birthday and isset_member_gender and isset_driver_license_expire and isset_driver_license_no and isset_driver_level_id and isset_member_status and isset_break_start_date and isset_break_end_date and isset_profile_image and isset_member_lang and isset_os_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['member_firstname_en']=="" or params['member_firstname_en'] is None:
				validate.append({"error_param" : "member_firstname_en","msg" : "Firstname (EN) is required."})
			if params['member_lastname_en']=="" or params['member_lastname_en'] is None:
				validate.append({"error_param" : "member_lastname_en","msg" : "Lastname (EN) is required."})
			if params['member_firstname_th']=="" or params['member_firstname_th'] is None:
				validate.append({"error_param" : "member_firstname_th","msg" : "Firstname (TH) is required."})
			if params['member_lastname_th']=="" or params['member_lastname_th'] is None:
				validate.append({"error_param" : "member_lastname_th","msg" : "Lastname (TH) is required."})

			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : "E-mail is required."})
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : "Tel is required."})
			if params['member_username']=="" or params['member_username'] is None:
				validate.append({"error_param" : "member_username","msg" : "Username is required."})
			
			if params['member_birthday']=="" or params['member_birthday'] is None:
				validate.append({"error_param" : "member_birthday","msg" : "Birthday is required."})
			if params['member_gender']=="" or params['member_gender'] is None:
				validate.append({"error_param" : "member_gender","msg" : "Gender is required."})
			if params['driver_license_expire']=="":
				validate.append({"error_param" : "driver_license_expire","msg" : "Driver license expire is required."})
			if params['driver_license_no']=="" or params['driver_license_no'] is None:
				validate.append({"error_param" : "driver_license_no","msg" : "Driver license no is required."})
			if params['member_status']=="" or params['member_status'] is None:
				validate.append({"error_param" : "member_status","msg" : "Status is required."})
			if params['member_lang']=="" or params['member_lang'] is None:
				validate.append({"error_param" : "member_lang","msg" : "Language is required."})

			#check already customer name
			if (params['member_firstname_en']!="" and params['member_firstname_en'] is not None) and (params['member_lastname_en']!="" and params['member_lastname_en'] is not None):
				check_customer_name = db.member.find({
														"member_type": "driver",
														"member_firstname_en": params['member_firstname_en'].title(),
														"member_lastname_en": params['member_lastname_en'].title(),
														"member_status": "1"
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname_en","msg" : "Firstname (EN) and lastname (EN) has been used."})

			if (params['member_firstname_th']!="" and params['member_firstname_th'] is not None) and (params['member_lastname_th']!="" and params['member_lastname_th'] is not None):
				check_customer_name = db.member.find({
														"member_type": "driver",
														"member_firstname_th": params['member_firstname_th'].title(),
														"member_lastname_th": params['member_lastname_th'].title(),
														"member_status": "1"
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname_th","msg" : "Firstname (TH) and lastname (TH) has been used."})
			
			#check already email
			if params['member_email']!="" and params['member_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['member_email'])

				if len(check_format_email) > 0:
					check_email = db.member.find({
													"member_type": "driver",
													"member_email": params['member_email'].lower()
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "member_email","msg" : "Email has been used."})
				else:
					validate.append({"error_param" : "member_email","msg" : "Invalid email format."})		

			#check tel format
			if params['member_tel']!="" and params['member_tel'] is not None:
				tel = params['member_tel'].replace("-", "")
				count_tel = len(tel)

				try:
					data_member_tel = int(params['member_tel'])
					check_data_member_tel = True
				except ValueError:
					check_data_member_tel = False

				if ((count_tel < 9) or (count_tel > 10) or (not check_data_member_tel)):
					validate.append({"error_param" : "member_tel","msg" : "Invalid tel format."})

			#check driver_license_no format
			if params['driver_license_no']!="" and params['driver_license_no'] is not None:
				driver_license_no = params['driver_license_no'].replace("-", "")
				count_driver_license_no = len(driver_license_no)

				try:
					data_license_no = int(params['driver_license_no'])
					check_data_license_no = True
				except ValueError:
					check_data_license_no = False

				if ((count_driver_license_no != 8) or (not check_data_license_no)):
					validate.append({"error_param" : "driver_license_no","msg" : "Invalid driver license no format."})

			#check already username
			if params['member_username']!="" and params['member_username'] is not None:
				#check username format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_username = regex.findall(params['member_username'])

				if len(check_format_username) > 0:
					check_username = db.member.find({
														"member_type": "driver",
														"member_username": params['member_username'].lower()
													}).count()
					if check_username > 0:
						validate.append({"error_param" : "member_username","msg" : "Username has been used."})
				else:
					validate.append({"error_param" : "member_username","msg" : "Invalid username format."})

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				if params['profile_image'] is None:
					image_name = None
				else:
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_profile_image(params['profile_image'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				if params['member_lang']=="en":
					member_lang = "en"
				else:
					member_lang = "th"

				if params['member_status'] == "4":
					break_start_date = params['break_start_date']
					break_end_date = params['break_end_date']
				else:
					break_start_date = None
					break_end_date = None

				if params['driver_level_id'] is not None:
					driver_level = db.driver_level.find_one({"_id": ObjectId(params['driver_level_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					driver_level_object = dumps(driver_level)
					driver_level_json = json.loads(driver_level_object)

					driver_level_id = params['driver_level_id']
					driver_level_priority = int(driver_level_json['level_priority'])
					driver_level_text = driver_level_json['level_name_th']
				else:
					driver_level_id = None
					driver_level_priority = 0
					driver_level_text = None

				#generate password
				generate_password = get_random_token(8)

				#เอา password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(generate_password.encode())
				hash_pass = hash_input_pass.hexdigest()

				#ดึง member_code ล่าสุดจาก tb member แล้วเอามา +1
				member = db.member.find_one({"member_type":"driver"}, sort=[("member_code", -1)])
				mid = 1

				if member is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					mid = int(member_json["member_code"][1:8])+1
					
				member_code = "D"+"%07d" % mid

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				member_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				member_id_string = str(member_id)

				if params['member_status'] == "":
					member_status = "1"
				else:
					member_status = params['member_status']

				member_age = 0
				#แปลง format วันที่
				if params['member_birthday'] is not None:
					member_birthday = datetime.strptime(params['member_birthday'], '%Y-%m-%d').strftime('%Y-%m-%d')
					member_age = get_member_age(member_birthday)

				driver_license_expire = None

				if params['driver_license_expire'] is not None:
					driver_license_expire = params['driver_license_expire']

				register_date_int = int(datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				data = { 
							"_id": member_id,
							"member_code": member_code,
							"member_username": params['member_username'].lower(),
							"member_password": hash_pass,
							"member_firstname_en": params['member_firstname_en'].title(),
							"member_lastname_en": params['member_lastname_en'].title(),
							"member_firstname_th": params['member_firstname_th'].title(),
							"member_lastname_th": params['member_lastname_th'].title(),
							"member_email": params['member_email'].lower(),
							"member_tel": params['member_tel'],
							"member_type": "driver",
							"member_birthday": params['member_birthday'],
							"member_gender": params['member_gender'],
							"driver_license_expire": driver_license_expire,
							"driver_license_no": params['driver_license_no'],
							"car_type": [],
							"car_type_en": None,
							"car_type_th": None,
							"car_gear": [],
							"car_gear_en": None,
							"car_gear_th": None,
							"service_area": [],
							"service_area_en": None,
							"service_area_th": None,
							"communication": [],
							"communication_en": None,
							"communication_th": None,
							"workday": [],
							"workday_en": None,
							"workday_th": None,
							"special_skill": [],
							"special_skill_en": None,
							"special_skill_th": None,
							"driver_level": driver_level_id,
							"driver_level_text": driver_level_text,
							"driver_level_priority": driver_level_priority,
							"driver_rating": float("0"),
							"profile_image": image_name,
							"member_lang": member_lang,
							"member_status": member_status,
							"break_start_date": break_start_date,
							"break_end_date": break_end_date,
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"register_date_int": register_date_int,
							"member_token": None,
							"noti_key": None,
							"os_type": params['os_type'],
							"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"approved_by_id": admin_info['_id']['$oid'],
							"approved_by_name": admin_info['admin_firstname']+" "+admin_info['admin_lastname'],
							"member_age": int(member_age),
							"sedan_job": int(0),
							"suv_job": int(0),
							"van_job": int(0),
							"last_latitude": None,
							"last_longitude": None,
							"last_location_at": None
						}

				if db.member.insert_one(data):
					#send email
					username = params['member_username'].lower()
					password = generate_password
					android_link = "https://play.google.com/store"
					ios_link = "https://www.apple.com/th/ios/app-store/"
						
					email_type = "add_driver"
					subject = "VR Driver : อนุมัติสมาชิกคนขับเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
					to_email = params['member_email'].lower()
					template_html = "add_driver.html"
					data_detail = { "username" : username, "password" : password, "android_link" : android_link , "ios_link" : ios_link }

					data_email = { 
									"email_type": email_type,
									"data": data_detail,
									"subject": subject,
									"to_email": to_email,
									"template_html": template_html,
									"send_status": "0",
									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
					db.queue_email.insert_one(data_email)

					result = {
								"status" : True,
								"msg" : "Add driver success.",
								"driver_profile" : {
									"member_id": member_id_string,
									"member_code": member_code,
									"member_username": params['member_username'].lower(),
									"member_firstname_en": params['member_firstname_en'].title(),
									"member_lastname_en": params['member_lastname_en'].title(),
									"member_firstname_th": params['member_firstname_th'].title(),
									"member_lastname_th": params['member_lastname_th'].title(),
									"member_email": params['member_email'].lower(),
									"member_tel": params['member_tel'],
									"member_birthday": params['member_birthday'],
									"member_gender": params['member_gender'],
									"driver_license_expire": driver_license_expire,
									"driver_license_no": params['driver_license_no'],
									"driver_level_id": params['driver_level_id'],
									"driver_level_priority": driver_level_priority,
									"driver_rating": float("0"),
									"member_status": params['member_status'],
									"break_start_date": break_start_date,
									"break_end_date": break_end_date,
									"profile_image": image_name
								}
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "add_driver"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_driver_level_id = "driver_level_id" in params
	isset_member_status = "member_status" in params
	isset_break_start_date = "break_start_date" in params
	isset_break_end_date = "break_end_date" in params
	isset_profile_image = "profile_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_driver_level_id and isset_member_status and isset_break_start_date and isset_break_end_date and isset_profile_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			driver_level = db.driver_level.find_one({"_id": ObjectId(params['driver_level_id'])})
					
			if driver_level is None:
				result = {
							"status" : False,
							"msg" : "Driver level not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)
				
				driver_level_id = params['driver_level_id']
				driver_level_priority = int(driver_level_json['level_priority'])
				driver_level_text = driver_level_json['level_name_th']

				member = db.member.find_one({
												"_id": ObjectId(params['member_id']),
												"member_type": "driver"
											})
				if member is None:
					result = { 
								"status" : False,
								"msg" : "Driver not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					#ถ้าไม่มีการแก้ไขรูป profile (profile_image เป็น null) ไม่ต้องอัพเดตรูป  
					if params['profile_image'] is None:
						image_name = member_json['profile_image']
					else:
						#เช็ค path และลบรูปเก่า
						if member_json['profile_image'] is not None:
							if os.path.exists("static/images/profiles/"+member_json['profile_image']):
								os.remove("static/images/profiles/"+member_json['profile_image'])

						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_profile_image(params['profile_image'], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

					if params['member_status'] == "4":
						break_start_date = params['break_start_date']
						break_end_date = params['break_end_date']
					else:
						break_start_date = None
						break_end_date = None

					# update data
					where_param = { "_id": ObjectId(params['member_id']) }
					value_param = {
									"$set":
										{
											"driver_level": driver_level_id,
											"driver_level_text": driver_level_text,
											"driver_level_priority": driver_level_priority,
											"member_status": params['member_status'],
											"break_start_date": break_start_date,
											"break_end_date": break_end_date,
											"profile_image": image_name,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.member.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit driver success."
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
	function_name = "edit_driver"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_car_type(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_car_type = "car_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_car_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set car_type_en & car_type_th
			car_type_in = []
			for i in range(len(params['car_type'])):
				car_type_in.append(ObjectId(params['car_type'][i]))

			car_type = db.car_type.find({"_id" : {"$in" : car_type_in}})

			if car_type is None or car_type.count() == 0:
				result = { 
							"status" : False,
							"msg" : "Car type not found."
						}
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				car_type_list = []

				car_type_en = ""
				car_type_th = ""

				for i in range(len(car_type_json)):
					if i == 0:
						car_type_en = car_type_json[i]['car_type_name_en']
						car_type_th = car_type_json[i]['car_type_name_th']
					else:
						car_type_en = car_type_en+" , "+car_type_json[i]['car_type_name_en']
						car_type_th = car_type_th+" , "+car_type_json[i]['car_type_name_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"car_type": params['car_type'],
										"car_type_en": car_type_en,
										"car_type_th": car_type_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver car type success."
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
	function_name = "edit_driver_car_type"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_car_gear(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_car_gear = "car_gear" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_car_gear:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set car_gear_en & car_gear_th
			car_gear_in = []
			for i in range(len(params['car_gear'])):
				car_gear_in.append(ObjectId(params['car_gear'][i]))

			car_gear = db.car_gear.find({"_id" : {"$in" : car_gear_in}})

			if car_gear is None or car_gear.count() == 0:
				result = { 
							"status" : False,
							"msg" : "Car gear not found."
						}
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_gear_object = dumps(car_gear)
				car_gear_json = json.loads(car_gear_object)

				car_gear_list = []

				car_gear_en = ""
				car_gear_th = ""

				for i in range(len(car_gear_json)):
					if i == 0:
						car_gear_en = car_gear_json[i]['car_gear_en']
						car_gear_th = car_gear_json[i]['car_gear_th']
					else:
						car_gear_en = car_gear_en+" , "+car_gear_json[i]['car_gear_en']
						car_gear_th = car_gear_th+" , "+car_gear_json[i]['car_gear_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"car_gear": params['car_gear'],
										"car_gear_en": car_gear_en,
										"car_gear_th": car_gear_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver car gear success."
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
	function_name = "edit_driver_car_gear"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_communication(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_communication = "communication" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_communication:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set communication_en & communication_th
			communication_in = []
			for i in range(len(params['communication'])):
				communication_in.append(ObjectId(params['communication'][i]))

			communication = db.communication.find({"_id" : {"$in" : communication_in}})

			if communication is None or communication.count() == 0:
				result = { 
							"status" : False,
							"msg" : "Communication not found."
						}
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)

				communication_list = []

				communication_en = ""
				communication_th = ""

				for i in range(len(communication_json)):
					if i == 0:
						communication_en = communication_json[i]['lang_name_en']
						communication_th = communication_json[i]['lang_name_th']
					else:
						communication_en = communication_en+" , "+communication_json[i]['lang_name_en']
						communication_th = communication_th+" , "+communication_json[i]['lang_name_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"communication": params['communication'],
										"communication_en": communication_en,
										"communication_th": communication_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver communication success."
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
	function_name = "edit_driver_communication"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_service_area(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_service_area = "service_area" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_service_area:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set service_area_en & service_area_th
			service_area_in = []
			for i in range(len(params['service_area'])):
				service_area_in.append(ObjectId(params['service_area'][i]))

			service_area = db.service_area.find({"_id" : {"$in" : service_area_in}})

			if service_area is None or service_area.count() == 0:
				result = { 
							"status" : False,
							"msg" : "Service area not found."
						}
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				service_area_object = dumps(service_area)
				service_area_json = json.loads(service_area_object)

				service_area_list = []

				service_area_en = ""
				service_area_th = ""

				for i in range(len(service_area_json)):
					if i == 0:
						service_area_en = service_area_json[i]['service_area_name_en']
						service_area_th = service_area_json[i]['service_area_name_th']
					else:
						service_area_en = service_area_en+" , "+service_area_json[i]['service_area_name_en']
						service_area_th = service_area_th+" , "+service_area_json[i]['service_area_name_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"service_area": params['service_area'],
										"service_area_en": service_area_en,
										"service_area_th": service_area_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver service area success."
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
	function_name = "edit_driver_service_area"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_workday(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_workday = "workday" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_workday:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set workday_en & workday_th
			workday_in = []
			for i in range(len(params['workday'])):
				workday_in.append(ObjectId(params['workday'][i]))

			workday = db.workday.find({"_id" : {"$in" : workday_in}})

			if workday is None or workday.count() == 0:
				validate.append({"error_param" : "workday","msg" : "Please check your workday value."})
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				workday_object = dumps(workday)
				workday_json = json.loads(workday_object)

				workday_list = []

				workday_en = ""
				workday_th = ""

				for i in range(len(workday_json)):
					if i == 0:
						workday_en = workday_json[i]['short_name_en']
						workday_th = workday_json[i]['short_name_th']
					else:
						workday_en = workday_en+" , "+workday_json[i]['short_name_en']
						workday_th = workday_th+" , "+workday_json[i]['short_name_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"workday": params['workday'],
										"workday_en": workday_en,
										"workday_th": workday_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver workday success."
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
	function_name = "edit_driver_workday"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

#add -- add special skill
def edit_driver_special_skill(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_special_skill = "special_skill" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_special_skill:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			#set workday_en & workday_th
			special_skill_in = []
			for i in range(len(params['special_skill'])):
				special_skill_in.append(ObjectId(params['special_skill'][i]))

			special_skill = db.special_skill.find({"_id" : {"$in" : special_skill_in}})

			if special_skill is None or special_skill.count() == 0:
				validate.append({"error_param" : "special_skill","msg" : "Please check your special skill value."})
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				special_skill_object = dumps(special_skill)
				special_skill_json = json.loads(special_skill_object)

				special_skill_list = []

				special_skill_en = ""
				special_skill_th = ""

				for i in range(len(special_skill_json)):
					if i == 0:
						special_skill_en = special_skill_json[i]['skill_en']
						special_skill_th = special_skill_json[i]['skill_th']
					else:
						special_skill_en = special_skill_en+" , "+special_skill_json[i]['skill_en']
						special_skill_th = special_skill_th+" , "+special_skill_json[i]['skill_th']

				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"special_skill": params['special_skill'],
										"special_skill_en": special_skill_en,
										"special_skill_th": special_skill_th,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit driver special skill success."
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
	function_name = "edit_driver_special_skill"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def package_purchase_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_purchase_channel = "purchase_channel" in params
	isset_start_purchase_date = "start_purchase_date" in params
	isset_end_purchase_date = "end_purchase_date" in params
	isset_order_status = "order_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_purchase_channel and isset_start_purchase_date and isset_end_purchase_date and isset_order_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				
				# payment_list = db.payment_list.find()

				# if payment_list is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	payment_list_object = dumps(payment_list)
				# 	payment_list_json = json.loads(payment_list_object)

				# 	for i in range(len(payment_list_json)):
						
					
				# 		order_package = db.order_package.find_one({"_id": ObjectId(payment_list_json[i]['order_id'])})

				# 		if order_package is not None:
				# 			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 			order_package_object = dumps(order_package)
				# 			order_package_json = json.loads(order_package_object)


				# 			member_info = get_member_info_by_id(order_package_json['member_id'])
				# 			customer_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
				# 			company_name = None

				# 			if member_info['company_name'] is not None:
				# 				company_name = member_info['company_name']


				# 			if order_package_json['os_type'] is not None:
				# 				if order_package_json['os_type'] == "ios" or order_package_json['os_type'] == "android":
				# 					purchase_channel = "app"
				# 					purchase_channel_show = "ผ่าน App"
				# 				else:
				# 					purchase_channel = "web"
				# 					purchase_channel_show = "ผ่านเว็บไซต์"
				# 			else:
				# 				purchase_channel = "web"
				# 				purchase_channel_show = "ผ่านเว็บไซต์"

				# 			purchase_date_int = int(datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))
				# 			purchase_date = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
				# 			purchase_time = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')

				# 			order_price = float(order_package_json['order_price'])
				# 			transfer_amount_text = str(order_package_json['order_price'])
				# 			os_type = order_package_json['os_type']

				# 			# update data
				# 			where_param = { "_id": ObjectId(payment_list_json[i]['_id']['$oid']) }
				# 			value_param = {
				# 							"$set":
				# 								{
				# 									"order_no": order_package_json['order_no'],
				# 									"order_price": order_price ,

				# 									"purchase_date_int" : purchase_date_int,
				# 									"purchase_date": purchase_date,
				# 									"purchase_time": purchase_time,
				# 									"purchase_channel": purchase_channel,
				# 									"company_name": company_name,
				# 									"customer_name": customer_name,
				# 									"transfer_amount_text" : transfer_amount_text,
				# 									"os_type" : os_type
				# 								}
				# 						}

				# 			db.payment_list.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}



				where_param = {}

				#order_no , transfer_amount , customer_name , company_name 
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "order_no": {"$regex": params['search_text']} },
												{ "transfer_amount_text": {"$regex": params['search_text']} },
												{ "customer_name": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)

				if params['order_status'] == "":
					add_params = {"order_status" : {"$in" : ["1","2","4"]}}
					where_param.update(add_params)
				else:
					add_params = {"order_status": params['order_status']}
					where_param.update(add_params)

				if params['purchase_channel'] == "web":
					add_params = {"os_type" : "web"}
					where_param.update(add_params)
				elif params['purchase_channel'] == "app":
					add_params = {"os_type" : {"$in" : ["ios","android"]}}
					where_param.update(add_params)

				if params['start_purchase_date'] != "" and params['end_purchase_date'] != "":
					start_purchase_date_int = int(datetime.strptime(params['start_purchase_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_purchase_date_int = int(datetime.strptime(params['end_purchase_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"purchase_date_int" : {"$gte" : start_purchase_date_int , "$lte" : end_purchase_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					#create_date = created_at
					#purchase_channel_show = purchase_channel
					#order_no = order_no
					#customer_name = customer_name
					#company_name = company_name
					#order_price = order_price
					#transfer_amount = transfer_amount
					#order_status = order_status

					if params['sort_name'] == "create_date":
						sort_name = "created_at"
					elif params['sort_name'] == "purchase_channel_show":
						sort_name = "purchase_channel"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				payment_list = db.payment_list.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.payment_list.find(where_param).count()

				if payment_list is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					payment_list_object = dumps(payment_list)
					payment_list_json = json.loads(payment_list_object)

					pm_list = []

					for i in range(len(payment_list_json)):
						if payment_list_json[i]['os_type'] is not None:
							if payment_list_json[i]['purchase_channel'] == "app":
								purchase_channel = "app"
								purchase_channel_show = "ผ่าน App"
							else:
								purchase_channel = "web"
								purchase_channel_show = "ผ่านเว็บไซต์"
						else:
							purchase_channel = "web"
							purchase_channel_show = "ผ่านเว็บไซต์"

						if payment_list_json[i]['order_status'] == "4":
							order_status_show = "ไม่อนุมัติ"
						elif payment_list_json[i]['order_status'] == "1":
							order_status_show = "อนุมัติ"
						#order_status = 2
						else:
							order_status_show = "รออนุมัติ"

						create_date = datetime.strptime(payment_list_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						create_time = datetime.strptime(payment_list_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')

						pm_list.append({
							"order_id" : payment_list_json[i]['order_id'],
							"purchase_date": payment_list_json[i]['purchase_date'],
							"purchase_time": payment_list_json[i]['purchase_time'],
							"purchase_channel": purchase_channel,
							"purchase_channel_show": purchase_channel_show,
							"order_no": payment_list_json[i]['order_no'],
							"company_name": payment_list_json[i]['company_name'],
							"customer_name": payment_list_json[i]['customer_name'],
							"order_price": float(payment_list_json[i]['order_price']),
							"payment_list_id": payment_list_json[i]['_id']['$oid'],
							"transfer_amount": float(payment_list_json[i]['transfer_amount']),
							"transfer_slip": payment_list_json[i]['transfer_slip'],
							"order_status": payment_list_json[i]['order_status'],
							"order_status_show": order_status_show,
							"create_date": create_date,
							"create_time": create_time
						})

					result = {
								"status" : True,
								"msg" : "Get package purchase list success.",
								"data" : pm_list,
								"total_data" : total_data
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
	function_name = "package_purchase_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_purchase_form(request):
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

			# package_model_list = [
			# 						{"code": "normal","name": "Normal"},
			# 						{"code": "special","name": "Special"}
			# 					]

			purchase_channel_list = [
										{"code": "app","name": "ผ่าน App"},
										{"code": "web","name": "ผ่านเว็บไซต์"}
									]

			order_status_list = [
									{"code": "1","name": "อนุมัติ"},
									{"code": "2","name": "รออนุมัติ"},
									{"code": "4","name": "ไม่อนุมัติ"}
								]

			result = {
						"status" : True,
						"msg" : "Get driver form success.",
						# "package_model" : package_model_list,
						"purchase_channel" : purchase_channel_list,
						"order_status" : order_status_list
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
	function_name = "get_package_purchase_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_purchase_detail(payment_list_id,request):
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

			payment_list = db.payment_list.find_one({"_id": ObjectId(payment_list_id)})
			
			if payment_list is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				payment_list_object = dumps(payment_list)
				payment_list_json = json.loads(payment_list_object)

				order_package = db.order_package.find_one({"_id": ObjectId(payment_list_json['order_id'])})
				if order_package is None:
					result = { 
								"status" : False,
								"msg" : "Order package not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					order_package_object = dumps(order_package)
					order_package_json = json.loads(order_package_object)

					member_info = get_member_info_by_id(order_package_json['member_id'])
					customer_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
					company_name = None

					if member_info['company_name'] is not None:
						company_name = member_info['company_name']

					if order_package_json['os_type'] == "ios" or order_package_json['os_type'] == "android":
						purchase_channel = "app"
						purchase_channel_show = "ผ่าน App"
					else:
						purchase_channel = "web"
						purchase_channel_show = "ผ่านเว็บไซต์"

					if payment_list_json['order_status'] == "4":
						order_status_show = "ไม่อนุมัติ"
					elif payment_list_json['order_status'] == "1":
						order_status_show = "อนุมัติ"
					#order_status = 2
					else:
						order_status_show = "รออนุมัติ"

					purchase_datetime = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

					transfer_datetime = None
					payment_channel_show = None
					transfer_amount = None

					if payment_list_json['transfer_date'] is not None and payment_list_json['transfer_time'] is not None:
						transfer_date = datetime.strptime(payment_list_json['transfer_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
						transfer_time = datetime.strptime(payment_list_json['transfer_time'], '%H:%M:%S').strftime('%H:%M')
						transfer_datetime = transfer_date+" "+transfer_time

					if payment_list_json['payment_channel_id'] is not None:
						payment_channel = db.payment_channel.find_one({"_id": ObjectId(payment_list_json['payment_channel_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						payment_channel_object = dumps(payment_channel)
						payment_channel_json = json.loads(payment_channel_object)
						payment_channel_show = payment_channel_json['bank_name_th']+" "+payment_channel_json['account_number']

					if payment_list_json['transfer_amount'] is not None:
						transfer_amount = float(payment_list_json['transfer_amount'])

					order_detail = []
					order_price_not_vat = 0

					for i in range(len(order_package_json['order_detail'])):
						package_name = order_package_json['order_detail'][i]['package_name_th']

						order_detail.append({
							"package_id" : order_package_json['order_detail'][i]['package_id'],
							"package_name": package_name,
							"package_type": order_package_json['order_detail'][i]['package_type'], 
							"package_type_amount": order_package_json['order_detail'][i]['package_type_amount'],
							"package_amount": order_package_json['order_detail'][i]['package_amount'],
							"package_price": float(order_package_json['order_detail'][i]['package_price']) 	
						})

					data = {
								"order_id": order_package_json['_id']['$oid'],
								"purchase_datetime": purchase_datetime,
								"purchase_channel": purchase_channel,
								"purchase_channel_show": purchase_channel_show,
								"order_no": order_package_json['order_no'],
								"company_name": company_name,
								"customer_name": customer_name,
								"order_price": float(order_package_json['order_price']),
								"order_price_not_vat": float(order_package_json['order_price_not_vat']),
								"order_vat": float(order_package_json['order_vat']),
								"payment_channel_show": payment_channel_show,
								"transfer_amount": transfer_amount,
								"transfer_datetime": transfer_datetime,
								"transfer_slip": payment_list_json['transfer_slip'],
								"order_status": payment_list_json['order_status'],
								"order_status_show": order_status_show,
								"order_remark": payment_list_json['order_remark'],
								"order_detail": order_detail
							}

					result = {
								"status" : True,
								"msg" : "Get package purchase detail success.",
								"data" : data
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
	function_name = "get_package_purchase_detail"
	request_headers = request.headers
	params_get = {"payment_list_id" : payment_list_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def approve_package_purchase(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_payment_list_id = "payment_list_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_payment_list_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			payment_list = db.payment_list.find_one({"_id": ObjectId(params['payment_list_id'])})
			
			if payment_list is None:
				result = { 
							"status" : False,
							"msg" : "Payment list not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				payment_list_object = dumps(payment_list)
				payment_list_json = json.loads(payment_list_object)
				payment_list_id = payment_list_json['_id']['$oid']
				order_id = payment_list_json['order_id']

				order_package = db.order_package.find_one({"_id": ObjectId(order_id)})

				if order_package is None:
					result = { 
								"status" : False,
								"msg" : "Order package not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					order_package_object = dumps(order_package)
					order_package_json = json.loads(order_package_object)
					order_no = order_package_json['order_no']
					order_price = '{:,.2f}'.format(round(float(order_package_json['order_price']) , 2))
					order_price_not_vat = '{:,.2f}'.format(round(float(order_package_json['order_price_not_vat']) , 2))
					order_vat = '{:,.2f}'.format(round(float(order_package_json['order_vat']) , 2))
					purchase_date_show = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
					vat_rate = order_package_json['order_detail'][0]['vat_rate']

					member_info = get_member_info_by_id(order_package_json['member_id'])
					member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']

					#เฉพาะ order_status กำลังตรวจสอบการชำระเงิน / รออนุมัติ เท่านั้น
					if order_package_json['order_status'] == "2":
						# update payment_list
						where_param = { "_id": ObjectId(payment_list_id) }
						value_param = {
										"$set":
											{
												"order_status": "1",
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.payment_list.update(where_param , value_param):
							# update data
							where_param = { "_id": ObjectId(order_id) }
							value_param = {
											"$set":
												{
													"order_status": "1",
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.order_package.update(where_param , value_param):
								order_package = db.order_package.find_one({"_id": ObjectId(order_id)})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								order_package_object = dumps(order_package)
								order_package_json = json.loads(order_package_object)

								#normal user
								if member_info['company_id'] is None:
									#insert member_package
									for i in range(len(order_package_json['order_detail'])):
										total_amount = order_package_json['order_detail'][i]['package_type_amount'] * order_package_json['order_detail'][i]['package_amount']
										start_date = datetime.now().strftime('%Y-%m-%d')
										add_date = date.today() + timedelta(days=int(order_package_json['order_detail'][i]['total_usage_date']))
										end_date = add_date.strftime('%Y-%m-%d')
										
										#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
										member_package_id = ObjectId()
										#แปลง ObjectId ให้เป็น string
										member_package_id_string = str(member_package_id)

										end_date_int = int(datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')) 

										data = { 
													"_id": member_package_id,
													"order_id": order_id,
													"order_no": order_no,
													"order_date": order_package_json['created_at'],
													"company_package_id": None,
													"company_id": None,
													"member_id": order_package_json['member_id'],
													"member_name": member_fullname,
													"package_id": order_package_json['order_detail'][i]['package_id'],
													
													"package_code": order_package_json['order_detail'][i]['package_code'],
													"package_type": order_package_json['order_detail'][i]['package_type'],
													"package_type_amount": order_package_json['order_detail'][i]['package_type_amount'],
													"package_name_en": order_package_json['order_detail'][i]['package_name_en'],
													"package_name_th": order_package_json['order_detail'][i]['package_name_th'],
													"package_detail_en": order_package_json['order_detail'][i]['package_detail_en'],
													"package_detail_th": order_package_json['order_detail'][i]['package_detail_th'],
													"package_condition_en": order_package_json['order_detail'][i]['package_condition_en'],
													"package_condition_th": order_package_json['order_detail'][i]['package_condition_th'],
													"package_model": order_package_json['order_detail'][i]['package_model'],
													"total_usage_date": order_package_json['order_detail'][i]['total_usage_date'],
													"special_company": order_package_json['order_detail'][i]['special_company'],
													"service_time": order_package_json['order_detail'][i]['service_time'],
													"driver_level": order_package_json['order_detail'][i]['driver_level'],
													"communication": order_package_json['order_detail'][i]['communication'],
													"communication_en": order_package_json['order_detail'][i]['communication_en'],
													"communication_th": order_package_json['order_detail'][i]['communication_th'],
													"normal_paid_rate": float(order_package_json['order_detail'][i]['normal_paid_rate']),
													"normal_received_rate": float(order_package_json['order_detail'][i]['normal_received_rate']),
													"overtime_paid_rate": float(order_package_json['order_detail'][i]['overtime_paid_rate']),
													"overtime_received_rate": float(order_package_json['order_detail'][i]['overtime_received_rate']),
													"package_image": order_package_json['order_detail'][i]['package_image'],
													"package_price": float(order_package_json['order_detail'][i]['package_price']),
													"package_price_not_vat": float(order_package_json['order_detail'][i]['package_price_not_vat']),
													"package_price_vat": float(order_package_json['order_detail'][i]['package_price_vat']),
													"vat_rate": float(order_package_json['order_detail'][i]['vat_rate']),

													"package_usage_type": "quota",
													"package_amount": int(order_package_json['order_detail'][i]['package_amount']),
													"total_amount": total_amount,
													"usage_amount": 0,
													"remaining_amount": total_amount,
													"member_package_status": "1",
													"start_date": start_date,
													"end_date": end_date,
													"end_date_int": end_date_int,
													"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}

										if db.member_package.insert_one(data):
											response = True
										else:
											response = False
									if response:
										#send noti
										noti_type = "approve_package_purchase"

										noti_title_en = "Approve the purchase of the package"
										noti_title_th = "อนุมัติการสั่งซื้อแพ็คเกจ"
										noti_message_en = "order number : "+order_no
										noti_message_th = "เลขที่ "+order_no

										if member_info['member_lang'] == "en":
											noti_title = noti_title_en
											noti_message = noti_message_en
											show_noti = noti_title_en+" "+noti_message_en
										else:
											noti_title = noti_title_th
											noti_message = noti_message_th
											show_noti = noti_title_th+" "+noti_message_th

										#แปลง format วันที่
										created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

										send_noti_key = member_info['noti_key']
										send_noti_title = noti_title
										send_noti_message = noti_message
										send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "order_id": order_id , "created_datetime" : created_datetime }
										send_noti_badge = 1

										#insert member_notification
										noti_detail = {
															"order_id": order_id,
															"order_no": order_no
														}

										data = { 
													"member_id": member_info['_id']['$oid'],
													"member_fullname": member_fullname,
													"noti_type": noti_type,
													"noti_message_en": noti_title_en+" "+noti_message_en,
													"noti_message_th": noti_title_th+" "+noti_message_th,
													"noti_detail": noti_detail,

													"send_noti_key": send_noti_key,
													"send_noti_title": send_noti_title,
													"send_noti_message": send_noti_message,
													"send_noti_data": send_noti_data,
													"send_noti_badge": send_noti_badge,

													"send_status": "0",
													"created_at": created_at,
													"updated_at": created_at
												}
										db.queue_notification.insert_one(data)

										#send email
										email_type = "approve_package_purchase"
										subject = "VR Driver : อนุมัติการสั่งซื้อแพ็คเกจเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
										to_email = member_info['member_email'].lower()
										template_html = "approve_package_purchase.html"
										data_detail = { "order_no" : order_no, "order_price" : order_price, "order_price_not_vat" : order_price_not_vat , "order_vat" : order_vat , "purchase_date_show" : purchase_date_show , "vat_rate" : vat_rate }

										data_email = { 
														"email_type": email_type,
														"data": data_detail,
														"subject": subject,
														"to_email": to_email,
														"template_html": template_html,
														"send_status": "0",
														"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
										db.queue_email.insert_one(data_email)

										result = {
													"status" : True,
													"msg" : "Approve package purchase success."
												}
									else:
										result = {
												"status" : False,
												"msg" : "Data insert failed."
											}
								#company user
								else:
									#insert company_package
									for i in range(len(order_package_json['order_detail'])):
										total_amount = order_package_json['order_detail'][i]['package_type_amount'] * order_package_json['order_detail'][i]['package_amount']
										start_date = datetime.now().strftime('%Y-%m-%d')
										add_date = date.today() + timedelta(days=int(order_package_json['order_detail'][i]['total_usage_date']))
										end_date = add_date.strftime('%Y-%m-%d')

										#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
										company_package_id = ObjectId()
										#แปลง ObjectId ให้เป็น string
										company_package_id_string = str(company_package_id)

										end_date_int = int(datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d'))

										data = { 
													"_id": company_package_id,
													"order_id": order_id,
													"order_no": order_no,
													"order_date": order_package_json['created_at'],
													"company_id": member_info['company_id'],
													"company_name": member_info['company_name'],
													"package_id": order_package_json['order_detail'][i]['package_id'],

													"package_code": order_package_json['order_detail'][i]['package_code'],
													"package_type": order_package_json['order_detail'][i]['package_type'],
													"package_type_amount": order_package_json['order_detail'][i]['package_type_amount'],
													"package_name_en": order_package_json['order_detail'][i]['package_name_en'],
													"package_name_th": order_package_json['order_detail'][i]['package_name_th'],
													"package_detail_en": order_package_json['order_detail'][i]['package_detail_en'],
													"package_detail_th": order_package_json['order_detail'][i]['package_detail_th'],
													"package_condition_en": order_package_json['order_detail'][i]['package_condition_en'],
													"package_condition_th": order_package_json['order_detail'][i]['package_condition_th'],
													"package_model": order_package_json['order_detail'][i]['package_model'],
													"total_usage_date": order_package_json['order_detail'][i]['total_usage_date'],
													"special_company": order_package_json['order_detail'][i]['special_company'],
													"service_time": order_package_json['order_detail'][i]['service_time'],
													"driver_level": order_package_json['order_detail'][i]['driver_level'],
													"communication": order_package_json['order_detail'][i]['communication'],
													"communication_en": order_package_json['order_detail'][i]['communication_en'],
													"communication_th": order_package_json['order_detail'][i]['communication_th'],
													"normal_paid_rate": float(order_package_json['order_detail'][i]['normal_paid_rate']),
													"normal_received_rate": float(order_package_json['order_detail'][i]['normal_received_rate']),
													"overtime_paid_rate": float(order_package_json['order_detail'][i]['overtime_paid_rate']),
													"overtime_received_rate": float(order_package_json['order_detail'][i]['overtime_received_rate']),
													"package_image": order_package_json['order_detail'][i]['package_image'],
													"package_price": float(order_package_json['order_detail'][i]['package_price']),
													"package_price_not_vat": float(order_package_json['order_detail'][i]['package_price_not_vat']),
													"package_price_vat": float(order_package_json['order_detail'][i]['package_price_vat']),
													"vat_rate": float(order_package_json['order_detail'][i]['vat_rate']),

													"package_usage_type": "share",
													"package_amount": int(order_package_json['order_detail'][i]['package_amount']),
													"total_amount": total_amount,
													"usage_amount": 0,
													"remaining_amount": total_amount,
													"company_package_status": "1",
													"start_date": start_date,
													"end_date": end_date,
													"end_date_int": end_date_int,
													"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}

										if db.company_package.insert_one(data):
											data = { 
													"company_package_id": company_package_id_string,
													"package_admin": [],
													"package_id": order_package_json['order_detail'][i]['package_id'],
													"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
											db.package_admin.insert_one(data)

											response = True
										else:
											response = False
									if response:
										#send noti
										noti_type = "approve_package_purchase"

										noti_title_en = "Approve the purchase of the package"
										noti_title_th = "อนุมัติการสั่งซื้อแพ็คเกจ"
										noti_message_en = "order number : "+order_no
										noti_message_th = "เลขที่ "+order_no

										if member_info['member_lang'] == "en":
											noti_title = noti_title_en
											noti_message = noti_message_en
											show_noti = noti_title_en+" "+noti_message_en
										else:
											noti_title = noti_title_th
											noti_message = noti_message_th
											show_noti = noti_title_th+" "+noti_message_th

										#แปลง format วันที่
										created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

										send_noti_key = member_info['noti_key']
										send_noti_title = noti_title
										send_noti_message = noti_message
										send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "order_id": order_id , "created_datetime" : created_datetime }
										send_noti_badge = 1

										#insert member_notification
										noti_detail = {
															"order_id": order_id,
															"order_no": order_no
														}

										data = { 
													"member_id": member_info['_id']['$oid'],
													"member_fullname": member_fullname,
													"noti_type": noti_type,
													"noti_message_en": noti_title_en+" "+noti_message_en,
													"noti_message_th": noti_title_th+" "+noti_message_th,
													"noti_detail": noti_detail,

													"send_noti_key": send_noti_key,
													"send_noti_title": send_noti_title,
													"send_noti_message": send_noti_message,
													"send_noti_data": send_noti_data,
													"send_noti_badge": send_noti_badge,

													"send_status": "0",
													"created_at": created_at,
													"updated_at": created_at
												}
										db.queue_notification.insert_one(data)

										#send email
										email_type = "approve_package_purchase"
										subject = "VR Driver : อนุมัติการสั่งซื้อแพ็คเกจ" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
										to_email = member_info['member_email'].lower()
										template_html = "approve_package_purchase.html"
										data_detail = { "order_no" : order_no, "order_price" : order_price, "order_price_not_vat" : order_price_not_vat , "order_vat" : order_vat , "purchase_date_show" : purchase_date_show , "vat_rate" : vat_rate }

										data_email = { 
														"email_type": email_type,
														"data": data_detail,
														"subject": subject,
														"to_email": to_email,
														"template_html": template_html,
														"send_status": "0",
														"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
										db.queue_email.insert_one(data_email)

										result = {
													"status" : True,
													"msg" : "Approve package purchase success."
												}
									else:
										result = {
												"status" : False,
												"msg" : "Data insert failed."
											}
							else:
								result = {
											"status" : False,
											"msg" : "Order package update failed."
										}
						else:
							result = {
										"status" : False,
										"msg" : "Payment list update failed."
									}
							
					else:
						result = { 
									"status" : False,
									"msg" : "Order status is invalid."
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
	function_name = "approve_package_purchase"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def not_approve_package_purchase(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_payment_list_id = "payment_list_id" in params
	isset_order_remark = "order_remark" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_payment_list_id and isset_order_remark:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			payment_list = db.payment_list.find_one({"_id": ObjectId(params['payment_list_id'])})
			
			if payment_list is None:
				result = { 
							"status" : False,
							"msg" : "Payment list not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				payment_list_object = dumps(payment_list)
				payment_list_json = json.loads(payment_list_object)
				payment_list_id = payment_list_json['_id']['$oid']
				order_id = payment_list_json['order_id']

				order_package = db.order_package.find_one({"_id": ObjectId(order_id)})
				if order_package is None:
					result = { 
								"status" : False,
								"msg" : "Order package not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					order_package_object = dumps(order_package)
					order_package_json = json.loads(order_package_object)
					order_no = order_package_json['order_no']
					order_price = '{:,.2f}'.format(round(float(order_package_json['order_price']) , 2))
					order_price_not_vat = '{:,.2f}'.format(round(float(order_package_json['order_price_not_vat']) , 2))
					order_vat = '{:,.2f}'.format(round(float(order_package_json['order_vat']) , 2))
					purchase_date_show = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
					vat_rate = str(order_package_json['order_detail'][0]['vat_rate'])

					member_info = get_member_info_by_id(order_package_json['member_id'])
					member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']

					#เฉพาะ order_status กำลังตรวจสอบการชำระเงิน / รออนุมัติ เท่านั้น
					if order_package_json['order_status'] == "2":
						# update payment_list
						where_param = { "_id": ObjectId(payment_list_id) }
						value_param = {
										"$set":
											{
												"order_status": "4",
												"order_remark": params['order_remark'],
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.payment_list.update(where_param , value_param):
							# update order_package
							where_param = { "_id": ObjectId(order_id) }
							value_param = {
											"$set":
												{
													"order_status": "4",
													"order_remark": params['order_remark'],
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.order_package.update(where_param , value_param):
								#send noti
								noti_type = "not_approve_package_purchase"

								noti_title_en = "Disapprove the purchase of the package"
								noti_title_th = "ไม่อนุมัติการสั่งซื้อแพ็คเกจ"
								noti_message_en = "order number : "+order_no+" because "+params['order_remark']
								noti_message_th = "เลขที่ "+order_no+" เนื่องจาก "+params['order_remark']

								if member_info['member_lang'] == "en":
									noti_title = noti_title_en
									noti_message = noti_message_en
									show_noti = noti_title_en+" "+noti_message_en
								else:
									noti_title = noti_title_th
									noti_message = noti_message_th
									show_noti = noti_title_th+" "+noti_message_th

								#แปลง format วันที่
								created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

								send_noti_key = member_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "order_id": order_id , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"order_id": order_id,
													"order_no": order_no
												}

								data = { 
											"member_id": member_info['_id']['$oid'],
											"member_fullname": member_fullname,
											"noti_type": noti_type,
											"noti_message_en": noti_title_en+" "+noti_message_en,
											"noti_message_th": noti_title_th+" "+noti_message_th,
											"noti_detail": noti_detail,

											"send_noti_key": send_noti_key,
											"send_noti_title": send_noti_title,
											"send_noti_message": send_noti_message,
											"send_noti_data": send_noti_data,
											"send_noti_badge": send_noti_badge,

											"send_status": "0",
											"created_at": created_at,
											"updated_at": created_at
										}
								db.queue_notification.insert_one(data)

								#send email
								email_type = "not_approve_package_purchase"
								subject = "VR Driver : ไม่อนุมัติการสั่งซื้อแพ็คเกจ" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
								to_email = member_info['member_email'].lower()
								template_html = "not_approve_package_purchase.html"
								data_detail = { "order_no" : order_no, "order_price" : order_price, "order_price_not_vat" : order_price_not_vat , "order_vat" : order_vat , "purchase_date_show" : purchase_date_show , "vat_rate" : vat_rate , "order_remark" : params['order_remark'] }

								data_email = { 
												"email_type": email_type,
												"data": data_detail,
												"subject": subject,
												"to_email": to_email,
												"template_html": template_html,
												"send_status": "0",
												"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
								db.queue_email.insert_one(data_email)

								result = {
										"status" : True,
										"msg" : "Not approve package purchase success."
									}
							else:
								result = {
											"status" : False,
											"msg" : "Order package update failed."
										}
						else:
							result = {
										"status" : False,
										"msg" : "Payment list update failed."
									}	
					else:
						result = { 
									"status" : False,
									"msg" : "Order status is invalid."
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
	function_name = "not_approve_package_purchase"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def admin_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		admin = db.admin.find().sort([("created_at", -1)])

		if admin is None:
			result = { 
					"status" : False,
					"msg" : "Data not found."
				}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			admin_object = dumps(admin)
			admin_json = json.loads(admin_object)

			admin_list = []

			for i in range(len(admin_json)):
				if admin_json[i]['admin_status'] == "1":
					admin_status_text = "เปิดใช้งาน"
				else:
					admin_status_text = "ปิดใช้งาน"

				admin_list.append({
					"id" : admin_json[i]['_id']['$oid'],
					"admin_username": admin_json[i]['admin_username'],
					"admin_firstname": admin_json[i]['admin_firstname'],
					"admin_lastname": admin_json[i]['admin_lastname'],
					"admin_email": admin_json[i]['admin_email'],
					"admin_tel": admin_json[i]['admin_tel'],
					"admin_status": admin_json[i]['admin_status'],
					"admin_status_text": admin_status_text
				})

		result = {
					"status" : True,
					"msg" : "Get admin list success.",
					"data" : admin_list
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "admin_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_admin(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_admin_username = "admin_username" in params
	isset_admin_firstname = "admin_firstname" in params
	isset_admin_lastname = "admin_lastname" in params
	isset_admin_email = "admin_email" in params
	isset_admin_tel = "admin_tel" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_admin_username and isset_admin_firstname and isset_admin_lastname and isset_admin_email and isset_admin_tel:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['admin_firstname']=="" or params['admin_firstname'] is None:
				validate.append({"error_param" : "admin_firstname","msg" : "Firstname is required."})
			if params['admin_lastname']=="" or params['admin_lastname'] is None:
				validate.append({"error_param" : "admin_lastname","msg" : "Lastname is required."})

			if params['admin_email']=="" or params['admin_email'] is None:
				validate.append({"error_param" : "admin_email","msg" : "E-mail is required."})
			if params['admin_tel']=="" or params['admin_tel'] is None:
				validate.append({"error_param" : "admin_tel","msg" : "Tel is required."})
			if params['admin_username']=="" or params['admin_username'] is None:
				validate.append({"error_param" : "admin_username","msg" : "Username is required."})

			#check already admin name
			if (params['admin_firstname']!="" and params['admin_firstname'] is not None) and (params['admin_lastname']!="" and params['admin_lastname'] is not None):
				check_admin_name = db.admin.find({
													"admin_firstname": params['admin_firstname'],
													"admin_lastname": params['admin_lastname']
												}).count()
				if check_admin_name > 0:
					validate.append({"error_param" : "admin_firstname","msg" : "Firstname and lastname has been used."})	
			
			#check already email
			if params['admin_email']!="" and params['admin_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['admin_email'])

				if len(check_format_email) > 0:
					check_email = db.admin.find({
													"admin_email": params['admin_email'].lower(),
													"member_status": "1"
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "admin_email","msg" : "Email has been used."})
				else:
					validate.append({"error_param" : "admin_email","msg" : "Invalid email format."})

			#check tel format
			if params['admin_tel']!="" and params['admin_tel'] is not None:
				tel = params['admin_tel'].replace("-", "")
				count_tel = len(tel)

				try:
					data_admin_tel = int(params['admin_tel'])
					check_data_admin_tel = True
				except ValueError:
					check_data_admin_tel = False

				if ((count_tel < 9) or (count_tel > 10) or (not check_data_admin_tel)):
					validate.append({"error_param" : "admin_tel","msg" : "Invalid tel format."})

			#check already username
			if params['admin_username']!="" and params['admin_username'] is not None:
				#check username format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_username = regex.findall(params['admin_username'])

				if len(check_format_username) > 0:
					check_username = db.member.find({
														"admin_username": params['admin_username'].lower()
													}).count()
					if check_username > 0:
						validate.append({"error_param" : "admin_username","msg" : "Username has been used."})
				else:
					validate.append({"error_param" : "admin_username","msg" : "Invalid username format."})

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				#generate password
				generate_password = get_random_token(8)

				#เอา password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(generate_password.encode())
				hash_pass = hash_input_pass.hexdigest()
				
				data = { 
							"admin_username": params['admin_username'].lower(),
							"admin_password": hash_pass,
							"admin_firstname": params['admin_firstname'],
							"admin_lastname": params['admin_lastname'],
							"admin_email": params['admin_email'].lower(),
							"admin_tel": params['admin_tel'],
							"admin_status": "1",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"admin_token": None
						}

				if db.admin.insert_one(data):
					#send email
					username = params['admin_username'].lower()
					password = generate_password
						
					email_type = "add_admin"
					subject = "VR Driver : เพิ่มข้อมูลผู้ดูแลระบบเรียบร้อยแล้ว" #subject ยาวเกินไปจะทำให้ส่งอีเมลบน server ไม่ได้
					to_email = params['admin_email'].lower()
					template_html = "add_admin.html"
					data_detail = { "username" : username, "password" : password }

					data_email = { 
									"email_type": email_type,
									"data": data_detail,
									"subject": subject,
									"to_email": to_email,
									"template_html": template_html,
									"send_status": "0",
									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
					db.queue_email.insert_one(data_email)

					result = {
								"status" : True,
								"msg" : "Add admin success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "add_admin"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_admin(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_admin_id = "admin_id" in params
	isset_admin_firstname = "admin_firstname" in params
	isset_admin_lastname = "admin_lastname" in params
	isset_admin_email = "admin_email" in params
	isset_admin_tel = "admin_tel" in params
	isset_admin_status = "admin_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_admin_id and isset_admin_firstname and isset_admin_lastname and isset_admin_email and isset_admin_tel and isset_admin_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['admin_id']=="" or params['admin_id'] is None:
				validate.append({"error_param" : "admin_id","msg" : "Admin id is required."})
			if params['admin_firstname']=="" or params['admin_firstname'] is None:
				validate.append({"error_param" : "admin_firstname","msg" : "Firstname is required."})
			if params['admin_lastname']=="" or params['admin_lastname'] is None:
				validate.append({"error_param" : "admin_lastname","msg" : "Lastname is required."})
			if params['admin_email']=="" or params['admin_email'] is None:
				validate.append({"error_param" : "admin_email","msg" : "E-mail is required."})
			if params['admin_tel']=="" or params['admin_tel'] is None:
				validate.append({"error_param" : "admin_tel","msg" : "Tel is required."})

			#check already customer name
			if (params['admin_firstname']!="" and params['admin_firstname'] is not None) and (params['admin_lastname']!="" and params['admin_lastname'] is not None):
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_admin_name = db.admin.find({
													"_id": {"$ne": ObjectId(params['admin_id'])},
													"admin_firstname": params['admin_firstname'],
													"admin_lastname": params['admin_lastname']
												}).count()
				if check_admin_name > 0:
					validate.append({"error_param" : "admin_firstname","msg" : "Firstname and lastname has been used."})
			
			#check already email
			if params['admin_email']!="" and params['admin_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['admin_email'])

				if len(check_format_email) > 0:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_email = db.admin.find({
													"_id": {"$ne": ObjectId(params['admin_id'])},
													"admin_email": params['admin_email'].lower()
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "admin_email","msg" : "Email has been used."})
				else:
					validate.append({"error_param" : "admin_email","msg" : "Invalid email format."})

			#check tel format
			if params['admin_tel']!="" and params['admin_tel'] is not None:
				tel = params['admin_tel'].replace("-", "")
				count_tel = len(tel)

				try:
					data_admin_tel = int(params['admin_tel'])
					check_data_admin_tel = True
				except ValueError:
					check_data_admin_tel = False

				if ((count_tel < 9) or (count_tel > 10) or (not check_data_admin_tel)):
					validate.append({"error_param" : "admin_tel","msg" : "Invalid tel format."})

			

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				admin = db.admin.find_one({"_id": ObjectId(params['admin_id'])})
				if admin is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					admin_object = dumps(admin)
					admin_json = json.loads(admin_object)

					if params['admin_status'] is None:
						admin_status = admin_json['admin_status']
					elif params['admin_status'] == "0":
						admin_status = "0"
					else:
						admin_status = "1"

					where_param = { "_id": ObjectId(params['admin_id']) }
					value_param = {
									"$set": {
												"admin_firstname": params['admin_firstname'],
												"admin_lastname": params['admin_lastname'],
												"admin_email": params['admin_email'].lower(),
												"admin_tel": params['admin_tel'],
												"admin_status": admin_status
											}
									}

					if db.admin.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Edit admin success."
								}
					else:
						result = {
								"status" : False,
								"msg" : "Data update failed."
								}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "edit_admin"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def request_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_request_date = "request_date" in params
	isset_start_date = "start_date" in params
	isset_request_status = "request_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_request_date and isset_start_date and isset_request_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:

				# request_driver = db.request_driver.find()

				# if request_driver is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	request_driver_object = dumps(request_driver)
				# 	request_driver_json = json.loads(request_driver_object)

				# 	for i in range(len(request_driver_json)):
						
				# 		if request_driver_json[i]['company_id'] is None:
				# 			company_name = None
				# 		else:
				# 			company = db.company.find_one({"_id": ObjectId(request_driver_json[i]['company_id'])})
				# 			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 			company_object = dumps(company)
				# 			company_json = json.loads(company_object)
				# 			company_name = company_json['company_name']

				# 		member_info = get_member_info_by_id(request_driver_json[i]['member_id'])
				# 		member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']

				# 		passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])
				# 		passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']

				# 		if request_driver_json[i]['driver_id'] is None:
				# 			driver_name = None
				# 		else:
				# 			driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				# 			driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

				# 		start_date_int = int(datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				# 		create_date_int = int(datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				# 		# update data
				# 		where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"company_name": company_name,
				# 								"member_name": member_name,
				# 								"passenger_name": passenger_name,
				# 								"driver_name": driver_name,
				# 								"start_date_int": start_date_int,
				# 								"create_date_int": create_date_int
				# 							}
				# 					}

				# 		db.request_driver.update(where_param , value_param)

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}




				where_param = { }

				#request_no , company_name , member_name , passenger_name , driver_name
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "request_no": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "member_name": {"$regex": params['search_text']} },
												{ "passenger_name": {"$regex": params['search_text']} },
												{ "driver_name": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)


				if params['request_status'] != "":
					add_params = {"request_status" : params['request_status']}
					where_param.update(add_params)

				if params['request_date'] != "":
					create_date_int = int(datetime.strptime(params['request_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"create_date_int" : create_date_int}
					where_param.update(add_params)

				if params['start_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 

					add_params = {"start_date_int" : start_date_int}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# request_no = request_no
					# create_date = created_at
					# start_date = start_date
					# company_name = company_name
					# member_name = member_name
					# passenger_name = passenger_name
					# driver_name = driver_name_th
					# request_status = request_status

					if params['sort_name'] == "create_date":
						sort_name = "created_at"
					elif params['sort_name'] == "driver_name":
						sort_name = "driver_name_th"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

				request_driver = db.request_driver.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.request_driver.find(where_param).count()

				if request_driver is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					request_driver_list = []

					for i in range(len(request_driver_json)):
						if request_driver_json[i]['request_status'] == "6":
							request_status_text = "สำเร็จ"
						elif request_driver_json[i]['request_status'] == "5":
							request_status_text = "กำลังเดินทาง"
						elif request_driver_json[i]['request_status'] == "4":
							request_status_text = "งานที่ใกล้จะถึง"
						elif request_driver_json[i]['request_status'] == "3":
							request_status_text = "ยกเลิกโดยคนขับ"
						elif request_driver_json[i]['request_status'] == "2":
							request_status_text = "ยกเลิกโดยลูกค้า"
						elif request_driver_json[i]['request_status'] == "1":
							request_status_text = "ตอบรับแล้ว"
						else:
							request_status_text = "รอตอบรับ"

						create_date = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						start_date = request_driver_json[i]['start_date']
						create_time = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
						start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')

						if request_driver_json[i]['company_id'] is not None:
							company = db.company.find_one({"_id": ObjectId(request_driver_json[i]['company_id'])})

							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_object = dumps(company)
							company_json = json.loads(company_object)
							company_name = company_json['company_name']
						else:
							company_name = None

						member_info = get_member_info_by_id(request_driver_json[i]['member_id'])
						passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])

						member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']

						if request_driver_json[i]['driver_id'] is not None:
							driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
							driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
						else:
							driver_name = None

						request_driver_list.append({
							"request_id" : request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"create_date": create_date,
							"create_time": create_time,
							"start_date": start_date,
							"start_time": start_time,
							"company_name": company_name,
							"member_name": member_name,
							"passenger_name": passenger_name,
							"driver_name": driver_name,
							"request_status": request_driver_json[i]['request_status'],
							"request_status_text": request_status_text
						})

				result = {
							"status" : True,
							"msg" : "Get request list success.",
							"data" : request_driver_list,
							"total_data" : total_data
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
	function_name = "request_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_request_detail(request_id,request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(request_id)})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['company_id'] is not None:
					company = db.company.find_one({"_id": ObjectId(request_driver_json['company_id'])})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)
					company_name = company_json['company_name']
				else:
					company_name = None

				member_info = get_member_info_by_id(request_driver_json['member_id'])
				passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])

				member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
				passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']
				member_tel = member_info['member_tel']

				if request_driver_json['driver_list_id'] is None and request_driver_json['request_status'] == "0":
					check_assgin_driver = "1"
				else:
					check_assgin_driver = "0"

				if request_driver_json['driver_id'] is not None:
					driver_info = get_member_info_by_id(request_driver_json['driver_id'])
					driver_id = request_driver_json['driver_id']
					driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
				else:
					driver_id = None
					driver_name = None

				start_date = datetime.strptime(request_driver_json['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				start_time = datetime.strptime(request_driver_json['start_time'], '%H:%M:%S').strftime('%H:%M')

				create_date = datetime.strptime(request_driver_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
				create_time = datetime.strptime(request_driver_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
				
				delay_end_date = datetime.strptime(request_driver_json['delay_end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				delay_end_time = datetime.strptime(request_driver_json['delay_end_time'], '%H:%M:%S').strftime('%H:%M')

				accept_start_date = None
				accept_start_time = None
				end_job_date = None
				end_job_time = None

				if request_driver_json['accept_start_request'] is not None:
					accept_start_date = datetime.strptime(request_driver_json['accept_start_request'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
					accept_start_time = datetime.strptime(request_driver_json['accept_start_request'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
				
				if request_driver_json['end_job_at'] is not None:
					end_job_date = datetime.strptime(request_driver_json['end_job_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
					end_job_time = datetime.strptime(request_driver_json['end_job_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

				car = db.car.find_one({"_id": ObjectId(request_driver_json['car_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				car_type = db.car_type.find_one({"_id": ObjectId(car_json['car_type_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)
				car_type_name = car_type_json['car_type_name_th']

				car_brand = db.car_brand.find_one({"_id": ObjectId(car_json['car_brand_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_brand_object = dumps(car_brand)
				car_brand_json = json.loads(car_brand_object)
				car_brand_name = car_brand_json['brand_name']
				license_plate = car_json['license_plate']
				car_detail = car_type_name+" "+car_brand_name+" : "+license_plate

				if request_driver_json['special_request'] is not None:
					driver_age_range_list = []
					communication_list = []
					driver_gender_list = []

					for i in range(len(request_driver_json['special_request']['driver_age_range'])):
						driver_age_range = db.driver_age_range.find_one({"_id": ObjectId(request_driver_json['special_request']['driver_age_range'][i])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						driver_age_range_object = dumps(driver_age_range)
						driver_age_range_json = json.loads(driver_age_range_object)

						driver_age_range_list.append({
							"id" : driver_age_range_json['_id']['$oid'],
							"range": driver_age_range_json['age_range']
						})

					for j in range(len(request_driver_json['special_request']['communication'])):
						communication = db.communication.find_one({"_id": ObjectId(request_driver_json['special_request']['communication'][j])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						communication_object = dumps(communication)
						communication_json = json.loads(communication_object)

						lang_name = communication_json['lang_name_th']

						communication_list.append({
							"communication_id" : communication_json['_id']['$oid'],
							"lang_name": lang_name,
							"lang_code": communication_json['lang_code'],
							"flag_image": communication_json['flag_image']
						})

					for k in range(len(request_driver_json['special_request']['driver_gender'])):
						code = request_driver_json['special_request']['driver_gender'][k]
						if code == "female":
							name = "หญิง"
						else:	
							name = "ชาย"
						driver_gender_list.append({"code": code,"name": name})
				else:
					driver_age_range_list = None
					communication_list = None
					driver_gender_list = None

				main_package_info = get_package_info(request_driver_json['main_package_id'])
				main_package_name = main_package_info['package_name_th']

				second_package_name = ""

				if len(request_driver_json['second_package']) > 0:
					for i in range(len(request_driver_json['second_package'])):
						second_package_info = get_package_info(request_driver_json['second_package'][i]['package_id'])
						
						if i == 0:
							second_package_name = second_package_info['package_name_th']
						else:
							second_package_name = second_package_name+" , "+second_package_info['package_name_th']
				
				if len(request_driver_json['billing_id']) > 0:
					if second_package_name == "":
						second_package_name = "วางบิลบริษัท"
					else:
						second_package_name = second_package_name+" , วางบิลบริษัท"

				if request_driver_json['request_status'] == "6":
					request_status_text = "สำเร็จ"
				elif request_driver_json['request_status'] == "5":
					request_status_text = "กำลังเดินทาง"
				elif request_driver_json['request_status'] == "4":
					request_status_text = "งานที่ใกล้จะถึง"
				elif request_driver_json['request_status'] == "3":
					request_status_text = "ยกเลิกโดยคนขับ"
				elif request_driver_json['request_status'] == "2":
					request_status_text = "ยกเลิกโดยลูกค้า"
				elif request_driver_json['request_status'] == "1":
					request_status_text = "ตอบรับแล้ว"
				else:
					request_status_text = "รอตอบรับ"

				data = {
							"request_id" : request_driver_json['_id']['$oid'],
							"request_no" : request_driver_json['request_no'],
							"create_date" : create_date,
							"create_time" : create_time,
							"company_name": company_name,
							"member_name": member_name,
							"member_tel": member_tel,
							"main_package_name": main_package_name,
							"second_package_name": second_package_name,
							"start_date": start_date,
							"start_time": start_time,
							"passenger_name": passenger_name,
							"hour_amount": request_driver_json['hour_amount'],
							"from_location_address": request_driver_json['from_location_address'],
							"to_location_address": request_driver_json['to_location_address'],
							"car_detail": car_detail,
							"driver_note": request_driver_json['driver_note'],
							"driver_id": driver_id,
							"driver_name": driver_name,
							"driver_gender": driver_gender_list,
							"driver_age_range": driver_age_range_list,
							"communication": communication_list,
							"check_assgin_driver": check_assgin_driver,
							"request_status": request_driver_json['request_status'],
							"request_status_text": request_status_text,

							"accept_start_date": accept_start_date,
							"accept_start_time": accept_start_time,
							"end_job_date": end_job_date,
							"end_job_time": end_job_time,

							"remark_id": request_driver_json['remark_id'],
							"admin_remark": request_driver_json['admin_remark']
						}

				result = {
							"status" : True,
							"msg" : "Get request detail success.",
							"data" : data
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
	function_name = "get_request_detail"
	request_headers = request.headers
	params_get = {"request_id" : request_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

# edit
def get_request_form(request):
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

			driver_level = db.driver_level.find({"level_status": "1"})
			driver_level_list = []

			if driver_level is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)

				for i in range(len(driver_level_json)):
					driver_level_list.append({
						"id" : driver_level_json[i]['_id']['$oid'],
						"name": driver_level_json[i]['level_name_th'],
						"priority": int(driver_level_json[i]['level_priority'])
					})

			remark = db.request_driver_remark.find({"remark_status": "1"})
			remark_list = []

			if remark is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				remark_object = dumps(remark)
				remark_json = json.loads(remark_object)

				for i in range(len(remark_json)):
					remark_list.append({
						"id" : remark_json[i]['_id']['$oid'],
						"name": remark_json[i]['remark_th']
					})

			request_status_list = [
									{"code": "0","name": "รอตอบรับ"},
									{"code": "1","name": "ตอบรับแล้ว"},
									{"code": "2","name": "ยกเลิกโดยลูกค้า"},
									{"code": "3","name": "ยกเลิกโดยคนขับ"},
									{"code": "4","name": "งานที่ใกล้จะถึง"},
									{"code": "5","name": "กำลังเดินทาง"},
									{"code": "6","name": "สำเร็จ"}
								]

			result = {
						"status" : True,
						"msg" : "Get request form success.",
						"request_status" : request_status_list,
						"driver_level" : driver_level_list,
						"request_driver_remark" : remark_list
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
	function_name = "get_request_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def assign_driver_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_search_text = "search_text" in params
	isset_driver_level_id = "driver_level_id" in params
	
	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_search_text and isset_driver_level_id:
	# if isset_accept and isset_content_type and isset_token and isset_app_version and isset_search_text and isset_driver_level_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			where_param = { "member_type" : "driver", "member_status" : "1" }

			if params['search_text'] != "":
				add_params = {
								"$or": [
									{ "member_firstname_en": {"$regex": params['search_text']} },
									{ "member_lastname_en": {"$regex": params['search_text']} },
									{ "member_firstname_th": {"$regex": params['search_text']} },
									{ "member_lastname_th": {"$regex": params['search_text']} },
									{ "member_email": {"$regex": params['search_text']} },
									{ "member_tel": {"$regex": params['search_text']} }
								]
							}
				where_param.update(add_params)

			if params['driver_level_id'] != "":
				add_params = {"driver_level" : params['driver_level_id']}
				where_param.update(add_params)

			driver = db.member.find(where_param).sort([("driver_rating", -1)])

			if driver is None:
				result = { 
						"status" : False,
						"msg" : "Data not found."
					}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_object = dumps(driver)
				driver_json = json.loads(driver_object)

				driver_list = []

				for i in range(len(driver_json)):
					if driver_json[i]['driver_level'] is not None and driver_json[i]['driver_level'] != "":
						driver_level = db.driver_level.find_one({"_id": ObjectId(driver_json[i]['driver_level'])})
						
						if driver_level is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							driver_level_object = dumps(driver_level)
							driver_level_json = json.loads(driver_level_object)

							level_name = driver_level_json["level_name_th"]
							level_detail = driver_level_json["level_detail_th"]
							level_image = driver_level_json["level_image"]

						register_status_show = "พร้อมให้บริการ"

						if driver_json[i]['member_gender'] == "female":
							member_gender_text = "หญิง"
						else:
							member_gender_text = "ชาย"

						communication_list = []

						for j in range(len(driver_json[i]['communication'])):
							communication = db.communication.find_one({"_id": ObjectId(driver_json[i]['communication'][j])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							communication_object = dumps(communication)
							communication_json = json.loads(communication_object)

							lang_name = communication_json['lang_name_th']

							communication_list.append({
								"communication_id" : communication_json['_id']['$oid'],
								"lang_name": lang_name,
								"lang_code": communication_json['lang_code'],
								"flag_image": communication_json['flag_image']
							})

						car_type_detail = []
						car_type_text = ""

						if driver_json[i]['car_type_th'] is not None:
							car_type_split = driver_json[i]['car_type_th'].split(" , ")

							for j in range(len(car_type_split)):
								if car_type_split[j] == "รถเก๋ง":
									car_type_text = car_type_split[j]+" "+str(driver_json[i]['sedan_job'])+" ครั้ง"
								elif car_type_split[j] == "รถ SUV":
									car_type_text = car_type_split[j]+" "+str(driver_json[i]['suv_job'])+" ครั้ง"
								else:
									car_type_text = car_type_split[j]+" "+str(driver_json[i]['van_job'])+" ครั้ง"

								car_type_detail.append(car_type_text)

						if driver_json[i]['driver_rating'] is not None:
							driver_rating = round(float(driver_json[i]['driver_rating']) , 1)
						else:
							driver_rating = float("0")

						driver_list.append({
							"member_id" : driver_json[i]['_id']['$oid'],
							"member_code": driver_json[i]['member_code'],
							"member_fullname": driver_json[i]['member_firstname_th']+" "+driver_json[i]['member_lastname_th'],
							"member_tel": driver_json[i]['member_tel'],
							"driver_level_id": driver_json[i]['driver_level'],
							"level_name": level_name,
							"level_detail": level_detail,
							"level_image": level_image,
							"driver_level_priority": driver_json[i]['driver_level_priority'],
							"driver_rating": driver_rating,
							"member_age": int(driver_json[i]['member_age']),
							"member_gender": driver_json[i]['member_gender'],
							"member_gender_text": member_gender_text,
							"profile_image": driver_json[i]['profile_image'],
							"car_type_detail": car_type_detail,
							"communication": communication_list
						})

			result = {
						"status" : True,
						"msg" : "Get assign driver list success.",
						"data" : driver_list
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
	function_name = "assign_driver_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

# def assign_driver(request):
# 	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_accept = "Accept" in request.headers
# 	isset_content_type = "Content-Type" in request.headers
# 	isset_token = "Authorization" in request.headers
# 	admin_id = None

# 	params = json.loads(request.data)

# 	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_app_version = "app_version" in params
# 	isset_request_id = "request_id" in params
# 	isset_member_id = "member_id" in params

# 	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_member_id:
# 		#เช็ค token ว่า expire แล้วหรือยัง
# 		token = request.headers['Authorization']
# 		check_token = check_token_expire_backend(token)

# 		if check_token:
# 			admin_info = get_admin_info(token)
# 			admin_id = admin_info['_id']['$oid']

# 			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
# 			if request_driver is None:
# 				result = { 
# 							"status" : False,
# 							"msg" : "Data not found.",
# 							"msg_code" : "0"
# 						}
# 			else:
# 				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 				request_driver_object = dumps(request_driver)
# 				request_driver_json = json.loads(request_driver_object)

# 				if request_driver_json['request_status'] == "0" and request_driver_json['driver_id'] is None:
# 					#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
# 					driver_list_id = ObjectId()
# 					#แปลง ObjectId ให้เป็น string
# 					driver_list_id_string = str(driver_list_id)

# 					driver_list = []

# 					driver_list.append({
# 						"driver_id" : params['member_id'],
# 						"driver_request_status": "1"
# 					})

# 					#insert driver_list
# 					driver_list_data = { 
# 								"_id": driver_list_id,
# 								"request_id": params['request_id'],
# 								"driver_list": driver_list,
# 								"driver_list_status": "1",
# 								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 							}
					
# 					if db.driver_list.insert_one(driver_list_data):
# 						driver_info = get_member_info_by_id(params['member_id'])
# 						driver_name_en = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
# 						driver_name_th = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
# 						driver_code = driver_info['member_code']

# 						# update request_driver
# 						where_param = { "_id": ObjectId(params['request_id']) }
# 						value_param = {
# 										"$set":
# 											{
# 												"driver_list_id": driver_list_id_string,
# 												"driver_id": params['member_id'],
# 												"driver_name_en": driver_name_en,
# 												"driver_name_th": driver_name_th,
# 												"driver_code": driver_code,
# 												"request_status": "1",
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}

# 						if db.request_driver.update(where_param , value_param):
# 							#ส่ง noti หาลูกค้าว่า คนขับรับงานแล้ว
# 							customer_info = get_member_info_by_id(request_driver_json['member_id'])
# 							member_info = get_member_info_by_id(params['member_id'])
# 							noti_type = "accept_job"
# 							request_no = request_driver_json['request_no']

# 							noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
# 							noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
# 							noti_message_en = "accept job : "+request_no
# 							noti_message_th = "รับงาน "+request_no

# 							if customer_info['member_lang'] == "en":
# 								noti_title = noti_title_en
# 								noti_message = noti_message_en
# 								show_noti = noti_title_en+" "+noti_message_en
# 							else:
# 								noti_title = noti_title_th
# 								noti_message = noti_message_th
# 								show_noti = noti_title_th+" "+noti_message_th

# 							#แปลง format วันที่
# 							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 							created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

# 							#ส่ง noti
# 							send_noti_key = customer_info['noti_key']
# 							send_noti_title = noti_title
# 							send_noti_message = noti_message
# 							send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
# 							send_noti_badge = 1

# 							#insert member_notification
# 							noti_detail = {
# 												"request_id": params['request_id'],
# 												"request_no": request_no
# 											}

# 							data = { 
# 										"member_id": customer_info['_id']['$oid'],
# 										"member_fullname": customer_info['member_firstname_en']+" "+customer_info['member_lastname_en'],
# 										"noti_type": noti_type,
# 										"noti_message_en": noti_title_en+" "+noti_message_en,
# 										"noti_message_th": noti_title_th+" "+noti_message_th,
# 										"noti_detail": noti_detail,
# 										"noti_status": "0",
# 										"created_at": created_at,
# 										"updated_at": created_at
# 									}
# 							db.member_notification.insert_one(data)

# 							try:
# 								send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
# 								send_status = True
# 							except:
# 								send_status = False


# 							#sent noti to passenger
# 							if request_driver_json['member_id'] != request_driver_json['passenger_id']:
# 								passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])
								
# 								if passenger_info['member_lang'] == "en":
# 									noti_title = noti_title_en
# 									noti_message = noti_message_en
# 									show_noti = noti_title_en+" "+noti_message_en
# 								else:
# 									noti_title = noti_title_th
# 									noti_message = noti_message_th
# 									show_noti = noti_title_th+" "+noti_message_th

# 								#แปลง format วันที่
# 								created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 								created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

# 								#ส่ง noti
# 								send_noti_key = passenger_info['noti_key']
# 								send_noti_title = noti_title
# 								send_noti_message = noti_message
# 								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
# 								send_noti_badge = 1

# 								#insert member_notification
# 								noti_detail = {
# 													"request_id": params['request_id'],
# 													"request_no": request_no
# 												}

# 								data = { 
# 											"member_id": passenger_info['_id']['$oid'],
# 											"member_fullname": passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en'],
# 											"noti_type": noti_type,
# 											"noti_message_en": noti_title_en+" "+noti_message_en,
# 											"noti_message_th": noti_title_th+" "+noti_message_th,
# 											"noti_detail": noti_detail,
# 											"noti_status": "0",
# 											"created_at": created_at,
# 											"updated_at": created_at
# 										}
# 								db.member_notification.insert_one(data)

# 								try:
# 									send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
# 									send_status = True
# 								except:
# 									send_status = False


# 							result = {
# 										"status" : True,
# 										"msg" : "Assign driver success.",
# 										"send_status" : send_status
# 									}
# 						else:
# 							result = {
# 										"status" : False,
# 										"msg" : "Request driver update failed."
# 									}
# 					else:
# 						result = {
# 									"status" : False,
# 									"msg" : "Driver list insert failed."
# 								}
# 				else:
# 					result = {
# 								"status" : False,
# 								"msg" : "Can't assign driver because someone already accepted this job."
# 							}	
# 		else:
# 			result = { 
# 				"status" : False,
# 				"error_code" : 401,
# 				"msg" : "Unauthorized."
# 			}
# 	else:
# 		result = { 
# 					"status" : False,
# 					"msg" : "Please check your parameters."
# 				}

# 	#set log detail
# 	user_type = "admin"
# 	function_name = "assign_driver"
# 	request_headers = request.headers
# 	params_get = None
# 	params_post = params
# 	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

# 	return result

# edit
def assign_driver(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_member_id = "member_id" in params
	isset_remark_id = "remark_id" in params
	isset_admin_remark = "admin_remark" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_member_id and isset_remark_id and isset_admin_remark:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Data not found.",
							"msg_code" : "0"
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['request_status'] == "0" and request_driver_json['driver_id'] is None and params['member_id'] is not None:
					#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
					driver_list_id = ObjectId()
					#แปลง ObjectId ให้เป็น string
					driver_list_id_string = str(driver_list_id)

					driver_list = []

					driver_list.append({
						"driver_id" : params['member_id'],
						"driver_request_status": "1"
					})

					#insert driver_list
					driver_list_data = { 
											"_id": driver_list_id,
											"request_id": params['request_id'],
											"driver_list": driver_list,
											"driver_list_status": "1",
											"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
					
					if db.driver_list.insert_one(driver_list_data):
						driver_info = get_member_info_by_id(params['member_id'])
						driver_name_en = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
						driver_name_th = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
						driver_code = driver_info['member_code']

						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"driver_list_id": driver_list_id_string,
												"driver_id": params['member_id'],
												"driver_name_en": driver_name_en,
												"driver_name_th": driver_name_th,
												"driver_code": driver_code,
												"request_status": "1",
												"remark_id": params['remark_id'],
												"admin_remark": params['admin_remark'],
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.request_driver.update(where_param , value_param):
							#ส่ง noti หาลูกค้าว่า คนขับรับงานแล้ว
							customer_info = get_member_info_by_id(request_driver_json['member_id'])
							member_info = get_member_info_by_id(params['member_id'])
							noti_type = "accept_job"
							request_no = request_driver_json['request_no']

							noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
							noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
							noti_message_en = "accept job : "+request_no
							noti_message_th = "รับงาน "+request_no

							if customer_info['member_lang'] == "en":
								noti_title = noti_title_en
								noti_message = noti_message_en
								show_noti = noti_title_en+" "+noti_message_en
							else:
								noti_title = noti_title_th
								noti_message = noti_message_th
								show_noti = noti_title_th+" "+noti_message_th

							#แปลง format วันที่
							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							#ส่ง noti
							send_noti_key = customer_info['noti_key']
							send_noti_title = noti_title
							send_noti_message = noti_message
							send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
							send_noti_badge = 1

							#insert member_notification
							noti_detail = {
												"request_id": params['request_id'],
												"request_no": request_no
											}

							data = { 
										"member_id": customer_info['_id']['$oid'],
										"member_fullname": customer_info['member_firstname_en']+" "+customer_info['member_lastname_en'],
										"noti_type": noti_type,
										"noti_message_en": noti_title_en+" "+noti_message_en,
										"noti_message_th": noti_title_th+" "+noti_message_th,
										"noti_detail": noti_detail,
										"noti_status": "0",
										"created_at": created_at,
										"updated_at": created_at
									}
							db.member_notification.insert_one(data)

							try:
								send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
								send_status = True
							except:
								send_status = False


							#sent noti to passenger
							if request_driver_json['member_id'] != request_driver_json['passenger_id']:
								passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])
								
								if passenger_info['member_lang'] == "en":
									noti_title = noti_title_en
									noti_message = noti_message_en
									show_noti = noti_title_en+" "+noti_message_en
								else:
									noti_title = noti_title_th
									noti_message = noti_message_th
									show_noti = noti_title_th+" "+noti_message_th

								#แปลง format วันที่
								created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

								#ส่ง noti
								send_noti_key = passenger_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"request_id": params['request_id'],
													"request_no": request_no
												}

								data = { 
											"member_id": passenger_info['_id']['$oid'],
											"member_fullname": passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en'],
											"noti_type": noti_type,
											"noti_message_en": noti_title_en+" "+noti_message_en,
											"noti_message_th": noti_title_th+" "+noti_message_th,
											"noti_detail": noti_detail,
											"noti_status": "0",
											"created_at": created_at,
											"updated_at": created_at
										}
								db.member_notification.insert_one(data)

								try:
									send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
									send_status = True
								except:
									send_status = False

							result = {
										"status" : True,
										"msg" : "Assign driver success."
									}
						else:
							result = {
										"status" : False,
										"msg" : "Request driver update failed."
									}
					else:
						result = {
									"status" : False,
									"msg" : "Driver list insert failed."
								}
				else:
					# update request_driver
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"remark_id": params['remark_id'],
											"admin_remark": params['admin_remark'],
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}
					db.request_driver.update(where_param , value_param)

					result = {
								"status" : True,
								"msg" : "Assign driver success."
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
	function_name = "assign_driver"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def news_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_display = "display" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_display:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { }

				#news_title_en , news_title_th
				if params['search_text'] != "":
					add_params = {
									"$and": [
										{
											"$or": [
												{ "news_title_en": {"$regex": params['search_text']} },
												{ "news_title_th": {"$regex": params['search_text']} }
											]
										}
									]
								}
					where_param.update(add_params)

				if params['display'] == "customer":
					add_params = {"display" : "customer"}
					where_param.update(add_params)
				elif params['display'] == "driver":
					add_params = {"display" : "driver"}
					where_param.update(add_params)
				elif params['display'] == "private":
					add_params = {"display" : "private"}
					where_param.update(add_params)
				elif params['display'] == "all":
					add_params = {"display" : "all"}
					where_param.update(add_params)

				if params['start_date'] != "" and params['end_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {
									"$or": [
												# #2020-06-01 >= 2020-08-01 and 2020-06-01 <= 2020-12-31
												# {"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}},
												# #2020-08-31 >= 2020-08-01
												# {"end_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}},
												
												{
													"$and": [
																{ "start_date_int" : {"$gte" : start_date_int} },
																{ "start_date_int" : {"$lte" : end_date_int} }
															]
												},
												{
													"$and": [
																{ "end_date_int" : {"$gte" : start_date_int} },
																{ "end_date_int" : {"$lte" : end_date_int} }
															]
												},
												{ 
													"$and": [ 
																{ "start_date_int" : {"$lte" : start_date_int} },
																{ "start_date_int" : {"$lte" : end_date_int} },
																{ "end_date_int" : {"$gte" : start_date_int} },
																{ "end_date_int" : {"$gte" : end_date_int} }
															]
												}
												
											],
									
								}
					where_param.update(add_params)

				news = db.news.find(where_param).sort([("pin", -1),("created_at", -1)]).skip(data_start_at).limit(data_length)
				total_data = db.news.find(where_param).count()

				if news is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					news_object = dumps(news)
					news_json = json.loads(news_object)

					news_list = []

					for i in range(len(news_json)):
						if news_json[i]['news_status'] == "1":
							news_status_text = "เปิดใช้งาน"
						else:
							news_status_text = "ปิดใช้งาน"

						if news_json[i]['display'] == "customer":
							display = "Customer"
						elif news_json[i]['display'] == "driver":
							display = "Driver"
						elif news_json[i]['display'] == "private":
							display = "ชื่อบริษัท"
						else:
							display = "ทั้งหมด"

						news_list.append({
							"news_id" : news_json[i]['_id']['$oid'],
							"news_title_en": news_json[i]['news_title_en'],
							"news_title_th": news_json[i]['news_title_th'],
							"news_detail_en": news_json[i]['news_detail_en'],
							"news_detail_th": news_json[i]['news_detail_th'],
							"start_date": news_json[i]['start_date'],
							"end_date": news_json[i]['end_date'],
							"display": display,
							"pin": news_json[i]['pin'],
							"private": news_json[i]['private'],
							"news_cover": news_json[i]['news_cover'],
							"news_status": news_json[i]['news_status'],
							"news_status_text": news_status_text
						})

				result = {
							"status" : True,
							"msg" : "Get news list success.",
							"data" : news_list,
							"total_data" : total_data,
							"where_param" : where_param,
							"search_text" : params['search_text'] 
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
	function_name = "news_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_news_form(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	if isset_accept and isset_content_type:
		company = db.company.find({"company_status" : "1"}).sort([("updated_at", -1)])

		if company is None:
			result = { 
					"status" : False,
					"msg" : "Data not found."
				}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			company_object = dumps(company)
			company_json = json.loads(company_object)

			company_list = []

			for i in range(len(company_json)):
				company_list.append({
					"value" : company_json[i]['_id']['$oid'],
					"label": company_json[i]['company_name']
				})

		display_list = [
							{"code": "all","name": "ทั้งหมด"},
							{"code": "customer","name": "Customer"},
							{"code": "driver","name": "Driver"},
							{"code": "private","name": "ชื่อบริษัท"}
						]	

		total_pin = count_pin()

		result = {
					"status" : True,
					"msg" : "Get news form success.",
					"company" : company_list,
					"display" : display_list,
					"total_pin" : total_pin
				}
	else:
		result = { 
					"status" : False,
					"msg" : "Please check your parameters."
				}

	#set log detail
	user_type = "admin"
	function_name = "get_news_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_news_detail(news_id,request):
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

			news = db.news.find_one({ "_id": ObjectId(news_id) })

			if news is None:
				result = { 
						"status" : False,
						"msg" : "Data not found."
					}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				news_object = dumps(news)
				news_json = json.loads(news_object)

				if news_json['news_status'] == "1":
					news_status_text = "เปิดใช้งาน"
				else:
					news_status_text = "ปิดใช้งาน"

				total_pin = count_pin(news_id)
				private_list = []

				for i in range(len(news_json['private'])):
					private_list.append({
						"value" : news_json['private'][i]['company_id'],
						"label": news_json['private'][i]['company_name']
					})

				result = {
							"status" : True,
							"msg" : "Get news detail success.",
							"news_id" : news_json['_id']['$oid'],
							"news_title_en": news_json['news_title_en'],
							"news_title_th": news_json['news_title_th'],
							"news_detail_en": news_json['news_detail_en'],
							"news_detail_th": news_json['news_detail_th'],
							"start_date": news_json['start_date'],
							"end_date": news_json['end_date'],
							"display": news_json['display'],
							"pin": news_json['pin'],
							"private": private_list,
							"news_cover": news_json['news_cover'],
							"news_status": news_json['news_status'],
							"news_status_text": news_status_text,
							"total_pin": total_pin
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
	function_name = "get_news_detail"
	request_headers = request.headers
	params_get = {"news_id" : news_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_news(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_news_title_en = "news_title_en" in params
	isset_news_title_th = "news_title_th" in params
	isset_news_detail_en = "news_detail_en" in params
	isset_news_detail_th = "news_detail_th" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_display = "display" in params
	isset_pin = "pin" in params
	isset_private = "private" in params
	isset_news_cover = "news_cover" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_news_title_en and isset_news_title_th and isset_news_detail_en and isset_news_detail_th and isset_start_date and isset_end_date and isset_display and isset_pin and isset_private and isset_news_cover:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['news_title_en']=="" or params['news_title_en'] is None:
				validate.append({"error_param" : "news_title_en","msg" : "News title (EN) is required."})
			if params['news_title_th']=="" or params['news_title_th'] is None:
				validate.append({"error_param" : "news_title_th","msg" : "News title (TH) is required."})
			if params['news_detail_en']=="" or params['news_detail_en'] is None:
				validate.append({"error_param" : "news_detail_en","msg" : "News detail (EN) is required."})
			if params['news_detail_th']=="" or params['news_detail_th'] is None:
				validate.append({"error_param" : "news_detail_th","msg" : "News detail (TH) is required."})

			if params['start_date']=="" or params['start_date'] is None:
				validate.append({"error_param" : "start_date","msg" : "Start date is required."})
			if params['end_date']=="" or params['end_date'] is None:
				validate.append({"error_param" : "end_date","msg" : "End date is required."})
			if params['display']=="" or params['display'] is None:
				validate.append({"error_param" : "display","msg" : "Display is required."})
			if params['pin']=="" or params['pin'] is None:
				validate.append({"error_param" : "pin","msg" : "Pin is required."})
			else:
				total_pin = count_pin()

				if total_pin == 3 and params['pin'] == "1":
					validate.append({"error_param" : "pin","msg" : "Pin more than 3."})
	

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				if params['news_cover'] is None:
					image_name = None
				else:
					#generate token
					generate_token = get_random_token(40)
					check_upload_image = upload_news_cover(params['news_cover'], generate_token)

					if check_upload_image is None:
						image_name = None
					else:
						image_name = check_upload_image

				#เช็ค start_date , end_date
				start_date_obj = datetime.strptime(params['start_date'], '%Y-%m-%d')
				end_date_obj = datetime.strptime(params['end_date'], '%Y-%m-%d')
				current_datetime_obj = datetime.now()

				start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 

				#ถ้าวันที่ปัจจุบัน มากกว่าหรือเท่ากับ start_date และ น้อยกว่าหรือเท่ากับ end_date ให้ news_status = '1'
				if current_datetime_obj >= start_date_obj and current_datetime_obj <= end_date_obj:
					news_status = "1"
				else:
					news_status = "0"

				private_list = []

				if len(params['private']) > 0:
					for i in range(len(params['private'])):
						private_list.append({
							"company_id" : params['private'][i]['value'],
							"company_name": params['private'][i]['label']
						})

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				news_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				news_id_string = str(news_id)
				
				data = { 
							"_id": news_id,
							"news_title_en": params['news_title_en'],
							"news_title_th": params['news_title_th'],
							"news_detail_en": params['news_detail_en'],
							"news_detail_th": params['news_detail_th'],
							"start_date": params['start_date'],
							"end_date": params['end_date'],
							"start_date_int": start_date_int,
							"end_date_int": end_date_int,
							"display": params['display'],
							"private": private_list,
							"pin": params['pin'],
							"news_cover": image_name,
							"news_status": news_status,
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.news.insert_one(data):
					if news_status == "1":
						if params['display'] == "customer":
							member = db.member.find({
														"member_type": "customer"
													})
						elif params['display'] == "driver":
							member = db.member.find({
														"member_type": "driver"
													})
						elif params['display'] == "private":
							company_in = []
							for i in range(len(params['private'])):
								company_in.append(params['private'][i]['value'])

							member = db.member.find({
														"member_type": "customer",
														"company_id": {"$in": company_in}
													})
						else:
							member = db.member.find()

						if member is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							member_object = dumps(member)
							member_json = json.loads(member_object)

							#วน loop ส่ง noti
							for i in range(len(member_json)):
								member_info = get_member_info_by_id(member_json[i]['_id']['$oid'])

								noti_title_en = "News & Promotion"
								noti_title_th = "ข่าวสารโปรโมชั่น"
								noti_message_en = params['news_title_en']
								noti_message_th = params['news_title_th']

								if member_info['member_lang'] == "en":
									member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									noti_title = noti_title_en
									noti_message = noti_message_en
									show_noti = noti_title_en+" "+noti_message_en
								else:
									member_fullname = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
									noti_title = noti_title_th
									noti_message = noti_message_th
									show_noti = noti_title_th+" "+noti_message_th

								#แปลง format วันที่
								created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')


								noti_type = "news_promotion"
								send_noti_key = member_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "news_id": params['news_id'] , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"news_id": news_id_string
												}

								data = { 
											"member_id": member_info['_id']['$oid'],
											"member_fullname": member_fullname,
											"noti_type": noti_type,
											"noti_message_en": noti_title_en+" "+noti_message_en,
											"noti_message_th": noti_title_th+" "+noti_message_th,
											"noti_detail": noti_detail,

											"send_noti_key": send_noti_key,
											"send_noti_title": send_noti_title,
											"send_noti_message": send_noti_message,
											"send_noti_data": send_noti_data,
											"send_noti_badge": send_noti_badge,

											"send_status": "0",
											"created_at": created_at,
											"updated_at": created_at
										}
								db.queue_notification.insert_one(data)

					result = {
								"status" : True,
								"msg" : "Add news success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Data insert failed."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "add_news"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_news(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_news_id = "news_id" in params
	isset_news_title_en = "news_title_en" in params
	isset_news_title_th = "news_title_th" in params
	isset_news_detail_en = "news_detail_en" in params
	isset_news_detail_th = "news_detail_th" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_display = "display" in params
	isset_pin = "pin" in params
	isset_private = "private" in params
	isset_send_noti = "send_noti" in params
	isset_news_cover = "news_cover" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_news_id and isset_news_title_en and isset_news_title_th and isset_news_detail_en and isset_news_detail_th and isset_start_date and isset_end_date and isset_display and isset_pin and isset_private and isset_send_noti and isset_news_cover:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			validate = []

			#check required
			if params['news_title_en']=="" or params['news_title_en'] is None:
				validate.append({"error_param" : "news_title_en","msg" : "News title (EN) is required."})
			if params['news_title_th']=="" or params['news_title_th'] is None:
				validate.append({"error_param" : "news_title_th","msg" : "News title (TH) is required."})
			if params['news_detail_en']=="" or params['news_detail_en'] is None:
				validate.append({"error_param" : "news_detail_en","msg" : "News detail (EN) is required."})
			if params['news_detail_th']=="" or params['news_detail_th'] is None:
				validate.append({"error_param" : "news_detail_th","msg" : "News detail (TH) is required."})

			if params['start_date']=="" or params['start_date'] is None:
				validate.append({"error_param" : "start_date","msg" : "Start date is required."})
			if params['end_date']=="" or params['end_date'] is None:
				validate.append({"error_param" : "end_date","msg" : "End date is required."})
			if params['display']=="" or params['display'] is None:
				validate.append({"error_param" : "display","msg" : "Display is required."})
			if params['pin']=="" or params['pin'] is None:
				validate.append({"error_param" : "pin","msg" : "Pin is required."})
			else:
				total_pin = count_pin(params['news_id'])

				if total_pin == 3 and params['pin'] == "1":
					validate.append({"error_param" : "pin","msg" : "Pin more than 3."})

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				news = db.news.find_one({
											"_id": ObjectId(params['news_id'])
										})
				if news is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					news_object = dumps(news)
					news_json = json.loads(news_object)

					#ถ้าไม่มีการแก้ไขรูป profile (profile_image เป็น null) ไม่ต้องอัพเดตรูป  
					if params['news_cover'] is None:
						image_name = news_json['news_cover']
					else:
						#เช็ค path และลบรูปเก่า
						if news_json['news_cover'] is not None:
							if os.path.exists("static/images/news/"+news_json['news_cover']):
								os.remove("static/images/news/"+news_json['news_cover'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_news_cover(params['news_cover'], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

					#เช็ค start_date , end_date
					start_date_obj = datetime.strptime(params['start_date']+" 00:00:00", '%Y-%m-%d %H:%M:%S')
					end_date_obj = datetime.strptime(params['end_date']+" 23:59:59", '%Y-%m-%d %H:%M:%S')
					current_datetime_obj = datetime.now()

					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 

					#ถ้าวันที่ปัจจุบัน มากกว่าหรือเท่ากับ start_date และ น้อยกว่าหรือเท่ากับ end_date ให้ news_status = '1'
					if current_datetime_obj >= start_date_obj and current_datetime_obj <= end_date_obj:
						news_status = "1"
					else:
						news_status = "0"

					private_list = []

					if len(params['private']) > 0:
						for i in range(len(params['private'])):
							private_list.append({
								"company_id" : params['private'][i]['value'],
								"company_name": params['private'][i]['label']
							})

					where_param = { "_id": ObjectId(params['news_id']) }
					value_param = {
									"$set": {
												"news_title_en": params['news_title_en'],
												"news_title_th": params['news_title_th'],
												"news_detail_en": params['news_detail_en'],
												"news_detail_th": params['news_detail_th'],
												"start_date": params['start_date'],
												"end_date": params['end_date'],
												"start_date_int": start_date_int,
												"end_date_int": end_date_int,
												"display": params['display'],
												"private": private_list,
												"pin": params['pin'],
												"news_cover": image_name,
												"news_status": news_status,
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

					if db.news.update(where_param , value_param):
						if news_status == "1" and int(params['send_noti']) == 1:
							if params['display'] == "customer":
								member = db.member.find({
															"member_type": "customer"
														})
							elif params['display'] == "driver":
								member = db.member.find({
															"member_type": "driver"
														})
							elif params['display'] == "private":
								company_in = []
								for i in range(len(params['private'])):
									company_in.append(params['private'][i]['value'])

								member = db.member.find({
															"member_type": "customer",
															"company_id": {"$in": company_in}
														})
							else:
								member = db.member.find()

							if member is not None:
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								member_object = dumps(member)
								member_json = json.loads(member_object)

								#วน loop ส่ง noti
								for i in range(len(member_json)):
									member_info = get_member_info_by_id(member_json[i]['_id']['$oid'])

									noti_title_en = "News & Promotion"
									noti_title_th = "ข่าวสารโปรโมชั่น"
									noti_message_en = params['news_title_en']
									noti_message_th = params['news_title_th']

									if member_info['member_lang'] == "en":
										member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']
										noti_title = noti_title_en
										noti_message = noti_message_en
										show_noti = noti_title_en+" "+noti_message_en
									else:
										member_fullname = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
										noti_title = noti_title_th
										noti_message = noti_message_th
										show_noti = noti_title_th+" "+noti_message_th

									#แปลง format วันที่
									created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')


									noti_type = "news_promotion"
									send_noti_key = member_info['noti_key']
									send_noti_title = noti_title
									send_noti_message = noti_message
									send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "news_id": params['news_id'] , "created_datetime" : created_datetime }
									send_noti_badge = 1

									#insert member_notification
									noti_detail = {
														"news_id": params['news_id']
													}

									data = { 
												"member_id": member_info['_id']['$oid'],
												"member_fullname": member_fullname,
												"noti_type": noti_type,
												"noti_message_en": noti_title_en+" "+noti_message_en,
												"noti_message_th": noti_title_th+" "+noti_message_th,
												"noti_detail": noti_detail,

												"send_noti_key": send_noti_key,
												"send_noti_title": send_noti_title,
												"send_noti_message": send_noti_message,
												"send_noti_data": send_noti_data,
												"send_noti_badge": send_noti_badge,

												"send_status": "0",
												"created_at": created_at,
												"updated_at": created_at
											}
									db.queue_notification.insert_one(data)

						result = {
									"status" : True,
									"msg" : "Edit news success."
								}
					else:
						result = {
									"status" : False,
									"msg" : "Data update failed."
								}
			else:
				result = {
							"status" : False,
							"msg" : "Please check your parameters value.",
							"error_list" : validate
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
	function_name = "edit_news"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def contact_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_topic_id = "topic_id" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_topic_id and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { }

				#contact_name , contact_email , contact_tel , contact_message
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "contact_firstname": {"$regex": params['search_text']} },
												{ "contact_lastname": {"$regex": params['search_text']} },
												{ "contact_email": {"$regex": params['search_text']} },
												{ "contact_tel": {"$regex": params['search_text']} },
												{ "contact_message": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)


				if params['topic_id'] != "":
					add_params = {"contact_topic_id" : params['topic_id']}
					where_param.update(add_params)

				if params['start_date'] != "" and params['end_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = { "create_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# create_date = created_at
					# topic_name = topic_name
					# contact_name = contact_firstname
					# contact_email = contact_email
					# contact_tel = contact_tel
					# contact_message = contact_message

					if params['sort_name'] == "create_date":
						sort_name = "created_at"
					elif params['sort_name'] == "contact_name":
						sort_name = "contact_firstname"
					elif params['sort_name'] == "topic_name":
						sort_name = "contact_topic_name"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

				contact = db.contact.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.contact.find(where_param).count()

				if contact is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					contact_object = dumps(contact)
					contact_json = json.loads(contact_object)

					contact_list = []

					for i in range(len(contact_json)):
						create_date = datetime.strptime(contact_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						create_time = datetime.strptime(contact_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

						contact_list.append({
							"contact_id" : contact_json[i]['_id']['$oid'],
							"create_date": create_date,
							"create_time": create_time,
							"topic_id": contact_json[i]['contact_topic_id'],
							"topic_name": contact_json[i]['contact_topic_name'],
							"contact_name": contact_json[i]['contact_firstname']+" "+contact_json[i]['contact_lastname'],
							"contact_email": contact_json[i]['contact_email'],
							"contact_tel": contact_json[i]['contact_tel'],
							"contact_message": contact_json[i]['contact_message']
						})

				result = {
							"status" : True,
							"msg" : "Get contact list success.",
							"data" : contact_list,
							"total_data" : total_data
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
	function_name = "contact_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_contact_form(request):
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

			contact_topic = db.contact_topic.find({"topic_status": "1"})

			if contact_topic is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				contact_topic_object = dumps(contact_topic)
				contact_topic_json = json.loads(contact_topic_object)

				contact_topic_list = []

				for i in range(len(contact_topic_json)):
					contact_topic_list.append({
						"topic_id" : contact_topic_json[i]['_id']['$oid'],
						"topic_name": contact_topic_json[i]['topic_th']
					})

			result = {
						"status" : True,
						"msg" : "Get contact form success.",
						"data" : contact_topic_list
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
	function_name = "get_contact_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def payment_driver_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_payment_status = "payment_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_payment_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:

				# request_driver = db.request_driver.find({
				# 											"request_status": "6",
				# 											"job_status" : {"$in" : ["8","10"]}
				# 										})

				# if request_driver is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	request_driver_object = dumps(request_driver)
				# 	request_driver_json = json.loads(request_driver_object)

				# 	for i in range(len(request_driver_json)):

				# 		if request_driver_json[i]['driver_id'] is not None:
				# 			driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				# 			driver_name_en = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
				# 			driver_name_th = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
				# 			driver_code = driver_info['member_code']
				# 		else:
				# 			driver_name_en = None
				# 			driver_name_th = None
				# 			driver_code = None

				# 		# update data
				# 		where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"driver_name_en": driver_name_en,
				# 								"driver_name_th": driver_name_th,
				# 								"driver_code": driver_code
				# 							}
				# 					}

				# 		db.request_driver.update(where_param , value_param)	

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = { "request_status": "6", "job_status" : {"$in" : ["8","10"]} }

				#driver_name , driver_code , request_no
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "driver_name_en": {"$regex": params['search_text']} },
												{ "driver_name_th": {"$regex": params['search_text']} },
												{ "driver_code": {"$regex": params['search_text']} },
												{ "request_no": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['payment_status'] == "0" or params['payment_status'] == "1" or params['payment_status'] == "2":
					add_params = {"payment_status" : params['payment_status']}
					where_param.update(add_params)
				else:
					add_params = {"payment_status" : {"$in" : ["0","1","2"]}}
					where_param.update(add_params)

				if params['start_date'] != "" and params['end_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# request_no = request_no
					# start_date = start_date
					# driver_name = driver_name_th
					# driver_code = driver_code
					# payment_amount = payment_amount
					# payment_status_text = payment_status

					if params['sort_name'] == "driver_name":
						sort_name = "driver_name_th"
					elif params['sort_name'] == "payment_status_text":
						sort_name = "payment_status"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				request_driver = db.request_driver.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.request_driver.find(where_param).count()

				if request_driver is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					payment_driver_list = []

					for i in range(len(request_driver_json)):
						create_datetime_obj = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S')
						create_date = create_datetime_obj.strftime('%Y-%m-%d')
						create_time = create_datetime_obj.strftime('%H:%M')
						start_date = request_driver_json[i]['start_date']
						start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')

						payment_date = None
						if request_driver_json[i]['payment_date'] is not None:
							payment_datetime_obj = datetime.strptime(request_driver_json[i]['payment_date'], '%Y-%m-%d')
							payment_date = payment_datetime_obj.strftime('%Y-%m-%d')

						driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
						driver_code = driver_info['member_code']
						driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

						if request_driver_json[i]['payment_status'] == "2":
							payment_status_text = "ตั้งค่าการจ่ายแล้ว"
						elif request_driver_json[i]['payment_status'] == "1":
							payment_status_text = "จ่ายแล้ว"
						else:
							payment_status_text = "รอดำเนินการ"

						payment_driver_list.append({
							"request_id": request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"create_date": create_date,
							"create_time": create_time,
							"start_date": start_date,
							"start_time": start_time,
							"driver_code": driver_code,
							"driver_name": driver_name,
							"normal_payment_amount": request_driver_json[i]['normal_payment_amount'],
							"total_overtime_usage": int(request_driver_json[i]['total_overtime_usage']),
							"overtime_payment_amount": request_driver_json[i]['overtime_payment_amount'],
							"payment_amount": request_driver_json[i]['payment_amount'],
							"payment_status": request_driver_json[i]['payment_status'],
							"payment_status_text": payment_status_text,
							"payment_date": payment_date
						})

				result = {
							"status" : True,
							"msg" : "Get payment driver list success.",
							"payment_driver" : payment_driver_list,
							"total_data" : total_data
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
	function_name = "payment_driver_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_payment_driver_form(request):
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

			payment_status_list = [
										{"code": "0","name": "รอดำเนินการ"},
										{"code": "1","name": "จ่ายแล้ว"},
										{"code": "2","name": "ตั้งค่าการจ่ายแล้ว"}
									]

			payment_status_report_list = [
											{"code": "0","name": "ยังไม่ได้จ่าย"},
											{"code": "1","name": "จ่ายแล้ว"}
										]

			result = {
						"status" : True,
						"msg" : "Get payment driver form success.",
						"payment_status" : payment_status_list,
						"payment_status_report" : payment_status_report_list
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
	function_name = "get_payment_driver_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_payment_driver_detail(request_id,request):
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

			request_driver = db.request_driver.find_one({ 
															"_id": ObjectId(request_id) , 
															"request_status": "6", 
															"job_status" : {"$in" : ["8","10"]} 
														})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				
				create_datetime_obj = datetime.strptime(request_driver_json['created_at'], '%Y-%m-%d %H:%M:%S')
				create_date = create_datetime_obj.strftime('%Y-%m-%d')
				create_time = create_datetime_obj.strftime('%H:%M')
				start_date = request_driver_json['start_date']
				start_time = datetime.strptime(request_driver_json['start_time'], '%H:%M:%S').strftime('%H:%M')

				payment_date = None
				if request_driver_json['payment_date'] is not None:
					payment_datetime_obj = datetime.strptime(request_driver_json['payment_date'], '%Y-%m-%d')
					payment_date = payment_datetime_obj.strftime('%Y-%m-%d')

				driver_info = get_member_info_by_id(request_driver_json['driver_id'])
				driver_code = driver_info['member_code']
				driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

				if request_driver_json['payment_status'] == "2":
					payment_status_text = "ตั้งค่าการจ่ายแล้ว"
				elif request_driver_json['payment_status'] == "1":
					payment_status_text = "จ่ายแล้ว"
				else:
					payment_status_text = "รอดำเนินการ"

				result = {
						"status" : True,
						"msg" : "Get payment driver detail success.",
						"request_id": request_driver_json['_id']['$oid'],
						"request_no": request_driver_json['request_no'],
						"create_date": create_date,
						"create_time": create_time,
						"start_date": start_date,
						"start_time": start_time,
						"driver_code": driver_code,
						"driver_name": driver_name,
						"normal_payment_amount": request_driver_json['normal_payment_amount'],
						"total_overtime_usage": int(request_driver_json['total_overtime_usage']),
						"overtime_payment_amount": request_driver_json['overtime_payment_amount'],
						"payment_amount": request_driver_json['payment_amount'],
						"payment_status": request_driver_json['payment_status'],
						"payment_status_text": payment_status_text,
						"payment_date": payment_date
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
	function_name = "get_payment_driver_detail"
	request_headers = request.headers
	params_get = {"request_id" : request_id}
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_payment_driver(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_payment_status = "payment_status" in params
	isset_payment_date = "payment_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_payment_status and isset_payment_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if params['payment_status'] == "2":
					# update data
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"payment_status": params['payment_status'],
											"payment_date": params['payment_date'],
											"payment_at": params['payment_date']+" "+" 00:00:00",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}
				elif params['payment_status'] == "1":
					# update data
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"payment_status": params['payment_status'],
											"payment_date": datetime.now().strftime('%Y-%m-%d'),
											"payment_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}
				else:
					# update data
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"payment_status": params['payment_status'],
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

				if db.request_driver.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit payment driver success."
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
	function_name = "edit_payment_driver"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def set_payment_date(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_payment_date = "payment_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_payment_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			for i in range(len(params['request_id'])):
				request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'][i])})
				
				if request_driver is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					# update data
					where_param = { "_id": ObjectId(params['request_id'][i]) }
					value_param = {
									"$set":
										{
											"payment_status": "2",
											"payment_date": params['payment_date'],
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.request_driver.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Set payment date success."
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
	function_name = "set_payment_date"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def billing_statement_list_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_billing_date = "start_billing_date" in params
	isset_end_billing_date = "end_billing_date" in params
	isset_billing_statement_status = "billing_statement_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_billing_date and isset_end_billing_date and isset_billing_statement_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				
				# billing_statement = db.billing_statement.find()

				# if billing_statement is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	billing_statement_object = dumps(billing_statement)
				# 	billing_statement_json = json.loads(billing_statement_object)

				# 	for i in range(len(billing_statement_json)):

				# 		# billing_statement_date_int = int(datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 
				# 		# billing_statement_month = int(datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%m'))

				# 		company = db.company.find_one({"_id": ObjectId(billing_statement_json[i]['company_id'])})
				# 		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 		company_object = dumps(company)
				# 		company_json = json.loads(company_object)
				# 		company_name = company_json['company_name']

				# 		# update data
				# 		where_param = { "_id": ObjectId(billing_statement_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"company_name": company_name
				# 							}
				# 					}

				# 		db.billing_statement.update(where_param , value_param)

						

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = {}

				#billing_statement_code , company_name , billing_statement_amount_text 
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "billing_statement_code": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "billing_statement_amount_text": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)


				if params['billing_statement_status'] != "":
					add_params = {"billing_statement_status" : params['billing_statement_status']}
					where_param.update(add_params)

				if params['start_billing_date'] != "" and params['end_billing_date'] != "":
					start_billing_date_int = int(datetime.strptime(params['start_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_billing_date_int = int(datetime.strptime(params['end_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"billing_statement_date_int" : {"$gte" : start_billing_date_int , "$lte" : end_billing_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					#billing_statement_code = billing_statement_code
					#billing_statement_month = billing_statement_month
					#billing_statement_date = created_at
					#company_name = company_name
					#billing_statement_amount = sum_paid
					#billing_statement_status = billing_statement_status

					if params['sort_name'] == "billing_statement_date":
						sort_name = "created_at"
					elif params['sort_name'] == "billing_statement_amount":
						sort_name = "sum_paid"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				billing_statement = db.billing_statement.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.billing_statement.find(where_param).count()

				if billing_statement is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_statement_object = dumps(billing_statement)
					billing_statement_json = json.loads(billing_statement_object)

					billing_statement_list = []

					for i in range(len(billing_statement_json)):
						if billing_statement_json[i]['billing_statement_month'] == 1:
							billing_statement_month_text = "มกราคม"
						elif billing_statement_json[i]['billing_statement_month'] == 2:
							billing_statement_month_text = "กุมภาพันธ์"
						elif billing_statement_json[i]['billing_statement_month'] == 3:
							billing_statement_month_text = "มีนาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 4:
							billing_statement_month_text = "เมษายน"
						elif billing_statement_json[i]['billing_statement_month'] == 5:
							billing_statement_month_text = "พฤษภาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 6:
							billing_statement_month_text = "มิถุนายน"
						elif billing_statement_json[i]['billing_statement_month'] == 7:
							billing_statement_month_text = "กรกฎาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 8:
							billing_statement_month_text = "สิงหาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 9:
							billing_statement_month_text = "กันยายน"
						elif billing_statement_json[i]['billing_statement_month'] == 10:
							billing_statement_month_text = "ตุลาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 11:
							billing_statement_month_text = "พฤศจิกายน"
						else:
							billing_statement_month_text = "ธันวาคม"

						billing_statement_date = datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						
						if billing_statement_json[i]['billing_statement_status'] == "2":
							billing_statement_status_show = "ยกเลิก"
						elif billing_statement_json[i]['billing_statement_status'] == "1":
							billing_statement_status_show = "ชำระแล้ว"
						#billing_statement_status = 0
						else:
							billing_statement_status_show = "รอดำเนินการ"

						billing_statement_list.append({
							"billing_statement_id" : billing_statement_json[i]['_id']['$oid'],
							"billing_statement_code": billing_statement_json[i]['billing_statement_code'],
							"billing_statement_month": billing_statement_month_text,
							"billing_statement_date": billing_statement_date,
							"company_name": billing_statement_json[i]['company_name'],
							"billing_statement_amount": float(billing_statement_json[i]['sum_paid']),
							"billing_statement_status": billing_statement_json[i]['billing_statement_status'],
							"billing_statement_status_show": billing_statement_status_show
						})

					result = {
								"status" : True,
								"msg" : "Get billing statement list success.",
								"data" : billing_statement_list,
								"total_data" : total_data
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
	function_name = "billing_statement_list_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_billing_form(request):
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

			billing_statement_status_list = [
												{"code": "0","name": "รอดำเนินการ"},
												{"code": "1","name": "ชำระแล้ว"},
												{"code": "2","name": "ยกเลิก"}
											]

			result = {
						"status" : True,
						"msg" : "Get billing form success.",
						"billing_statement_status" : billing_statement_status_list
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
	function_name = "get_billing_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_billing_statement_detail_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_billing_statement_id = "billing_statement_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_billing_statement_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
				
			billing_statement = db.billing_statement.find_one({"_id": ObjectId(params['billing_statement_id'])})

			if billing_statement is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_object = dumps(billing_statement)
				billing_statement_json = json.loads(billing_statement_object)

				company = db.company.find_one({"_id": ObjectId(billing_statement_json['company_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)

				if billing_statement_json['billing_statement_month'] == 1:
					billing_statement_month_text = "มกราคม"
				elif billing_statement_json['billing_statement_month'] == 2:
					billing_statement_month_text = "กุมภาพันธ์"
				elif billing_statement_json['billing_statement_month'] == 3:
					billing_statement_month_text = "มีนาคม"
				elif billing_statement_json['billing_statement_month'] == 4:
					billing_statement_month_text = "เมษายน"
				elif billing_statement_json['billing_statement_month'] == 5:
					billing_statement_month_text = "พฤษภาคม"
				elif billing_statement_json['billing_statement_month'] == 6:
					billing_statement_month_text = "มิถุนายน"
				elif billing_statement_json['billing_statement_month'] == 7:
					billing_statement_month_text = "กรกฎาคม"
				elif billing_statement_json['billing_statement_month'] == 8:
					billing_statement_month_text = "สิงหาคม"
				elif billing_statement_json['billing_statement_month'] == 9:
					billing_statement_month_text = "กันยายน"
				elif billing_statement_json['billing_statement_month'] == 10:
					billing_statement_month_text = "ตุลาคม"
				elif billing_statement_json['billing_statement_month'] == 11:
					billing_statement_month_text = "พฤศจิกายน"
				else:
					billing_statement_month_text = "ธันวาคม"

				billing_statement_date = datetime.strptime(billing_statement_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
				
				if billing_statement_json['billing_statement_status'] == "2":
					billing_statement_status_show = "ยกเลิก"
				elif billing_statement_json['billing_statement_status'] == "1":
					billing_statement_status_show = "ชำระแล้ว"
				#billing_statement_status = 0
				else:
					billing_statement_status_show = "รอดำเนินการ"

				billing_address = company_json['billing_address']

				if company_json['billing_province_th'] == "กรุงเทพมหานคร":
					billing_address = billing_address + ' แขวง'+company_json['billing_sub_district_th']
					billing_address = billing_address + ' เขต'+company_json['billing_district_th']
					billing_address = billing_address + ' '+company_json['billing_province_th']
					billing_address = billing_address + ' '+company_json['billing_postcode']
				else:
					billing_address = billing_address + ' ตำบล'+company_json['billing_sub_district_th']
					billing_address = billing_address + ' อำเภอ'+company_json['billing_district_th']
					billing_address = billing_address + ' '+company_json['billing_province_th']
					billing_address = billing_address + ' '+company_json['billing_postcode']


				billing_in = []
				

				for i in range(len(billing_statement_json['billing'])):
					billing_in.append(ObjectId(billing_statement_json['billing'][i]))

				billing = db.billing.find({"_id" : {"$in" : billing_in}})

				if billing is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_object = dumps(billing)
					billing_json = json.loads(billing_object)

					billing_list = []

					for i in range(len(billing_json)):
						request_driver = db.request_driver.find_one({"_id": ObjectId(billing_json[i]['request_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						request_driver_object = dumps(request_driver)
						request_driver_json = json.loads(request_driver_object)

						billing_date = datetime.strptime(billing_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						request_no = billing_json[i]['request_no']

						customer_info = get_member_info_by_id(request_driver_json['member_id'])
						member_fullname = customer_info['member_firstname_th']+' '+customer_info['member_lastname_th']

						package_info = get_package_info(request_driver_json['main_package_id'])
						package_name = package_info['package_name_th']

						if package_info['package_type'] == "hour":
							package_type_text = "รายชั่วโมง"
						else:
							package_type_text = "รายครั้ง"

						if billing_json[i]['service_period'] == "normal":
							billing_period = "จอง"
						else:
							billing_period = "ใช้เกินเวลาที่จอง"

						if request_driver is not None:
							if request_driver_json['request_status'] == "6" and (request_driver_json['job_status'] == "8" or request_driver_json['job_status'] == "10"):
								billing_list.append({
									"billing_id" : billing_json[i]['_id']['$oid'],
									"billing_date" : billing_date,
									"request_no": request_no,
									"member_fullname": member_fullname,
									"package_name": package_name,
									"package_type_text": package_type_text,
									"billing_period": billing_period,
									"normal_usage": billing_json[i]['normal_usage'],
									"overtime_usage": billing_json[i]['overtime_usage'],
									"billing_amount": billing_json[i]['sum_paid'],
									"status": ""
								})

				result = {
							"status" : True,
							"msg" : "Get billing statement detail success.",
							"billing_statement_id": billing_statement_json['_id']['$oid'],
							"billing_statement_code": billing_statement_json['billing_statement_code'],
							"billing_statement_month": billing_statement_month_text,
							"billing_statement_date": billing_statement_date,
							"billing_statement_amount": billing_statement_json['sum_paid'],
							"company_name": company_json['company_name'],
							"company_tax_id": company_json['company_tax_id'],
							"billing_date": company_json['billing_date'],
							"billing_receiver_fullname": company_json['billing_receiver_firstname']+' '+company_json['billing_receiver_lastname'],
							"billing_receiver_tel": company_json['billing_receiver_tel'],
							"billing_receiver_email": company_json['billing_receiver_email'],
							"billing_address": billing_address,
							"billing_statement_status": billing_statement_json['billing_statement_status'],
							"billing_list": billing_list
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
	function_name = "get_billing_statement_detail_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def change_billing_statement_status(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_billing_statement_id = "billing_statement_id" in params
	isset_billing_statement_status = "billing_statement_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_billing_statement_id and isset_billing_statement_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			billing_statement = db.billing_statement.find_one({
																"_id": ObjectId(params['billing_statement_id'])
															})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			billing_statement_object = dumps(billing_statement)
			billing_statement_json = json.loads(billing_statement_object)

			if params['billing_statement_status'] is None:
				billing_statement_status = billing_statement_json['billing_statement_status']
			elif params['billing_statement_status'] == "2":
				billing_statement_status = "2"
			elif params['billing_statement_status'] == "1":
				billing_statement_status = "1"
			else:
				billing_statement_status = "0"

			# update data
			where_param = { "_id": ObjectId(params['billing_statement_id']) }
			value_param = {
							"$set":
								{
									"billing_statement_status": billing_statement_status,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.billing_statement.update(where_param , value_param):
				for i in range(len(billing_statement_json['billing'])):  
					#update data to tb billing
					where_param = { "_id": ObjectId(billing_statement_json['billing'][i]) }
					value_param = {
									"$set":
										{
											"billing_status": "0",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}
					db.billing.update(where_param , value_param)

				result = {
							"status" : True,
							"msg" : "Change billing statement status success."
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
	function_name = "change_billing_statement_status"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def billing_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
	isset_start_billing_date = "start_billing_date" in params
	isset_end_billing_date = "end_billing_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_start_billing_date and isset_end_billing_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']
			
			company = db.company.find_one({"_id": ObjectId(params['company_id'])})

			if company is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				owner_admin_email = "admin@thitaram.com"

				where_param = { 
								"company_id" : company_json['_id']['$oid'],
								"billing_status" : "0"
							}

				if params['start_billing_date'] != "" and params['end_billing_date'] != "":
					start_billing_date_int = int(datetime.strptime(params['start_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_billing_date_int = int(datetime.strptime(params['end_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"billing_date_int" : {"$gte" : start_billing_date_int , "$lte" : end_billing_date_int}}
					where_param.update(add_params)

				billing_list = []

				billing = db.billing.find(where_param).sort([("request_no", 1),("created_at", 1)])

				if billing is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_object = dumps(billing)
					billing_json = json.loads(billing_object)

					for i in range(len(billing_json)):
						request_driver = db.request_driver.find_one({"_id": ObjectId(billing_json[i]['request_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						request_driver_object = dumps(request_driver)
						request_driver_json = json.loads(request_driver_object)

						billing_date = datetime.strptime(billing_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						request_no = billing_json[i]['request_no']

						customer_info = get_member_info_by_id(request_driver_json['member_id'])
						member_fullname = customer_info['member_firstname_th']+' '+customer_info['member_lastname_th']

						package_info = get_package_info(request_driver_json['main_package_id'])
						package_name = package_info['package_name_th']

						if package_info['package_type'] == "hour":
							package_type_text = "รายชั่วโมง"
						else:
							package_type_text = "รายครั้ง"

						if billing_json[i]['service_period'] == "normal":
							billing_period = "จอง"
						else:
							billing_period = "ใช้เกินเวลาที่จอง"

						if request_driver is not None:
							if request_driver_json['request_status'] == "6" and (request_driver_json['job_status'] == "8" or request_driver_json['job_status'] == "10"):
								billing_list.append({
									"billing_id" : billing_json[i]['_id']['$oid'],
									"billing_date" : billing_date,
									"request_no": request_no,
									"member_fullname": member_fullname,
									"package_name": package_name,
									"package_type_text": package_type_text,
									"billing_period": billing_period,
									"normal_usage": billing_json[i]['normal_usage'],
									"overtime_usage": billing_json[i]['overtime_usage'],
									"billing_amount": billing_json[i]['sum_paid'],
									"status": ""
								})

				billing_address = company_json['billing_address']

				if company_json['billing_province_th'] == "กรุงเทพมหานคร":
					billing_address = billing_address + ' แขวง'+company_json['billing_sub_district_th']
					billing_address = billing_address + ' เขต'+company_json['billing_district_th']
					billing_address = billing_address + ' '+company_json['billing_province_th']
					billing_address = billing_address + ' '+company_json['billing_postcode']
				else:
					billing_address = billing_address + ' ตำบล'+company_json['billing_sub_district_th']
					billing_address = billing_address + ' อำเภอ'+company_json['billing_district_th']
					billing_address = billing_address + ' '+company_json['billing_province_th']
					billing_address = billing_address + ' '+company_json['billing_postcode']


				billing_statement_detail = {
					"company_name": company_json['company_name'],
					"company_tax_id": company_json['company_tax_id'],
					"billing_date": company_json['billing_date'],
					"billing_receiver_fullname": company_json['billing_receiver_firstname']+' '+company_json['billing_receiver_lastname'],
					"billing_receiver_tel": company_json['billing_receiver_tel'],
					"billing_receiver_email": company_json['billing_receiver_email'],
					"billing_address": billing_address,
					"owner_admin_email": owner_admin_email,
					"billing_list": billing_list
				}

				result = {
							"status" : True,
							"msg" : "Get billing list success.",
							"data" : billing_statement_detail
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
	function_name = "billing_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_billing_statement(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
	isset_billing_id = "billing_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_billing_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			# order_package = db.order_package.find()

			# if order_package is None:
			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "Data not found."
			# 			}
			# else:
			# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			# 	order_package_object = dumps(order_package)
			# 	order_package_json = json.loads(order_package_object)

				

			# 	for i in range(len(order_package_json)):
			# 		order_detail_list = []

			# 		for j in range(len(order_package_json[i]['order_detail'])):
			# 			package_price = round(float(order_package_json[i]['order_detail'][j]['package_price']) , 2)
			# 			vat_rate = get_vat_rate()
			# 			package_price_vat = round(((package_price * vat_rate) / 100) , 2)
			# 			package_price_not_vat = round(package_price - package_price_vat , 2)

			# 			order_detail_list.append({
			# 				"package_id" : order_package_json[i]['order_detail'][j]['package_id'],
			# 				"package_code": order_package_json[i]['order_detail'][j]['package_code'],
			# 				"package_name_en": order_package_json[i]['order_detail'][j]['package_name_en'],
			# 				"package_name_th": order_package_json[i]['order_detail'][j]['package_name_th'],
			# 				"package_detail_en": order_package_json[i]['order_detail'][j]['package_detail_en'],
			# 				"package_detail_th": order_package_json[i]['order_detail'][j]['package_detail_th'],
			# 				"package_condition_en": order_package_json[i]['order_detail'][j]['package_condition_en'],
			# 				"package_condition_th": order_package_json[i]['order_detail'][j]['package_condition_th'],
			# 				"package_model": order_package_json[i]['order_detail'][j]['package_model'],
			# 				"package_type": order_package_json[i]['order_detail'][j]['package_type'],
			# 				"package_type_amount": order_package_json[i]['order_detail'][j]['package_type_amount'],
			# 				"total_usage_date": int(order_package_json[i]['order_detail'][j]['total_usage_date']),
			# 				"special_company": order_package_json[i]['order_detail'][j]['special_company'],
			# 				"service_time": order_package_json[i]['order_detail'][j]['service_time'],
			# 				"driver_level": order_package_json[i]['order_detail'][j]['driver_level'],
			# 				"communication": order_package_json[i]['order_detail'][j]['communication'],
			# 				"communication_en": order_package_json[i]['order_detail'][j]['communication_en'],
			# 				"communication_th": order_package_json[i]['order_detail'][j]['communication_th'],
			# 				"normal_paid_rate": float(order_package_json[i]['order_detail'][j]['normal_paid_rate']),
			# 				"normal_received_rate": float(order_package_json[i]['order_detail'][j]['normal_received_rate']),
			# 				"overtime_paid_rate": float(order_package_json[i]['order_detail'][j]['overtime_paid_rate']),
			# 				"overtime_received_rate": float(order_package_json[i]['order_detail'][j]['overtime_received_rate']),
			# 				"package_image": order_package_json[i]['order_detail'][j]['package_image'],
			# 				"package_amount": int(order_package_json[i]['order_detail'][j]['package_amount']),

			# 				"package_price": float(package_price),
			# 				"package_price_not_vat": float(package_price_not_vat),
			# 				"package_price_vat": float(package_price_vat),
			# 				"vat_rate": float(vat_rate)
			# 			})


			# 		# update data
			# 		where_param = { "_id": ObjectId(order_package_json[i]['_id']['$oid']) }
			# 		value_param = {
			# 						"$set":
			# 							{
			# 								"order_detail": order_detail_list
			# 							}
			# 					}

			# 		db.order_package.update(where_param , value_param)	

			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "OK"
			# 			}


			# order_package = db.order_package.find({"order_no" : "VRD0000112"})

			# if order_package is None:
			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "Data not found."
			# 			}
			# else:
			# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			# 	order_package_object = dumps(order_package)
			# 	order_package_json = json.loads(order_package_object)

			# 	order_detail_list = []

			# 	aaa = []
			# 	bbb = []

			# 	for i in range(len(order_package_json)):
			# 		order_price = 0
			# 		order_vat = 0
			# 		order_price_not_vat = 0

			# 		for j in range(len(order_package_json[i]['order_detail'])):
			# 			package_price = round(float(order_package_json[i]['order_detail'][j]['package_price']) , 2)
			# 			vat_rate = get_vat_rate()
			# 			package_price_vat = round(((package_price * vat_rate) / 100) , 2)
			# 			package_price_not_vat = round(package_price - package_price_vat , 2)

			# 			package_amount = int(order_package_json[i]['order_detail'][j]['package_amount'])

			# 			order_detail_list.append({
			# 				"package_id" : order_package_json[i]['order_detail'][j]['package_id'],
			# 				"package_code": order_package_json[i]['order_detail'][j]['package_code'],
			# 				"package_name_en": order_package_json[i]['order_detail'][j]['package_name_en'],
			# 				"package_name_th": order_package_json[i]['order_detail'][j]['package_name_th'],
			# 				"package_detail_en": order_package_json[i]['order_detail'][j]['package_detail_en'],
			# 				"package_detail_th": order_package_json[i]['order_detail'][j]['package_detail_th'],
			# 				"package_condition_en": order_package_json[i]['order_detail'][j]['package_condition_en'],
			# 				"package_condition_th": order_package_json[i]['order_detail'][j]['package_condition_th'],
			# 				"package_model": order_package_json[i]['order_detail'][j]['package_model'],
			# 				"package_type": order_package_json[i]['order_detail'][j]['package_type'],
			# 				"package_type_amount": order_package_json[i]['order_detail'][j]['package_type_amount'],
			# 				"total_usage_date": int(order_package_json[i]['order_detail'][j]['total_usage_date']),
			# 				"special_company": order_package_json[i]['order_detail'][j]['special_company'],
			# 				"service_time": order_package_json[i]['order_detail'][j]['service_time'],
			# 				"driver_level": order_package_json[i]['order_detail'][j]['driver_level'],
			# 				"communication": order_package_json[i]['order_detail'][j]['communication'],
			# 				"communication_en": order_package_json[i]['order_detail'][j]['communication_en'],
			# 				"communication_th": order_package_json[i]['order_detail'][j]['communication_th'],
			# 				"normal_paid_rate": float(order_package_json[i]['order_detail'][j]['normal_paid_rate']),
			# 				"normal_received_rate": float(order_package_json[i]['order_detail'][j]['normal_received_rate']),
			# 				"overtime_paid_rate": float(order_package_json[i]['order_detail'][j]['overtime_paid_rate']),
			# 				"overtime_received_rate": float(order_package_json[i]['order_detail'][j]['overtime_received_rate']),
			# 				"package_image": order_package_json[i]['order_detail'][j]['package_image'],
			# 				"package_amount": package_amount,

			# 				"package_price": package_price,
			# 				"package_price_not_vat": package_price_not_vat,
			# 				"package_price_vat": package_price_vat,
			# 				"vat_rate": vat_rate
			# 			})

			# 			order_price = order_price + (package_price * package_amount)
			# 			order_vat = order_vat + (((package_price * package_amount) * vat_rate) / 100)
			# 			order_price_not_vat = order_price_not_vat + ((package_price * package_amount) - (package_price_vat * package_amount))


			# 		aaa.append({
			# 			"order_price": order_price,
			# 			"order_price_not_vat": order_price_not_vat,
			# 			"order_vat": order_vat
			# 		})


			# 		# update data
			# 		where_param = { "_id": ObjectId(order_package_json[i]['_id']['$oid']) }
			# 		value_param = {
			# 						"$set":
			# 							{
			# 								"order_price": order_price,
			# 								"order_price_not_vat": order_price_not_vat,
			# 								"order_vat": order_vat
			# 							}
			# 					}

			# 		db.order_package.update(where_param , value_param)		

			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "OK",
			# 				"order_detail_list" : order_detail_list,
			# 				"aaa" : aaa
			# 			}









			# package = db.package.find()

			# if package is None:
			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "Data not found."
			# 			}
			# else:
			# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			# 	package_object = dumps(package)
			# 	package_json = json.loads(package_object)

			# 	for i in range(len(package_json)):
			# 		package_price = round(float(package_json[i]['package_price']) , 2)
			# 		vat_rate = get_vat_rate()
			# 		package_price_vat = round(((package_price * vat_rate) / 100) , 2)
			# 		package_price_not_vat = round(package_price - package_price_vat , 2)

			# 		# update data
			# 		where_param = { "_id": ObjectId(package_json[i]['_id']['$oid']) }
			# 		value_param = {
			# 						"$set":
			# 							{
			# 								"package_price_not_vat": package_price_not_vat,
			# 								"package_price_vat": package_price_vat,
			# 								"vat_rate": vat_rate
			# 							}
			# 					}

			# 		db.package.update(where_param , value_param)		

			# 	result = { 
			# 				"status" : False,
			# 				"msg" : "OK"
			# 			}




			billing_in = []
			for i in range(len(params['billing_id'])):
				billing_in.append(ObjectId(params['billing_id'][i]))

			billing = db.billing.find({"_id" : {"$in" : billing_in}})

			if billing is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_object = dumps(billing)
				billing_json = json.loads(billing_object)

				company = db.company.find_one({"_id": ObjectId(params['company_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				company_name = company_json['company_name']
				billing_receiver_fullname = company_json['billing_receiver_firstname']+" "+company_json['billing_receiver_lastname']
				billing_receiver_tel = company_json['billing_receiver_tel']
				billing_receiver_email = company_json['billing_receiver_email']

				#แปลง format วันที่
				created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

				billing_statement_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 
				billing_statement_month = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%m'))

				sum_paid = 0

				for i in range(len(billing_json)):
					sum_paid = sum_paid + billing_json[i]['sum_paid']

					#update data to tb billing
					where_param = { "_id": ObjectId(billing_json[i]['_id']['$oid']) }
					value_param = {
									"$set":
										{
											"billing_status": "1",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					db.billing.update(where_param , value_param)

				#ดึง billing_statement_code ล่าสุดจาก tb billing_statement แล้วเอามา +1
				billing_statement = db.billing_statement.find_one(sort=[("billing_statement_code", -1)])
				bid = 1

				if billing_statement is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_statement_object = dumps(billing_statement)
					billing_statement_json = json.loads(billing_statement_object)

					bid = int(billing_statement_json["billing_statement_code"][1:8])+1

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				billing_statement_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				billing_statement_id_string = str(billing_statement_id)

				billing_statement_code = "B"+"%07d" % bid
				
				data = { 
							"_id": billing_statement_id,
							"billing_statement_code": billing_statement_code,
							"company_id": params['company_id'],
							"company_name": company_name,
							"billing_receiver_fullname": billing_receiver_fullname,
							"billing_receiver_email": billing_receiver_email,
							"billing_receiver_tel": billing_receiver_tel,
							"billing": params['billing_id'],
							"sum_paid": sum_paid,
							"billing_statement_status": "0",
							"billing_statement_date_int": billing_statement_date_int,
							"billing_statement_month": billing_statement_month,
							"created_at": created_at,
							"updated_at": created_at
						}		    

				if db.billing_statement.insert_one(data):
					#ส่ง noti หา master admin ของ company นั้นๆ
					master_admin = db.member.find({
													"company_id": params['company_id'],
													"company_user_type": "2"
												})

					if master_admin is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						master_admin_object = dumps(master_admin)
						master_admin_json = json.loads(master_admin_object)
						
						noti_type = "add_billing_statement"
						billing_amount = '{:,.2f}'.format(round(float(sum_paid) , 2))

						send_email_list = []

						for i in range(len(master_admin_json)):
							#sent noti to member
							customer_info = get_member_info_by_id(master_admin_json[i]['_id']['$oid'])
							member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']

							noti_title_en = "Company "+company_name+" has a billing number "+billing_statement_code
							noti_title_th = "บริษัท "+company_name+" มีการวางบิลเลขที่ "+billing_statement_code
							noti_message_en = "for "+billing_amount+" baht."
							noti_message_th = "จำนวน "+billing_amount+" บาท"

							if customer_info['member_lang'] == "en":
								noti_title = noti_title_en
								noti_message = noti_message_en
								show_noti = noti_title_en+" "+noti_message_en
							else:
								noti_title = noti_title_th
								noti_message = noti_message_th
								show_noti = noti_title_th+" "+noti_message_th

							#แปลง format วันที่
							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							#ส่ง noti
							send_noti_key = customer_info['noti_key']
							send_noti_title = noti_title
							send_noti_message = noti_message
							send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": params['company_id'] , "created_datetime" : created_datetime }
							send_noti_badge = 1

							#insert member_notification
							noti_detail = {
												"company_id": params['company_id'],
												"billing_statement_id": billing_statement_id_string,
												"billing_statement_code": billing_statement_code
											}

							data = { 
										"member_id": customer_info['_id']['$oid'],
										"member_fullname": member_fullname,
										"noti_type": noti_type,
										"noti_message_en": noti_title_en+" "+noti_message_en,
										"noti_message_th": noti_title_th+" "+noti_message_th,
										"noti_detail": noti_detail,

										"send_noti_key": send_noti_key,
										"send_noti_title": send_noti_title,
										"send_noti_message": send_noti_message,
										"send_noti_data": send_noti_data,
										"send_noti_badge": send_noti_badge,

										"send_status": "0",
										"created_at": created_at,
										"updated_at": created_at
									}
							db.queue_notification.insert_one(data)					

							#send email
							email_type = "add_billing_statement"
							subject = "VR Driver : ออกใบวางบิลสำเร็จ"
							to_email = master_admin_json[i]['member_email'].lower()
							template_html = "add_billing_statement.html"
							data_detail = { "company_name" : company_name, "billing_statement_code" : billing_statement_code, "billing_amount" : billing_amount }	

							#put email ใส่ array 
							send_email_list.append(master_admin_json[i]['member_email'])

							data_email = { 
											"email_type": email_type,
											"data": data_detail,
											"subject": subject,
											"to_email": to_email,
											"template_html": template_html,
											"send_status": "0",
											"created_at": created_at,
											"updated_at": created_at
										}
							db.queue_email.insert_one(data_email)

						#ถ้า อีเมลของ master admin เป็นคนละค่ากับ billing_receiver_email จะส่งอีเมลหา billing_receiver_email ด้วย
						if billing_receiver_email not in send_email_list:
							#send email
							email_type = "add_billing_statement"
							subject = "VR Driver : ออกใบวางบิลสำเร็จ"
							to_email = billing_receiver_email.lower()
							template_html = "add_billing_statement.html"
							data_detail = { "company_name" : company_name, "billing_statement_code" : billing_statement_code, "billing_amount" : billing_amount }

							data_email = { 
											"email_type": email_type,
											"data": data_detail,
											"subject": subject,
											"to_email": to_email,
											"template_html": template_html,
											"send_status": "0",
											"created_at": created_at,
											"updated_at": created_at
										}
							db.queue_email.insert_one(data_email)

					result = {
								"status" : True,
								"msg" : "Add billing statement success.",
								"billing_statement_code" : billing_statement_code,
								"billing_receiver_email" : billing_receiver_email,
								"company_name" : company_name
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
	function_name = "add_billing_statement"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_inspection_detail_backend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Request not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				car_id = request_driver_json['car_id']

				car = db.car.find_one({"_id": ObjectId(car_id)})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				car_type = db.car_type.find_one({"_id": ObjectId(car_json['car_type_id'])})
				car_brand = db.car_brand.find_one({"_id": ObjectId(car_json['car_brand_id'])})
				car_gear = db.car_gear.find_one({"_id": ObjectId(car_json['car_gear_id'])})
				car_engine = db.car_engine.find_one({"_id": ObjectId(car_json['car_engine_id'])})
				
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				car_brand_object = dumps(car_brand)
				car_brand_json = json.loads(car_brand_object)

				car_gear_object = dumps(car_gear)
				car_gear_json = json.loads(car_gear_object)

				car_engine_object = dumps(car_engine)
				car_engine_json = json.loads(car_engine_object)

				license_plate = car_json['license_plate']
				car_type_code = car_type_json['car_type_code']
				car_brand_name = car_brand_json['brand_name']

				car_type_name = car_type_json['car_type_name_th']
				car_gear_name = car_gear_json['car_gear_th']
				car_engine_name = car_engine_json['car_engine_th']
				car_image = None

				if car_json['car_image'] is not None:
					car_image = car_json['car_image']

				if car_json['car_group'] == "company":
					car_group_name = "รถบริษัท"
				else:
					car_group_name = "รถส่วนตัว"

				outside_inspection_list = []
				inspection_before_use_list = []
				inspection_before_use_comment = None
				inspection_before_use_image = []
				start_mileage = None
				end_mileage = None
				check_status = None

				if request_driver_json['check_status'] is not None and request_driver_json['check_status'] != "0" and request_driver_json['check_status'] != "1":
					# outside_inspection = db.outside_inspection.find({"car_type_code": car_type_code})
					# inspection_before_use = db.inspection_before_use.find({"check_status": "1"})

					car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_inspection_object = dumps(car_inspection)
					car_inspection_json = json.loads(car_inspection_object)

					outside_inspection_json = car_inspection_json['outside_inspection']
					inspection_before_use_json = car_inspection_json['inspection_before_use']

					for i in range(len(outside_inspection_json)):
						point_name = outside_inspection_json[i]['point_name_th']

						part_list = []
						check_error = "0"

						for j in range(len(outside_inspection_json[i]['part'])):
							part_name = outside_inspection_json[i]['part'][j]['part_name_th']

							#ดึงเฉพาะข้อมูลที่ผิดปกติไปแสดงผล
							if outside_inspection_json[i]['part'][j]['check_result'] == "0":
								part_list.append({
									"part_code": outside_inspection_json[i]['part'][j]['part_code'],
									"part_name": part_name,
									"check_result": outside_inspection_json[i]['part'][j]['check_result'],
									"check_remark": outside_inspection_json[i]['part'][j]['check_remark'],
									"check_image": outside_inspection_json[i]['part'][j]['check_image'],
								})

								check_error = "1"

						if check_error == "1":
							outside_inspection_list.append({
								"outside_inspection_id" : outside_inspection_json[i]['outside_inspection_id'],
								"car_type_id": car_json['car_type_id'],
								"car_type_code": car_type_code,
								"point_name": point_name,
								"part": part_list,
								"point_number": outside_inspection_json[i]['point_number']
							})

					for i in range(len(inspection_before_use_json)):
						check_name = inspection_before_use_json[i]['check_name_th']
					
						inspection_before_use_list.append({
							"inspection_before_use_id" : inspection_before_use_json[i]['inspection_before_use_id'],
							"check_name": check_name,
							"check_result": inspection_before_use_json[i]['check_result'],
							"check_remark": inspection_before_use_json[i]['check_remark']
						})

					start_mileage = car_inspection_json['start_mileage']
					end_mileage = car_inspection_json['end_mileage']
					inspection_before_use_comment = car_inspection_json['inspection_before_use_comment']
					inspection_before_use_image = car_inspection_json['inspection_before_use_image']
					check_status = car_inspection_json['check_status']

				result = {
							"status" : True,
							"msg": "Get car inspection form detail.", 
							"request_id": params['request_id'],
							"car_id": car_id,
							"car_brand_name": car_brand_name,
							"license_plate": license_plate,
							"car_type_code": car_type_code,
							"car_type_name": car_type_name,
							"car_gear_name": car_gear_name,
							"car_engine_name": car_engine_name,
							"car_group_name": car_group_name,
							"car_image": car_image,
							"start_mileage": start_mileage,
							"end_mileage": end_mileage,
							"outside_inspection": outside_inspection_list,
							"inspection_before_use": inspection_before_use_list,
							"inspection_before_use_comment": inspection_before_use_comment,
							"inspection_before_use_image": inspection_before_use_image,
							"check_status": check_status
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
	function_name = "get_car_inspection_detail_backend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_driver_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_driver_id = "driver_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_driver_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			driver_info = get_member_info_by_id(params['driver_id'])

			last_location_date = datetime.strptime(driver_info['last_location_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
			last_location_time = datetime.strptime(driver_info['last_location_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')

			result = {
						"status" : True,
						"msg": "Get driver location success.",
						"member_code": driver_info['member_code'],
						"member_fullname": driver_info['member_firstname_th']+" "+driver_info['member_lastname_th'],
						"member_email": driver_info['member_email'],
						"member_tel": driver_info['member_tel'],
						"profile_image": driver_info['profile_image'],
						"last_latitude": driver_info['last_latitude'],
						"last_longitude": driver_info['last_longitude'],
						"last_location_date": last_location_date,
						"last_location_time": last_location_time
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
	function_name = "get_driver_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_package_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_package_type = "package_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_data_start_at and isset_data_length and isset_search_text and isset_package_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { "company_id" : params['company_id'] }

				#order_no , package_code , package_name_en , package_name_th
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "order_no": {"$regex": params['search_text']} },
												{ "package_code": {"$regex": params['search_text']} },
												{ "package_name_en": {"$regex": params['search_text']} },
												{ "package_name_th": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)

				if params['package_type'] == "hour" or params['package_type'] == "time":
					add_params = {"package_type" : params['package_type']}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# order_no = order_no
					# package_code = package_code
					# package_type = package_type
					# package_name = package_name_th
					# package_price = package_price
					# end_date = end_date
					# remaining_amount = remaining_amount

					if params['sort_name'] == "package_name":
						sort_name = "package_name_th"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1


				company_package_list = []

				company_package = db.company_package.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.company_package.find(where_param).count()

				if company_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_package_object = dumps(company_package)
					company_package_json = json.loads(company_package_object)

					for i in range(len(company_package_json)):
						if company_package_json[i]['package_type'] == "hour":
							package_type_text = "รายชั่วโมง"
						else:
							package_type_text = "รายครั้ง"

						end_date = datetime.strptime(company_package_json[i]['end_date'], '%Y-%m-%d')
						today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
						
						delta = end_date - today
						remaining_date_amount = delta.days

						if company_package_json[i]['package_type'] == "weekday":
							service_time = "Weekday"
						elif company_package_json[i]['package_type'] == "weekend":
							service_time = "Weekend"
						else:
							service_time = "All day"

						driver_level = db.driver_level.find_one({"_id": ObjectId(company_package_json[i]['driver_level'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						driver_level_object = dumps(driver_level)
						driver_level_json = json.loads(driver_level_object)
						level_name = driver_level_json['level_name_th']

						company_package_list.append({
							"order_no": company_package_json[i]['order_no'],
							"company_package_id": company_package_json[i]['_id']['$oid'],
							"company_id": company_package_json[i]['company_id'],
							"package_id": company_package_json[i]['package_id'],
							"package_code": company_package_json[i]['package_code'],
							"package_model": company_package_json[i]['package_model'],
							"package_type": company_package_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_name": company_package_json[i]['package_name_th'],
							"package_price": company_package_json[i]['package_price'],
							"package_price_not_vat": company_package_json[i]['package_price_not_vat'],
							"package_price_vat": company_package_json[i]['package_price_vat'],
							"vat_rate": company_package_json[i]['vat_rate'],
							"end_date": company_package_json[i]['end_date'],
							"package_type_amount": company_package_json[i]['package_type_amount'],
							"remaining_date_amount": remaining_date_amount,
							"remaining_amount": company_package_json[i]['remaining_amount'],
							"usage_amount": company_package_json[i]['usage_amount'],
							"total_amount": company_package_json[i]['total_amount'],
							"service_time": service_time,
							"level_name": level_name,
							"communication": company_package_json[i]['communication_th'],
							"package_detail": company_package_json[i]['package_detail_th'],
							"package_condition": company_package_json[i]['package_condition_th']
						})

				result = {
							"status" : True,
							"msg" : "Get company package list success.",
							"total_data" : total_data,
							"data" : company_package_list
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
	function_name = "company_package_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_package_form(request):
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

			package_type_list = [
									{"code": "hour","name": "รายชั่วโมง"},
									{"code": "time","name": "รายครั้ง"}
								]

			result = {
						"status" : True,
						"msg" : "Get company package form success.",
						"package_type" : package_type_list
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
	function_name = "get_company_package_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_package_detail(company_package_id,request):
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

			company_package = db.company_package.find_one({"_id": ObjectId(company_package_id)})
			
			if company_package is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)

				if company_package_json['package_type'] == "hour":
					package_type_text = "รายชั่วโมง"
				else:
					package_type_text = "รายครั้ง"

				end_date = datetime.strptime(company_package_json['end_date'], '%Y-%m-%d')
				today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
				
				delta = end_date - today
				remaining_date_amount = delta.days

				if company_package_json['package_type'] == "weekday":
					service_time = "Weekday"
				elif company_package_json['package_type'] == "weekend":
					service_time = "Weekend"
				else:
					service_time = "All day"

				driver_level = db.driver_level.find_one({"_id": ObjectId(company_package_json['driver_level'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)
				level_name = driver_level_json['level_name_th']

				result = {
							"status" : True,
							"msg" : "Get company package detail success.",
							"order_no": company_package_json['order_no'],
							"company_package_id": company_package_json['_id']['$oid'],
							"company_id": company_package_json['company_id'],
							"package_id": company_package_json['package_id'],
							"package_code": company_package_json['package_code'],
							"package_model": company_package_json['package_model'],
							"package_type": company_package_json['package_type'],
							"package_type_text": package_type_text,
							"package_name": company_package_json['package_name_th'],
							"package_price": company_package_json['package_price'],
							"package_price_not_vat": company_package_json['package_price_not_vat'],
							"package_price_vat": company_package_json['package_price_vat'],
							"vat_rate": company_package_json['vat_rate'],
							"end_date": company_package_json['end_date'],
							"package_type_amount": company_package_json['package_type_amount'],
							"remaining_date_amount": remaining_date_amount,
							"remaining_amount": company_package_json['remaining_amount'],
							"usage_amount": company_package_json['usage_amount'],
							"total_amount": company_package_json['total_amount'],
							"service_time": service_time,
							"level_name": level_name,
							"communication": company_package_json['communication_th'],
							"package_detail": company_package_json['package_detail_th'],
							"package_condition": company_package_json['package_condition_th']
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
	function_name = "get_company_package_detail"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_company_package(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params
	isset_remaining_date_amount = "remaining_date_amount" in params
	isset_remaining_amount = "remaining_amount" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id and isset_remaining_date_amount and isset_remaining_amount:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})
			
			if company_package is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)

				end_date = datetime.strptime(company_package_json['end_date'], '%Y-%m-%d')
				today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
				
				delta = end_date - today
				remaining_date_amount = delta.days

				end_date_obj = datetime.strptime(company_package_json['end_date'], '%Y-%m-%d')

				#ค่าเก่า น้อยกว่าหรือเท่ากับ ค่าใหม่ 27 <= 30
				if remaining_date_amount <= params['remaining_date_amount']:
					#3 = 30 - 27
					add_remaining_amount = params['remaining_date_amount'] - remaining_date_amount
					new_end_date_obj = end_date_obj + timedelta(days=add_remaining_amount)
				#ค่าเก่า มากกว่า ค่าใหม่ 27 > 20
				else:
					#7 = 27 - 20
					add_remaining_amount = remaining_date_amount - params['remaining_date_amount']
					new_end_date_obj = end_date_obj - timedelta(days=add_remaining_amount)
					
				end_date = new_end_date_obj.strftime('%Y-%m-%d')
				total_amount = company_package_json['usage_amount'] + int(params['remaining_amount'])
				
				end_date_int = int(datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d'))

				# update data
				where_param = { "_id": ObjectId(params['company_package_id']) }
				value_param = {
								"$set":
									{
										"total_amount": int(total_amount),
										"remaining_amount": int(params['remaining_amount']),
										"end_date": end_date,
										"end_date_int": end_date_int,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.company_package.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit company package success."
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
	function_name = "edit_company_package"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_request_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_request_date = "request_date" in params
	isset_start_date = "start_date" in params
	isset_request_status = "request_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_data_start_at and isset_data_length and isset_search_text and isset_request_date and isset_start_date and isset_request_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:

				# request_driver = db.request_driver.find()

				# if request_driver is None:
				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "Data not found."
				# 			}
				# else:
				# 	#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 	request_driver_object = dumps(request_driver)
				# 	request_driver_json = json.loads(request_driver_object)

				# 	for i in range(len(request_driver_json)):
						
				# 		if request_driver_json[i]['company_id'] is None:
				# 			company_name = None
				# 		else:
				# 			company = db.company.find_one({"_id": ObjectId(request_driver_json[i]['company_id'])})
				# 			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				# 			company_object = dumps(company)
				# 			company_json = json.loads(company_object)
				# 			company_name = company_json['company_name']

				# 		member_info = get_member_info_by_id(request_driver_json[i]['member_id'])
				# 		member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']

				# 		passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])
				# 		passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']

				# 		if request_driver_json[i]['driver_id'] is None:
				# 			driver_name = None
				# 		else:
				# 			driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				# 			driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

				# 		start_date_int = int(datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				# 		create_date_int = int(datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				# 		# update data
				# 		where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				# 		value_param = {
				# 						"$set":
				# 							{
				# 								"company_name": company_name,
				# 								"member_name": member_name,
				# 								"passenger_name": passenger_name,
				# 								"driver_name": driver_name,
				# 								"start_date_int": start_date_int,
				# 								"create_date_int": create_date_int
				# 							}
				# 					}

				# 		db.request_driver.update(where_param , value_param)

				# 	result = { 
				# 				"status" : False,
				# 				"msg" : "OK"
				# 			}

				where_param = { "company_id" : params['company_id'] }

				#request_no , company_name , member_name , passenger_name , driver_name
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "request_no": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "member_name": {"$regex": params['search_text']} },
												{ "passenger_name": {"$regex": params['search_text']} },
												{ "driver_name": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)


				if params['request_status'] != "":
					add_params = {"request_status" : params['request_status']}
					where_param.update(add_params)

				if params['request_date'] != "":
					create_date_int = int(datetime.strptime(params['request_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"create_date_int" : create_date_int}
					where_param.update(add_params)

				if params['start_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 

					add_params = {"start_date_int" : start_date_int}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "created_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# request_no = request_no
					# create_date = created_at
					# start_date = start_date
					# company_name = company_name
					# member_name = member_name
					# passenger_name = passenger_name
					# driver_name = driver_name
					# request_status = request_status

					if params['sort_name'] == "create_date":
						sort_name = "created_at"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

				request_driver = db.request_driver.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.request_driver.find(where_param).count()

				if request_driver is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					request_driver_list = []

					for i in range(len(request_driver_json)):
						if request_driver_json[i]['request_status'] == "6":
							request_status_text = "สำเร็จ"
						elif request_driver_json[i]['request_status'] == "5":
							request_status_text = "กำลังเดินทาง"
						elif request_driver_json[i]['request_status'] == "4":
							request_status_text = "งานที่ใกล้จะถึง"
						elif request_driver_json[i]['request_status'] == "3":
							request_status_text = "ยกเลิกโดยคนขับ"
						elif request_driver_json[i]['request_status'] == "2":
							request_status_text = "ยกเลิกโดยลูกค้า"
						elif request_driver_json[i]['request_status'] == "1":
							request_status_text = "ตอบรับแล้ว"
						else:
							request_status_text = "รอตอบรับ"

						create_date = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						start_date = request_driver_json[i]['start_date']
						create_time = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
						start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')

						if request_driver_json[i]['company_id'] is not None:
							company = db.company.find_one({"_id": ObjectId(request_driver_json[i]['company_id'])})

							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_object = dumps(company)
							company_json = json.loads(company_object)
							company_name = company_json['company_name']
						else:
							company_name = None

						member_info = get_member_info_by_id(request_driver_json[i]['member_id'])
						passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])

						member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']

						if request_driver_json[i]['driver_id'] is not None:
							driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
							driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
						else:
							driver_name = None

						request_driver_list.append({
							"request_id" : request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"create_date": create_date,
							"create_time": create_time,
							"start_date": start_date,
							"start_time": start_time,
							"company_name": company_name,
							"member_name": member_name,
							"passenger_name": passenger_name,
							"driver_name": driver_name,
							"request_status": request_driver_json[i]['request_status'],
							"request_status_text": request_status_text
						})

				result = {
							"status" : True,
							"msg" : "Get request list success.",
							"data" : request_driver_list,
							"total_data" : total_data
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
	function_name = "company_request_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_billing_statement_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_billing_date = "start_billing_date" in params
	isset_end_billing_date = "end_billing_date" in params
	isset_billing_statement_status = "billing_statement_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_data_start_at and isset_data_length and isset_search_text and isset_start_billing_date and isset_end_billing_date and isset_billing_statement_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { "company_id" : params['company_id'] }

				#billing_statement_code , company_name , billing_statement_amount_text 
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "billing_statement_code": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "billing_statement_amount_text": {"$regex": params['search_text']} }
											]

								}
					where_param.update(add_params)


				if params['billing_statement_status'] != "":
					add_params = {"billing_statement_status" : params['billing_statement_status']}
					where_param.update(add_params)

				if params['start_billing_date'] != "" and params['end_billing_date'] != "":
					start_billing_date_int = int(datetime.strptime(params['start_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_billing_date_int = int(datetime.strptime(params['end_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"billing_statement_date_int" : {"$gte" : start_billing_date_int , "$lte" : end_billing_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "updated_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					#billing_statement_code = billing_statement_code
					#billing_statement_month = billing_statement_month
					#billing_statement_date = created_at
					#company_name = company_name
					#billing_statement_amount = sum_paid
					#billing_statement_status = billing_statement_status

					if params['sort_name'] == "billing_statement_date":
						sort_name = "created_at"
					elif params['sort_name'] == "billing_statement_amount":
						sort_name = "sum_paid"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				billing_statement = db.billing_statement.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.billing_statement.find(where_param).count()

				if billing_statement is None:
					result = { 
							"status" : False,
							"msg" : "Data not found."
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_statement_object = dumps(billing_statement)
					billing_statement_json = json.loads(billing_statement_object)

					billing_statement_list = []

					for i in range(len(billing_statement_json)):
						if billing_statement_json[i]['billing_statement_month'] == 1:
							billing_statement_month_text = "มกราคม"
						elif billing_statement_json[i]['billing_statement_month'] == 2:
							billing_statement_month_text = "กุมภาพันธ์"
						elif billing_statement_json[i]['billing_statement_month'] == 3:
							billing_statement_month_text = "มีนาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 4:
							billing_statement_month_text = "เมษายน"
						elif billing_statement_json[i]['billing_statement_month'] == 5:
							billing_statement_month_text = "พฤษภาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 6:
							billing_statement_month_text = "มิถุนายน"
						elif billing_statement_json[i]['billing_statement_month'] == 7:
							billing_statement_month_text = "กรกฎาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 8:
							billing_statement_month_text = "สิงหาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 9:
							billing_statement_month_text = "กันยายน"
						elif billing_statement_json[i]['billing_statement_month'] == 10:
							billing_statement_month_text = "ตุลาคม"
						elif billing_statement_json[i]['billing_statement_month'] == 11:
							billing_statement_month_text = "พฤศจิกายน"
						else:
							billing_statement_month_text = "ธันวาคม"

						billing_statement_date = datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						
						if billing_statement_json[i]['billing_statement_status'] == "2":
							billing_statement_status_show = "ยกเลิก"
						elif billing_statement_json[i]['billing_statement_status'] == "1":
							billing_statement_status_show = "ชำระแล้ว"
						#billing_statement_status = 0
						else:
							billing_statement_status_show = "รอดำเนินการ"

						billing_statement_list.append({
							"billing_statement_id" : billing_statement_json[i]['_id']['$oid'],
							"billing_statement_code": billing_statement_json[i]['billing_statement_code'],
							"billing_statement_month": billing_statement_month_text,
							"billing_statement_date": billing_statement_date,
							"company_name": billing_statement_json[i]['company_name'],
							"billing_statement_amount": float(billing_statement_json[i]['sum_paid']),
							"billing_statement_status": billing_statement_json[i]['billing_statement_status'],
							"billing_statement_status_show": billing_statement_status_show
						})

					result = {
								"status" : True,
								"msg" : "Get billing statement list success.",
								"data" : billing_statement_list,
								"total_data" : total_data,

								# "where_param" : where_param
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
	function_name = "company_billing_statement_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def app_version_list(request):
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

			app_version = db.app_version.find().sort([("created_at", -1)])

			if app_version is None:
				result = { 
						"status" : False,
						"msg" : "Data not found."
					}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				app_version_object = dumps(app_version)
				app_version_json = json.loads(app_version_object)

				app_version_list = []

				for i in range(len(app_version_json)):
					if app_version_json[i]['app_code'] == "driver":
						app_name = "VR Driver (Driver)"
					else:
						app_name = "VR Driver (Customer)"

					if app_version_json[i]['os_type'] == "ios":
						os_type_text = "iOS"
					else:
						os_type_text = "Android"

					if app_version_json[i]['version_status'] == "1":
						version_status_text = "เปิดใช้งาน"
					else:
						version_status_text = "ปิดใช้งาน"

					app_version_list.append({
						"id": app_version_json[i]['_id']['$oid'],
						"app_code": app_version_json[i]['app_code'],
						"app_name": app_name,
						"app_version": app_version_json[i]['app_version'],
						"os_type": app_version_json[i]['os_type'],
						"os_type_text": os_type_text,
						"version_status": app_version_json[i]['version_status'],
						"version_status_text": version_status_text
					})

			result = {
						"status" : True,
						"msg" : "Get app version list success.",
						"data" : app_version_list
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
	function_name = "app_version_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_app_version_form(request):
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
			app_list = [
							{"code": "all","name": "ทั้งหมด"},
							{"code": "customer","name": "VR Driver (Customer)"},
							{"code": "driver","name": "VR Driver (Driver)"}
						]

			os_list = [
							{"code": "all","name": "ทั้งหมด"},
							{"code": "android","name": "Android"},
							{"code": "ios","name": "iOS"}
						]

			status_list = [
								{"code": "all","name": "ทั้งหมด"},
								{"code": "0","name": "ปิดใช้งาน"},
								{"code": "1","name": "เปิดใช้งาน"}
							]	

			result = {
						"status" : True,
						"msg" : "Get app version form success.",
						"app" : app_list,
						"os" : os_list,
						"status" : status_list
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
	function_name = "get_app_version_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_app_version(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_app_code = "app_code" in params
	isset_os_type = "os_type" in params
	isset_version_status = "version_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_app_code and isset_os_type and isset_version_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_app_version = db.app_version.find({
															"app_version": params['app_version'],
															"app_code": params['app_code'],
															"os_type": params['os_type']
														}).count()
				
			if check_app_version > 0:
				result = { 
							"status" : False,
							"msg" : "App version has been used."
						}
			else:
				data = { 
							"app_code": params['app_code'],
							"app_version": params['app_version'],
							"os_type": params['os_type'],
							"version_status": params['version_status'],
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if db.app_version.insert_one(data):
					result = {
								"status" : True,
								"msg" : "Add app version success."
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
	function_name = "add_app_version"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_app_version(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_id = "id" in params
	isset_app_version = "app_version" in params
	isset_app_code = "app_code" in params
	isset_os_type = "os_type" in params
	isset_version_status = "version_status" in params

	if isset_accept and isset_content_type and isset_token and isset_id and isset_app_version and isset_app_code and isset_os_type and isset_version_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			check_app_version = db.app_version.find({
															"_id": {"$ne": ObjectId(params['id'])},
															"app_version": params['app_version'],
															"app_code": params['app_code'],
															"os_type": params['os_type']
														}).count()
				
			if check_app_version > 0:
				result = { 
							"status" : False,
							"msg" : "App version has been used."
						}
			else:
				where_param = { "_id": ObjectId(params['id']) }
				value_param = {
								"$set": {
											"app_code": params['app_code'],
											"app_version": params['app_version'],
											"os_type": params['os_type'],
											"version_status": params['version_status'],
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

				if db.app_version.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Edit app version success."
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
	function_name = "edit_app_version"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def admin_noti_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_noti_start_at = "noti_start_at" in params
	isset_noti_length = "noti_length" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_noti_start_at and isset_noti_length:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				noti_start_at = int(params['noti_start_at'])
				check_noti_start_at = True
			except ValueError:
				check_noti_start_at = False

			try:
				noti_length = int(params['noti_length'])
				check_noti_length = True
			except ValueError:
				check_noti_length = False


			if not check_noti_start_at:
				result = { 
						"status" : False,
						"msg" : "Notification start at is not a number."
					}
			elif not check_noti_length:
				result = { 
						"status" : False,
						"msg" : "Notification length is not a number."
					}
			else:
				notification = db.admin_notification.find({
																"noti_status" : {"$in" : ["0","1"]}
															}).sort([("created_at", -1)]).skip(noti_start_at).limit(noti_length)
			
				total_data = db.admin_notification.find({
															"noti_status" : {"$in" : ["0","1"]}
														}).count()

				if notification is None:
					result = { 
								"status" : False,
								"msg" : "Data not found."
							}
				else:
					noti = db.admin_notification.find({
															"noti_status" : {"$in" : ["0","1"]}
														}).sort([("created_at", -1)])

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					noti_object = dumps(noti)
					noti_json = json.loads(noti_object)
					notification_object = dumps(notification)
					notification_json = json.loads(notification_object)

					noti_list = []
					count_badge = 0

					for i in range(len(noti_json)):
						if noti_json[i]['noti_status'] == "0":
							count_badge = count_badge + 1	

					for j in range(len(notification_json)):
						#แปลง format วันที่
						created_datetime = datetime.strptime(notification_json[j]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

						noti_list.append({
							"noti_id": notification_json[j]['_id']['$oid'],
							"noti_title": notification_json[j]['noti_title_th'],
							"noti_message": notification_json[j]['noti_message_th'],
							"noti_type": notification_json[j]['noti_type'],
							"noti_detail": notification_json[j]['noti_detail'],
							"noti_status": notification_json[j]['noti_status'],
							"created_datetime": created_datetime
						})

					result = {
								"status" : True,
								"msg" : "Get admin notification list success.",
								"noti_list" : noti_list,
								"badge" : count_badge,
								"total_data" : total_data
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
	function_name = "admin_noti_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def set_read_noti_backend(request):
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

			admin_notification = db.admin_notification.find({
																"noti_status": "0"
															})
			
			if admin_notification is None:
				result = { 
							"status" : False,
							"msg" : "Data not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				admin_notification_object = dumps(admin_notification)
				admin_notification_json = json.loads(admin_notification_object)
				update_status = 1

				for i in range(len(admin_notification_json)):
					# update member_notification
					where_param = { "_id": ObjectId(admin_notification_json[i]['_id']['$oid']) }
					value_param = {
									"$set":
										{
											"noti_status": "1",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.admin_notification.update(where_param , value_param):
						update_status = 1
					else:
						update_status = 0
						break
						
				if update_status == 1:
					result = {
								"status" : True,
								"msg" : "Set read noti success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Member noti update failed."
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
	function_name = "set_read_noti_backend"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def payment_driver_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_payment_status = "payment_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_payment_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { "request_status": "6", "job_status" : {"$in" : ["8","10"]} }

				#driver_name , driver_code , request_no
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "driver_name_en": {"$regex": params['search_text']} },
												{ "driver_name_th": {"$regex": params['search_text']} },
												{ "driver_code": {"$regex": params['search_text']} },
												{ "request_no": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['payment_status'] == "0":
					add_params = {"payment_status" : "0"}
					where_param.update(add_params)
				elif params['payment_status'] == "1":
					add_params = {"payment_status" : "1"}
					where_param.update(add_params)
				elif params['payment_status'] == "2":
					add_params = {"payment_status" : "2"}
					where_param.update(add_params)
				else:
					add_params = {"payment_status" : {"$in" : ["0","1","2"]}}
					where_param.update(add_params)

				if params['start_date'] != "" and params['end_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "updated_at"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# request_no = request_no
					# start_date = start_date
					# driver_name = driver_name_th
					# driver_code = driver_code
					# payment_amount = payment_amount
					# payment_status_text = payment_status
					# payment_date = payment_date

					if params['sort_name'] == "driver_name":
						sort_name = "driver_name_th"
					elif params['sort_name'] == "payment_status_text":
						sort_name = "payment_status"
					elif params['sort_name'] == "start_date":
						sort_name = "start_at"
					elif params['sort_name'] == "payment_date":
						sort_name = "payment_at"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				request_driver = db.request_driver.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.request_driver.find(where_param).count()

				if request_driver is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					payment_driver_list = []

					for i in range(len(request_driver_json)):
						start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
						start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')
						start_datetime = start_date+" เวลา "+start_time

						payment_datetime = None
						if request_driver_json[i]['payment_at'] is not None:
							payment_date = datetime.strptime(request_driver_json[i]['payment_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
							payment_time = datetime.strptime(request_driver_json[i]['payment_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
							payment_datetime = payment_date+" เวลา "+payment_time
						elif request_driver_json[i]['payment_at'] is None and request_driver_json[i]['payment_date'] is not None:
							payment_date = datetime.strptime(request_driver_json[i]['payment_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
							payment_datetime = payment_date+" เวลา 00:00"

						driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
						driver_code = driver_info['member_code']
						driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

						if request_driver_json[i]['payment_status'] == "2":
							payment_status_text = "ตั้งค่าการจ่ายแล้ว"
						elif request_driver_json[i]['payment_status'] == "1":
							payment_status_text = "จ่ายแล้ว"
						else:
							payment_status_text = "รอดำเนินการ"

						payment_driver_list.append({
							"id_index": data_start_at+(i+1),
							"request_id": request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"start_date": start_datetime,
							"driver_code": driver_code,
							"driver_name": driver_name,
							"normal_payment_amount": request_driver_json[i]['normal_payment_amount'],
							"total_overtime_usage": int(request_driver_json[i]['total_overtime_usage']),
							"overtime_payment_amount": request_driver_json[i]['overtime_payment_amount'],
							"payment_amount": request_driver_json[i]['payment_amount'],
							"payment_status": request_driver_json[i]['payment_status'],
							"payment_status_text": payment_status_text,
							"payment_date": payment_datetime
						})

				result = {
							"status" : True,
							"msg" : "Get payment driver report success.",
							"payment_driver" : payment_driver_list,
							"total_data" : total_data
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
	function_name = "payment_driver_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def summary_payment_driver_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_payment_status = "payment_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_payment_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { "request_status": "6", "job_status" : {"$in" : ["8","10"]} }

				#driver_name , driver_code , request_no
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "driver_name_en": {"$regex": params['search_text']} },
												{ "driver_name_th": {"$regex": params['search_text']} },
												{ "driver_code": {"$regex": params['search_text']} },
												{ "request_no": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['payment_status'] == "0":
					add_params = {"payment_status" : {"$in" : ["0","2"]}}
					where_param.update(add_params)
				elif params['payment_status'] == "1":
					add_params = {"payment_status" : "1"}
					where_param.update(add_params)
				else:
					add_params = {"payment_status" : {"$in" : ["0","1","2"]}}
					where_param.update(add_params)

				if params['start_date'] != "" and params['end_date'] != "":
					start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "updated_at"
					sort_type = -1
				else:
					# driver_name = driver_name_th
					# driver_code = driver_code
					# payment_amount = updated_at
					# payment_status_text = payment_status

					if params['sort_name'] == "driver_name":
						sort_name = "driver_name_th"
					elif params['sort_name'] == "payment_amount":
						sort_name = "updated_at"
					elif params['sort_name'] == "payment_status_text":
						sort_name = "payment_status"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

				rd = db.request_driver.find(where_param).sort([(sort_name, sort_type)])

				if rd is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					rd_object = dumps(rd)
					rd_json = json.loads(rd_object)

					driver_id_in = []
					summary_list = []
					summary_payment_driver_list = []
					spd_list = []
					start_row = data_start_at
					end_row = data_start_at + data_length
					data_index = start_row

					for i in range(len(rd_json)):
						if rd_json[i]['driver_id'] not in driver_id_in:
							driver_id_in.append(rd_json[i]['driver_id'])

					for x in range(len(driver_id_in)):
						member_info = get_member_info_by_id(driver_id_in[x])
						member_code = member_info['member_code']
						member_fullname = member_info['member_firstname_th']+" "+member_info['member_lastname_th']

						where_param_x = where_param
						add_params = {"driver_id" : driver_id_in[x]}
						where_param_x.update(add_params)

						request_driver = db.request_driver.find(where_param_x).sort([(sort_name, sort_type)])
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						request_driver_object = dumps(request_driver)
						request_driver_json = json.loads(request_driver_object)

						count_payment_amount_pending = 0
						count_payment_amount_success = 0
						
						for j in range(len(request_driver_json)):
							if request_driver_json[j]['payment_status'] == "1":
								count_payment_amount_success = count_payment_amount_success + request_driver_json[j]['payment_amount']
							else:
								count_payment_amount_pending = count_payment_amount_pending + request_driver_json[j]['payment_amount']
						
						if count_payment_amount_success > 0:
							#นับ count_summary ล่าสุด
							count_summary = len(summary_list)

							summary_list.append({
								"member_code": member_code,
								"member_fullname": member_fullname,
								"payment_amount": count_payment_amount_success,
								"payment_status": "1",
								"payment_status_text": "จ่ายแล้ว"
							})

							#ถ้า count_summary อยู่ในช่วงข้อมูลที่ต้องการ ให้เอาข้อมูลมาแสดง
							if count_summary >= start_row and count_summary < end_row:
								summary_payment_driver_list.append({
									"member_code": member_code,
									"member_fullname": member_fullname,
									"payment_amount": count_payment_amount_success,
									"payment_status": "1",
									"payment_status_text": "จ่ายแล้ว"
								})

						if count_payment_amount_pending > 0:
							#นับ count_summary ล่าสุด
							count_summary = len(summary_list)

							summary_list.append({
								"member_code": member_code,
								"member_fullname": member_fullname,
								"payment_amount": count_payment_amount_pending,
								"payment_status": "0",
								"payment_status_text": "ยังไม่ได้จ่าย"
							})

							#ถ้า count_summary อยู่ในช่วงข้อมูลที่ต้องการ ให้เอาข้อมูลมาแสดง
							if count_summary >= start_row and count_summary < end_row:
								summary_payment_driver_list.append({
									"member_code": member_code,
									"member_fullname": member_fullname,
									"payment_amount": count_payment_amount_pending,
									"payment_status": "0",
									"payment_status_text": "ยังไม่ได้จ่าย"
								})

					if params['sort_name'] == "payment_amount" and params['sort_type'] == "desc":
						summary_payment_driver_list.sort(key=lambda x: x.get('payment_amount'), reverse=True)
					elif params['sort_name'] == "payment_amount" and params['sort_type'] == "asc":
						summary_payment_driver_list.sort(key=lambda x: x.get('payment_amount'))
					elif params['sort_name'] == "payment_status_text" and params['sort_type'] == "desc":
						summary_payment_driver_list.sort(key=lambda x: x.get('payment_status'), reverse=True)
					elif params['sort_name'] == "payment_status_text" and params['sort_type'] == "asc":
						summary_payment_driver_list.sort(key=lambda x: x.get('payment_status'))

					for y in range(len(summary_payment_driver_list)):
						data_index = data_index+1

						spd_list.append({
							"id_index": data_index,
							"member_code": summary_payment_driver_list[y]["member_code"],
							"member_fullname": summary_payment_driver_list[y]["member_fullname"],
							"payment_amount": summary_payment_driver_list[y]["payment_amount"],
							"payment_status": summary_payment_driver_list[y]["payment_status"],
							"payment_status_text": summary_payment_driver_list[y]["payment_status_text"]
						})

				total_data = len(summary_list)

				result = {
							"status" : True,
							"msg" : "Get summary payment driver report success.",
							"summary_payment_driver" : spd_list,
							"total_data" : total_data
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
	function_name = "summary_payment_driver_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def billing_statement_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_billing_date = "start_billing_date" in params
	isset_end_billing_date = "end_billing_date" in params
	isset_billing_statement_status = "billing_statement_status" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_billing_date and isset_end_billing_date and isset_billing_statement_status and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = {}

				#billing_statement_code , company_name , billing_receiver_fullname , billing_receiver_tel , billing_receiver_email , billing_statement_amount
				if params['search_text'] != "":
					add_params = {
									"$or": [
												{ "billing_statement_code": {"$regex": params['search_text']} },
												{ "company_name": {"$regex": params['search_text']} },
												{ "billing_receiver_fullname": {"$regex": params['search_text']} },
												{ "billing_receiver_tel": {"$regex": params['search_text']} },
												{ "billing_receiver_email": {"$regex": params['search_text']} },
												{ "sum_paid": {"$regex": params['search_text']} }
											]
								}
					where_param.update(add_params)

				if params['billing_statement_status'] == "0":
					add_params = {"billing_statement_status" : "0"}
					where_param.update(add_params)
				elif params['billing_statement_status'] == "1":
					add_params = {"billing_statement_status" : "1"}
					where_param.update(add_params)
				elif params['billing_statement_status'] == "2":
					add_params = {"billing_statement_status" : "2"}
					where_param.update(add_params)
				else:
					add_params = {"billing_statement_status" : {"$in" : ["0","1","2"]}}
					where_param.update(add_params)

				if params['start_billing_date'] != "" and params['end_billing_date'] != "":
					start_billing_date_int = int(datetime.strptime(params['start_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					end_billing_date_int = int(datetime.strptime(params['end_billing_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				
					add_params = {"billing_statement_date_int" : {"$gte" : start_billing_date_int , "$lte" : end_billing_date_int}}
					where_param.update(add_params)

				if params['sort_name'] == "":
					sort_name = "billing_statement_code"
					sort_type = -1
				else:
					#การ sort ข้อมูล
					# billing_statement_code = billing_statement_code
					# billing_statement_date = billing_statement_date_int
					# company_name = company_name
					# billing_receiver_fullname = billing_receiver_fullname
					# billing_receiver_tel = billing_receiver_tel
					# billing_receiver_email = billing_receiver_email
					# sum_paid = sum_paid
					# billing_statement_status = billing_statement_status

					if params['sort_name'] == "billing_statement_date":
						sort_name = "created_at"
					else:
						sort_name = params['sort_name']

					if params['sort_type'] == "desc":
						sort_type = -1
					else:
						sort_type = 1

					
				billing_statement = db.billing_statement.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
				total_data = db.billing_statement.find(where_param).count()

				if billing_statement is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_statement_object = dumps(billing_statement)
					billing_statement_json = json.loads(billing_statement_object)

					billing_statement_list = []

					for i in range(len(billing_statement_json)):
						billing_statement_date = datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

						if billing_statement_json[i]['billing_statement_status'] == "2":
							billing_statement_status_text = "ยกเลิก"
						elif billing_statement_json[i]['billing_statement_status'] == "1":
							billing_statement_status_text = "ชำระแล้ว"
						else:
							billing_statement_status_text = "รอดำเนินการ"

						sum_paid = '{:,.2f}'.format(round(float(billing_statement_json[i]['sum_paid']) , 2))

						billing_statement_list.append({
							"id_index": data_start_at+(i+1),
							"billing_statement_code": billing_statement_json[i]['billing_statement_code'],
							"billing_statement_date": billing_statement_date,
							"company_name": billing_statement_json[i]['company_name'],
							"billing_receiver_fullname": billing_statement_json[i]['billing_receiver_fullname'],
							"billing_receiver_tel": billing_statement_json[i]['billing_receiver_tel'],
							"billing_receiver_email": billing_statement_json[i]['billing_receiver_email'],
							"sum_paid": sum_paid,
							"billing_statement_status": billing_statement_json[i]['billing_statement_status'],
							"billing_statement_status_text": billing_statement_status_text
						})

				result = {
							"status" : True,
							"msg" : "Get billing statement report success.",
							"billing_statement" : billing_statement_list,
							"total_data" : total_data
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
	function_name = "billing_statement_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def summary_service_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_customer_type = "customer_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_customer_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = { "member_type": "customer", "member_status" : "1" }

				if params['customer_type'] == "company":
					add_params = {"company_id" : {"$ne": None}}
					where_param.update(add_params)

					#customer_name
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "company_name": {"$regex": params['search_text']} }
												]
									}
						where_param.update(add_params)
				else:
					add_params = {"company_id" : None}
					where_param.update(add_params)

					#customer_name
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "member_firstname_en": {"$regex": params['search_text']} },
													{ "member_lastname_en": {"$regex": params['search_text']} }
												]
									}
						where_param.update(add_params)


				member = db.member.find(where_param)

				if member is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					unique_list = []
					summary_service_list = []
					summary_list = []
					ss_list = []
					start_row = data_start_at
					end_row = data_start_at + data_length
					data_index = start_row

					for i in range(len(member_json)):
						if member_json[i]['company_id'] is not None:
							customer_type = "นิติบุคคล"
							customer_name = member_json[i]['company_name']
							company_id = member_json[i]['company_id']

							company = db.company.find_one({"_id": ObjectId(company_id)})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_object = dumps(company)
							company_json = json.loads(company_object)
							customer_tel = company_json['company_tel']
							customer_email = company_json['company_email']
							sum_paid = 0
							total_paid_amount = 0

							request_driver = db.request_driver.find({
																		"company_id": company_id,
																		"request_status" : "6",
																		"job_status" : {"$in" : ["8","10"]}
																	})

							if request_driver is not None:
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								request_driver_object = dumps(request_driver)
								request_driver_json = json.loads(request_driver_object)

								len1 = len(request_driver_json)

								for j in range(len(request_driver_json)):
									main_package_info = request_driver_json[j]['main_package'][0]

									#คำนวณรายรับทั้งหมดของคนขับ
									main_package_normal_paid = 0
									main_package_overtime_paid = 0
									main_package_paid = 0

									second_package_normal_paid = 0
									second_package_overtime_paid = 0
									second_package_paid = 0

									overtime_package_normal_paid = 0
									overtime_package_overtime_paid = 0
									overtime_package_paid = 0

									billing_normal_paid = 0
									billing_overtime_paid = 0
									billing_paid = 0

									for k in range(len(request_driver_json[j]['main_package'])):
										main_package_normal_paid = main_package_normal_paid + (request_driver_json[j]['main_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
										main_package_overtime_paid = main_package_overtime_paid + (request_driver_json[j]['main_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

									main_package_paid = main_package_normal_paid + main_package_overtime_paid

									if len(request_driver_json[j]['second_package']) > 0:
										for k in range(len(request_driver_json[j]['second_package'])):
											second_package_normal_paid = second_package_normal_paid + (request_driver_json[j]['second_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
											second_package_overtime_paid = second_package_overtime_paid + (request_driver_json[j]['second_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

										second_package_paid = second_package_normal_paid + second_package_overtime_paid

									if len(request_driver_json[j]['overtime_package']) > 0:
										for k in range(len(request_driver_json[j]['overtime_package'])):
											overtime_package_normal_paid = overtime_package_normal_paid + (request_driver_json[j]['overtime_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
											overtime_package_overtime_paid = overtime_package_overtime_paid + (request_driver_json[j]['overtime_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

										overtime_package_paid = overtime_package_normal_paid + overtime_package_overtime_paid

									if len(request_driver_json[j]['billing_id']) > 0:
										for k in range(len(request_driver_json[j]['billing_id'])):
											billing = db.billing.find_one({"_id": ObjectId(request_driver_json[j]['billing_id'][k])})
											#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
											billing_object = dumps(billing)
											billing_json = json.loads(billing_object)

											billing_normal_paid = billing_normal_paid + (billing_json['normal_usage'] * main_package_info['normal_paid_rate'])
											billing_overtime_paid = billing_overtime_paid + (billing_json['overtime_usage'] * main_package_info['overtime_paid_rate'])

										billing_paid = billing_normal_paid + billing_overtime_paid

									sum_paid = sum_paid + float(main_package_paid + second_package_paid + overtime_package_paid + billing_paid)

								total_paid_amount = '{:,.2f}'.format(round(float(sum_paid) , 2))

							if company_id not in unique_list:
								#put email ใส่ array 
								unique_list.append(company_id)

								summary_service_list.append({
									"customer_type": customer_type,
									"customer_name": customer_name,
									"customer_tel": customer_tel,
									"customer_email": customer_email,
									"total_paid_amount": total_paid_amount
								})

						else:
							customer_type = "บุคคลทั่วไป"
							customer_name = member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']
							customer_tel = member_json[i]['member_tel']
							customer_email = member_json[i]['member_email']
							member_id = member_json[i]['_id']['$oid']
							sum_paid = 0
							total_paid_amount = 0

							request_driver = db.request_driver.find({
																		"member_id": member_id,
																		"request_status" : "6",
																		"job_status" : {"$in" : ["8","10"]}
																	})

							if request_driver is not None:
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								request_driver_object = dumps(request_driver)
								request_driver_json = json.loads(request_driver_object)

								len1 = len(request_driver_json)

								for j in range(len(request_driver_json)):
									main_package_info = request_driver_json[j]['main_package'][0]

									#คำนวณรายรับทั้งหมดของคนขับ
									main_package_normal_paid = 0
									main_package_overtime_paid = 0
									main_package_paid = 0

									second_package_normal_paid = 0
									second_package_overtime_paid = 0
									second_package_paid = 0

									overtime_package_normal_paid = 0
									overtime_package_overtime_paid = 0
									overtime_package_paid = 0

									billing_normal_paid = 0
									billing_overtime_paid = 0
									billing_paid = 0

									for k in range(len(request_driver_json[j]['main_package'])):
										main_package_normal_paid = main_package_normal_paid + (request_driver_json[j]['main_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
										main_package_overtime_paid = main_package_overtime_paid + (request_driver_json[j]['main_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

									main_package_paid = main_package_normal_paid + main_package_overtime_paid

									if len(request_driver_json[j]['second_package']) > 0:
										for k in range(len(request_driver_json[j]['second_package'])):
											second_package_normal_paid = second_package_normal_paid + (request_driver_json[j]['second_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
											second_package_overtime_paid = second_package_overtime_paid + (request_driver_json[j]['second_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

										second_package_paid = second_package_normal_paid + second_package_overtime_paid

									if len(request_driver_json[j]['overtime_package']) > 0:
										for k in range(len(request_driver_json[j]['overtime_package'])):
											overtime_package_normal_paid = overtime_package_normal_paid + (request_driver_json[j]['overtime_package'][k]['normal_usage'] * main_package_info['normal_paid_rate'])
											overtime_package_overtime_paid = overtime_package_overtime_paid + (request_driver_json[j]['overtime_package'][k]['overtime_usage'] * main_package_info['overtime_paid_rate'])

										overtime_package_paid = overtime_package_normal_paid + overtime_package_overtime_paid

									if len(request_driver_json[j]['billing_id']) > 0:
										for k in range(len(request_driver_json[j]['billing_id'])):
											billing = db.billing.find_one({"_id": ObjectId(request_driver_json[j]['billing_id'][k])})
											#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
											billing_object = dumps(billing)
											billing_json = json.loads(billing_object)

											billing_normal_paid = billing_normal_paid + (billing_json['normal_usage'] * main_package_info['normal_paid_rate'])
											billing_overtime_paid = billing_overtime_paid + (billing_json['overtime_usage'] * main_package_info['overtime_paid_rate'])

										billing_paid = billing_normal_paid + billing_overtime_paid

									sum_paid = sum_paid + float(main_package_paid + second_package_paid + overtime_package_paid + billing_paid)

								total_paid_amount = '{:,.2f}'.format(round(float(sum_paid) , 2))

							summary_service_list.append({
								"customer_type": customer_type,
								"customer_name": customer_name,
								"customer_tel": customer_tel,
								"customer_email": customer_email,
								"total_paid_amount": total_paid_amount
							})

					if params['sort_name'] == "customer_name" and params['sort_type'] == "desc":
						summary_service_list.sort(key=lambda x: x.get('customer_name'), reverse=True)
					elif params['sort_name'] == "customer_name" and params['sort_type'] == "asc":
						summary_service_list.sort(key=lambda x: x.get('customer_name'))
					elif params['sort_name'] == "customer_tel" and params['sort_type'] == "desc":
						summary_service_list.sort(key=lambda x: x.get('customer_tel'), reverse=True)
					elif params['sort_name'] == "customer_tel" and params['sort_type'] == "asc":
						summary_service_list.sort(key=lambda x: x.get('customer_tel'))
					elif params['sort_name'] == "customer_email" and params['sort_type'] == "desc":
						summary_service_list.sort(key=lambda x: x.get('customer_email'), reverse=True)
					elif params['sort_name'] == "customer_email" and params['sort_type'] == "asc":
						summary_service_list.sort(key=lambda x: x.get('customer_email'))
					elif params['sort_name'] == "total_paid_amount" and params['sort_type'] == "desc":
						summary_service_list.sort(key=lambda x: x.get('total_paid_amount'), reverse=True)
					elif params['sort_name'] == "total_paid_amount" and params['sort_type'] == "asc":
						summary_service_list.sort(key=lambda x: x.get('total_paid_amount'))

					for y in range(len(summary_service_list)):
						# y >= 0 and y < (0+10) -> 0-9
						# y >= 10 and y < (10+10) -> 10-19
						if y >= start_row and y < end_row:
							data_index = data_index+1

							ss_list.append({
								"id_index": data_index,
								"customer_type": summary_service_list[y]["customer_type"],
								"customer_name": summary_service_list[y]["customer_name"],
								"customer_tel": summary_service_list[y]["customer_tel"],
								"customer_email": summary_service_list[y]["customer_email"],
								"total_paid_amount": summary_service_list[y]["total_paid_amount"]
							})

				total_data = len(summary_service_list)

				result = {
							"status" : True,
							"msg" : "Get summary service report success.",
							"summary_service" : ss_list,
							"total_data" : total_data
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
	function_name = "summary_service_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_summary_service_report_form(request):
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
			customer_type_list = [
									{"code": "normal","name": "บุคคลทั่วไป"},
									{"code": "company","name": "นิติบุคคล"}
								]

			result = {
						"status" : True,
						"msg" : "Get summary service report form success.",
						"customer_type" : customer_type_list
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
	function_name = "get_summary_service_report_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def package_purchase_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_customer_type = "customer_type" in params
	isset_package_type = "package_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_customer_type and isset_package_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			try:
				data_start_at = int(params['data_start_at'])
				check_data_start_at = True
			except ValueError:
				check_data_start_at = False

			try:
				data_length = int(params['data_length'])
				check_data_length = True
			except ValueError:
				check_data_length = False


			if not check_data_start_at:
				result = { 
						"status" : False,
						"msg" : "Data start is not a number."
					}
			elif not check_data_length:
				result = { 
						"status" : False,
						"msg" : "Data length is not a number."
					}
			else:
				where_param = {}

				if params['customer_type'] == "company":
					#order_no , customer_name , package_code , package_name
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "order_no": {"$regex": params['search_text']} },
													{ "company_name": {"$regex": params['search_text']} },
													{ "package_code": {"$regex": params['search_text']} },
													{ "package_name_th": {"$regex": params['search_text']} }
												]
									}
						where_param.update(add_params)

					if params['package_type'] == "hour":
						add_params = {"package_type" : "hour"}
						where_param.update(add_params)
					elif params['package_type'] == "time":
						add_params = {"package_type" : "time"}
						where_param.update(add_params)


					if params['sort_name'] == "":
						sort_name = "order_no"
						sort_type = -1
					else:
						#การ sort ข้อมูล
						# order_date = order_date
						# order_no = order_no
						# customer_name = company_name
						# package_code = package_code
						# package_type = package_type
						# package_name = package_name_th
						# package_amount = package_amount
						# package_price = package_price

						if params['sort_name'] == "customer_name":
							sort_name = "company_name"
						else:
							sort_name = params['sort_name']

						if params['sort_type'] == "desc":
							sort_type = -1
						else:
							sort_type = 1

					package_purchase = db.company_package.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
					total_data = db.company_package.find(where_param).count()

					if package_purchase is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						package_purchase_object = dumps(package_purchase)
						package_purchase_json = json.loads(package_purchase_object)

						package_purchase_list = []

						for i in range(len(package_purchase_json)):
							order_date = datetime.strptime(package_purchase_json[i]['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

							if package_purchase_json[i]['package_type'] == "time":
								package_type = "รายครั้ง"
							else:
								package_type = "รายชั่วโมง"

							package_price = '{:,.2f}'.format(round(float(package_purchase_json[i]['package_price']) , 2))

							package_purchase_list.append({
								"id_index": data_start_at+(i+1),
								"order_date": order_date,
								"order_no": package_purchase_json[i]['order_no'],
								"customer_type": "นิติบุคคล",
								"customer_name": package_purchase_json[i]['company_name'],
								"package_code": package_purchase_json[i]['package_code'],
								"package_type": package_type,
								"package_name": package_purchase_json[i]['package_name_th'],
								"package_amount": package_purchase_json[i]['package_amount'],
								"package_price": package_price
							})
				else:
					add_params = {"company_package_id" : None}
					where_param.update(add_params)

					#order_no , customer_name , package_code , package_name
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "order_no": {"$regex": params['search_text']} },
													{ "member_name": {"$regex": params['search_text']} },
													{ "package_code": {"$regex": params['search_text']} },
													{ "package_name_th": {"$regex": params['search_text']} }
												]
									}
						where_param.update(add_params)

					if params['package_type'] == "hour":
						add_params = {"package_type" : "hour"}
						where_param.update(add_params)
					elif params['package_type'] == "time":
						add_params = {"package_type" : "time"}
						where_param.update(add_params)
				

					if params['sort_name'] == "":
						sort_name = "order_no"
						sort_type = -1
					else:
						#การ sort ข้อมูล
						# order_date = order_date
						# order_no = order_no
						# customer_name = member_name
						# package_code = package_code
						# package_type = package_type
						# package_name = package_name_th
						# package_amount = package_amount
						# package_price = package_price

						if params['sort_name'] == "customer_name":
							sort_name = "member_name"
						else:
							sort_name = params['sort_name']

						if params['sort_type'] == "desc":
							sort_type = -1
						else:
							sort_type = 1

					package_purchase = db.member_package.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
					total_data = db.member_package.find(where_param).count()

					if package_purchase is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						package_purchase_object = dumps(package_purchase)
						package_purchase_json = json.loads(package_purchase_object)

						package_purchase_list = []

						for i in range(len(package_purchase_json)):
							order_date = datetime.strptime(package_purchase_json[i]['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')

							if package_purchase_json[i]['package_type'] == "time":
								package_type = "รายครั้ง"
							else:
								package_type = "รายชั่วโมง"

							package_price = '{:,.2f}'.format(round(float(package_purchase_json[i]['package_price']) , 2))

							package_purchase_list.append({
								"id_index": data_start_at+(i+1),
								"order_date": order_date,
								"order_no": package_purchase_json[i]['order_no'],
								"customer_type": "บุคคลทั่วไป",
								"customer_name": package_purchase_json[i]['member_name'],
								"package_code": package_purchase_json[i]['package_code'],
								"package_type": package_type,
								"package_name": package_purchase_json[i]['package_name_th'],
								"package_amount": package_purchase_json[i]['package_amount'],
								"package_price": package_price
							})

				result = {
							"status" : True,
							"msg" : "Get package purchase report success.",
							"package_purchase" : package_purchase_list,
							"total_data" : total_data
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
	function_name = "package_purchase_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_purchase_report_form(request):
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
			customer_type_list = [
									{"code": "normal","name": "บุคคลทั่วไป"},
									{"code": "company","name": "นิติบุคคล"}
								]

			package_type_list = [
									{"code": "hour","name": "รายชั่วโมง"},
									{"code": "time","name": "รายครั้ง"}
								]

			result = {
						"status" : True,
						"msg" : "Get package purchase report form success.",
						"customer_type" : customer_type_list,
						"package_type" : package_type_list
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
	function_name = "get_package_purchase_report_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def dashboard_1(request):
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

			count_request_status_0 = 0
			count_request_status_4 = 0
			count_request_status_5 = 0
			count_assign_driver = 0
			count_billing_statement_status_0 = 0
			count_all_member = 0
			count_company_member = 0
			count_old_company_member = 0
			count_new_company_member = 0
			count_normal_member = 0
			count_old_normal_member = 0
			count_new_normal_member = 0
			count_company_member_status_0 = 0
			count_all_driver = 0
			count_old_driver = 0
			count_new_driver = 0
			count_driver_status_0 = 0
			count_driver_status_1 = 0
			count_driver_status_3 = 0
			count_driver_status_4 = 0

			#1
			check_request_status_0 = db.request_driver.find({"request_status": "0"}).count()
			if check_request_status_0 > 0:
				count_request_status_0 = check_request_status_0

			#2
			check_request_status_4 = db.request_driver.find({"request_status": "4"}).count()
			if check_request_status_4 > 0:
				count_request_status_4 = check_request_status_4

			#3
			check_request_status_5 = db.request_driver.find({"request_status": "5"}).count()
			if check_request_status_5 > 0:
				count_request_status_5 = check_request_status_5

			#4
			check_assign_driver = db.request_driver.find({
																"driver_list_id": None,
																"request_status": "0"
															}).count()
			if check_assign_driver > 0:
				count_assign_driver = check_assign_driver

			#5
			check_billing_statement_status_0 = db.billing_statement.find({"billing_statement_status": "0"}).count()

			if check_billing_statement_status_0 > 0:
				count_billing_statement_status_0 = check_billing_statement_status_0

			#6
			check_all_member = db.member.find({
												"member_type": "customer",
												"member_status": "1"
											}).count()

			if check_all_member > 0:
				count_all_member = check_all_member

			#7
			check_company_member = db.member.find({
													"member_type": "customer",
													"company_id": {"$ne": None},
													"member_status": "1"
												}).count()

			if check_company_member > 0:
				count_company_member = check_company_member


			current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
			current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
			before_30_datetime_obj = current_datetime_obj - timedelta(days=30)
			before_30_date = before_30_datetime_obj.strftime('%Y-%m-%d')
			before_30_time = before_30_datetime_obj.strftime('%H:%M:%S')
			before_30_datetime = before_30_date+" "+before_30_time

			#8
			check_old_company_member = db.member.find({
															"member_type": "customer",
															"company_id": {"$ne": None},
															"member_status": "1",
															"created_at": {"$lte": before_30_datetime}
														}).count()

			if check_old_company_member > 0:
				count_old_company_member = check_old_company_member

			#9
			check_new_company_member = db.member.find({
															"member_type": "customer",
															"company_id": {"$ne": None},
															"member_status": "1",
															"created_at": {"$gte": before_30_datetime}
														}).count()

			if check_new_company_member > 0:
				count_new_company_member = check_new_company_member

			#10
			check_company_member_status_0 = db.member.find({
													"member_type": "customer",
													"company_id": {"$ne": None},
													"member_status": "0"
												}).count()

			if check_company_member_status_0 > 0:
				count_company_member_status_0 = check_company_member_status_0



			#11
			check_normal_member = db.member.find({
													"member_type": "customer",
													"company_id": None,
													"member_status": "1"
												}).count()

			if check_normal_member > 0:
				count_normal_member = check_normal_member

			#12
			check_old_normal_member = db.member.find({
															"member_type": "customer",
															"company_id": None,
															"member_status": "1",
															"created_at": {"$lte": before_30_datetime}
														}).count()

			if check_old_normal_member > 0:
				count_old_normal_member = check_old_normal_member

			#13
			check_new_normal_member = db.member.find({
															"member_type": "customer",
															"company_id": None,
															"member_status": "1",
															"created_at": {"$gte": before_30_datetime}
														}).count()

			if check_new_normal_member > 0:
				count_new_normal_member = check_new_normal_member

			#14
			check_all_driver = db.member.find({
													"member_type": "driver",
													"member_status": "1"
												}).count()

			if check_all_driver > 0:
				count_all_driver = check_all_driver

			#15
			check_old_driver = db.member.find({
													"member_type": "driver",
													"member_status": "1",
													"created_at": {"$lte": before_30_datetime}
												}).count()

			if check_old_driver > 0:
				count_old_driver = check_old_driver

			#16
			check_new_driver = db.member.find({
													"member_type": "driver",
													"member_status": "1",
													"created_at": {"$gte": before_30_datetime}
												}).count()

			if check_new_driver > 0:
				count_new_driver = check_new_driver

			#17
			check_driver_status_0 = db.member.find({
														"member_type": "driver",
														"member_status": "0"
													}).count()

			if check_driver_status_0 > 0:
				count_driver_status_0 = check_driver_status_0




			#18
			check_driver_status_1 = db.member.find({
														"member_type": "driver",
														"member_status": "1"
													}).count()

			if check_driver_status_1 > 0:
				count_driver_status_1 = check_driver_status_1

			#19
			check_driver_status_3 = db.member.find({
														"member_type": "driver",
														"member_status": "3"
													}).count()

			if check_driver_status_3 > 0:
				count_driver_status_3 = check_driver_status_3

			#20
			check_driver_status_4 = db.member.find({
														"member_type": "driver",
														"member_status": "4"
													}).count()

			if check_driver_status_4 > 0:
				count_driver_status_4 = check_driver_status_4

			result = {
						"status" : True,
						"msg" : "Get dashboard 1 success.",
						"count_request_status_0" : count_request_status_0,
						"count_request_status_4" : count_request_status_4,
						"count_request_status_5" : count_request_status_5,
						"count_assign_driver" : count_assign_driver,
						"count_billing_statement_status_0" : count_billing_statement_status_0,
						"count_all_member" : count_all_member,
						"count_company_member" : count_company_member,
						"count_old_company_member" : count_old_company_member,
						"count_new_company_member" : count_new_company_member,
						"count_company_member_status_0" : count_company_member_status_0,
						"count_normal_member" : count_normal_member,
						"count_old_normal_member" : count_old_normal_member,
						"count_new_normal_member" : count_new_normal_member,
						"count_all_driver" : count_all_driver,
						"count_old_driver" : count_old_driver,
						"count_new_driver" : count_new_driver,
						"count_driver_status_0" : count_driver_status_0,
						"count_driver_status_1" : count_driver_status_1,
						"count_driver_status_3" : count_driver_status_3,
						"count_driver_status_4" : count_driver_status_4,
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
	function_name = "dashboard_1"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def dashboard_2(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_year = "year" in params
	isset_month = "month" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_year and isset_month:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			if params['year'] is None or params['year'] == "":
				year = datetime.now().strftime('%Y')
			else:
				year = str(params['year'])

			if params['month'] is None or params['month'] == "" or params['month'] == "all":
				month = "all"
			else:
				month = str(params['month'])

			#ถ้าเลือกเดือนเป็น ทุกเดือน จะค้นหาจากปีเท่านั้น
			if month == "all":
				search_text = year
			#ถ้าไม่ได้เลือกเป็น ทุกเดือน จะค้นหาจากปีและเดือน
			else:
				search_text = year+"-"+month

			normal_income = 0
			company_income = 0
			billing_income = 0
			normal_member_income = 0
			company_member_income = 0
			all_member_income = 0
			count_request_status_all = 0
			count_request_status_0 = 0
			count_request_status_145 = 0
			count_request_status_6 = 0
			count_request_status_2 = 0
			count_request_status_3 = 0

			#ยอดขาย Package (บุคคลทั่วไป)
			normal_member_order = db.order_package.find({
															"company_name": None,
															"order_status": "1",
															"created_at": {"$regex": search_text}
														})

			if normal_member_order is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				normal_member_order_object = dumps(normal_member_order)
				normal_member_order_json = json.loads(normal_member_order_object)

				for i in range(len(normal_member_order_json)):
					normal_income = normal_income + float(normal_member_order_json[i]['order_price'])

			#ยอดขาย Package (นิติบุคคล)
			company_member_order = db.order_package.find({
															"company_name" : {"$ne": None},
															"order_status": "1",
															"created_at": {"$regex": search_text}
														})

			if company_member_order is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_member_order_object = dumps(company_member_order)
				company_member_order_json = json.loads(company_member_order_object)

				for i in range(len(company_member_order_json)):
					company_income = company_income + float(company_member_order_json[i]['order_price'])

			#ยอดวางบิลที่ชำระสำเร็จ (นิติบุคคล)
			billing_statement = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": search_text}
															})

			if billing_statement is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_object = dumps(billing_statement)
				billing_statement_json = json.loads(billing_statement_object)

				for i in range(len(billing_statement_json)):
					billing_income = billing_income + float(billing_statement_json[i]['sum_paid'])

			#1
			normal_member_income = normal_income
			#2
			company_member_income = company_income + billing_income
			#3
			all_member_income = normal_member_income + company_member_income


			#4
			check_request_status_all = db.request_driver.find({
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_all > 0:
				count_request_status_all = check_request_status_all

			#5
			check_request_status_0 = db.request_driver.find({
																"request_status": "0",
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_0 > 0:
				count_request_status_0 = check_request_status_0

			#6
			check_request_status_145 = db.request_driver.find({
																"request_status": {"$in" : ["1","4","5"]},
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_145 > 0:
				count_request_status_145 = check_request_status_145

			#7
			check_request_status_6 = db.request_driver.find({
																"request_status": "6",
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_6 > 0:
				count_request_status_6 = check_request_status_6

			#8
			check_request_status_2 = db.request_driver.find({
																"request_status": "2",
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_2 > 0:
				count_request_status_2 = check_request_status_2

			#9
			check_request_status_3 = db.request_driver.find({
																"request_status": "3",
																"created_at": {"$regex": search_text}
															}).count()
			if check_request_status_3 > 0:
				count_request_status_3 = check_request_status_3

			result = {
						"status" : True,
						"msg" : "Get dashboard 2 success.",
						# "normal_income" : normal_income,
						# "company_income" : company_income,
						# "billing_income" : billing_income,

						"all_member_income" : all_member_income,
						"company_member_income" : company_member_income,
						"normal_member_income" : normal_member_income,

						"count_request_status_all" : count_request_status_all,
						"count_request_status_0" : count_request_status_0,
						"count_request_status_145" : count_request_status_145,
						"count_request_status_6" : count_request_status_6,
						"count_request_status_2" : count_request_status_2,
						"count_request_status_3" : count_request_status_3,
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
	function_name = "dashboard_2"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def dashboard_3(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_year = "year" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_year:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			admin_info = get_admin_info(token)
			admin_id = admin_info['_id']['$oid']

			if params['year'] is None or params['year'] == "":
				year = datetime.now().strftime('%Y')
			else:
				year = str(params['year'])

			package_purchase_income_1 = 0
			package_purchase_income_2 = 0
			package_purchase_income_3 = 0
			package_purchase_income_4 = 0
			package_purchase_income_5 = 0
			package_purchase_income_6 = 0
			package_purchase_income_7 = 0
			package_purchase_income_8 = 0
			package_purchase_income_9 = 0
			package_purchase_income_10 = 0
			package_purchase_income_11 = 0
			package_purchase_income_12 = 0

			billing_income_1 = 0
			billing_income_2 = 0
			billing_income_3 = 0
			billing_income_4 = 0
			billing_income_5 = 0
			billing_income_6 = 0
			billing_income_7 = 0
			billing_income_8 = 0
			billing_income_9 = 0
			billing_income_10 = 0
			billing_income_11 = 0
			billing_income_12 = 0

			payment_driver_1 = 0
			payment_driver_2 = 0
			payment_driver_3 = 0
			payment_driver_4 = 0
			payment_driver_5 = 0
			payment_driver_6 = 0
			payment_driver_7 = 0
			payment_driver_8 = 0
			payment_driver_9 = 0
			payment_driver_10 = 0
			payment_driver_11 = 0
			payment_driver_12 = 0

			package_purchase_income = []
			billing_income = []
			payment_driver = []

			#ยอดขาย Package เดือน 1
			order_package_1 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-01"}
													})

			if order_package_1 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_1_object = dumps(order_package_1)
				order_package_1_json = json.loads(order_package_1_object)

				for i in range(len(order_package_1_json)):
					package_purchase_income_1 = package_purchase_income_1 + float(order_package_1_json[i]['order_price'])

			#ยอดขาย Package เดือน 2
			order_package_2 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-02"}
													})

			if order_package_2 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_2_object = dumps(order_package_2)
				order_package_2_json = json.loads(order_package_2_object)

				for i in range(len(order_package_2_json)):
					package_purchase_income_2 = package_purchase_income_2 + float(order_package_2_json[i]['order_price'])

			#ยอดขาย Package เดือน 3
			order_package_3 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-03"}
													})

			if order_package_3 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_3_object = dumps(order_package_3)
				order_package_3_json = json.loads(order_package_3_object)

				for i in range(len(order_package_3_json)):
					package_purchase_income_3 = package_purchase_income_3 + float(order_package_3_json[i]['order_price'])

			#ยอดขาย Package เดือน 4
			order_package_4 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-04"}
													})

			if order_package_4 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_4_object = dumps(order_package_4)
				order_package_4_json = json.loads(order_package_4_object)

				for i in range(len(order_package_4_json)):
					package_purchase_income_4 = package_purchase_income_4 + float(order_package_4_json[i]['order_price'])

			#ยอดขาย Package เดือน 5
			order_package_5 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-05"}
													})

			if order_package_5 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_5_object = dumps(order_package_5)
				order_package_5_json = json.loads(order_package_5_object)

				for i in range(len(order_package_5_json)):
					package_purchase_income5 = package_purchase_income_5 + float(order_package_5_json[i]['order_price'])

			#ยอดขาย Package เดือน 6
			order_package_6 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-06"}
													})

			if order_package_6 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_6_object = dumps(order_package_6)
				order_package_6_json = json.loads(order_package_6_object)

				for i in range(len(order_package_6_json)):
					package_purchase_income_6 = package_purchase_income_6 + float(order_package_6_json[i]['order_price'])

			#ยอดขาย Package เดือน 7
			order_package_7 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-07"}
													})

			if order_package_7 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_7_object = dumps(order_package_7)
				order_package_7_json = json.loads(order_package_7_object)

				for i in range(len(order_package_7_json)):
					package_purchase_income_7 = package_purchase_income_7 + float(order_package_7_json[i]['order_price'])

			#ยอดขาย Package เดือน 8
			order_package_8 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-08"}
													})

			if order_package_8 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_8_object = dumps(order_package_8)
				order_package_8_json = json.loads(order_package_8_object)

				for i in range(len(order_package_8_json)):
					package_purchase_income_8 = package_purchase_income_8 + float(order_package_8_json[i]['order_price'])

			#ยอดขาย Package เดือน 9
			order_package_9 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-09"}
													})

			if order_package_9 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_9_object = dumps(order_package_9)
				order_package_9_json = json.loads(order_package_9_object)

				for i in range(len(order_package_9_json)):
					package_purchase_income_9 = package_purchase_income_9 + float(order_package_9_json[i]['order_price'])

			#ยอดขาย Package เดือน 10
			order_package_10 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-10"}
													})

			if order_package_10 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_10_object = dumps(order_package_10)
				order_package_10_json = json.loads(order_package_10_object)

				for i in range(len(order_package_10_json)):
					package_purchase_income_10 = package_purchase_income_10 + float(order_package_10_json[i]['order_price'])
			
			#ยอดขาย Package เดือน 11
			order_package_11 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-11"}
													})

			if order_package_11 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_11_object = dumps(order_package_11)
				order_package_11_json = json.loads(order_package_11_object)

				for i in range(len(order_package_11_json)):
					package_purchase_income_11 = package_purchase_income_11 + float(order_package_11_json[i]['order_price'])
			
			#ยอดขาย Package เดือน 12
			order_package_12 = db.order_package.find({
														"order_status": "1",
														"created_at": {"$regex": year+"-12"}
													})

			if order_package_12 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_12_object = dumps(order_package_12)
				order_package_12_json = json.loads(order_package_12_object)

				for i in range(len(order_package_12_json)):
					package_purchase_income_12 = package_purchase_income_12 + float(order_package_12_json[i]['order_price'])


			package_purchase_income = [
				package_purchase_income_1,
				package_purchase_income_2,
				package_purchase_income_3,
				package_purchase_income_4,
				package_purchase_income_5,
				package_purchase_income_6,
				package_purchase_income_7,
				package_purchase_income_8,
				package_purchase_income_9,
				package_purchase_income_10,
				package_purchase_income_11,
				package_purchase_income_12,
			]


			#ยอดวางบิลที่ชำระสำเร็จ เดือน 1
			billing_statement_1 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-01"}
															})

			if billing_statement_1 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_1_object = dumps(billing_statement_1)
				billing_statement_1_json = json.loads(billing_statement_1_object)

				for i in range(len(billing_statement_1_json)):
					billing_income_1 = billing_income_1 + float(billing_statement_1_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 2
			billing_statement_2 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-02"}
															})

			if billing_statement_2 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_2_object = dumps(billing_statement_2)
				billing_statement_2_json = json.loads(billing_statement_2_object)

				for i in range(len(billing_statement_2_json)):
					billing_income_2 = billing_income_2 + float(billing_statement_2_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 3
			billing_statement_3 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-03"}
															})

			if billing_statement_3 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_3_object = dumps(billing_statement_3)
				billing_statement_3_json = json.loads(billing_statement_3_object)

				for i in range(len(billing_statement_3_json)):
					billing_income_3 = billing_income_3 + float(billing_statement_3_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 4
			billing_statement_4 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-04"}
															})

			if billing_statement_4 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_4_object = dumps(billing_statement_4)
				billing_statement_4_json = json.loads(billing_statement_4_object)

				for i in range(len(billing_statement_4_json)):
					billing_income_4 = billing_income_4 + float(billing_statement_4_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 5
			billing_statement_5 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-05"}
															})

			if billing_statement_5 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_5_object = dumps(billing_statement_5)
				billing_statement_5_json = json.loads(billing_statement_5_object)

				for i in range(len(billing_statement_5_json)):
					billing_income_5 = billing_income_5 + float(billing_statement_5_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 6
			billing_statement_6 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-06"}
															})

			if billing_statement_6 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_6_object = dumps(billing_statement_6)
				billing_statement_6_json = json.loads(billing_statement_6_object)

				for i in range(len(billing_statement_6_json)):
					billing_income_6 = billing_income_6 + float(billing_statement_6_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 7
			billing_statement_7 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-07"}
															})

			if billing_statement_7 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_7_object = dumps(billing_statement_7)
				billing_statement_7_json = json.loads(billing_statement_7_object)

				for i in range(len(billing_statement_7_json)):
					billing_income_7 = billing_income_7 + float(billing_statement_7_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 8
			billing_statement_8 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-08"}
															})

			if billing_statement_8 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_8_object = dumps(billing_statement_8)
				billing_statement_8_json = json.loads(billing_statement_8_object)

				for i in range(len(billing_statement_8_json)):
					billing_income_8 = billing_income_8 + float(billing_statement_8_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 9
			billing_statement_9 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-09"}
															})

			if billing_statement_9 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_9_object = dumps(billing_statement_9)
				billing_statement_9_json = json.loads(billing_statement_9_object)

				for i in range(len(billing_statement_9_json)):
					billing_income_9 = billing_income_9 + float(billing_statement_9_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 10
			billing_statement_10 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-10"}
															})

			if billing_statement_10 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_10_object = dumps(billing_statement_10)
				billing_statement_10_json = json.loads(billing_statement_10_object)

				for i in range(len(billing_statement_10_json)):
					billing_income_10 = billing_income_10 + float(billing_statement_10_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 11
			billing_statement_11 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-11"}
															})

			if billing_statement_11 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_11_object = dumps(billing_statement_11)
				billing_statement_11_json = json.loads(billing_statement_11_object)

				for i in range(len(billing_statement_11_json)):
					billing_income_11 = billing_income_11 + float(billing_statement_11_json[i]['sum_paid'])

			#ยอดวางบิลที่ชำระสำเร็จ เดือน 12
			billing_statement_12 = db.billing_statement.find({
																"billing_statement_status": "1",
																"created_at": {"$regex": year+"-12"}
															})

			if billing_statement_12 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_12_object = dumps(billing_statement_12)
				billing_statement_12_json = json.loads(billing_statement_12_object)

				for i in range(len(billing_statement_12_json)):
					billing_income_12 = billing_income_12 + float(billing_statement_12_json[i]['sum_paid'])


			billing_income = [
				billing_income_1,
				billing_income_2,
				billing_income_3,
				billing_income_4,
				billing_income_5,
				billing_income_6,
				billing_income_7,
				billing_income_8,
				billing_income_9,
				billing_income_10,
				billing_income_11,
				billing_income_12,
			]


			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 1
			request_driver_1 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-01"}
													})

			if request_driver_1 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_1_object = dumps(request_driver_1)
				request_driver_1_json = json.loads(request_driver_1_object)

				for i in range(len(request_driver_1_json)):
					payment_driver_1 = payment_driver_1 + float(request_driver_1_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 2
			request_driver_2 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-02"}
													})

			if request_driver_2 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_2_object = dumps(request_driver_2)
				request_driver_2_json = json.loads(request_driver_2_object)

				for i in range(len(request_driver_2_json)):
					payment_driver_2 = payment_driver_2 + float(request_driver_2_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 3
			request_driver_3 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-03"}
													})

			if request_driver_3 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_3_object = dumps(request_driver_3)
				request_driver_3_json = json.loads(request_driver_3_object)

				for i in range(len(request_driver_3_json)):
					payment_driver_3 = payment_driver_3 + float(request_driver_3_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 4
			request_driver_4 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-04"}
													})

			if request_driver_4 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_4_object = dumps(request_driver_4)
				request_driver_4_json = json.loads(request_driver_4_object)

				for i in range(len(request_driver_4_json)):
					payment_driver_4 = payment_driver_4 + float(request_driver_4_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 5
			request_driver_5 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-05"}
													})

			if request_driver_5 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_5_object = dumps(request_driver_5)
				request_driver_5_json = json.loads(request_driver_5_object)

				for i in range(len(request_driver_5_json)):
					payment_driver_5 = payment_driver_5 + float(request_driver_5_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 6
			request_driver_6 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-06"}
													})

			if request_driver_6 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_6_object = dumps(request_driver_6)
				request_driver_6_json = json.loads(request_driver_6_object)

				for i in range(len(request_driver_6_json)):
					payment_driver_6 = payment_driver_6 + float(request_driver_6_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 7
			request_driver_7 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-07"}
													})

			if request_driver_7 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_7_object = dumps(request_driver_7)
				request_driver_7_json = json.loads(request_driver_7_object)

				for i in range(len(request_driver_7_json)):
					payment_driver_7 = payment_driver_7 + float(request_driver_7_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 8
			request_driver_8 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-08"}
													})

			if request_driver_8 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_8_object = dumps(request_driver_8)
				request_driver_8_json = json.loads(request_driver_8_object)

				for i in range(len(request_driver_8_json)):
					payment_driver_8 = payment_driver_8 + float(request_driver_8_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 9
			request_driver_9 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-09"}
													})

			if request_driver_9 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_9_object = dumps(request_driver_9)
				request_driver_9_json = json.loads(request_driver_9_object)

				for i in range(len(request_driver_9_json)):
					payment_driver_9 = payment_driver_9 + float(request_driver_9_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 10
			request_driver_10 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-10"}
													})

			if request_driver_10 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_10_object = dumps(request_driver_10)
				request_driver_10_json = json.loads(request_driver_10_object)

				for i in range(len(request_driver_10_json)):
					payment_driver_10 = payment_driver_10 + float(request_driver_10_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 11
			request_driver_11 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-11"}
													})

			if request_driver_11 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_11_object = dumps(request_driver_11)
				request_driver_11_json = json.loads(request_driver_11_object)

				for i in range(len(request_driver_11_json)):
					payment_driver_11 = payment_driver_11 + float(request_driver_11_json[i]['payment_amount'])

			#ยอดจ่ายเงินคนขับที่ชำระสำเร็จ เดือน 12
			request_driver_12 = db.request_driver.find({
														"payment_status": "1",
														"payment_at": {"$regex": year+"-12"}
													})

			if request_driver_12 is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_12_object = dumps(request_driver_12)
				request_driver_12_json = json.loads(request_driver_12_object)

				for i in range(len(request_driver_12_json)):
					payment_driver_12 = payment_driver_12 + float(request_driver_12_json[i]['payment_amount'])


			payment_driver = [
				payment_driver_1,
				payment_driver_2,
				payment_driver_3,
				payment_driver_4,
				payment_driver_5,
				payment_driver_6,
				payment_driver_7,
				payment_driver_8,
				payment_driver_9,
				payment_driver_10,
				payment_driver_11,
				payment_driver_12,
			]

			result = {
						"status" : True,
						"msg" : "Get dashboard 3 success.",
						"package_purchase_income" : package_purchase_income,
						"billing_income" : billing_income,
						"payment_driver" : payment_driver,
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
	function_name = "dashboard_3"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

