from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from function.notification import send_push_message
from function.checktokenexpire import check_token_expire
from function.checkrequeststatus import check_request_status
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

def get_customer_profile(mem_id,request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None
	
	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member = db.member.find_one({
											"_id": ObjectId(mem_id),
											"member_type": "customer"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_customer_profile" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				if member_json['company_id'] is not None:
					company_id = member_json['company_id']
					company_name = member_json['company_name']
					company_user_type = member_json['company_user_type']
				else:
					company_id = None
					company_name = None
					company_user_type = None

				emergency_call = db.emergency_call.find_one()
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				emergency_call_object = dumps(emergency_call)
				emergency_call_json = json.loads(emergency_call_object)

				if member_lang == "en":
					member_firstname = member_json['member_firstname_en']
					member_lastname = member_json['member_lastname_en']
				else:
					member_firstname = member_json['member_firstname_th']
					member_lastname = member_json['member_lastname_th']

				user_profile = {
									"member_id" : member_json['_id']['$oid'],
									"member_code": member_json['member_code'],
									"member_username": member_json['member_username'],
									"member_firstname": member_firstname,
									"member_lastname": member_lastname,
									"member_email": member_json['member_email'],
									"member_tel": member_json['member_tel'],
									"member_type": member_json['member_type'],

									"company_id": company_id,
									"company_name": company_name,
									"company_user_type": company_user_type, #2=master admin company,1=admin company,0=user company

									"profile_image": member_json['profile_image'],
									"member_lang": member_json['member_lang'],
									"member_token": member_json['member_token'],
									"noti_key": member_json['noti_key'],
									"member_status": member_json['member_status'],
									"customer_emergency" : emergency_call_json['call_customer_admin'],
									"system" : "frontend",

									"social_type": member_json['social_type'],
									"social_id": member_json['social_id']
								}

				result = {
							"status" : True,
							"msg" : get_api_message("get_customer_profile" , "get_customer_profile_success" , member_lang),
							"user_profile" : user_profile
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_customer_profile"
	request_headers = request.headers
	params_get = {"member_id" : mem_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def get_my_customer_profile(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member = db.member.find_one({
											"member_token": token,
											"member_type": "customer"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_customer_profile" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				if member_json['company_id'] is not None:
					company_id = member_json['company_id']
					company_name = member_json['company_name']
					company_user_type = member_json['company_user_type']
				else:
					company_id = None
					company_name = None
					company_user_type = None

				emergency_call = db.emergency_call.find_one()
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				emergency_call_object = dumps(emergency_call)
				emergency_call_json = json.loads(emergency_call_object)

				if member_lang == "en":
					member_firstname = member_json['member_firstname_en']
					member_lastname = member_json['member_lastname_en']
				else:
					member_firstname = member_json['member_firstname_th']
					member_lastname = member_json['member_lastname_th']

				user_profile = {
									"member_id" : member_json['_id']['$oid'],
									"member_code": member_json['member_code'],
									"member_username": member_json['member_username'],
									"member_firstname": member_firstname,
									"member_lastname": member_lastname,
									"member_email": member_json['member_email'],
									"member_tel": member_json['member_tel'],
									"member_type": member_json['member_type'],

									"company_id": company_id,
									"company_name": company_name,
									"company_user_type": company_user_type, #2=master admin company,1=admin company,0=user company

									"profile_image": member_json['profile_image'],
									"member_lang": member_json['member_lang'],
									"member_token": member_json['member_token'],
									"noti_key": member_json['noti_key'],
									"member_status": member_json['member_status'],
									"customer_emergency" : emergency_call_json['call_customer_admin'],
									"system" : "frontend",

									"social_type": member_json['social_type'],
									"social_id": member_json['social_id']
								}

				result = {
							"status" : True,
							"msg" : get_api_message("get_customer_profile" , "get_customer_profile_success" , member_lang),
							"user_profile" : user_profile
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_my_customer_profile"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def customer_news_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_news_start_at = "news_start_at" in params
	isset_news_length = "news_length" in params
	isset_member_lang = "member_lang" in params	

	if isset_accept and isset_content_type and isset_app_version and isset_news_start_at and isset_news_length and isset_member_lang:
		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		try:
			news_start_at = int(params['news_start_at'])
			check_news_start_at = True
		except ValueError:
			check_news_start_at = False

		try:
			news_length = int(params['news_length'])
			check_news_length = True
		except ValueError:
			check_news_length = False


		if not check_news_start_at:
			result = { 
					"status" : False,
					"msg" : get_api_message("customer_news_list" , "news_start_at_is_not_a_number" , member_lang)
				}
		elif not check_news_length:
			result = { 
					"status" : False,
					"msg" : get_api_message("customer_news_list" , "news_length_is_not_a_number" , member_lang)
				}
		else:
			if isset_token:
				#เช็ค token ว่า expire แล้วหรือยัง
				token = request.headers['Authorization']
				check_token = check_token_expire(token)

				if check_token:
					member_info = get_member_info(token)
					member_lang = member_info['member_lang']
					company_id = member_info['company_id']

					#ถ้าเป็น normal user
					if member_info['company_id'] is None:
						news = db.news.find({
												"display" : {"$in" : ["all","customer"]}, 
												"news_status" : "1"
											}).sort([("pin", -1),("updated_at", -1)]).skip(news_start_at).limit(news_length)
					#ถ้าเป็น company user
					else:
						news = db.news.find({
												"$or": [
													{"display" : {"$in" : ["all","customer"]}}, {"private.company_id" : company_id}
												], 
												"news_status" : "1"
											}).sort([("pin", -1),("updated_at", -1)]).skip(news_start_at).limit(news_length)

				else:
					news = db.news.find({
											"display" : {"$in" : ["all","customer"]}, 
											"news_status" : "1"
										}).sort([("pin", -1),("updated_at", -1)]).skip(news_start_at).limit(news_length)
			else:
				news = db.news.find({
										"display" : {"$in" : ["all","customer"]}, 
										"news_status" : "1"
									}).sort([("pin", -1),("updated_at", -1)]).skip(news_start_at).limit(news_length)

			if news is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("customer_news_list" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				news_object = dumps(news)
				news_json = json.loads(news_object)

				news_list = []

				for i in range(len(news_json)):
					if member_lang == "en":
						news_title = news_json[i]['news_title_en']
						news_detail = news_json[i]['news_detail_en']
					else:
						news_title = news_json[i]['news_title_th']
						news_detail = news_json[i]['news_detail_th']

					news_list.append({
						"news_id" : news_json[i]['_id']['$oid'],
						"news_title": news_title,
						"news_detail": news_detail,
						"start_date": news_json[i]['start_date'],
						"end_date": news_json[i]['end_date'],
						"display": news_json[i]['display'],
						"pin": news_json[i]['pin'],
						"news_cover": news_json[i]['news_cover']
					})

				result = {
							"status" : True,
							"msg" : get_api_message("customer_news_list" , "get_customer_news_list_success" , member_lang),
							"news_list" : news_list
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "customer_news_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_news_detail_frontend(news_id,request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	if isset_accept and isset_content_type:
		member_lang = "en"

		news = db.news.find_one({ "_id": ObjectId(news_id) , "news_status": "1" })

		if news is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("get_news_detail_frontend" , "data_not_found" , member_lang)
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			news_object = dumps(news)
			news_json = json.loads(news_object)

			result = {
						"status" : True,
						"msg" : get_api_message("get_news_detail_frontend" , "get_news_detail_success" , member_lang),
						"news_id" : news_json['_id']['$oid'],
						"news_title_en": news_json['news_title_en'],
						"news_title_th": news_json['news_title_th'],
						"news_detail_en": news_json['news_detail_en'],
						"news_detail_th": news_json['news_detail_th'],
						"start_date": news_json['start_date'],
						"end_date": news_json['end_date'],
						"display": news_json['display'],
						"pin": news_json['pin'],
						"news_cover": news_json['news_cover']
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_news_detail_frontend"
	request_headers = request.headers
	params_get = {"news_id" : news_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def main_customer_guest(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_os_type = "os_type" in params
	isset_number_news = "number_news" in params
	isset_member_lang = "member_lang" in params

	if isset_accept and isset_content_type and isset_app_version and isset_os_type and isset_number_news and isset_member_lang:
		check_version = check_update_version("customer" , params['app_version'] , params['os_type'])

		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		try:
			number_news = int(params['number_news'])
			check_number_news = True
		except ValueError:
			check_number_news = False

		if not check_number_news:
			result = { 
						"status" : False,
						"msg" : get_api_message("main_customer_guest" , "number_news_is_not_a_number" , member_lang)
					}
		else:
			news = db.news.find({
									"display" : {"$in" : ["all","customer"]},
									"news_status": "1"
								}).sort([("pin", -1),("updated_at", -1)]).limit(number_news)
			driver = db.member.find({"member_type" : "driver","member_status" : "1"}).sort([("driver_rating", -1),("updated_at", -1)]).limit(3)

			news_list = []
			driver_list = []

			if news is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				news_object = dumps(news)
				news_json = json.loads(news_object)

				for i in range(len(news_json)):
					if member_lang == "en":
						news_title = news_json[i]['news_title_en']
						news_detail = news_json[i]['news_detail_en']
					else:
						news_title = news_json[i]['news_title_th']
						news_detail = news_json[i]['news_detail_th']

					news_list.append({
						"news_id" : news_json[i]['_id']['$oid'],
						"news_title": news_title,
						"news_detail": news_detail,
						"start_date": news_json[i]['start_date'],
						"end_date": news_json[i]['end_date'],
						"display": news_json[i]['display'],
						"pin": news_json[i]['pin'],
						"news_cover": news_json[i]['news_cover']
					})

			if driver is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_object = dumps(driver)
				driver_json = json.loads(driver_object)

				for j in range(len(driver_json)):
					level_name = None
					level_detail = None
					level_image = None

					if driver_json[j]['driver_level'] is not None:
						driver_level = db.driver_level.find_one({"_id": ObjectId(driver_json[j]['driver_level'])})
						
						if driver_level is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							driver_level_object = dumps(driver_level)
							driver_level_json = json.loads(driver_level_object)

							if member_lang == "en":
								level_name = driver_level_json["level_name_en"]
								level_detail = driver_level_json["level_detail_en"]
							else:
								level_name = driver_level_json["level_name_th"]
								level_detail = driver_level_json["level_detail_th"]

							level_image = driver_level_json["level_image"]

					member_age = None
					if driver_json[j]['member_birthday'] is not None:
						member_age = get_member_age(driver_json[j]['member_birthday'])

					if member_lang == "en":
						if driver_json[j]['member_gender'] == "female":
							member_gender_text = "Female"
						else:
							member_gender_text = "Male"

						car_gear_text = driver_json[j]['car_gear_en']
						service_area_text = driver_json[j]['service_area_en']
						communication_text = driver_json[j]['communication_en']
						workday_text = driver_json[j]['workday_en']
						special_skill_text = driver_json[j]['special_skill_en']
						car_type_detail = []
						car_type_text = ""

						if driver_json[j]['car_type_en'] is not None:
							car_type_split = driver_json[j]['car_type_en'].split(" , ")

							for k in range(len(car_type_split)):
								if car_type_split[k] == "Sedan":
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['sedan_job'])+" times"
								elif car_type_split[k] == "SUV":
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['suv_job'])+" times"
								else:
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['van_job'])+" times"

								car_type_detail.append(car_type_text)
					else:
						if driver_json[j]['member_gender'] == "female":
							member_gender_text = "หญิง"
						else:
							member_gender_text = "ชาย"

						car_gear_text = driver_json[j]['car_gear_th']
						service_area_text = driver_json[j]['service_area_th']
						communication_text = driver_json[j]['communication_th']
						workday_text = driver_json[j]['workday_th']
						special_skill_text = driver_json[j]['special_skill_th']
						car_type_detail = []
						car_type_text = ""

						if driver_json[j]['car_type_th'] is not None:
							car_type_split = driver_json[j]['car_type_th'].split(" , ")

							for k in range(len(car_type_split)):
								if car_type_split[k] == "รถเก๋ง":
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['sedan_job'])+" ครั้ง"
								elif car_type_split[k] == "รถ SUV":
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['suv_job'])+" ครั้ง"
								else:
									car_type_text = car_type_split[k]+" "+str(driver_json[j]['van_job'])+" ครั้ง"

								car_type_detail.append(car_type_text)

					communication_list = []

					for k in range(len(driver_json[j]['communication'])):
						communication = db.communication.find_one({"_id": ObjectId(driver_json[j]['communication'][k])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						communication_object = dumps(communication)
						communication_json = json.loads(communication_object)

						if member_lang == "en":
							lang_name = communication_json['lang_name_en']
						else:
							lang_name = communication_json['lang_name_th']

						communication_list.append({
							"communication_id" : communication_json['_id']['$oid'],
							"lang_name": lang_name,
							"lang_code": communication_json['lang_code'],
							"flag_image": communication_json['flag_image']
						})

					if driver_json[j]['profile_image'] is not None:
						profile_image = driver_json[j]['profile_image']
					else:
						profile_image = "default_driver.jpg"

					if driver_json[j]['driver_rating'] is not None:
						driver_rating = round(float(driver_json[j]['driver_rating']) , 1)
					else:
						driver_rating = float("0")

					driver_list.append({
						"member_id" : driver_json[j]['_id']['$oid'],
						"member_code": driver_json[j]['member_code'],
						"member_username": driver_json[j]['member_username'],
						"member_firstname_en": driver_json[j]['member_firstname_en'],
						"member_lastname_en": driver_json[j]['member_lastname_en'],
						"member_firstname_th": driver_json[j]['member_firstname_th'],
						"member_lastname_th": driver_json[j]['member_lastname_th'],
						"member_email": driver_json[j]['member_email'],
						"member_tel": driver_json[j]['member_tel'],
						"member_birthday": driver_json[j]['member_birthday'],
						"member_gender": driver_json[j]['member_gender'],
						"member_gender_text": member_gender_text,
						"member_type": driver_json[j]['member_type'],
						"profile_image": profile_image,
						"driver_license_expire": driver_json[j]['driver_license_expire'],
						"driver_license_no": driver_json[j]['driver_license_no'],
						"car_type": driver_json[j]['car_type'],
						"car_type_detail": car_type_detail,
						"car_gear": driver_json[j]['car_gear'],
						"car_gear_text": car_gear_text,
						"service_area": driver_json[j]['service_area'],
						"service_area_text": service_area_text,
						"communication": communication_list,
						"communication_text": communication_text,
						"workday": driver_json[j]['workday'],
						"workday_text": workday_text,
						"special_skill": driver_json[j]['special_skill'],
						"special_skill_text": special_skill_text,
						"driver_rating": driver_rating,
						"driver_level": driver_json[j]['driver_level'],
						"level_name": level_name,
						"level_detail": level_detail,
						"level_image": level_image,
						"member_age" : member_age,
						"member_lang": driver_json[j]['member_lang'],
						"member_token": driver_json[j]['member_token'],
						"noti_key": driver_json[j]['noti_key']
					})
				
			result = {
						"status" : True,
						"msg" : get_api_message("main_customer_guest" , "get_main_customer_guest_success" , member_lang),
						"news" : news_list,
						"recommend_driver" : driver_list,
						"check_version" : check_version
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "main_customer_guest"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def main_customer(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_os_type = "os_type" in params
	isset_number_news = "number_news" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_os_type and isset_number_news:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			check_version = check_update_version("customer" , params['app_version'] , params['os_type'])
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member = db.member.find_one({
											"member_token": token,
											"member_type": "customer"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("main_customer" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				try:
					number_news = int(params['number_news'])
					check_number_news = True
				except ValueError:
					check_number_news = False

				if not check_number_news:
					result = { 
								"status" : False,
								"msg" : get_api_message("main_customer" , "number_news_is_not_a_number" , member_lang)
							}
				else:
					#set ค่า default ภาษาให้เป็นค่า member_lang จาก member
					company_id = member_json['company_id']
					news_list = []
					request_driver_list = []

					#ถ้าเป็น normal user
					if member_json['company_id'] is None:
						news = db.news.find({
												"display" : {"$in" : ["all","customer"]},
												"news_status": "1"
											}).sort([("pin", -1),("updated_at", -1)]).limit(number_news)
					#ถ้าเป็น company user
					else:
						news = db.news.find({
												"$or": [
													{"display" : {"$in" : ["all","customer"]}}, {"private.company_id" : company_id}
												],
												"news_status": "1"
											}).sort([("pin", -1),("updated_at", -1)]).limit(number_news)

					if news is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						news_object = dumps(news)
						news_json = json.loads(news_object)

						for i in range(len(news_json)):
							if member_lang == "en":
								news_title = news_json[i]['news_title_en']
								news_detail = news_json[i]['news_detail_en']
							else:
								news_title = news_json[i]['news_title_th']
								news_detail = news_json[i]['news_detail_th']

							news_list.append({
								"news_id" : news_json[i]['_id']['$oid'],
								"news_title": news_title,
								"news_detail": news_detail,
								"start_date": news_json[i]['start_date'],
								"end_date": news_json[i]['end_date'],
								"display": news_json[i]['display'],
								"pin": news_json[i]['pin'],
								"news_cover": news_json[i]['news_cover']
							})

					today_date = datetime.now().strftime('%Y-%m-%d')
					today_time = datetime.now().strftime('%H:%M:%S')
					today_date_int = int(datetime.strptime(today_date, '%Y-%m-%d').strftime('%Y%m%d')) 

					request_driver = db.request_driver.find({
																"$or": [
																	{ "member_id": member_info['_id']['$oid'] },
																	{ "passenger_id": member_info['_id']['$oid'] }
																],
																"$and": [
																	{ "start_date_int" : {"$gte" : today_date_int} },
																	{ "request_status" : {"$in" : ["1","4","5"]} }
																]
															}).sort([("start_date", 1)]).skip(0).limit(2)

					if request_driver is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						request_driver_object = dumps(request_driver)
						request_driver_json = json.loads(request_driver_object)

						for i in range(len(request_driver_json)):
							package_info = get_package_info(request_driver_json[i]['main_package_id'])

							if member_lang == "en":
								main_package_name = package_info['package_name_en']
							else:
								main_package_name = package_info['package_name_th']

							if request_driver_json[i]['request_status'] == "6":
								if member_lang == "en":
									request_status_text = "Finish"
								else:
									request_status_text = "สำเร็จ"
							elif request_driver_json[i]['request_status'] == "5":
								if member_lang == "en":
									request_status_text = "Traveling"
								else:
									request_status_text = "กำลังเดินทาง"
							elif request_driver_json[i]['request_status'] == "4":
								if member_lang == "en":
									request_status_text = "Upcoming work"
								else:
									request_status_text = "งานที่ใกล้จะถึง"
							elif request_driver_json[i]['request_status'] == "3":
								if member_lang == "en":
									request_status_text = "Canceled by driver"
								else:
									request_status_text = "ยกเลิกโดยคนขับ"
							elif request_driver_json[i]['request_status'] == "2":
								if member_lang == "en":
									request_status_text = "Canceled by customer"
								else:
									request_status_text = "ยกเลิกโดยลูกค้า"
							elif request_driver_json[i]['request_status'] == "1":
								if member_lang == "en":
									request_status_text = "Accepted"
								else:
									request_status_text = "ตอบรับแล้ว"
							else:
								if member_lang == "en":
									request_status_text = "Waiting for reply"
								else:
									request_status_text = "รอตอบรับ"						

							start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
							start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')
							start_datetime = start_date+" "+start_time

							request_driver_list.append({
								"request_id" : request_driver_json[i]['_id']['$oid'],
								"request_no": request_driver_json[i]['request_no'],
								"company_id": request_driver_json[i]['company_id'],
								"member_id": request_driver_json[i]['member_id'],
								"passenger_id": request_driver_json[i]['passenger_id'],
								"request_to": request_driver_json[i]['request_to'],
								"start_datetime": start_datetime,
								"from_location_name": request_driver_json[i]['from_location_name'],
								"from_location_address": request_driver_json[i]['from_location_address'],
								"to_location_name": request_driver_json[i]['to_location_name'],
								"main_package_name": main_package_name,
								"request_status": request_driver_json[i]['request_status'],
								"request_status_text": request_status_text
							})

					vat_rate = get_vat_rate()

					result = {
								"status" : True,
								"msg" : get_api_message("main_customer" , "get_main_customer_success" , member_lang),
								"news" : news_list,
								"request" : request_driver_list,
								"vat_rate" : vat_rate,
								"check_version" : check_version
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "main_customer"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

# def send_customer_register(request):
# 	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_accept = "Accept" in request.headers
# 	isset_content_type = "Content-Type" in request.headers
# 	member_id = None

# 	params = json.loads(request.data)

# 	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_app_version = "app_version" in params
# 	isset_firstname = "member_firstname" in params
# 	isset_lastname = "member_lastname" in params
# 	isset_email = "member_email" in params
# 	isset_tel = "member_tel" in params
# 	isset_username = "member_username" in params
# 	isset_password = "member_password" in params
# 	isset_company_name = "company_name" in params
# 	isset_tax_id = "company_tax_id" in params
# 	isset_profile_image = "profile_image" in params
# 	isset_member_lang = "member_lang" in params
# 	isset_os_type = "os_type" in params

# 	if isset_accept and isset_content_type and isset_app_version and isset_firstname and isset_lastname and isset_email and isset_tel and isset_username and isset_password and isset_company_name and isset_tax_id and isset_profile_image and isset_member_lang and isset_os_type:
# 		if params['member_lang'] == "en":
# 			member_lang = "en"
# 		else:
# 			member_lang = "th"

# 		validate = []

# 		#check required
# 		if params['member_firstname']=="" or params['member_firstname'] is None:
# 			validate.append({"error_param" : "member_firstname","msg" : get_api_message("send_customer_register" , "firstname_is_required" , member_lang)})
# 		if params['member_lastname']=="" or params['member_lastname'] is None:
# 			validate.append({"error_param" : "member_lastname","msg" : get_api_message("send_customer_register" , "lastname_is_required" , member_lang)})
# 		if params['member_email']=="" or params['member_email'] is None:
# 			validate.append({"error_param" : "member_email","msg" : get_api_message("send_customer_register" , "email_is_required" , member_lang)})
# 		if params['member_tel']=="" or params['member_tel'] is None:
# 			validate.append({"error_param" : "member_tel","msg" : get_api_message("send_customer_register" , "tel_is_required" , member_lang)})
# 		if params['member_username']=="" or params['member_username'] is None:
# 			validate.append({"error_param" : "member_username","msg" : get_api_message("send_customer_register" , "username_is_required" , member_lang)})
# 		if params['member_password']=="" or params['member_password'] is None:
# 			validate.append({"error_param" : "member_password","msg" : get_api_message("send_customer_register" , "password_is_required" , member_lang)})
# 		if params['company_name']=="":
# 			validate.append({"error_param" : "company_name","msg" : get_api_message("send_customer_register" , "company_name_is_required" , member_lang)})
# 		if params['company_tax_id']=="":
# 			validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "tax_id_is_required" , member_lang)})
# 		if params['member_lang']=="" or params['member_lang'] is None:
# 			validate.append({"error_param" : "member_lang","msg" : get_api_message("send_customer_register" , "language_is_required" , member_lang)})

# 		#check already customer name
# 		if (params['member_firstname']!="" and params['member_firstname'] is not None) and (params['member_lastname']!="" and params['member_lastname'] is not None):
# 			check_customer_name = db.member.find({
# 													"member_type": "customer",
# 													"member_firstname_en": params['member_firstname'].strip().title(),
# 													"member_lastname_en": params['member_lastname'].strip().title()
# 												}).count()
# 			if check_customer_name > 0:
# 				validate.append({"error_param" : "member_firstname","msg" : get_api_message("send_customer_register" , "firstname_and_lastname_has_been_used" , member_lang)})
		
# 		#check already email
# 		if params['member_email']!="" and params['member_email'] is not None:
# 			#check email format

# 			check_email = db.member.find({
# 											"member_type": "customer",
# 											"member_email": params['member_email'].strip().lower()
# 										}).count()
# 			if check_email > 0:
# 				validate.append({"error_param" : "member_email","msg" : get_api_message("send_customer_register" , "email_has_been_used" , member_lang)})

# 		#check tel format
# 		if params['member_tel']!="" and params['member_tel'] is not None:
# 			tel = params['member_tel'].replace("-", "")
# 			count_tel = len(tel)

# 			try:
# 				data_member_tel = int(params['member_tel'])
# 				check_data_member_tel = True
# 			except ValueError:
# 				check_data_member_tel = False

# 			if ((count_tel < 9) or (count_tel > 10) or (not check_data_member_tel)):
# 				validate.append({"error_param" : "member_tel","msg" : get_api_message("send_customer_register" , "invalid_tel_format" , member_lang)})

# 		#check already username
# 		if params['member_username']!="" and params['member_username'] is not None:
# 			#check username format

# 			check_username = db.member.find({
# 												"member_type": "customer",
# 												"member_username": params['member_username'].strip().lower()
# 											}).count()
# 			if check_username > 0:
# 				validate.append({"error_param" : "member_username","msg" : get_api_message("send_customer_register" , "username_has_been_used" , member_lang)})

# 		#check password format
# 		if params['member_password']!="" and params['member_password'] is not None:
# 			count_password = len(params['member_password'])

# 			if count_password < 6:
# 				validate.append({"error_param" : "member_password","msg" : get_api_message("send_customer_register" , "password_less_than_6_character" , member_lang)})

# 		#check already company
# 		if (params['company_name']!="" and params['company_name'] is not None) and (params['company_tax_id']!="" and params['company_tax_id'] is not None):
# 			check_company = db.company.find({
# 												"company_tax_id": params['company_tax_id'].strip(),
# 												"company_status": "1"
# 											}).count()
# 			if check_company > 0:
# 				validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "tax_id_has_been_used" , member_lang)})
# 		elif (params['company_name']!="" and params['company_name'] is not None) or (params['company_tax_id']!="" and params['company_tax_id'] is not None):
# 			validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "company_name_and_tax_id_is_required" , member_lang)})
		

# 		#ถ้า validate ผ่าน
# 		if len(validate) == 0:
# 			if params['profile_image'] is None:
# 				image_name = None
# 			else:
# 				#generate token
# 				generate_token = get_random_token(40)
# 				check_upload_image = upload_profile_image(params['profile_image'], generate_token)

# 				if check_upload_image is None:
# 					image_name = None
# 				else:
# 					image_name = check_upload_image

# 			if params['member_lang']=="en":
# 				member_lang = "en"
# 			else:
# 				member_lang = "th"

# 			if params['os_type'] == "ios" or params['os_type'] == "android":
# 				register_channel = "app"
# 			else:
# 				register_channel = "web"

# 			#เอา password ที่รับมาเข้ารหัส
# 			hash_input_pass = hashlib.md5(params['member_password'].encode())
# 			hash_pass = hash_input_pass.hexdigest()

# 			if params['company_name'] is None or params['company_tax_id'] is None:
# 				#ดึง member_code ล่าสุดจาก tb member แล้วเอามา +1
# 				member = db.member.find_one({"member_type":"customer", "company_id":{"$in": [None, ""]}}, sort=[("member_code", -1)])
# 				mid = 1

# 				if member is not None:
# 					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 					member_object = dumps(member)
# 					member_json = json.loads(member_object)

# 					mid = int(member_json["member_code"][1:8])+1

# 				member_code = "N"+"%07d" % mid

# 				data = { 
# 							"member_code": member_code,
# 							"member_username": params['member_username'].strip().lower(),
# 							"member_password": hash_pass,
# 							"member_firstname_en": params['member_firstname'].strip().title(),
# 							"member_lastname_en": params['member_lastname'].strip().title(),
# 							"member_firstname_th": params['member_firstname'].strip().title(),
# 							"member_lastname_th": params['member_lastname'].strip().title(),
# 							"member_email": params['member_email'].strip().lower(),
# 							"member_tel": params['member_tel'].strip(),
# 							"member_type": "customer",
# 							"company_id": None,
# 							"company_name": None,
# 							"company_user_type": None,
# 							"company_status": None,
# 							"profile_image": image_name,
# 							"member_lang": member_lang,
# 							"member_status": "1",
# 							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"approved_at": None,
# 							"member_token": None,
# 							"noti_key": None,
# 							"os_type": params['os_type']
# 						}

# 				if db.member.insert_one(data):
# 					username = params['member_username'].strip().lower()
# 					password = params['member_password']
# 					android_link = "https://play.google.com/store"
# 					ios_link = "https://www.apple.com/th/ios/app-store/"

# 					#send email
# 					email_type = "register_success_normal"
# 					subject = "VR Driver : สมัครสมาชิกสำเร็จ"
# 					to_email = params['member_email'].strip().lower()
# 					template_html = "register_success_normal.html"
# 					data_detail = { "username" : username, "password" : password, "android_link" : android_link , "ios_link" : ios_link }

# 					data_email = { 
# 									"email_type": email_type,
# 									"data": data_detail,
# 									"subject": subject,
# 									"to_email": to_email,
# 									"template_html": template_html,
# 									"send_status": "0",
# 									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 								}
# 					db.queue_email.insert_one(data_email)

# 					result = {
# 								"status" : True,
# 								"msg" : get_api_message("send_customer_register" , "register_success" , member_lang)
# 							}
# 				else:
# 					result = {
# 								"status" : False,
# 								"msg" : get_api_message("send_customer_register" , "member_insert_failed" , member_lang)
# 							}
# 			else:
# 				#ดึง member_code ล่าสุดจาก tb member แล้วเอามา +1
# 				member = db.member.find_one({"member_type":"customer", "company_id":{"$nin": [None, ""]}}, sort=[("member_code", -1)])
# 				mid = 1

# 				if member is not None:
# 					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 					member_object = dumps(member)
# 					member_json = json.loads(member_object)

# 					mid = int(member_json["member_code"][1:8])+1

# 				member_code = "C"+"%07d" % mid

# 				#กรณีมีการแก้ไข company_status ใน tb company ให้กลับไปอัพเดต company_status ใน tb member ที่มี company_id เดียวกันด้วย
# 				company_id = ObjectId()
# 				company_data = {
# 									"_id": company_id,
# 									"company_name": params['company_name'].strip(),
# 									"company_tax_id": params['company_tax_id'].strip(),
# 									"company_email": params['member_email'].strip().lower(),
# 									"company_tel": params['member_tel'].strip(),

# 									"company_address": None,
# 									"company_postcode": None,
# 									"company_province_en": None,
# 									"company_province_th": None,
# 									"company_province_code": None,
# 									"company_district_en": None,
# 									"company_district_th": None,
# 									"company_district_code": None,
# 									"company_sub_district_en": None,
# 									"company_sub_district_th": None,
# 									"company_sub_district_code": None,

# 									"billing_date": None,
# 									"billing_receiver_firstname": None,
# 									"billing_receiver_lastname": None,
# 									"billing_receiver_email": None,
# 									"billing_receiver_tel": None,

# 									"same_company_address": "0",
# 									"billing_address": None,
# 									"billing_postcode": None,
# 									"billing_province_en": None,
# 									"billing_province_th": None,
# 									"billing_province_code": None,
# 									"billing_district_en": None,
# 									"billing_district_th": None,
# 									"billing_district_code": None,
# 									"billing_sub_district_en": None,
# 									"billing_sub_district_th": None,
# 									"billing_sub_district_code": None,

# 									"vat_registration_doc": None,
# 									"vat_registration_doc_type": None,
# 									"vat_registration_doc_name": None,
# 									"company_certificate_doc": None,
# 									"company_certificate_doc_type": None,
# 									"company_certificate_doc_name": None,
# 									"company_logo": None,
# 									"os_type": params['os_type'],
# 									"register_channel": register_channel,
# 									"company_status": "0",
# 									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 									"approved_at": None
# 								}

# 				data = { 
# 							"member_code": member_code,
# 							"member_username": params['member_username'].strip().lower(),
# 							"member_password": hash_pass,
# 							"member_firstname_en": params['member_firstname'].strip().title(),
# 							"member_lastname_en": params['member_lastname'].strip().title(),
# 							"member_firstname_th": params['member_firstname'].strip().title(),
# 							"member_lastname_th": params['member_lastname'].strip().title(),
# 							"member_email": params['member_email'].strip().lower(),
# 							"member_tel": params['member_tel'].strip(),
# 							"member_type": "customer",
# 							"company_id": str(company_id),
# 							"company_name": params['company_name'].strip(),
# 							"company_user_type": "2",
# 							"company_status": "0",
# 							"profile_image": image_name,
# 							"member_lang": member_lang,
# 							"member_status": "0",
# 							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 							"approved_at": None,
# 							"member_token": None,
# 							"noti_key": None,
# 							"os_type": params['os_type']
# 						}

# 				if db.company.insert_one(company_data):
# 					if db.member.insert_one(data):
# 						# ส่งเมล์หลังจากสมัครสมาชิกนิติบุคคลสำเร็จ
# 						username = params['member_username'].strip().lower()
# 						password = params['member_password']
# 						web_link = "https://play.google.com/store"

# 						#send email
# 						email_type = "register_success_company"
# 						subject = "VR Driver : สมัครสมาชิกนิติบุคคลสำเร็จ"
# 						to_email = params['member_email'].strip().lower()
# 						template_html = "register_success_company.html"
# 						data_detail = { "username" : username, "password" : password, "web_link" : web_link }
						
# 						data_email = { 
# 										"email_type": email_type,
# 										"data": data_detail,
# 										"subject": subject,
# 										"to_email": to_email,
# 										"template_html": template_html,
# 										"send_status": "0",
# 										"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 									}
# 						db.queue_email.insert_one(data_email)

# 						result = {
# 									"status" : True,
# 									"msg" : get_api_message("send_customer_register" , "register_success" , member_lang)
# 								}
# 					else:
# 						result = {
# 								"status" : False,
# 								"msg" : get_api_message("send_customer_register" , "member_insert_failed" , member_lang)
# 							}
# 				else:
# 					result = {
# 							"status" : False,
# 							"msg" : get_api_message("send_customer_register" , "company_insert_failed" , member_lang)
# 						}
# 		else:
# 			result = {
# 						"status" : False,
# 						"msg" : get_api_message("all" , "please_check_your_parameters_value"),
# 						"error_list" : validate
# 					}
# 	else:
# 		result = { 
# 					"status" : False,
# 					"msg" : get_api_message("all" , "please_check_your_parameters")
# 				}

# 	#set log detail
# 	user_type = "customer"
# 	function_name = "send_customer_register"
# 	request_headers = request.headers
# 	params_get = None
# 	params_post = params
# 	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
# 	return result

def send_customer_register(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_firstname = "member_firstname" in params
	isset_lastname = "member_lastname" in params
	isset_email = "member_email" in params
	isset_tel = "member_tel" in params
	isset_username = "member_username" in params
	isset_password = "member_password" in params
	isset_company_name = "company_name" in params
	isset_tax_id = "company_tax_id" in params
	isset_profile_image = "profile_image" in params
	isset_member_lang = "member_lang" in params
	isset_os_type = "os_type" in params
	isset_social_type = "social_type" in params
	isset_social_id = "social_id" in params

	if isset_accept and isset_content_type and isset_app_version and isset_firstname and isset_lastname and isset_email and isset_tel and isset_username and isset_password and isset_company_name and isset_tax_id and isset_profile_image and isset_member_lang and isset_os_type and isset_social_type and isset_social_id:
		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		validate = []

		#check required
		if params['member_firstname']=="" or params['member_firstname'] is None:
			validate.append({"error_param" : "member_firstname","msg" : get_api_message("send_customer_register" , "firstname_is_required" , member_lang)})
		if params['member_lastname']=="" or params['member_lastname'] is None:
			validate.append({"error_param" : "member_lastname","msg" : get_api_message("send_customer_register" , "lastname_is_required" , member_lang)})
		if params['member_email']=="" or params['member_email'] is None:
			validate.append({"error_param" : "member_email","msg" : get_api_message("send_customer_register" , "email_is_required" , member_lang)})
		if params['member_tel']=="" or params['member_tel'] is None:
			validate.append({"error_param" : "member_tel","msg" : get_api_message("send_customer_register" , "tel_is_required" , member_lang)})
		if params['member_username']=="" or params['member_username'] is None:
			validate.append({"error_param" : "member_username","msg" : get_api_message("send_customer_register" , "username_is_required" , member_lang)})
		if params['member_password']=="" or params['member_password'] is None:
			validate.append({"error_param" : "member_password","msg" : get_api_message("send_customer_register" , "password_is_required" , member_lang)})
		if params['company_name']=="":
			validate.append({"error_param" : "company_name","msg" : get_api_message("send_customer_register" , "company_name_is_required" , member_lang)})
		if params['company_tax_id']=="":
			validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "tax_id_is_required" , member_lang)})
		if params['member_lang']=="" or params['member_lang'] is None:
			validate.append({"error_param" : "member_lang","msg" : get_api_message("send_customer_register" , "language_is_required" , member_lang)})

		if params['social_type']!="line" and params['social_type'] is not None:
			validate.append({"error_param" : "social_type","msg" : get_api_message("send_customer_register" , "social_type_is_invalid" , member_lang)})
		if params['social_type']=="line" and (params['social_id']=="" or params['social_type'] is None):
			validate.append({"error_param" : "social_id","msg" : get_api_message("send_customer_register" , "social_id_is_required" , member_lang)})

		#check already customer name
		if (params['member_firstname']!="" and params['member_firstname'] is not None) and (params['member_lastname']!="" and params['member_lastname'] is not None):
			check_customer_name = db.member.find({
													"member_type": "customer",
													"member_firstname_en": params['member_firstname'].strip().title(),
													"member_lastname_en": params['member_lastname'].strip().title()
												}).count()
			if check_customer_name > 0:
				validate.append({"error_param" : "member_firstname","msg" : get_api_message("send_customer_register" , "firstname_and_lastname_has_been_used" , member_lang)})
		
		#check already email
		if params['member_email']!="" and params['member_email'] is not None:
			#check email format
			pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
			regex = re.compile(pattern)
			check_format_email = regex.findall(params['member_email'])

			if len(check_format_email) > 0:
				check_email = db.member.find({
												"member_type": "customer",
												"member_email": params['member_email'].strip().lower()
											}).count()
				if check_email > 0:
					validate.append({"error_param" : "member_email","msg" : get_api_message("send_customer_register" , "email_has_been_used" , member_lang)})
			else:
				validate.append({"error_param" : "member_email","msg" : get_api_message("send_customer_register" , "invalid_email_format" , member_lang)})		

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
				validate.append({"error_param" : "member_tel","msg" : get_api_message("send_customer_register" , "invalid_tel_format" , member_lang)})

		#check already username
		if params['member_username']!="" and params['member_username'] is not None:
			#check username format
			pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
			regex = re.compile(pattern)
			check_format_username = regex.findall(params['member_username'])

			if len(check_format_username) > 0:
				check_username = db.member.find({
													"member_type": "customer",
													"member_username": params['member_username'].strip().lower()
												}).count()
				if check_username > 0:
					validate.append({"error_param" : "member_username","msg" : get_api_message("send_customer_register" , "username_has_been_used" , member_lang)})
			else:
				validate.append({"error_param" : "member_username","msg" : get_api_message("send_customer_register" , "invalid_username_format" , member_lang)})

		#check password format
		if params['member_password']!="" and params['member_password'] is not None:
			count_password = len(params['member_password'])

			if count_password < 6:
				validate.append({"error_param" : "member_password","msg" : get_api_message("send_customer_register" , "password_less_than_6_character" , member_lang)})

		#check already company
		if (params['company_name']!="" and params['company_name'] is not None) and (params['company_tax_id']!="" and params['company_tax_id'] is not None):
			check_company = db.company.find({
												"company_tax_id": params['company_tax_id'].strip(),
												"company_status": "1"
											}).count()
			if check_company > 0:
				validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "tax_id_has_been_used" , member_lang)})
		elif (params['company_name']!="" and params['company_name'] is not None) or (params['company_tax_id']!="" and params['company_tax_id'] is not None):
			validate.append({"error_param" : "company_tax_id","msg" : get_api_message("send_customer_register" , "company_name_and_tax_id_is_required" , member_lang)})

		#check already social
		if params['social_type']=="line" and params['social_id'] is not None:
			check_social_id = db.member.find({
												"member_type": "customer",
												"social_type": "line",
												"social_id": params['social_id']
											}).count()
			if check_social_id > 0:
				validate.append({"error_param" : "social_id","msg" : get_api_message("send_customer_register" , "social_id_has_been_used" , member_lang)})

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

			if params['os_type'] == "ios" or params['os_type'] == "android":
				register_channel = "app"
			else:
				register_channel = "web"

			#เอา password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(params['member_password'].encode())
			hash_pass = hash_input_pass.hexdigest()

			if params['social_type']=="line" and params['social_id'] is not None:
				social_type = params['social_type']
				social_id = params['social_id']
			else:
				social_type = None
				social_id = None

			if params['company_name'] is None or params['company_tax_id'] is None:
				#ดึง member_code ล่าสุดจาก tb member แล้วเอามา +1
				member = db.member.find_one({"member_type":"customer", "company_id":{"$in": [None, ""]}}, sort=[("member_code", -1)])
				mid = 1

				if member is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					mid = int(member_json["member_code"][1:8])+1

				member_code = "N"+"%07d" % mid

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				member_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				member_id_string = str(member_id)

				data = { 
							"_id": member_id,
							"member_code": member_code,
							"member_username": params['member_username'].strip().lower(),
							"member_password": hash_pass,
							"member_firstname_en": params['member_firstname'].strip().title(),
							"member_lastname_en": params['member_lastname'].strip().title(),
							"member_firstname_th": params['member_firstname'].strip().title(),
							"member_lastname_th": params['member_lastname'].strip().title(),
							"member_email": params['member_email'].strip().lower(),
							"member_tel": params['member_tel'].strip(),
							"member_type": "customer",
							"company_id": None,
							"company_name": None,
							"company_user_type": None,
							"company_status": None,
							"profile_image": image_name,
							"member_lang": member_lang,
							"member_status": "1",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"activated_at": None,
							"approved_at": None,
							"member_token": None,
							"noti_key": None,
							"os_type": params['os_type'],
							"social_type": social_type,
							"social_id": social_id
						}

				if db.member.insert_one(data):
					# ส่งเมล์เพื่อยืนยันตัวตน
					username = params['member_username'].strip().lower()
					password = params['member_password']
					activate_link = "http://178.128.88.86/activate/"+member_id_string

					email_type = "activate_user"
					subject = "VR Driver : ยืนยันตัวตนสำหรับเข้าใช้งาน VR Driver"
					to_email = params['member_email'].strip().lower()
					template_html = "activate_user.html"
					data_detail = { "username" : username, "password" : password, "activate_link" : activate_link }

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
								"msg" : get_api_message("send_customer_register" , "register_success" , member_lang)
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("send_customer_register" , "member_insert_failed" , member_lang)
							}
			else:
				#ดึง member_code ล่าสุดจาก tb member แล้วเอามา +1
				member = db.member.find_one({"member_type":"customer", "company_id":{"$nin": [None, ""]}}, sort=[("member_code", -1)])
				mid = 1

				if member is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					mid = int(member_json["member_code"][1:8])+1

				member_code = "C"+"%07d" % mid

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				member_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				member_id_string = str(member_id)

				#กรณีมีการแก้ไข company_status ใน tb company ให้กลับไปอัพเดต company_status ใน tb member ที่มี company_id เดียวกันด้วย
				company_id = ObjectId()
				company_data = {
									"_id": company_id,
									"company_name": params['company_name'].strip(),
									"company_tax_id": params['company_tax_id'].strip(),
									"company_email": params['member_email'].strip().lower(),
									"company_tel": params['member_tel'].strip(),

									"company_address": None,
									"company_postcode": None,
									"company_province_en": None,
									"company_province_th": None,
									"company_province_code": None,
									"company_district_en": None,
									"company_district_th": None,
									"company_district_code": None,
									"company_sub_district_en": None,
									"company_sub_district_th": None,
									"company_sub_district_code": None,

									"billing_date": None,
									"billing_receiver_firstname": None,
									"billing_receiver_lastname": None,
									"billing_receiver_email": None,
									"billing_receiver_tel": None,

									"same_company_address": "0",
									"billing_address": None,
									"billing_postcode": None,
									"billing_province_en": None,
									"billing_province_th": None,
									"billing_province_code": None,
									"billing_district_en": None,
									"billing_district_th": None,
									"billing_district_code": None,
									"billing_sub_district_en": None,
									"billing_sub_district_th": None,
									"billing_sub_district_code": None,

									"vat_registration_doc": None,
									"vat_registration_doc_type": None,
									"vat_registration_doc_name": None,
									"company_certificate_doc": None,
									"company_certificate_doc_type": None,
									"company_certificate_doc_name": None,
									"company_logo": None,
									"os_type": params['os_type'],
									"register_channel": register_channel,
									"company_status": "0",
									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"approved_at": None
								}

				data = { 
							"_id": member_id,
							"member_code": member_code,
							"member_username": params['member_username'].strip().lower(),
							"member_password": hash_pass,
							"member_firstname_en": params['member_firstname'].strip().title(),
							"member_lastname_en": params['member_lastname'].strip().title(),
							"member_firstname_th": params['member_firstname'].strip().title(),
							"member_lastname_th": params['member_lastname'].strip().title(),
							"member_email": params['member_email'].strip().lower(),
							"member_tel": params['member_tel'].strip(),
							"member_type": "customer",
							"company_id": str(company_id),
							"company_name": params['company_name'].strip(),
							"company_user_type": "2",
							"company_status": "0",
							"profile_image": image_name,
							"member_lang": member_lang,
							"member_status": "0",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"activated_at": None,
							"approved_at": None,
							"member_token": None,
							"noti_key": None,
							"os_type": params['os_type'],
							"social_type": social_type,
							"social_id": social_id
						}

				if db.company.insert_one(company_data):
					if db.member.insert_one(data):
						# ส่งเมล์เพื่อยืนยันตัวตน
						username = params['member_username'].strip().lower()
						password = params['member_password']
						activate_link = "http://178.128.88.86/activate/"+member_id_string

						email_type = "activate_user"
						subject = "VR Driver : ยืนยันตัวตนสำหรับเข้าใช้งาน VR Driver"
						to_email = params['member_email'].strip().lower()
						template_html = "activate_user.html"
						data_detail = { "username" : username, "password" : password, "activate_link" : activate_link }

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
									"msg" : get_api_message("send_customer_register" , "register_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("send_customer_register" , "member_insert_failed" , member_lang)
								}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("send_customer_register" , "company_insert_failed" , member_lang)
							}
		else:
			result = {
						"status" : False,
						"msg" : get_api_message("all" , "please_check_your_parameters_value"),
						"error_list" : validate
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "send_customer_register"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def edit_my_customer_profile(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_firstname = "member_firstname" in params
	isset_lastname = "member_lastname" in params
	isset_email = "member_email" in params
	isset_tel = "member_tel" in params
	isset_profile_image = "profile_image" in params
	isset_social_type = "social_type" in params
	isset_social_id = "social_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_firstname and isset_lastname and isset_email and isset_tel and isset_profile_image and isset_social_type and isset_social_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']
			member_firstname = member_info['member_firstname_en']
			member_lastname = member_info['member_lastname_en']

			validate = []

			#check required
			if params['member_firstname']=="" or params['member_firstname'] is None:
				validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_my_customer_profile" , "firstname_is_required" , member_lang)})
			if params['member_lastname']=="" or params['member_lastname'] is None:
				validate.append({"error_param" : "member_lastname","msg" : get_api_message("edit_my_customer_profile" , "lastname_is_required" , member_lang)})
			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_customer_profile" , "email_is_required" , member_lang)})
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_customer_profile" , "tel_is_required" , member_lang)})

			if params['social_type']!="line" and params['social_type'] is not None:
				validate.append({"error_param" : "social_type","msg" : get_api_message("edit_my_customer_profile" , "social_type_is_invalid" , member_lang)})
			if params['social_type']=="line" and (params['social_id']=="" or params['social_type'] is None):
				validate.append({"error_param" : "social_id","msg" : get_api_message("edit_my_customer_profile" , "social_id_is_required" , member_lang)})

			#check already customer name
			if (params['member_firstname']!="" and params['member_firstname'] is not None) and (params['member_lastname']!="" and params['member_lastname'] is not None):
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_customer_name = db.member.find({
														"member_token": {"$ne": token},
														"member_type": "customer",
														"member_firstname_en": params['member_firstname'].strip().title(),
														"member_lastname_en": params['member_lastname'].strip().title()
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_my_customer_profile" , "firstname_and_lastname_has_been_used" , member_lang)})
			
			#check already email
			if params['member_email']!="" and params['member_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['member_email'])

				if len(check_format_email) > 0:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_email = db.member.find({
													"member_token": {"$ne": token},
													"member_type": "customer",
													"member_email": params['member_email'].strip().lower()
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_customer_profile" , "email_has_been_used" , member_lang)})
				else:
					validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_customer_profile" , "invalid_email_format" , member_lang)})		

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
					validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_customer_profile" , "invalid_tel_format" , member_lang)})

			#check already social
			if params['social_type']=="line" and params['social_id'] is not None:
				check_social_id = db.member.find({
													"member_token": {"$ne": token},
													"member_type": "customer",
													"social_type": "line",
													"social_id": params['social_id']
												}).count()
				if check_social_id > 0:
					validate.append({"error_param" : "social_id","msg" : get_api_message("send_customer_register" , "social_id_has_been_used" , member_lang)})

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				member = db.member.find_one({
												"member_token": token,
												"member_type": "customer"
											})
				if member is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("edit_my_customer_profile" , "data_not_found" , member_lang)
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

					if params['social_type']=="line" and params['social_id'] is not None:
						social_type = params['social_type']
						social_id = params['social_id']
					else:
						social_type = None
						social_id = None

					where_param = { "member_token": token }
					value_param = {
									"$set": {
												"member_firstname_en": params['member_firstname'].strip().title(),
												"member_lastname_en": params['member_lastname'].strip().title(),
												"member_firstname_th": params['member_firstname'].strip().title(),
												"member_lastname_th": params['member_lastname'].strip().title(),
												"member_email": params['member_email'].strip().lower(),
												"member_tel": params['member_tel'].strip(),
												"profile_image": image_name,
												"social_type": social_type,
												"social_id": social_id,
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

					if db.member.update(where_param , value_param):
						old_member_fullname = member_firstname+" "+member_lastname
						new_member_fullname = params['member_firstname']+" "+params['member_lastname']

						#ถ้าเป็น company user และ ชื่อ-นามสกุลเก่า ไม่ตรงกับ ชื่อ-นามสกุลใหม่ ให้ส่ง noti หา master admin และ admin company
						if company_id is not None:
							if member_firstname != params['member_firstname'] or member_lastname != params['member_lastname']:
								#ส่ง noti
								admin = db.member.find({
															"company_id": company_id,
															"company_user_type": {"$in" : ["2","1"]}
														})

								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								admin_object = dumps(admin)
								admin_json = json.loads(admin_object)

								noti_type = "change_customer_name"

								for i in range(len(admin_json)):
									#sent noti to member
									customer_info = get_member_info_by_id(admin_json[i]['_id']['$oid'])
									member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']

									noti_title_en = "System will inform that "+old_member_fullname
									noti_title_th = "ระบบขอแจ้งว่าคุณ "+old_member_fullname
									noti_message_en = "has changed the name to "+new_member_fullname
									noti_message_th = "ได้ทำการเปลี่ยนชื่อเป็น "+new_member_fullname

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
									send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "created_datetime" : created_datetime }
									send_noti_badge = 1

									#insert member_notification
									noti_detail = {
														"company_id": company_id,
														"old_member_fullname": old_member_fullname,
														"new_member_fullname": new_member_fullname
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
									email_type = "change_customer_name"
									subject = "VR Driver : แจ้งเตือนการเปลี่ยนชื่อของผู้ใช้งาน"
									to_email = admin_json[i]['member_email'].lower()
									template_html = "change_customer_name.html"
									data_detail = { "old_member_fullname" : old_member_fullname, "new_member_fullname" : new_member_fullname }	

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
									"msg" : get_api_message("edit_my_customer_profile" , "edit_profile_success" , member_lang)
								}
					else:
						result = {
								"status" : False,
								"msg" : get_api_message("edit_my_customer_profile" , "data_update_failed" , member_lang)
								}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("all" , "please_check_your_parameters_value"),
							"error_list" : validate
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "customer"
	function_name = "edit_my_customer_profile"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def package_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_lang = "member_lang" in params

	if isset_accept and isset_content_type and isset_app_version and isset_member_lang:
		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		#customer user
		if isset_token:
			#เช็ค token ว่า expire แล้วหรือยัง
			token = request.headers['Authorization']
			check_token = check_token_expire(token)

			if check_token:
				member_info = get_member_info(token)
				member_lang = member_info['member_lang']
				member_id = member_info['_id']['$oid']
				company_id = member_info['company_id']

				#ถ้าเป็น normal user
				if company_id is None:
					package_hour = db.package.find({
												"package_type": "hour",
												"package_status": "1",
												"special_company": {"$size": 0}
											}).sort([("created_at", -1)])

					package_time = db.package.find({
												"package_type": "time",
												"package_status": "1",
												"special_company": {"$size": 0}
											}).sort([("created_at", -1)])
				#ถ้าเป็น company user
				else:
					package_hour = db.package.find({
												"$or": [
													{"special_company": {"$size": 0}},
													{"special_company": company_id}
												]
												,
												"$and": [
													{"package_type": "hour"},
													{"package_status": "1"}
												]
											}).sort([("created_at", -1)])

					package_time = db.package.find({
												"$or": [
													{"special_company": {"$size": 0}},
													{"special_company": company_id}
												]
												,
												"$and": [
													{"package_type": "time"},
													{"package_status": "1"}
												]
											}).sort([("created_at", -1)])
						
				package_hour_list = []
				package_time_list = []
				
				if package_hour is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_hour_object = dumps(package_hour)
					package_hour_json = json.loads(package_hour_object)

					for i in range(len(package_hour_json)):
						if member_lang == "en":
							package_name = package_hour_json[i]['package_name_en']
						else:
							package_name = package_hour_json[i]['package_name_th']

						if package_hour_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if member_lang == "en":
							package_type_text = "Per Hour"
						else:
							package_type_text = "รายชั่วโมง"

						package_type_amount = package_hour_json[i]['hour_amount']
						
						package_hour_list.append({
							"package_id" : package_hour_json[i]['_id']['$oid'],
							"package_code": package_hour_json[i]['package_code'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": package_hour_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_type_amount": package_type_amount,
							"package_price": package_hour_json[i]['package_price'],
							"package_image": package_hour_json[i]['package_image']
						})

				if package_time is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_time_object = dumps(package_time)
					package_time_json = json.loads(package_time_object)

					for i in range(len(package_time_json)):
						if member_lang == "en":
							package_name = package_time_json[i]['package_name_en']
						else:
							package_name = package_time_json[i]['package_name_th']

						if package_time_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if member_lang == "en":
							package_type_text = "Per Time"
						else:
							package_type_text = "รายครั้ง"

						package_type_amount = package_time_json[i]['time_amount']

						package_time_list.append({
							"package_id" : package_time_json[i]['_id']['$oid'],
							"package_code": package_time_json[i]['package_code'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": package_time_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_type_amount": package_type_amount,
							"package_price": package_time_json[i]['package_price'],
							"package_image": package_time_json[i]['package_image']
						})

				result = {
							"status" : True,
							"msg" : get_api_message("package_list" , "get_package_list_success" , member_lang),
							"package_type_hour" : package_hour_list,
							"package_type_time" : package_time_list
						}
			else:
				result = { 
							"status" : False,
							"error_code" : 401,
							"msg" : get_api_message("all" , "unauthorized")
						}	
		#guest
		else:
			package_hour = db.package.find({
										"package_type": "hour",
										"package_status": "1",
										"special_company": {"$size": 0}
									}).sort([("created_at", -1)])

			package_time = db.package.find({
										"package_type": "time",
										"package_status": "1",
										"special_company": {"$size": 0}
									}).sort([("created_at", -1)])

			package_hour_list = []
			package_time_list = []
			
			if package_hour is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_hour_object = dumps(package_hour)
				package_hour_json = json.loads(package_hour_object)

				for i in range(len(package_hour_json)):
					if member_lang == "en":
						package_name = package_hour_json[i]['package_name_en']
					else:
						package_name = package_hour_json[i]['package_name_th']

					if package_hour_json[i]['package_model'] == "special":
						package_model = "Special"
					else:
						package_model = "Normal"

					if member_lang == "en":
						package_type_text = "Per Hour"
					else:
						package_type_text = "รายชั่วโมง"
						
					package_type_amount = package_hour_json[i]['hour_amount']

					package_hour_list.append({
						"package_id" : package_hour_json[i]['_id']['$oid'],
						"package_code": package_hour_json[i]['package_code'],
						"package_name": package_name,
						"package_model": package_model,
						"package_type": package_hour_json[i]['package_type'],
						"package_type_amount": package_type_amount,
						"package_type_text": package_type_text,
						"package_price": package_hour_json[i]['package_price'],
						"package_image": package_hour_json[i]['package_image']
					})

			if package_time is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_time_object = dumps(package_time)
				package_time_json = json.loads(package_time_object)

				for i in range(len(package_time_json)):
					if member_lang == "en":
						package_name = package_time_json[i]['package_name_en']
					else:
						package_name = package_time_json[i]['package_name_th']

					if package_time_json[i]['package_model'] == "special":
						package_model = "Special"
					else:
						package_model = "Normal"

					if member_lang == "en":
						package_type_text = "Per Time"
					else:
						package_type_text = "รายครั้ง"

					package_type_amount = package_time_json[i]['time_amount']

					package_time_list.append({
						"package_id" : package_time_json[i]['_id']['$oid'],
						"package_code": package_time_json[i]['package_code'],
						"package_name": package_name,
						"package_model": package_model,
						"package_type": package_time_json[i]['package_type'],
						"package_type_amount": package_type_amount,
						"package_type_text": package_type_text,
						"package_price": package_time_json[i]['package_price'],
						"package_image": package_time_json[i]['package_image']
					})

			result = {
						"status" : True,
						"msg" : get_api_message("package_list" , "get_package_list_success" , member_lang),
						"package_type_hour" : package_hour_list,
						"package_type_time" : package_time_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "package_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_detail(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params
	isset_member_lang = "member_lang" in params

	if isset_accept and isset_content_type and isset_app_version and isset_package_id and isset_member_lang:
		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		#customer user
		if isset_token:
			#เช็ค token ว่า expire แล้วหรือยัง
			token = request.headers['Authorization']
			check_token = check_token_expire(token)

			if check_token:
				member_info = get_member_info(token)
				member_lang = member_info['member_lang']
				member_id = member_info['_id']['$oid']

				package = db.package.find_one({
												"_id": ObjectId(params['package_id']),
												"package_status": "1"
											})
				if package is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("get_package_detail" , "data_not_found" , member_lang)
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					package_name = {
						"en" : package_json['package_name_en'],
						"th" : package_json['package_name_th']
					}

					if member_lang == "en":
						# package_name = package_json['package_name_en']
						package_detail = package_json['package_detail_en']
						package_condition = package_json['package_condition_en']

						if package_json['package_status'] == "1":
							package_status_show = "Active"
						else:
							package_status_show = "Inactive"

						if package_json['service_time'] == "weekday":
							service_time_text = "Weekday"
						elif package_json['service_time'] == "weekend":
							service_time_text = "Weekend"
						else:
							service_time_text = "All day"
					else:
						# package_name = package_json['package_name_th']
						package_detail = package_json['package_detail_th']
						package_condition = package_json['package_condition_th']

						if package_json['package_status'] == "1":
							package_status_show = "เปิดใช้งาน"
						else:
							package_status_show = "ปิดใช้งาน"

						if package_json['service_time'] == "weekday":
							service_time_text = "จันทร์-ศุกร์"
						elif package_json['service_time'] == "weekend":
							service_time_text = "เสาร์-อาทิตย์"
						else:
							service_time_text = "ทุกวัน"

					special_company = []
					
					#ถ้า special_company ไม่ใช่ array เปล่า
					if len(package_json['special_company']) > 0:
						company_in = []
						package_auth = "0"

						for i in range(len(package_json['special_company'])):
							company_in.append(ObjectId(package_json['special_company'][i]))

							#ถ้าเจอ company_id อยู่ใน special_company แสดงว่ามีสิทธิ์ใช้งานได้
							if member_info['company_id'] == package_json['special_company'][i]:
								package_auth = "1"

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
					else:
						package_auth = "1"

					communication_in = []
					for i in range(len(package_json['communication'])):
						communication_in.append(ObjectId(package_json['communication'][i]))

					communication = db.communication.find({"_id" : {"$in" : communication_in}})

					if communication is not None or communication.count() > 0:
						# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						communication_object = dumps(communication)
						communication_json = json.loads(communication_object)

						communication_data = []

						for j in range(len(communication_json)):
							if member_lang == "en":
								lang_name = communication_json[j]['lang_name_en']
							else:
								lang_name = communication_json[j]['lang_name_th']

							communication_data.append({
								"id" : communication_json[j]['_id']['$oid'],
								"name": lang_name,
								"image": communication_json[j]['flag_image']
							})

					data = {
								"package_id": package_json['_id']['$oid'],
								"package_code": package_json['package_code'],
								"package_name": package_name,
								"package_detail": package_detail,
								"package_condition": package_condition,
								"package_model": package_json['package_model'],
								"package_type": package_json['package_type'],
								"hour_amount": package_json['hour_amount'],
								"time_amount": package_json['time_amount'],
								"package_price": float(package_json['package_price']),
								"total_usage_date": package_json['total_usage_date'],
								"special_company": special_company,
								"service_time": package_json['service_time'],
								"service_time_text": service_time_text,
								"driver_level": package_json['driver_level'],
								"communication": package_json['communication'],
								"communication_data": communication_data,
								"normal_paid_rate": float(package_json['normal_paid_rate']),
								"normal_received_rate": float(package_json['normal_received_rate']),
								"overtime_paid_rate": float(package_json['overtime_paid_rate']),
								"overtime_received_rate": float(package_json['overtime_received_rate']),
								"package_status": package_json['package_status'],
								"package_status_show": package_status_show,
								"package_image": package_json['package_image'],
								"package_auth": package_auth
							}

					result = {
								"status" : True,
								"msg" : get_api_message("get_package_detail" , "get_package_detail_success" , member_lang),
								"data" : data
							}
			else:
				result = { 
					"status" : False,
					"error_code" : 401,
					"msg" : get_api_message("all" , "unauthorized")
				}
		#guest
		else:
			package = db.package.find_one({
											"_id": ObjectId(params['package_id']),
											"package_status": "1"
										})
			if package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_package_detail" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_object = dumps(package)
				package_json = json.loads(package_object)

				package_name = {
									"en" : package_json['package_name_en'],
									"th" : package_json['package_name_th']
								}

				if member_lang == "en":
					# package_name = package_json['package_name_en']
					package_detail = package_json['package_detail_en']
					package_condition = package_json['package_condition_en']

					if package_json['package_status'] == "1":
						package_status_show = "Active"
					else:
						package_status_show = "Inactive"

					if package_json['service_time'] == "weekday":
						service_time_text = "Weekday"
					elif package_json['service_time'] == "weekend":
						service_time_text = "Weekend"
					else:
						service_time_text = "All day"
				else:
					# package_name = package_json['package_name_th']
					package_detail = package_json['package_detail_th']
					package_condition = package_json['package_condition_th']

					if package_json['package_status'] == "1":
						package_status_show = "เปิดใช้งาน"
					else:
						package_status_show = "ปิดใช้งาน"

					if package_json['service_time'] == "weekday":
						service_time_text = "จันทร์-ศุกร์"
					elif package_json['service_time'] == "weekend":
						service_time_text = "เสาร์-อาทิตย์"
					else:
						service_time_text = "ทุกวัน"

				special_company = []
				
				#ถ้า special_company ไม่ใช่ array เปล่า
				if len(package_json['special_company']) > 0:
					company_in = []
					package_auth = "0"

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
				else:
					package_auth = "1"

				communication_in = []
				for i in range(len(package_json['communication'])):
					communication_in.append(ObjectId(package_json['communication'][i]))

				communication = db.communication.find({"_id" : {"$in" : communication_in}})

				if communication is not None or communication.count() > 0:
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					communication_object = dumps(communication)
					communication_json = json.loads(communication_object)

					communication_data = []

					for j in range(len(communication_json)):
						if member_lang == "en":
							lang_name = communication_json[j]['lang_name_en']
						else:
							lang_name = communication_json[j]['lang_name_th']

						communication_data.append({
							"id" : communication_json[j]['_id']['$oid'],
							"name": lang_name,
							"image": communication_json[j]['flag_image']
						})

				data = {
							"package_id": package_json['_id']['$oid'],
							"package_code": package_json['package_code'],
							"package_name": package_name,
							"package_detail": package_detail,
							"package_condition": package_condition,
							"package_model": package_json['package_model'],
							"package_type": package_json['package_type'],
							"hour_amount": package_json['hour_amount'],
							"time_amount": package_json['time_amount'],
							"package_price": float(package_json['package_price']),
							"total_usage_date": package_json['total_usage_date'],
							"special_company": special_company,
							"service_time": package_json['service_time'],
							"service_time_text": service_time_text,
							"driver_level": package_json['driver_level'],
							"communication": package_json['communication'],
							"communication_data": communication_data,
							"normal_paid_rate": float(package_json['normal_paid_rate']),
							"normal_received_rate": float(package_json['normal_received_rate']),
							"overtime_paid_rate": float(package_json['overtime_paid_rate']),
							"overtime_received_rate": float(package_json['overtime_received_rate']),
							"package_status": package_json['package_status'],
							"package_status_show": package_status_show,
							"package_image": package_json['package_image'],
							"package_auth": package_auth
						}

				result = {
							"status" : True,
							"msg" : get_api_message("get_package_detail" , "get_package_detail_success" , member_lang),
							"data" : data
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
				
	#set log detail
	user_type = "customer"
	function_name = "get_package_detail"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def order_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_order_status = "order_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_order_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			if params['order_status'] == "all":
				order_package = db.order_package.find({
													"member_id": member_info['_id']['$oid']
												}).sort([("created_at", -1)])
			else:
				order_package = db.order_package.find({
													"member_id": member_info['_id']['$oid'],
													"order_status": params['order_status']
												}).sort([("created_at", -1)])
				
			order_package_list = []
			
			if order_package is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_object = dumps(order_package)
				order_package_json = json.loads(order_package_object)

				for i in range(len(order_package_json)):
					if order_package_json[i]['order_status'] == "4":
						if member_lang == "en":
							order_status_text = "สั่งซื้อไม่สำเร็จ"
						else:
							order_status_text = "สั่งซื้อไม่สำเร็จ"
					elif order_package_json[i]['order_status'] == "3":
						if member_lang == "en":
							order_status_text = "ยกเลิกการสั่งซื้อ"
						else:
							order_status_text = "ยกเลิกการสั่งซื้อ"
					elif order_package_json[i]['order_status'] == "2":
						if member_lang == "en":
							order_status_text = "กำลังตรวจสอบการชำระเงิน"
						else:
							order_status_text = "กำลังตรวจสอบการชำระเงิน"
					elif order_package_json[i]['order_status'] == "1":
						if member_lang == "en":
							order_status_text = "สั่งซื้อสำเร็จ"
						else:
							order_status_text = "สั่งซื้อสำเร็จ"
					else:
						if member_lang == "en":
							order_status_text = "รอการแจ้งชำระเงิน"
						else:
							order_status_text = "รอการแจ้งชำระเงิน"

					#แปลง format วันที่
					order_datetime = datetime.strptime(order_package_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

					order_package_list.append({
						"order_id" : order_package_json[i]['_id']['$oid'],
						"order_no": order_package_json[i]['order_no'],
						"order_price": float(order_package_json[i]['order_price']), 
						"order_status": order_package_json[i]['order_status'],
						"order_status_text": order_status_text,
						"order_datetime": order_datetime
					})

			result = {
						"status" : True,
						"msg" : get_api_message("order_list" , "get_order_list_success" , member_lang),
						"data" : order_package_list
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "order_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_order_detail(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_order_id = "order_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_order_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			order_package = db.order_package.find_one({"_id": ObjectId(params['order_id'])})
			if order_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_order_detail" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_object = dumps(order_package)
				order_package_json = json.loads(order_package_object)

				if order_package_json['payment_list_id'] is not None:
					payment_list = db.payment_list.find_one({"_id": ObjectId(order_package_json['payment_list_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					payment_list_object = dumps(payment_list)
					payment_list_json = json.loads(payment_list_object)

					if member_lang == "en":
						payment_channel_name = payment_list_json['bank_name_en']
					else:
						payment_channel_name = payment_list_json['bank_name_th']

					if payment_list_json['transfer_amount'] is None:
						transfer_amount = None
					else:
						transfer_amount = payment_list_json['transfer_amount']

					if payment_list_json['transfer_date'] is None:
						transfer_date = None
					else:
						transfer_date = datetime.strptime(payment_list_json['transfer_date'], '%Y-%m-%d').strftime('%d/%m/%Y')

					if payment_list_json['transfer_time'] is None:
						transfer_time = None
					else:
						transfer_time = datetime.strptime(payment_list_json['transfer_time'], '%H:%M:%S').strftime('%H:%M')
				
					payment_channel_id = payment_list_json['payment_channel_id']
					transfer_slip = payment_list_json['transfer_slip']
					order_remark = payment_list_json['order_remark']

				else:
					payment_channel_name = None
					transfer_amount = None
					transfer_date = None
					transfer_time = None
					payment_channel_id = None
					transfer_slip = None
					order_remark = None

				order_detail = []
				order_price = 0
				order_price_not_vat = 0

				for i in range(len(order_package_json['order_detail'])):
					if member_lang == "en":
						package_name = order_package_json['order_detail'][i]['package_name_en']
					else:
						package_name = order_package_json['order_detail'][i]['package_name_th']

					order_detail.append({
						"package_id" : order_package_json['order_detail'][i]['package_id'],
						"package_name": package_name,
						"package_type": order_package_json['order_detail'][i]['package_type'], 
						"package_type_amount": order_package_json['order_detail'][i]['package_type_amount'],
						"package_amount": order_package_json['order_detail'][i]['package_amount'],
						"package_price": float(order_package_json['order_detail'][i]['package_price'])
					})

				if order_package_json['order_status'] == "4":
					if member_lang == "en":
						order_status_text = "สั่งซื้อไม่สำเร็จ"
					else:
						order_status_text = "สั่งซื้อไม่สำเร็จ"
				elif order_package_json['order_status'] == "3":
					if member_lang == "en":
						order_status_text = "ยกเลิกการสั่งซื้อ"
					else:
						order_status_text = "ยกเลิกการสั่งซื้อ"
				elif order_package_json['order_status'] == "2":
					if member_lang == "en":
						order_status_text = "กำลังตรวจสอบการชำระเงิน"
					else:
						order_status_text = "กำลังตรวจสอบการชำระเงิน"
				elif order_package_json['order_status'] == "1":
					if member_lang == "en":
						order_status_text = "สั่งซื้อสำเร็จ"
					else:
						order_status_text = "สั่งซื้อสำเร็จ"
				else:
					if member_lang == "en":
						order_status_text = "รอการแจ้งชำระเงิน"
					else:
						order_status_text = "รอการแจ้งชำระเงิน"

				#แปลง format วันที่
				order_datetime = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

				data = {
							"order_id": order_package_json['_id']['$oid'],
							"member_id": order_package_json['member_id'],
							"order_no": order_package_json['order_no'],
							"order_detail": order_detail,
							"order_price": float(order_package_json['order_price']),
							"order_price_not_vat": float(order_package_json['order_price_not_vat']),
							"order_vat": float(order_package_json['order_vat']),
							"payment_channel_id": payment_channel_id,
							"payment_channel_name": payment_channel_name,
							"transfer_amount": transfer_amount,
							"transfer_date": transfer_date,
							"transfer_time": transfer_time,
							"transfer_slip": transfer_slip,
							"order_status": order_package_json['order_status'],
							"order_status_text": order_status_text,
							"order_remark": order_remark,
							"order_datetime": order_datetime
						}

				result = {
							"status" : True,
							"msg" : get_api_message("get_order_detail" , "get_order_detail_success" , member_lang),
							"data" : data
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_order_detail"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_order(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_order_detail = "order_detail" in params
	isset_os_type = "os_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_order_detail and isset_os_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			if member_info['member_status'] == "0":
				result = {
							"status" : False,
							"msg" : get_api_message("add_order" , "please_check_your_member_status" , member_lang)
						}
			else:
				customer_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
				company_name = None

				if member_info['company_name'] is not None:
					company_name = member_info['company_name']

				#ดึง order_no ล่าสุดจาก tb order_package แล้วเอามา +1
				order_package = db.order_package.find_one(sort=[("order_no", -1)])
				oid = 1

				if order_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					order_package_object = dumps(order_package)
					order_package_json = json.loads(order_package_object)
					oid = int(order_package_json["order_no"][3:10])+1

				order_no = "VRD"+"%07d" % oid
				order_price = 0
				order_vat = 0
				order_price_not_vat = 0

				#set order_detail
				order_detail_list = []
				for i in range(len(params['order_detail'])):
					package = db.package.find_one({"_id": ObjectId(params['order_detail'][i]['package_id'])})
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					if package_json['package_type'] == "hour":
						package_type_amount = int(package_json['hour_amount'])
					else:
						package_type_amount = int(package_json['time_amount'])

					order_detail_list.append({
						"package_id" : params['order_detail'][i]['package_id'],
						"package_code": package_json['package_code'],
						"package_name_en": package_json['package_name_en'],
						"package_name_th": package_json['package_name_th'],
						"package_detail_en": package_json['package_detail_en'],
						"package_detail_th": package_json['package_detail_th'],
						"package_condition_en": package_json['package_condition_en'],
						"package_condition_th": package_json['package_condition_th'],
						"package_model": package_json['package_model'],
						"package_type": package_json['package_type'],
						"package_type_amount": package_type_amount,
						"total_usage_date": int(package_json['total_usage_date']),
						"special_company": package_json['special_company'],
						"service_time": package_json['service_time'],
						"driver_level": package_json['driver_level'],
						"communication": package_json['communication'],
						"communication_en": package_json['communication_en'],
						"communication_th": package_json['communication_th'],
						"normal_paid_rate": float(package_json['normal_paid_rate']),
						"normal_received_rate": float(package_json['normal_received_rate']),
						"overtime_paid_rate": float(package_json['overtime_paid_rate']),
						"overtime_received_rate": float(package_json['overtime_received_rate']),
						"package_image": package_json['package_image'],
						"package_amount": int(params['order_detail'][i]['package_amount']),
						"package_price": float(package_json['package_price']),
						"package_price_not_vat": float(package_json['package_price_not_vat']),
						"package_price_vat": float(package_json['package_price_vat']),
						"vat_rate": float(package_json['vat_rate'])
					})

					order_price = order_price + (float(package_json['package_price']) * params['order_detail'][i]['package_amount'])
					# order_vat = order_vat + ((package_json['package_price'] * package_json['vat_rate']) / 100)
					# order_price_not_vat = order_price_not_vat + (package_json['package_price'] - package_json['vat_rate'])

				vat_rate = float(package_json['vat_rate'])
				order_vat = (order_price * vat_rate) / 100
				order_price_not_vat = order_price - order_vat

				if params['os_type'] == "web":
					purchase_channel = "web"
				else:
					purchase_channel = "app"

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				order_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				order_id_string = str(order_id)

				#แปลง format วันที่
				created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				purchase_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))
				
				data = { 
							"_id": order_id,
							"member_id": member_info['_id']['$oid'],
							"customer_name": customer_name,
							"company_name": company_name,
							"order_no": order_no,
							"order_detail": order_detail_list,
							"order_price": order_price,
							"order_price_not_vat": order_price_not_vat,
							"order_vat": order_vat,
							"payment_list_id": None,
							"transfer_amount": None,
							"transfer_amount_text": None,
							"order_status": "0",
							"order_remark": None,
							"os_type": params['os_type'],
							"purchase_channel": purchase_channel,
							"purchase_date_int": purchase_date_int,
							"created_at": created_at,
							"updated_at": created_at
						}

				if db.order_package.insert_one(data):
					result = {
								"status" : True,
								"msg" : get_api_message("add_order" , "add_order_success" , member_lang),
								"order_id" : order_id_string
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("add_order" , "order_insert_failed" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "add_order"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def cancel_order(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_order_id = "order_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_order_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['order_id']) }
			value_param = {
							"$set":
								{
									"order_status": "3",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.order_package.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("cancel_order" , "cancel_order_success" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("cancel_order" , "data_update_failed" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "cancel_order"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def confirm_order_payment(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_order_id = "order_id" in params
	isset_payment_channel_id = "payment_channel_id" in params
	isset_transfer_amount = "transfer_amount" in params
	isset_transfer_date = "transfer_date" in params
	isset_transfer_time = "transfer_time" in params
	isset_transfer_slip = "transfer_slip" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_order_id and isset_payment_channel_id and isset_transfer_amount and isset_transfer_date and isset_transfer_time and isset_transfer_slip:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			order_package = db.order_package.find_one({"_id": ObjectId(params['order_id'])})

			if order_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("confirm_order_payment" , "order_package_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				order_package_object = dumps(order_package)
				order_package_json = json.loads(order_package_object)
				order_no = order_package_json['order_no']
				transfer_amount = float(params['transfer_amount'])
				transfer_amount_text = str(params['transfer_amount'])
				tf_amount = '{:,.2f}'.format(round(float(params['transfer_amount']) , 2))
				
				#เฉพาะ order_status รอการแจ้งชำระเงิน หรือ ไม่อนุมัติ เท่านั้น
				if order_package_json['order_status'] == "0" or order_package_json['order_status'] == "4":
					payment_channel = db.payment_channel.find_one({
																	"_id": ObjectId(params['payment_channel_id']),
																	"account_status": "1"
																})

					if payment_channel is None:
						result = { 
									"status" : False,
									"msg" : get_api_message("confirm_order_payment" , "payment_channel_not_found" , member_lang)
								}
					else:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						payment_channel_object = dumps(payment_channel)
						payment_channel_json = json.loads(payment_channel_object)

						bank_name_en = payment_channel_json['bank_name_en']
						bank_name_th = payment_channel_json['bank_name_th']

						if params['transfer_slip'] is None:
							transfer_slip = None
						else:
							#generate token
							generate_token = get_random_token(40)
							check_upload_image = upload_transfer_slip(params['transfer_slip'], generate_token)

							if check_upload_image is None:
								transfer_slip = None
							else:
								transfer_slip = check_upload_image

						transfer_date = datetime.strptime(params['transfer_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
						transfer_time = datetime.strptime(params['transfer_time'], '%H:%M').strftime('%H:%M:%S')

						#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
						payment_list_id = ObjectId()
						#แปลง ObjectId ให้เป็น string
						payment_list_id_string = str(payment_list_id)


						member_info = get_member_info_by_id(order_package_json['member_id'])
						customer_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						company_name = None

						if member_info['company_name'] is not None:
							company_name = member_info['company_name']

						if order_package_json['os_type'] is not None:
							if order_package_json['os_type'] == "ios" or order_package_json['os_type'] == "android":
								purchase_channel = "app"
							else:
								purchase_channel = "web"
						else:
							purchase_channel = "web"

						purchase_date_int = int(datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))
						purchase_date = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
						purchase_time = datetime.strptime(order_package_json['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')

						order_price = float(order_package_json['order_price'])


						data = { 
								"_id": payment_list_id,
								"order_id": params['order_id'],
								"order_no": order_package_json['order_no'],
								"order_price": order_price,
								"purchase_date_int" : purchase_date_int,
								"purchase_date": purchase_date,
								"purchase_time": purchase_time,
								"purchase_channel": purchase_channel,
								"company_name": company_name,
								"customer_name": customer_name,
								"os_type" : order_package_json['os_type'],

								"payment_channel_id": params['payment_channel_id'],
								"bank_name_en": bank_name_en,
								"bank_name_th": bank_name_th,
								"transfer_amount": transfer_amount,
								"transfer_amount_text" : transfer_amount_text,
								"transfer_date": transfer_date,
								"transfer_time": transfer_time,
								"transfer_slip": transfer_slip,
								"order_status": "2",
								"order_remark": None,
								"payment_status": "1",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

						if db.payment_list.insert_one(data):
							# update data
							where_param = { "_id": ObjectId(params['order_id']) }
							value_param = {
											"$set":
												{
													"payment_list_id": payment_list_id_string,
													"transfer_amount": transfer_amount,
													"transfer_amount_text": transfer_amount_text,
													"order_status": "2",
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.order_package.update(where_param , value_param):
								noti_title_en = "Payment notification"
								noti_title_th = "มีการแจ้งชำระเงิน"
								noti_message_en = "order no : "+order_no+" amount "+tf_amount+" baht."
								noti_message_th = "เลขที่สั่งซื้อ "+order_no+" ยอด "+tf_amount+" บาท"

								#insert admin_notification
								noti_type = "confirm_order_payment"
								noti_detail = {
													"order_id": params['order_id'],
													"order_no": order_no,
													"transfer_amount": transfer_amount,
													"payment_list_id": payment_list_id_string
												}

								data_admin = { 
												"noti_type": noti_type,
												"noti_title_en": noti_title_en,
												"noti_title_th": noti_title_th,
												"noti_message_en": noti_message_en,
												"noti_message_th": noti_message_th,
												"noti_detail": noti_detail,
												"noti_status": "0",
												"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
								db.admin_notification.insert_one(data_admin)

								result = {
										"status" : True,
										"msg" : get_api_message("confirm_order_payment" , "confirm_order_payment_success" , member_lang)
									}
							else:
								result = {
										"status" : False,
										"msg" : get_api_message("confirm_order_payment" , "data_update_failed" , member_lang)
									}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("confirm_order_payment" , "data_insert_failed" , member_lang)
									}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("confirm_order_payment" , "order_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "confirm_order_payment"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def payment_channel_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			payment_channel = db.payment_channel.find({"account_status": "1"})
			payment_channel_list = []

			if payment_channel is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				payment_channel_object = dumps(payment_channel)
				payment_channel_json = json.loads(payment_channel_object)

				payment_channel_list = []

				for i in range(len(payment_channel_json)):
					if member_lang == "en":
						bank_name = payment_channel_json[i]['bank_name_en']
					else:
						bank_name = payment_channel_json[i]['bank_name_th']

					payment_channel_list.append({
						"payment_channel_id" : payment_channel_json[i]['_id']['$oid'],
						"account_name": payment_channel_json[i]['account_name'],
						"account_number": payment_channel_json[i]['account_number'],
						"bank_name": bank_name,
						"bank_logo": payment_channel_json[i]['bank_logo']
					})

			result = {
						"status" : True,
						"msg" : get_api_message("payment_channel_list" , "get_payment_channel_success" , member_lang),
						"data" : payment_channel_list
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "payment_channel_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def my_package_list_customer(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_start_date = "start_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_start_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if params['start_date'] is None:
				package = db.member_package.aggregate([
														{
															"$match": {
																"member_id": member_info['_id']['$oid'],
																"member_package_status": "1"
															}
														},
														{
															"$group" : {
																"_id" : "$package_id"
															}
														}
													])
			else:
				start_date_obj = datetime.strptime(params['start_date'], '%d/%m/%Y')
				start_workday = start_date_obj.strftime('%a')

				#weekend
				if start_workday == "Sun" or start_workday == "Sat":
					service_time_in = ["allday" , "weekend"]
				#weekday
				else:
					service_time_in = ["allday" , "weekday"]

				package = db.member_package.aggregate([
														{
															"$match": {
																"member_id": member_info['_id']['$oid'],
																"service_time": {"$in": service_time_in},
																"member_package_status": "1"
															}
														},
														{
															"$group" : {
																"_id" : "$package_id"
															}
														}
													])
			

			package_list = []
			
			if package is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_object = dumps(package)
				package_json = json.loads(package_object)

				for i in range(len(package_json)):
					member_package = db.member_package.find({
															"member_id": member_info['_id']['$oid'],
															"package_id": package_json[i]['_id'],
															"member_package_status": "1"
														})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					
					remaining_package_list = []
					min_remaining_date = 0

					for j in range(len(member_package_json)):
						end_date = datetime.strptime(member_package_json[j]['end_date'], '%Y-%m-%d')
						today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
						
						delta = end_date - today
						remaining_date = delta.days

						if remaining_date >= 0:
							#***#
							if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
								company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								company_package_object = dumps(company_package)
								company_package_json = json.loads(company_package_object)

								remaining_amount = company_package_json['remaining_amount']
							else:
								remaining_amount = member_package_json[j]['remaining_amount']

							remaining_package_list.append({
								"member_package_id" : member_package_json[j]['_id']['$oid'],
								"remaining_date" : remaining_date,
								"remaining_amount" : remaining_amount
							})

							if min_remaining_date == 0:
								min_remaining_date = remaining_date
							else:
								if min_remaining_date <= remaining_date:
									min_remaining_date = min_remaining_date
								else:
									min_remaining_date = remaining_date

					if len(remaining_package_list) > 0:
						if member_lang == "en":
							package_name = member_package_json[j]['package_name_en']
						else:
							package_name = member_package_json[j]['package_name_th']

						if member_package_json[j]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if member_package_json[j]['package_type'] == "hour":
							if member_lang == "en":
								package_type_text = "Per Hour"
							else:
								package_type_text = "รายชั่วโมง"
						else:
							if member_lang == "en":
								package_type_text = "Per Time"
							else:
								package_type_text = "รายครั้ง"

						package_type_amount = member_package_json[j]['package_type_amount']
					
						package_list.append({
							"package_id": member_package_json[j]['package_id'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": member_package_json[j]['package_type'],
							"package_type_text": package_type_text,
							"total_usage_date": member_package_json[j]['total_usage_date'],
							"package_type_amount": package_type_amount,
							"package_image": member_package_json[j]['package_image'],
							"remaining_package": remaining_package_list,
							"min_remaining_date": min_remaining_date
						})

				package_list.sort(key=lambda x: x.get('min_remaining_date'))

			result = {
						"status" : True,
						"msg" : get_api_message("my_package_list_customer" , "get_my_package_list_success" , member_lang),
						"data" : package_list
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "my_package_list_customer"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def personal_car_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_start_date = "start_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_start_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			car = db.car.find({
								"car_group": "personal",
								"member_id": member_info['_id']['$oid'],
								"car_status": "1"
							})
			car_list = []

			if params['start_date'] is not None:
				#แปลง format วันที่
				start_date = datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
			
			if car is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				for i in range(len(car_json)):
					if params['start_date'] is not None:
						#เช็คว่ามีรถที่ถูกใช้งานในวันและเวลาที่ระบุมาหรือไม่
						check_car = db.request_driver.find({
																"car_id": car_json[i]['_id']['$oid'],
																"start_date": start_date,
																"request_status": {"$nin" : ["2"]}
															}).count()
					else:
						check_car = 0

					#ถ้าไม่เจอข้อมูลการใช้รถ แสดงว่าสามารถใช้รถคันนั้นได้
					if check_car == 0:
						car_type = db.car_type.find_one({"_id": ObjectId(car_json[i]['car_type_id'])})
						car_brand = db.car_brand.find_one({"_id": ObjectId(car_json[i]['car_brand_id'])})
						car_gear = db.car_gear.find_one({"_id": ObjectId(car_json[i]['car_gear_id'])})
						car_engine = db.car_engine.find_one({"_id": ObjectId(car_json[i]['car_engine_id'])})

						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						car_type_object = dumps(car_type)
						car_type_json = json.loads(car_type_object)

						car_brand_object = dumps(car_brand)
						car_brand_json = json.loads(car_brand_object)

						car_gear_object = dumps(car_gear)
						car_gear_json = json.loads(car_gear_object)

						car_engine_object = dumps(car_engine)
						car_engine_json = json.loads(car_engine_object)

						if member_lang == "en":
							car_type_name = car_type_json['car_type_name_en']
							car_brand_name = car_brand_json['brand_name']
							car_gear_name = car_gear_json['car_gear_en']
							car_engine_name = car_engine_json['car_engine_en']
							car_group_text = "Personal car"
						else:
							car_type_name = car_type_json['car_type_name_th']
							car_brand_name = car_brand_json['brand_name']
							car_gear_name = car_gear_json['car_gear_th']
							car_engine_name = car_engine_json['car_engine_th']
							car_group_text = "รถส่วนตัว"

						car_list.append({
							"car_id" : car_json[i]['_id']['$oid'],
							"member_id": car_json[i]['member_id'],
							"car_type_id": car_json[i]['car_type_id'],
							"car_type_name": car_type_name,
							"car_brand_id": car_json[i]['car_brand_id'],
							"car_brand_name": car_brand_name,
							"car_gear_id": car_json[i]['car_gear_id'],
							"car_gear_name": car_gear_name,
							"car_engine_id": car_json[i]['car_engine_id'],
							"car_engine_name": car_engine_name,
							"license_plate": car_json[i]['license_plate'],
							"car_group": car_json[i]['car_group'],
							"car_group_text": car_group_text,
							"car_image": car_json[i]['car_image']
						})

			result = {
						"status" : True,
						"msg" : get_api_message("personal_car_list" , "get_personal_car_list_success" , member_lang),
						"data" : car_list
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "personal_car_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_form(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			car_type = db.car_type.find()
			car_gear = db.car_gear.find({"car_gear_status": "1"})
			car_engine = db.car_engine.find({"car_engine_status": "1"})

			if car_type is None or car_gear is None or car_engine is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_car_form" , "please_check_your_master_data_in_database" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				car_gear_object = dumps(car_gear)
				car_gear_json = json.loads(car_gear_object)

				car_engine_object = dumps(car_engine)
				car_engine_json = json.loads(car_engine_object)

				car_type_list = []
				car_gear_list = []
				car_engine_list = []

				for i in range(len(car_type_json)):
					if member_lang == "en":
						car_type_name = car_type_json[i]['car_type_name_en']
					else:
						car_type_name = car_type_json[i]['car_type_name_th']

					car_type_list.append({
						"car_type_id" : car_type_json[i]['_id']['$oid'],
						"car_type_name": car_type_name
					})

				for j in range(len(car_gear_json)):
					if member_lang == "en":
						car_gear_name = car_gear_json[j]['car_gear_en']
					else:
						car_gear_name = car_gear_json[j]['car_gear_th']

					car_gear_list.append({
						"car_gear_id" : car_gear_json[j]['_id']['$oid'],
						"car_gear_name": car_gear_name
					})

				for k in range(len(car_engine_json)):
					if member_lang == "en":
						car_engine_name = car_engine_json[k]['car_engine_en']
					else:
						car_engine_name = car_engine_json[k]['car_engine_th']

					car_engine_list.append({
						"car_engine_id" : car_engine_json[k]['_id']['$oid'],
						"car_engine_name": car_engine_name
					})

				if member_lang == "en":
					car_status_0 = "Inactive"
					car_status_1 = "Active"
				else:
					car_status_0 = "ปิดใช้งาน"
					car_status_1 = "เปิดใช้งาน"

				car_status_list = [
										{"code": "0","name": car_status_0},
										{"code": "1","name": car_status_1}
									]

				result = {
							"status" : True,
							"msg" : get_api_message("get_car_form" , "get_car_form_success" , member_lang),
							"car_type" : car_type_list,
							"car_gear" : car_gear_list,
							"car_engine" : car_engine_list,
							"car_status" : car_status_list
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_car_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_brand(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type_id = "car_type_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_type_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			car_brand = db.car_brand.find({
											"car_type_id": params['car_type_id'],
											"brand_status": "1"
										})

			if car_brand is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_car_brand" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_brand_object = dumps(car_brand)
				car_brand_json = json.loads(car_brand_object)

				car_brand_list = []

				for i in range(len(car_brand_json)):
					car_brand_list.append({
						"car_brand_id" : car_brand_json[i]['_id']['$oid'],
						"car_brand_name": car_brand_json[i]['brand_name']
					})

				result = {
							"status" : True,
							"msg" : get_api_message("get_car_brand" , "get_car_brand_success" , member_lang),
							"data" : car_brand_list
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_car_brand"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_personal_car(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type_id = "car_type_id" in params
	isset_car_brand_id = "car_brand_id" in params
	isset_car_gear_id = "car_gear_id" in params
	isset_car_engine_id = "car_engine_id" in params
	isset_license_plate = "license_plate" in params
	isset_car_image = "car_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_type_id and isset_car_brand_id and isset_car_gear_id and isset_car_engine_id and isset_license_plate and isset_car_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check license plate format
			pattern = pattern = r'[ก-ฮ0-9 ]+'
			regex = re.compile(pattern)
			check_format_license_plate = regex.findall(params['license_plate'])

			if len(check_format_license_plate) > 0:
				check_car = db.car.find({
											"license_plate": params['license_plate'].strip()
										}).count()

				if check_car > 0:
					validate.append({"error_param" : "license_plate","msg" : get_api_message("add_personal_car" , "car_has_been_used" , member_lang)})

					result = {
								"status" : False,
								"msg" : get_api_message("add_personal_car" , "car_has_been_used" , member_lang),
								"error_list" : validate
							}
				else:
					if params['car_image'] is None:
						image_name = None
					else:
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_car_image(params['car_image'], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

					data = { 
								"car_group": "personal",
								"company_id": None,
								"member_id": member_info['_id']['$oid'],
								"car_type_id": params['car_type_id'],
								"car_brand_id": params['car_brand_id'],
								"car_gear_id": params['car_gear_id'],
								"car_engine_id": params['car_engine_id'],
								"license_plate": params['license_plate'].strip(),
								"car_image": image_name,
								"car_status": "1",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

					if db.car.insert_one(data):
						result = {
									"status" : True,
									"msg" : get_api_message("add_personal_car" , "add_personal_car_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("add_personal_car" , "data_insert_failed" , member_lang)
								}
			else:
				validate.append({"error_param" : "license_plate","msg" : get_api_message("add_personal_car" , "invalid_license_plate_format" , member_lang)})

				result = {
							"status" : False,
							"msg" : get_api_message("add_personal_car" , "invalid_license_plate_format" , member_lang),
							"error_list" : validate
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "add_personal_car"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_personal_car(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_id = "car_id" in params
	isset_car_type_id = "car_type_id" in params
	isset_car_brand_id = "car_brand_id" in params
	isset_car_gear_id = "car_gear_id" in params
	isset_car_engine_id = "car_engine_id" in params
	isset_license_plate = "license_plate" in params
	isset_car_image = "car_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_id and isset_car_type_id and isset_car_brand_id and isset_car_gear_id and isset_car_engine_id and isset_license_plate and isset_car_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check license plate format
			pattern = pattern = r'[ก-ฮ0-9 ]+'
			regex = re.compile(pattern)
			check_format_license_plate = regex.findall(params['license_plate'])

			if len(check_format_license_plate) > 0:
				check_car = db.car.find({
											"_id": {"$ne": ObjectId(params['car_id'])},
											"license_plate": params['license_plate']
										}).count()

				if check_car > 0:
					validate.append({"error_param" : "license_plate","msg" : get_api_message("edit_personal_car" , "car_has_been_used" , member_lang)})

					result = {
								"status" : False,
								"msg" : get_api_message("edit_personal_car" , "car_has_been_used" , member_lang),
								"error_list" : validate
							}
				else:
					car = db.car.find_one({"_id": ObjectId(params['car_id'])})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_object = dumps(car)
					car_json = json.loads(car_object)

					#ถ้าไม่มีการแก้ไขรูปรถ (car_image เป็น null) ไม่ต้องอัพเดตรูป  
					if params['car_image'] is None:
						image_name = car_json['car_image']
					else:
						#เช็ค path และลบรูปเก่า
						if car_json['car_image'] is not None:
							if os.path.exists("static/images/car/"+car_json['car_image']):
								os.remove("static/images/car/"+car_json['car_image'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_car_image(params['car_image'], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

					# if params['car_status'] is None:
					# 	car_status = car_json['car_status']
					# elif params['car_status'] == "0":
					# 	car_status = "0"
					# else:
					# 	car_status = "1"

					# update data
					where_param = { "_id": ObjectId(params['car_id']) }
					value_param = {
									"$set":
										{
											"car_type_id": params['car_type_id'],
											"car_brand_id": params['car_brand_id'],
											"car_gear_id": params['car_gear_id'],
											"car_engine_id": params['car_engine_id'],
											"license_plate": params['license_plate'].strip(),
											"car_image": image_name,
											# "car_status": car_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.car.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : get_api_message("edit_personal_car" , "edit_personal_car_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_personal_car" , "data_update_failed" , member_lang)
								}
			else:
				validate.append({"error_param" : "license_plate","msg" : get_api_message("edit_personal_car" , "invalid_license_plate_format" , member_lang)})

				result = {
							"status" : False,
							"msg" : get_api_message("edit_personal_car" , "invalid_license_plate_format" , member_lang),
							"error_list" : validate
						}	
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "edit_personal_car"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_personal_car(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_id = "car_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			
			# update data
			where_param = { "_id": ObjectId(params['car_id']) } 
			value_param = {
							"$set":
								{
									"car_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.car.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("delete_personal_car" , "delete_personal_car_success" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("delete_personal_car" , "data_update_failed" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "delete_personal_car"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def location_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			location = db.location.find({
											"member_id": member_info['_id']['$oid'],
											"location_status": "1"
										})
			location_list = []

			if location is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				location_object = dumps(location)
				location_json = json.loads(location_object)

				for i in range(len(location_json)):
					province = db.province.find_one({"province_code": location_json[i]['location_province_code']})
					district = db.district.find_one({"district_code": location_json[i]['location_district_code']})
					sub_district = db.sub_district.find_one({"sub_district_code": location_json[i]['location_sub_district_code']})
					
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					province_object = dumps(province)
					province_json = json.loads(province_object)

					district_object = dumps(district)
					district_json = json.loads(district_object)

					sub_district_object = dumps(sub_district)
					sub_district_json = json.loads(sub_district_object)

					if member_lang == "en":
						location_province_name = province_json['province_en']
						location_district_name = district_json['district_en']
						location_sub_district_name = sub_district_json['sub_district_en']
					else:
						if location_json[i]['location_province_code'] == "10":
							location_province_name = province_json['province_th']
							location_district_name = "เขต" + district_json['district_th']
							location_sub_district_name = "แขวง" + sub_district_json['sub_district_th']
						else:
							location_province_name = "จังหวัด" + province_json['province_th']
							location_district_name = "อำเภอ" + district_json['district_th']
							location_sub_district_name = "ตำบล" + sub_district_json['sub_district_th']

					location_list.append({
						"location_id" : location_json[i]['_id']['$oid'],
						"member_id": location_json[i]['member_id'],
						"location_name": location_json[i]['location_name'],
						"location_address": location_json[i]['location_address'],
						"location_postcode": location_json[i]['location_postcode'],
						"location_province_code": location_json[i]['location_province_code'],
						"location_province_name": location_province_name,
						"location_district_code": location_json[i]['location_district_code'],
						"location_district_name": location_district_name,
						"location_sub_district_code": location_json[i]['location_sub_district_code'],
						"location_sub_district_name": location_sub_district_name,
						"location_latitude": location_json[i]['location_latitude'],
						"location_longitude": location_json[i]['location_longitude']
					})

			result = {
						"status" : True,
						"msg" : get_api_message("location_list" , "get_location_list_success" , member_lang),
						"data" : location_list
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "location_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_location_name = "location_name" in params
	isset_location_address = "location_address" in params
	isset_location_postcode = "location_postcode" in params
	isset_location_province_code = "location_province_code" in params
	isset_location_district_code = "location_district_code" in params
	isset_location_sub_district_code = "location_sub_district_code" in params
	isset_location_latitude = "location_latitude" in params
	isset_location_longitude = "location_longitude" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_location_name and isset_location_address and isset_location_postcode and isset_location_province_code and isset_location_district_code and isset_location_sub_district_code and isset_location_latitude and isset_location_longitude:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			data = { 
						"member_id": member_info['_id']['$oid'],
						"location_name": params['location_name'].strip(),
						"location_address": params['location_address'].strip(),
						"location_postcode": params['location_postcode'],
						"location_province_code": params['location_province_code'],
						"location_district_code": params['location_district_code'],
						"location_sub_district_code": params['location_sub_district_code'],
						"location_latitude": params['location_latitude'],
						"location_longitude": params['location_longitude'],
						"location_status": "1",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}

			if db.location.insert_one(data):
				result = {
							"status" : True,
							"msg" : get_api_message("add_location" , "add_location_success" , member_lang)
						}
			else:
				result = {
						"status" : False,
						"msg" : get_api_message("add_location" , "data_insert_failed" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "add_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_location_id = "location_id" in params
	isset_location_name = "location_name" in params
	isset_location_address = "location_address" in params
	isset_location_postcode = "location_postcode" in params
	isset_location_province_code = "location_province_code" in params
	isset_location_district_code = "location_district_code" in params
	isset_location_sub_district_code = "location_sub_district_code" in params
	isset_location_latitude = "location_latitude" in params
	isset_location_longitude = "location_longitude" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_location_id and isset_location_name and isset_location_address and isset_location_postcode and isset_location_province_code and isset_location_district_code and isset_location_sub_district_code and isset_location_latitude and isset_location_longitude:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			check_location = db.location.find({
												"_id": {"$ne": ObjectId(params['location_id'])},
												"location_name": params['location_name']
											}).count()

			if check_location > 0:
				result = {
							"status" : False,
							"msg" : get_api_message("edit_location" , "location_has_been_used" , member_lang)
						}
			else:
				# update data
				where_param = { "_id": ObjectId(params['location_id']) }
				value_param = {
								"$set":
									{
										"location_name": params['location_name'].strip(),
										"location_address": params['location_address'].strip(),
										"location_postcode": params['location_postcode'],
										"location_province_code": params['location_province_code'],
										"location_district_code": params['location_district_code'],
										"location_sub_district_code": params['location_sub_district_code'],
										"location_latitude": params['location_latitude'],
										"location_longitude": params['location_longitude'],
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.location.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : get_api_message("edit_location" , "edit_location_success" , member_lang)
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("edit_location" , "data_update_failed" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "edit_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_location_id = "location_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_location_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['location_id']) }
			value_param = {
							"$set":
								{
									"location_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.location.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("delete_location" , "delete_location_success" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("delete_location" , "data_update_failed" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "delete_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def request_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_status = "request_status" in params
	isset_request_start_at = "request_start_at" in params
	isset_request_length = "request_length" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_status and isset_request_start_at and isset_request_length:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			try:
				request_start_at = int(params['request_start_at'])
				check_request_start_at = True
			except ValueError:
				check_request_start_at = False

			try:
				request_length = int(params['request_length'])
				check_request_length = True
			except ValueError:
				check_request_length = False


			if not check_request_start_at:
				result = { 
						"status" : False,
						"msg" : get_api_message("request_list" , "request_start_at_is_not_a_number" , member_lang)
					}
			elif not check_request_length:
				result = { 
						"status" : False,
						"msg" : get_api_message("request_list" , "request_length_is_not_a_number" , member_lang)
					}
			else:
				#ถ้า request_status = null ให้ดึงสถานะทั้งหมดมาแสดง
				if params['request_status'] is None:
					request_driver = db.request_driver.find({
																"$or": [
																	{ "member_id": member_id },
																	{ "passenger_id": member_id }
																]
															}).sort([("created_at", -1)]).skip(request_start_at).limit(request_length)
				#ถ้า request_status = "1" ให้ดึงสถานะ ตอบรับแล้ว ("1") และ งานที่ใกล้จะถึง ("4") มาแสดง
				elif params['request_status'] == "1":
					request_driver = db.request_driver.find({
																"$or": [
																	{ "member_id": member_id },
																	{ "passenger_id": member_id }
																],
																"request_status": {"$in" : ["1","4"]}
															}).sort([("created_at", -1)]).skip(request_start_at).limit(request_length)
				#ถ้า request_status != null ให้ดึงเฉพาะสถานะที่เลือกมาแสดง
				else:
					request_driver = db.request_driver.find({
																"$or": [
																	{ "member_id": member_id },
																	{ "passenger_id": member_id }
																],
																"request_status": params['request_status']
															}).sort([("created_at", -1)]).skip(request_start_at).limit(request_length)

				request_driver_list = []

				if request_driver is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					for i in range(len(request_driver_json)):
						package_info = get_package_info(request_driver_json[i]['main_package_id'])

						if member_lang == "en":
							main_package_name = package_info['package_name_en']
						else:
							main_package_name = package_info['package_name_th']

						if request_driver_json[i]['request_status'] == "6":
							if member_lang == "en":
								request_status_text = "Finish"
							else:
								request_status_text = "สำเร็จ"
						elif request_driver_json[i]['request_status'] == "5":
							if member_lang == "en":
								request_status_text = "Traveling"
							else:
								request_status_text = "กำลังเดินทาง"
						elif request_driver_json[i]['request_status'] == "4":
							if member_lang == "en":
								request_status_text = "Upcoming work"
							else:
								request_status_text = "งานที่ใกล้จะถึง"
						elif request_driver_json[i]['request_status'] == "3":
							if member_lang == "en":
								request_status_text = "Canceled by driver"
							else:
								request_status_text = "ยกเลิกโดยคนขับ"
						elif request_driver_json[i]['request_status'] == "2":
							if member_lang == "en":
								request_status_text = "Canceled by customer"
							else:
								request_status_text = "ยกเลิกโดยลูกค้า"
						elif request_driver_json[i]['request_status'] == "1":
							if member_lang == "en":
								request_status_text = "Accepted"
							else:
								request_status_text = "ตอบรับแล้ว"
						else:
							if member_lang == "en":
								request_status_text = "Waiting for reply"
							else:
								request_status_text = "รอตอบรับ"	

						start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
						start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')
						start_datetime = start_date+" "+start_time

						request_driver_list.append({
							"request_id" : request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"company_id": request_driver_json[i]['company_id'],
							"member_id": request_driver_json[i]['member_id'],
							"passenger_id": request_driver_json[i]['passenger_id'],
							"request_to": request_driver_json[i]['request_to'],
							"start_datetime": start_datetime,
							"from_location_name": request_driver_json[i]['from_location_name'],
							"from_location_address": request_driver_json[i]['from_location_address'],
							"to_location_name": request_driver_json[i]['to_location_name'],
							"main_package_name": main_package_name,
							"request_status": request_driver_json[i]['request_status'],
							"request_status_text": request_status_text
						})

				result = {
							"status" : True,
							"msg" : get_api_message("request_list" , "get_request_list_success" , member_lang),
							"data" : request_driver_list
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "request_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def request_detail(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
														"_id": ObjectId(params['request_id']),
														# "$or": [
														# 	{ "member_id": member_id },
														# 	{ "passenger_id": member_id }
														# ]
													})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("request_detail" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				mem_info = get_member_info_by_id(request_driver_json['member_id'])
				member_fullname = mem_info['member_firstname_en']+" "+mem_info['member_lastname_en']

				passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])
				passenger_fullname = passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en']

				start_date = datetime.strptime(request_driver_json['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				end_date = datetime.strptime(request_driver_json['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				start_time = datetime.strptime(request_driver_json['start_time'], '%H:%M:%S').strftime('%H:%M')
				end_time = datetime.strptime(request_driver_json['end_time'], '%H:%M:%S').strftime('%H:%M')

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

				delay_end_date = datetime.strptime(request_driver_json['delay_end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
				delay_end_time = datetime.strptime(request_driver_json['delay_end_time'], '%H:%M:%S').strftime('%H:%M')

				if int(request_driver_json['delay_minute']) <= 30:
					delay_hour = 0
					delay_minute = int(request_driver_json['delay_minute'])
				else:
					delay_hour = int(request_driver_json['delay_minute']) // 60 
					delay_minute = int(request_driver_json['delay_minute']) % 60 

				car = db.car.find_one({"_id": ObjectId(request_driver_json['car_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				car_brand = db.car_brand.find_one({"_id": ObjectId(car_json['car_brand_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_brand_object = dumps(car_brand)
				car_brand_json = json.loads(car_brand_object)
				
				car_brand_name = car_brand_json['brand_name']
				license_plate = car_json['license_plate']

				if request_driver_json['special_request'] is not None:
					driver_age_range_list = []
					communication_list = []
					driver_gender_list = []
					special_skill_list = []
					driver_age_range_text = ""
					driver_gender_text = ""
					special_skill_text = ""

					for i in range(len(request_driver_json['special_request']['driver_age_range'])):
						driver_age_range = db.driver_age_range.find_one({"_id": ObjectId(request_driver_json['special_request']['driver_age_range'][i])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						driver_age_range_object = dumps(driver_age_range)
						driver_age_range_json = json.loads(driver_age_range_object)

						driver_age_range_list.append({
							"id" : driver_age_range_json['_id']['$oid'],
							"range": driver_age_range_json['age_range']
						})

						if i == 0:
							driver_age_range_text = driver_age_range_text + driver_age_range_json['age_range']
						else:
							driver_age_range_text = driver_age_range_text + " , " + driver_age_range_json['age_range']

					for j in range(len(request_driver_json['special_request']['communication'])):
						communication = db.communication.find_one({"_id": ObjectId(request_driver_json['special_request']['communication'][j])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						communication_object = dumps(communication)
						communication_json = json.loads(communication_object)

						if member_lang == "en":
							lang_name = communication_json['lang_name_en']
						else:
							lang_name = communication_json['lang_name_th']

						communication_list.append({
							"communication_id" : communication_json['_id']['$oid'],
							"lang_name": lang_name,
							"lang_code": communication_json['lang_code'],
							"flag_image": communication_json['flag_image']
						})

					for k in range(len(request_driver_json['special_request']['driver_gender'])):
						code = request_driver_json['special_request']['driver_gender'][k]
						if member_lang == "en":
							if code == "female":
								name = "Female"
							else:	
								name = "Male"
						else:
							if code == "female":
								name = "หญิง"
							else:	
								name = "ชาย"
						driver_gender_list.append({"code": code,"name": name})
						driver_gender_text = driver_gender_text + name
				
					for l in range(len(request_driver_json['special_request']['special_skill'])):
						special_skill = db.special_skill.find_one({"_id": ObjectId(request_driver_json['special_request']['special_skill'][l])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						special_skill_object = dumps(special_skill)
						special_skill_json = json.loads(special_skill_object)

						if member_lang == "en":
							special_skill_text = special_skill_json['skill_en']
						else:
							special_skill_text = special_skill_json['skill_th']

						special_skill_list.append({
							"skill_id" : special_skill_json['_id']['$oid'],
							"skill_name": special_skill_text
						})
				else:
					driver_age_range_list = None
					communication_list = None
					driver_gender_list = None
					special_skill_list = None
					driver_gender_text = None

				driver_detail = None
				if request_driver_json['driver_id'] is not None:
					driver_info = get_member_info_by_id(request_driver_json['driver_id'])

					if member_lang == "en":
						driver_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
					else:
						driver_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

					driver_detail = {
										"driver_id": driver_info['_id']['$oid'],
										"driver_code": driver_info['member_code'],
										"driver_fullname": driver_fullname,
										"driver_tel": driver_info['member_tel'],
										"driver_image": driver_info['profile_image']
									}

				driver_list = []
				if request_driver_json['driver_list_id'] is not None:
					dl = db.driver_list.find_one({"_id": ObjectId(request_driver_json['driver_list_id'])})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					dl_object = dumps(dl)
					dl_json = json.loads(dl_object)

					for j in range(len(dl_json['driver_list'])):
						driver_list.append(dl_json['driver_list'][j]['driver_id'])

				package_info = get_package_info(request_driver_json['main_package_id'])
				overtime_paid_rate = package_info['overtime_paid_rate']

				package_detail_list = []

				for i in range(len(request_driver_json['main_package'])):
					member_package = db.member_package.find_one({"_id": ObjectId(request_driver_json['main_package'][i]['member_package_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)

					if member_lang == "en":
						package_name = member_package_json['package_name_en']

						if request_driver_json['main_package'][i]['package_type'] == "hour":
							usage_text = "use "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" hour"
						else:
							usage_text = "use "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" time"
					else:
						package_name = member_package_json['package_name_th']

						if request_driver_json['main_package'][i]['package_type'] == "hour":
							usage_text = "ใช้ "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" ชั่วโมง"
						else:
							usage_text = "ใช้ "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" ครั้ง"

					package_detail_list.append({
						"package_name": package_name,
						"usage_text": usage_text
					})

				for i in range(len(request_driver_json['second_package'])):
					member_package = db.member_package.find_one({"_id": ObjectId(request_driver_json['second_package'][i]['member_package_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					
					if member_lang == "en":
						package_name = member_package_json['package_name_en']

						if request_driver_json['second_package'][i]['package_type'] == "hour":
							usage_text = "use "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" hour"
						else:
							usage_text = "use "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" time"
					else:
						package_name = member_package_json['package_name_th']

						if request_driver_json['second_package'][i]['package_type'] == "hour":
							usage_text = "ใช้ "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" ชั่วโมง"
						else:
							usage_text = "ใช้ "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" ครั้ง"

					package_detail_list.append({
						"package_name": package_name,
						"usage_text": usage_text
					})

				for i in range(len(request_driver_json['overtime_package'])):
					member_package = db.member_package.find_one({"_id": ObjectId(request_driver_json['overtime_package'][i]['member_package_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					
					if member_lang == "en":
						package_name = member_package_json['package_name_en']

						if request_driver_json['overtime_package'][i]['package_type'] == "hour":
							usage_text = "use "+str(int(request_driver_json['overtime_package'][i]['usage_amount']))+" hour"
						else:
							usage_text = "use "+str(int(request_driver_json['overtime_package'][i]['usage_amount']))+" time"
					else:
						package_name = member_package_json['package_name_th']

						if request_driver_json['overtime_package'][i]['package_type'] == "hour":
							usage_text = "ใช้ "+str(int(request_driver_json['overtime_package'][i]['usage_amount']))+" ชั่วโมง"
						else:
							usage_text = "ใช้ "+str(int(request_driver_json['overtime_package'][i]['usage_amount']))+" ครั้ง"

					package_detail_list.append({
						"package_name": package_name,
						"usage_text": usage_text
					})
				
				if request_driver_json['request_status'] == "6":
					if member_lang == "en":
						request_status_text = "Finish"
					else:
						request_status_text = "สำเร็จ"
				elif request_driver_json['request_status'] == "5":
					if member_lang == "en":
						request_status_text = "Traveling"
					else:
						request_status_text = "กำลังเดินทาง"
				elif request_driver_json['request_status'] == "4":
					if member_lang == "en":
						request_status_text = "Upcoming work"
					else:
						request_status_text = "งานที่ใกล้จะถึง"
				elif request_driver_json['request_status'] == "3":
					if member_lang == "en":
						request_status_text = "Canceled by driver"
					else:
						request_status_text = "ยกเลิกโดยคนขับ"
				elif request_driver_json['request_status'] == "2":
					if member_lang == "en":
						request_status_text = "Canceled by customer"
					else:
						request_status_text = "ยกเลิกโดยลูกค้า"
				elif request_driver_json['request_status'] == "1":
					if member_lang == "en":
						request_status_text = "Accepted"
					else:
						request_status_text = "ตอบรับแล้ว"
				else:
					if member_lang == "en":
						request_status_text = "Waiting for reply"
					else:
						request_status_text = "รอตอบรับ"	


				if request_driver_json['job_status'] == "10":
					if member_lang == "en":
						job_status_text = "จบงานเกินเวลาที่จอง และชำระค่าใช้จ่ายเพิ่มเติมแล้ว"
					else:
						job_status_text = "จบงานเกินเวลาที่จอง และชำระค่าใช้จ่ายเพิ่มเติมแล้ว"
				elif request_driver_json['job_status'] == "9":
					if member_lang == "en":
						job_status_text = "จบงานเกินเวลาที่จองและมีค่าใช้จ่ายเพิ่ม"
					else:
						job_status_text = "จบงานเกินเวลาที่จองและมีค่าใช้จ่ายเพิ่ม"
				elif request_driver_json['job_status'] == "8":
					if member_lang == "en":
						job_status_text = "จบงานตามเวลาที่จอง"
					else:
						job_status_text = "จบงานตามเวลาที่จอง"
				elif request_driver_json['job_status'] == "7":
					if member_lang == "en":
						job_status_text = "15 นาทีก่อนถึงเวลาจบงาน"
					else:
						job_status_text = "15 นาทีก่อนถึงเวลาจบงาน"
				elif request_driver_json['job_status'] == "6":
					if member_lang == "en":
						if request_driver_json['check_status'] == "0":
							job_status_text = "ลูกค้าตอบรับการเริ่มงาน และให้คนขับตรวจสภาพรถ"
						else:
							job_status_text = "กำลังเดินทาง"
					else:
						if request_driver_json['check_status'] == "0":
							job_status_text = "ลูกค้าตอบรับการเริ่มงาน และให้คนขับตรวจสภาพรถ"
						else:
							job_status_text = "กำลังเดินทาง"
				elif request_driver_json['job_status'] == "5":
					if member_lang == "en":
						job_status_text = "คนขับยืนยันการเริ่มงาน"
					else:
						job_status_text = "คนขับยืนยันการเริ่มงาน"
				elif request_driver_json['job_status'] == "4":
					if member_lang == "en":
						job_status_text = "คนขับไม่ยืนยันเวลาการถึงจุดหมาย"
					else:
						job_status_text = "คนขับไม่ยืนยันเวลาการถึงจุดหมาย"
				elif request_driver_json['job_status'] == "3":
					if member_lang == "en":
						job_status_text = "คนขับยืนยันเวลาการถึงจุดหมาย"
					else:
						job_status_text = "คนขับยืนยันเวลาการถึงจุดหมาย"
				elif request_driver_json['job_status'] == "2":
					if member_lang == "en":
						job_status_text = "ก่อนเริ่มงาน 1 ชม."
					else:
						job_status_text = "ก่อนเริ่มงาน 1 ชม."
				elif request_driver_json['job_status'] == "1":
					if member_lang == "en":
						job_status_text = "ก่อนเริ่มงาน 12 ชม."
					else:
						job_status_text = "ก่อนเริ่มงาน 12 ชม."
				else:
					if member_lang == "en":
						job_status_text = "ก่อนเริ่มงาน"
					else:
						job_status_text = "ก่อนเริ่มงาน"


				billing_detail_list = []

				if len(request_driver_json['billing_id']) > 0:
					for i in range(len(request_driver_json['billing_id'])):
						billing = db.billing.find_one({"_id": ObjectId(request_driver_json['billing_id'][i])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						billing_object = dumps(billing)
						billing_json = json.loads(billing_object)

						billing_text = ""
					
						if member_lang == "en":
							if billing_json['service_period'] == "overtime":
								billing_text = billing_text + "ใช้เกินเวลาที่จอง "
							else:
								billing_text = billing_text + "จอง "

							if billing_json['normal_usage'] > 0 and billing_json['overtime_usage'] > 0:
								billing_text = billing_text + "ในเวลาทำงาน "+str(billing_json['normal_usage'])+" ชม. "
								billing_text = billing_text + "และนอกเวลาทำงาน "+str(billing_json['overtime_usage'])+" ชม. "

							if billing_json['normal_usage'] > 0:
								billing_text = billing_text + "ในเวลาทำงาน "+str(billing_json['normal_usage'])+" ชม. "

							if billing_json['overtime_usage'] > 0:
								billing_text = billing_text + "นอกเวลาทำงาน "+str(billing_json['overtime_usage'])+" ชม. "

							billing_text = billing_text + "ยอดวางบิล "+str(billing_json['sum_paid'])+" บาท"
						else:
							if billing_json['service_period'] == "overtime":
								billing_text = billing_text + "ใช้เกินเวลาที่จอง "
							else:
								billing_text = billing_text + "จอง "

							if billing_json['normal_usage'] > 0 and billing_json['overtime_usage'] > 0:
								billing_text = billing_text + "ในเวลาทำงาน "+str(billing_json['normal_usage'])+" ชม. "
								billing_text = billing_text + "และนอกเวลาทำงาน "+str(billing_json['overtime_usage'])+" ชม. "

							if billing_json['normal_usage'] > 0:
								billing_text = billing_text + "ในเวลาทำงาน "+str(billing_json['normal_usage'])+" ชม. "

							if billing_json['overtime_usage'] > 0:
								billing_text = billing_text + "นอกเวลาทำงาน "+str(billing_json['overtime_usage'])+" ชม. "

							billing_text = billing_text + "ยอดวางบิล "+str(billing_json['sum_paid'])+" บาท"
						
						billing_detail_list.append({
							#"billing_detail_text": billing_text,
							"service_period": billing_json['service_period'],
							"normal_usage": billing_json['normal_usage'],
							"overtime_usage": billing_json['overtime_usage'],
							"sum_paid": billing_json['sum_paid']
						})

				check_status = request_driver_json['check_status']
				if check_status is not None:
					# '0' = ยังไม่ได้ตรวจสภาพรถ
					# '1' = ข้ามการตรวจสภาพรถ
					# '2' = รอยืนยันการตรวจสภาพรถจากผู้โดยสาร
					# '3' = ตรวจสภาพรถไม่ผ่าน
					# '4' = ตรวจสภาพรถเรียบร้อย
					# '5' = ผู้โดยสารไม่ยืนยันการตรวจสภาพรถ (ใช้ cronjob update จาก 2 เป็น 5 เมื่อจบงาน 2 ชม.แล้วแต่ผู้โดยสารไม่ยืนยันการตรวจสภาพรถ)

					if check_status == "5":
						if member_lang == "en":
							check_status_text = "The passenger did not confirm the car inspection"
						else:
							check_status_text = "ผู้โดยสารไม่ยืนยันการตรวจสภาพรถ"
					elif check_status == "4":
						if member_lang == "en":
							check_status_text = "Successfully inspected the car"
						else:
							check_status_text = "ตรวจสภาพรถเรียบร้อย"
					elif check_status == "3":
						if member_lang == "en":
							check_status_text = "Inspect the car does not pass"
						else:
							check_status_text = "ตรวจสภาพรถไม่ผ่าน"
					elif check_status == "2":
						if member_lang == "en":
							check_status_text = "Waiting for confirmation of car inspection from passengers"
						else:
							check_status_text = "รอยืนยันการตรวจสภาพรถจากผู้โดยสาร"
					elif check_status == "1":
						if member_lang == "en":
							check_status_text = "Skip the car inspection"
						else:
							check_status_text = "ข้ามการตรวจสภาพรถ"
					else:
						if member_lang == "en":
							check_status_text = "Have not checked the car inspection"
						else:
							check_status_text = "ยังไม่ได้ตรวจสภาพรถ"

					if check_status != "0":
						car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})
						if car_inspection is None:
							start_mileage = None
							end_mileage = None
						else:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							car_inspection_object = dumps(car_inspection)
							car_inspection_json = json.loads(car_inspection_object)

							start_mileage = car_inspection_json['start_mileage']
							end_mileage = car_inspection_json['end_mileage']
					else:
						start_mileage = None
						end_mileage = None
				else:
					check_status_text = None
					start_mileage = None
					end_mileage = None

				service_rating = db.service_rating.find_one({
																"request_id": params['request_id'],
																"rating_status": "1"
															})

				if service_rating is None:
					send_rating_status = '0'
				else:
					send_rating_status = '1'

				check_request_info = check_request_status(params['request_id'])

				if check_request_info is None:
					select_new_driver = "0"
				else:
					#request ไปแล้ว 45 นาทีแล้ว แต่มีมีคนขับรับงาน
					if request_driver_json['request_status'] == "0" and request_driver_json['driver_list_id'] is None:
						select_new_driver = "1"
					#คนขับยกเลิกงาน
					elif request_driver_json['request_status'] == "3":
						select_new_driver = "1"
					#ยกเลิกโดยลูกค้า
					elif request_driver_json['request_status'] == "2":
						select_new_driver = "0"
					#จำนวนคนที่ปฏิเสธงาน เท่ากับ จำนวนคนขับที่ request ทั้งหมด
					elif check_request_info['all_driver'] == check_request_info['count_reject']:
						select_new_driver = "1"
					else:
						select_new_driver = "0"

				data = {
							"request_id" : request_driver_json['_id']['$oid'],
							"request_no": request_driver_json['request_no'],
							"company_id": request_driver_json['company_id'],
							"member_id": request_driver_json['member_id'],
							"passenger_id": request_driver_json['passenger_id'],
							"member_fullname": member_fullname,
							"passenger_fullname": passenger_fullname,
							"request_to": request_driver_json['request_to'],
							"overtime_paid_rate": overtime_paid_rate,
							"hour_amount": request_driver_json['hour_amount'],

							"start_date": start_date,
							"end_date": end_date,
							"start_time": start_time,
							"end_time": end_time,
							"from_location_name": request_driver_json['from_location_name'],
							"from_location_address": request_driver_json['from_location_address'],
							"to_location_name": request_driver_json['to_location_name'],
							"to_location_address": request_driver_json['to_location_address'],

							"car_id": request_driver_json['car_id'],
							"car_brand_name": car_brand_name,
							"license_plate": license_plate,
							"driver_note": request_driver_json['driver_note'],
							"driver_gender": driver_gender_list,
							"driver_gender_text": driver_gender_text,
							"driver_age_range": driver_age_range_list,
							"driver_age_range_text": driver_age_range_text,
							"communication": communication_list,
							"special_skill": special_skill_list,
							"special_skill_text": special_skill_text,
							"package_detail": package_detail_list,
							"billing_detail": billing_detail_list,
							"driver_detail": driver_detail,
							"request_status": request_driver_json['request_status'],
							"request_status_text": request_status_text,
							"job_status": request_driver_json['job_status'],
							"job_status_text": job_status_text,
							"check_status": check_status,
							"check_status_text": check_status_text,
							"start_mileage": start_mileage,
							"end_mileage": end_mileage,

							"delay_hour": delay_hour,
							"delay_minute": delay_minute,
							"delay_end_date": delay_end_date,
							"delay_end_time": delay_end_time,

							"driver_list_id": request_driver_json['driver_list_id'],
							"driver_list": driver_list,
							"send_rating_status": send_rating_status,
							"select_new_driver": select_new_driver,

							"accept_start_date": accept_start_date,
							"accept_start_time": accept_start_time,
							"end_job_date": end_job_date,
							"end_job_time": end_job_time
						}

				result = {
							"status" : True,
							"msg" : get_api_message("request_detail" , "get_request_detail_success" , member_lang),
							"data" : data
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "request_detail"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def driver_request_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params
	isset_start_date = "start_date" in params
	isset_start_time = "start_time" in params
	isset_hour_amount = "hour_amount" in params
	isset_from_location_id = "from_location_id" in params
	isset_to_location_id = "to_location_id" in params
	isset_from_location_address = "from_location_address" in params
	isset_to_location_address = "to_location_address" in params
	isset_car_id = "car_id" in params
	isset_driver_gender = "driver_gender" in params
	isset_driver_age_range = "driver_age_range" in params
	isset_communication = "communication" in params
	isset_special_skill = "special_skill" in params

	#if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id and isset_start_date and isset_start_time and isset_hour_amount and isset_from_location_id and isset_to_location_id and isset_from_location_address and isset_to_location_address and isset_car_id and isset_driver_gender and isset_driver_age_range and isset_communication:
	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id and isset_start_date and isset_start_time and isset_hour_amount and isset_from_location_id and isset_to_location_id and isset_from_location_address and isset_to_location_address and isset_car_id and isset_driver_gender and isset_driver_age_range and isset_communication and isset_special_skill:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
	
			start_date_obj = datetime.strptime(params['start_date'], '%d/%m/%Y')
			workday = db.workday.find_one({"short_name_en": start_date_obj.strftime('%a')})

			# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			workday_object = dumps(workday)
			workday_json = json.loads(workday_object)
			workday_id = workday_json['_id']['$oid']

			where_param = {
							"member_type": "driver",
							"member_status" : "1",
							"workday" : {"$in": [workday_id]}
						}

			check_gender = ""
			#เช็คค่า member_gender
			if len(params['driver_gender']) > 0:
				for i in range(len(params['driver_gender'])):
					if i == 0:
						check_gender = params['driver_gender'][i]
					else:
						check_gender = check_gender+" , "+params['driver_gender'][i]

			#ถ้าเลือกค่าใดค่าหนึ่ง ให้ไป where member_gender นั้น
			if check_gender != "female , male" and check_gender != "male , female" and check_gender != "":
				add_params = {"member_gender": check_gender}
				where_param.update(add_params)

			min_age = 0
			max_age = 0
			#เช็คค่า driver_age_range
			if len(params['driver_age_range']) > 0:
				for i in range(len(params['driver_age_range'])):
					driver_age_range = db.driver_age_range.find_one({"_id": ObjectId(params['driver_age_range'][i])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					driver_age_range_object = dumps(driver_age_range)
					driver_age_range_json = json.loads(driver_age_range_object)

					if i == 0:
						min_age = driver_age_range_json['min_age']
						max_age = driver_age_range_json['max_age']
					else:
						#ถ้า min_age ล่าสุดน้อยกว่าค่าจาก db ให้ใช้ค่าเดิม
						if min_age < driver_age_range_json['min_age']:
							min_age = min_age
						#ถ้า min_age ล่าสุดมากกว่าค่าจาก db ให้ใช้ค่าจาก db
						else:
							min_age = driver_age_range_json['min_age']
						#ถ้า max_age ล่าสุดน้อยกว่าค่าจาก db ให้ใช้ค่าจาก db
						if max_age < driver_age_range_json['max_age']:
							max_age = driver_age_range_json['max_age']
						#ถ้า max_age ล่าสุดมากกว่าค่าจาก db ให้ใช้ค่าเดิม
						else:
							max_age = max_age

				# add_params = {"$and": [{"member_age": {"$gte" : min_age}},{"member_age": {"$lte" : max_age}}]}
				add_params = {"member_age": {"$gte" : min_age , "$lte" : max_age}}
				where_param.update(add_params)

			#เช็คค่า communication
			if len(params['communication']) > 0:
				add_params = {"communication" : {"$all": params['communication']}}
				where_param.update(add_params)

			#เช็คค่า special_skill
			if len(params['special_skill']) > 0:
				add_params = {"special_skill" : {"$all": params['special_skill']}}
				where_param.update(add_params)

			#เช็คค่า car_type
			if params['car_id'] is not None:
				car = db.car.find_one({"_id": ObjectId(params['car_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				# add_params = {"car_type": car_json['car_type_id']}
				add_params = {
								"car_type" : {"$all": [car_json['car_type_id']]},
								"car_gear" : {"$all": [car_json['car_gear_id']]} 
							}
				where_param.update(add_params)

			package_info = get_package_info(params['package_id'])

			driver_level = db.driver_level.find_one({"_id": ObjectId(package_info['driver_level'])})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			driver_level_object = dumps(driver_level)
			driver_level_json = json.loads(driver_level_object)

			#เช็คค่า driver_level_priority จาก tb member ต้องน้อยกว่าหรือเท่ากับ level_priority ที่อ้างอิงจาก package_id
			add_params = {"driver_level_priority" : {"$lte": driver_level_json['level_priority']}}
			where_param.update(add_params)

			all_bangkok_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพทั้งหมด"})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			all_bangkok_service_area_object = dumps(all_bangkok_service_area)
			all_bangkok_service_area_json = json.loads(all_bangkok_service_area_object)
			all_bangkok_service_area_id = all_bangkok_service_area_json['_id']['$oid']

			if params['from_location_id'] is None:
				#เช็คสถานที่เดินทางว่าตรงกับ service_area ไหน แล้วค่อยเอา service_area_id ไปหาคนขับที่มี service_area_id ตรงกัน 
				from_address = params['from_location_address']
				
				if "กรุงเทพ" in from_address and "เขต" in from_address:
					sub_address_1 = from_address.split("เขต")
					sub_address_2 = sub_address_1[1].split(" ")
					f_province = "กรุงเทพมหานคร"
					f_district = sub_address_2[0]
				elif "อำเภอ" in from_address:
					sub_address_1 = from_address.split("อำเภอ")
					sub_address_2 = sub_address_1[1].split(" ")
					f_province = sub_address_2[1]
					f_district = sub_address_2[0]
				else:
					f_province = None
					f_district = None
			else:
				from_location = db.location.find_one({"_id": ObjectId(params['from_location_id'])})
				
				if from_location is None:
					f_province = None
					f_district = None
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					from_location_object = dumps(from_location)
					from_location_json = json.loads(from_location_object)

					from_district = db.district.find_one({"district_code": from_location_json['location_district_code']})
					from_province = db.province.find_one({"province_code": from_location_json['location_province_code']})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					from_district_object = dumps(from_district)
					from_district_json = json.loads(from_district_object)
					from_province_object = dumps(from_province)
					from_province_json = json.loads(from_province_object)
					f_province = from_province_json['province_th']
					f_district = from_district_json['district_th']

			if params['to_location_id'] is None:
				#เช็คสถานที่เดินทางว่าตรงกับ service_area ไหน แล้วค่อยเอา service_area_id ไปหาคนขับที่มี service_area_id ตรงกัน 
				to_address = params['to_location_address']

				if "กรุงเทพ" in to_address and "เขต" in to_address:
					sub_address_1 = to_address.split("เขต")
					sub_address_2 = sub_address_1[1].split(" ")
					t_province = "กรุงเทพมหานคร"
					t_district = sub_address_2[0]
				elif "อำเภอ" in to_address:
					sub_address_1 = to_address.split("อำเภอ")
					sub_address_2 = sub_address_1[1].split(" ")
					t_province = sub_address_2[1]
					t_district = sub_address_2[0]	
				else:
					t_province = None
					t_district = None
			else:
				to_location = db.location.find_one({"_id": ObjectId(params['to_location_id'])})
				
				if to_location is None:
					t_province = None
					t_district = None
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					to_location_object = dumps(to_location)
					to_location_json = json.loads(to_location_object)

					to_district = db.district.find_one({"district_code": to_location_json['location_district_code']})
					to_province = db.province.find_one({"province_code": to_location_json['location_province_code']})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					to_district_object = dumps(to_district)
					to_district_json = json.loads(to_district_object)
					to_province_object = dumps(to_province)
					to_province_json = json.loads(to_province_object)
					t_province = to_province_json['province_th']
					t_district = to_district_json['district_th']

			if f_province is not None and t_province is not None:
				if f_province == "กรุงเทพมหานคร":
					from_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพ - "+f_district})
				else:
					from_service_area = db.service_area.find_one({"service_area_name_th": f_province})
		
				if t_province == "กรุงเทพมหานคร":
					to_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพ - "+t_district})
				else:
					to_service_area = db.service_area.find_one({"service_area_name_th": t_province})
				
				if from_service_area is not None and to_service_area is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					from_service_area_object = dumps(from_service_area)
					from_service_area_json = json.loads(from_service_area_object)
					to_service_area_object = dumps(to_service_area)
					to_service_area_json = json.loads(to_service_area_object)

				
					from_service_area_id = from_service_area_json['_id']['$oid']
					to_service_area_id = to_service_area_json['_id']['$oid']

					#ถ้าจุดรับเป็น กรุงเทพ
					if f_province == "กรุงเทพมหานคร" or t_province == "กรุงเทพมหานคร":
						add_params = {
										"service_area" : {"$in": [all_bangkok_service_area_id , from_service_area_id , to_service_area_id]}
									}
						where_param.update(add_params)
					#ถ้าจุดรับเป็น ตจว.
					else:
						add_params = {
										"service_area" : {"$in": [from_service_area_id , to_service_area_id]}
									}
						where_param.update(add_params)
			

			member = db.member.find(where_param).sort([("driver_rating", -1),("driver_level_priority", -1)])
			member_list = []

			if member is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				for i in range(len(member_json)):
					level_name = None
					level_detail = None
					level_image = None

					if member_json[i]['driver_level'] is not None:
						driver_level = db.driver_level.find_one({"_id": ObjectId(member_json[i]['driver_level'])})
						
						if driver_level is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							driver_level_object = dumps(driver_level)
							driver_level_json = json.loads(driver_level_object)

							if member_lang == "en":
								level_name = driver_level_json["level_name_en"]
								level_detail = driver_level_json["level_detail_en"]
							else:
								level_name = driver_level_json["level_name_th"]
								level_detail = driver_level_json["level_detail_th"]

							level_image = driver_level_json["level_image"]

					member_age = None
					if member_json[i]['member_birthday'] is not None:
						member_age = get_member_age(member_json[i]['member_birthday'])

					if member_lang == "en":
						member_fullname = member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']

						if member_json[i]['member_gender'] == "female":
							member_gender_text = "Female"
						else:
							member_gender_text = "Male"

						car_gear_text = member_json[i]['car_gear_en']
						communication_text = member_json[i]['communication_en']
						service_area_text = member_json[i]['service_area_en']
						workday_text = member_json[i]['workday_en']
						special_skill_text = member_json[i]['special_skill_en']
						car_type_detail = []
						car_type_text = ""

						if member_json[i]['car_type_en'] is not None:
							car_type_split = member_json[i]['car_type_en'].split(" , ")

							for j in range(len(car_type_split)):
								if car_type_split[j] == "Sedan":
									car_type_text = car_type_split[j]+" "+str(member_json[i]['sedan_job'])+" times"
								elif car_type_split[j] == "SUV":
									car_type_text = car_type_split[j]+" "+str(member_json[i]['suv_job'])+" times"
								else:
									car_type_text = car_type_split[j]+" "+str(member_json[i]['van_job'])+" times"

								car_type_detail.append(car_type_text)
					else:
						member_fullname = member_json[i]['member_firstname_th']+" "+member_json[i]['member_lastname_th']

						if member_json[i]['member_gender'] == "female":
							member_gender_text = "หญิง"
						else:
							member_gender_text = "ชาย"

						car_gear_text = member_json[i]['car_gear_th']
						communication_text = member_json[i]['communication_th']
						service_area_text = member_json[i]['service_area_th']
						workday_text = member_json[i]['workday_th']
						special_skill_text = member_json[i]['special_skill_th']
						car_type_detail = []
						car_type_text = ""

						if member_json[i]['car_type_th'] is not None:
							car_type_split = member_json[i]['car_type_th'].split(" , ")

							for j in range(len(car_type_split)):
								if car_type_split[j] == "รถเก๋ง":
									car_type_text = car_type_split[j]+" "+str(member_json[i]['sedan_job'])+" ครั้ง"
								elif car_type_split[j] == "รถ SUV":
									car_type_text = car_type_split[j]+" "+str(member_json[i]['suv_job'])+" ครั้ง"
								else:
									car_type_text = car_type_split[j]+" "+str(member_json[i]['van_job'])+" ครั้ง"

								car_type_detail.append(car_type_text)

					communication_list = []

					for j in range(len(member_json[i]['communication'])):
						communication = db.communication.find_one({"_id": ObjectId(member_json[i]['communication'][j])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						communication_object = dumps(communication)
						communication_json = json.loads(communication_object)

						if member_lang == "en":
							lang_name = communication_json['lang_name_en']
						else:
							lang_name = communication_json['lang_name_th']

						communication_list.append({
							"communication_id" : communication_json['_id']['$oid'],
							"lang_name": lang_name,
							"lang_code": communication_json['lang_code'],
							"flag_image": communication_json['flag_image']
						})

					#เช็คการรับงานของคนขับจาก tb request_driver

					sd = datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')

					#2020-07-10 01:00:00
					start_datetime_obj = datetime.strptime(sd+" "+params['start_time']+":00", '%Y-%m-%d %H:%M:%S')
					end_datetime_obj = start_datetime_obj + timedelta(hours=int(params['hour_amount']))

					#2020-07-10 13:00:00
					# end_datetime_obj = datetime.strptime(request_driver_json['end_date']+" "+request_driver_json['end_time'], '%Y-%m-%d %H:%M:%S')

					#2020-07-09 17:00:00
					before_start_datetime_obj = start_datetime_obj - timedelta(hours=8)
					#2020-07-10 21:00:00
					after_end_datetime_obj = end_datetime_obj + timedelta(hours=8)

					start_date = start_datetime_obj.strftime('%Y-%m-%d')
					start_time = start_datetime_obj.strftime('%H:%M:%S')
					end_date = end_datetime_obj.strftime('%Y-%m-%d')
					end_time = end_datetime_obj.strftime('%H:%M:%S')

					before_start_date = before_start_datetime_obj.strftime('%Y-%m-%d')
					before_start_time = before_start_datetime_obj.strftime('%H:%M:%S')
					after_end_date = after_end_datetime_obj.strftime('%Y-%m-%d')
					after_end_time = after_end_datetime_obj.strftime('%H:%M:%S')

					#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก ก่อนรับงานนี้ 8 ชม.
					check_before = db.request_driver.find_one({
																"driver_id": member_json[i]['_id']['$oid'],
																"start_date": before_start_date,
																"start_time": {"$gte" : before_start_time},
																"start_time": {"$lte" : start_time},
																"request_status": {"$nin" : ["2","3"]}
															})

					#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก หลังจบงานนี้ 8 ชม.
					check_after = db.request_driver.find_one({
																"driver_id": member_json[i]['_id']['$oid'],
																"start_date": start_date,
																"start_time": {"$gte" : end_time},
																"start_time": {"$lte" : after_end_time},
																"request_status": {"$nin" : ["2","3"]}
															})

					if member_json[i]['driver_rating'] is not None:
						driver_rating = round(float(member_json[i]['driver_rating']) , 1)
					else:
						driver_rating = float("0")

					#ถ้าไม่เจองาน ก่อนรับงานนี้ 8 ชม. และ หลังจบงานนี้ 8 ชม. จึงจะสามารถรับงานนี้ได้
					if check_before is None and check_after is None:
						member_list.append({
							"member_id" : member_json[i]['_id']['$oid'],
							"member_code": member_json[i]['member_code'],
							"member_username": member_json[i]['member_username'],
							"member_firstname_en": member_json[i]['member_firstname_en'],
							"member_lastname_en": member_json[i]['member_lastname_en'],
							"member_firstname_th": member_json[i]['member_firstname_th'],
							"member_lastname_th": member_json[i]['member_lastname_th'],
							"member_email": member_json[i]['member_email'],
							"member_tel": member_json[i]['member_tel'],
							"member_birthday": member_json[i]['member_birthday'],
							"member_gender" : member_json[i]['member_gender'],
							"member_gender_text" : member_gender_text,
							"member_type": member_json[i]['member_type'],
							"profile_image": member_json[i]['profile_image'],
							"driver_license_expire": member_json[i]['driver_license_expire'],
							"driver_license_no": member_json[i]['driver_license_no'],
							"car_type": member_json[i]['car_type'],
							"car_type_detail": car_type_detail,
							"car_gear": member_json[i]['car_gear'],
							"car_gear_text": car_gear_text,
							"service_area": member_json[i]['service_area'],
							"service_area_text": service_area_text,
							"communication": communication_list,
							"communication_text": communication_text,
							"workday": member_json[i]['workday'],
							"workday_text": workday_text,
							"special_skill": member_json[i]['special_skill'],
 							"special_skill_text": special_skill_text,
							"driver_rating": driver_rating,
							"driver_level": member_json[i]['driver_level'],
							"level_name": level_name,
							"level_detail": level_detail,
							"level_image": level_image,
							"member_age" : member_age,
							"member_lang": member_json[i]['member_lang'],
							"member_token": member_json[i]['member_token'],
							"noti_key": member_json[i]['noti_key']
						})

			if len(member_list) > 0:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				check_before_object = dumps(check_before)
				check_before_json = json.loads(check_before_object)

				check_after_object = dumps(check_after)
				check_after_json = json.loads(check_after_object)

				result = {
							"status" : True,
							"msg" : get_api_message("driver_request_list" , "get_driver_request_list_success" , member_lang),
							"data" : member_list
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("driver_request_list" , "data_not_found" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "driver_request_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def edit_driver_request_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_driver_list = "driver_list" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_driver_list:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("edit_driver_request_list" , "request_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				start_date_obj = datetime.strptime(request_driver_json['start_date'], '%Y-%m-%d')
				workday = db.workday.find_one({"short_name_en": start_date_obj.strftime('%a')})

				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				workday_object = dumps(workday)
				workday_json = json.loads(workday_object)
				workday_id = workday_json['_id']['$oid']

				where_param = {
								"member_type": "driver",
								"member_status" : "1",
								"workday" : {"$in": [workday_id]}
							}

				check_gender = ""
				#เช็คค่า member_gender
				if len(request_driver_json['special_request']['driver_gender']) > 0:
					for i in range(len(request_driver_json['special_request']['driver_gender'])):
						if i == 0:
							check_gender = request_driver_json['special_request']['driver_gender'][i]
						else:
							check_gender = check_gender+" , "+request_driver_json['special_request']['driver_gender'][i]

				#ถ้าเลือกค่าใดค่าหนึ่ง ให้ไป where member_gender นั้น
				if check_gender != "female , male" and check_gender != "male , female" and check_gender != "":
					add_params = {"member_gender": check_gender}
					where_param.update(add_params)

				min_age = 0
				max_age = 0
				#เช็คค่า driver_age_range
				if len(request_driver_json['special_request']['driver_age_range']) > 0:
					for i in range(len(request_driver_json['special_request']['driver_age_range'])):
						driver_age_range = db.driver_age_range.find_one({"_id": ObjectId(request_driver_json['special_request']['driver_age_range'][i])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						driver_age_range_object = dumps(driver_age_range)
						driver_age_range_json = json.loads(driver_age_range_object)

						if i == 0:
							min_age = driver_age_range_json['min_age']
							max_age = driver_age_range_json['max_age']
						else:
							#ถ้า min_age ล่าสุดน้อยกว่าค่าจาก db ให้ใช้ค่าเดิม
							if min_age < driver_age_range_json['min_age']:
								min_age = min_age
							#ถ้า min_age ล่าสุดมากกว่าค่าจาก db ให้ใช้ค่าจาก db
							else:
								min_age = driver_age_range_json['min_age']
							#ถ้า max_age ล่าสุดน้อยกว่าค่าจาก db ให้ใช้ค่าจาก db
							if max_age < driver_age_range_json['max_age']:
								max_age = driver_age_range_json['max_age']
							#ถ้า max_age ล่าสุดมากกว่าค่าจาก db ให้ใช้ค่าเดิม
							else:
								max_age = max_age

					# add_params = {"$and": [{"member_age": {"$gte" : min_age}},{"member_age": {"$lte" : max_age}}]}
					add_params = {"member_age": {"$gte" : min_age , "$lte" : max_age}}
					where_param.update(add_params)

				#เช็คค่า communication
				if len(request_driver_json['special_request']['communication']) > 0:
					add_params = {"communication" : {"$all": request_driver_json['special_request']['communication']}}
					where_param.update(add_params)

				#เช็คค่า special_skill
				if len(request_driver_json['special_request']['special_skill']) > 0:
					add_params = {"special_skill" : {"$all": request_driver_json['special_request']['special_skill']}}
					where_param.update(add_params)

				#เช็คค่า car_type
				if request_driver_json['car_id'] is not None:
					car = db.car.find_one({"_id": ObjectId(request_driver_json['car_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_object = dumps(car)
					car_json = json.loads(car_object)

					# add_params = {"car_type": car_json['car_type_id']}
					add_params = {
									"car_type" : {"$all": [car_json['car_type_id']]},
									"car_gear" : {"$all": [car_json['car_gear_id']]} 
								}
					where_param.update(add_params)

				package_info = get_package_info(request_driver_json['main_package_id'])

				driver_level = db.driver_level.find_one({"_id": ObjectId(package_info['driver_level'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				driver_level_object = dumps(driver_level)
				driver_level_json = json.loads(driver_level_object)

				#เช็คค่า driver_level_priority จาก tb member ต้องน้อยกว่าหรือเท่ากับ level_priority ที่อ้างอิงจาก package_id
				add_params = {"driver_level_priority" : {"$lte": driver_level_json['level_priority']}}
				where_param.update(add_params)

				#ถ้า driver_list ไม่ใช่ [] จะไม่เลือกคนขับที่มี member_id ตรงกับ driver_list นี้
				# if len(params['driver_list']) > 0: 
				if len(params['driver_list']) > 0 and params['driver_list'][0] is not None:
					member_in = []
					for i in range(len(params['driver_list'])):
						mem_info = get_member_info_by_id(params['driver_list'][i])
						mem_code = mem_info['member_code']
						member_in.append(mem_code)

					add_params = {
									"member_code" : {"$nin" : member_in}
								}
					where_param.update(add_params)

				all_bangkok_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพทั้งหมด"})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				all_bangkok_service_area_object = dumps(all_bangkok_service_area)
				all_bangkok_service_area_json = json.loads(all_bangkok_service_area_object)
				all_bangkok_service_area_id = all_bangkok_service_area_json['_id']['$oid']

				#เช็คสถานที่เดินทางว่าตรงกับ service_area ไหน แล้วค่อยเอา service_area_id ไปหาคนขับที่มี service_area_id ตรงกัน 
				from_address = request_driver_json['from_location_address']
				
				if "กรุงเทพ" in from_address and "เขต" in from_address:
					sub_address_1 = from_address.split("เขต")
					sub_address_2 = sub_address_1[1].split(" ")
					f_province = "กรุงเทพมหานคร"
					f_district = sub_address_2[0]
				elif "อำเภอ" in from_address:
					sub_address_1 = from_address.split("อำเภอ")
					sub_address_2 = sub_address_1[1].split(" ")
					f_province = sub_address_2[1].replace("จังหวัด", "")
					f_district = sub_address_2[0]
				else:
					f_province = None
					f_district = None
				
				#เช็คสถานที่เดินทางว่าตรงกับ service_area ไหน แล้วค่อยเอา service_area_id ไปหาคนขับที่มี service_area_id ตรงกัน 
				to_address = request_driver_json['to_location_address']

				if "กรุงเทพ" in to_address and "เขต" in to_address:
					sub_address_1 = to_address.split("เขต")
					sub_address_2 = sub_address_1[1].split(" ")
					t_province = "กรุงเทพมหานคร"
					t_district = sub_address_2[0]
				elif "อำเภอ" in to_address:
					sub_address_1 = to_address.split("อำเภอ")
					sub_address_2 = sub_address_1[1].split(" ")
					t_province = sub_address_2[1].replace("จังหวัด", "")
					t_district = sub_address_2[0]	
				else:
					t_province = None
					t_district = None		

				if f_province is not None and t_province is not None:
					if f_province == "กรุงเทพมหานคร":
						from_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพ - "+f_district})
					else:
						from_service_area = db.service_area.find_one({"service_area_name_th": f_province})
			
					if t_province == "กรุงเทพมหานคร":
						to_service_area = db.service_area.find_one({"service_area_name_th": "กรุงเทพ - "+t_district})
					else:
						to_service_area = db.service_area.find_one({"service_area_name_th": t_province})

					if from_service_area is not None and to_service_area is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						from_service_area_object = dumps(from_service_area)
						from_service_area_json = json.loads(from_service_area_object)
						to_service_area_object = dumps(to_service_area)
						to_service_area_json = json.loads(to_service_area_object)

						from_service_area_id = from_service_area_json['_id']['$oid']
						to_service_area_id = to_service_area_json['_id']['$oid']

						#ถ้าจุดรับเป็น กรุงเทพ
						if f_province == "กรุงเทพมหานคร" or t_province == "กรุงเทพมหานคร":
							add_params = {
											"service_area" : {"$in": [all_bangkok_service_area_id , from_service_area_id , to_service_area_id]}
										}
							where_param.update(add_params)
						#ถ้าจุดรับเป็น ตจว.
						else:
							add_params = {
											"service_area" : {"$in": [from_service_area_id , to_service_area_id]}
										}
							where_param.update(add_params)

				member = db.member.find(where_param).sort([("driver_rating", -1),("driver_level_priority", -1)])
				member_list = []

				if member is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					for i in range(len(member_json)):
						level_name = None

						if member_json[i]['driver_level'] is not None:
							driver_level = db.driver_level.find_one({"_id": ObjectId(member_json[i]['driver_level'])})
							
							if driver_level is not None:
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								driver_level_object = dumps(driver_level)
								driver_level_json = json.loads(driver_level_object)

								if member_lang == "en":
									level_name = driver_level_json["level_name_en"]
									level_detail = driver_level_json["level_detail_en"]
								else:
									level_name = driver_level_json["level_name_th"]
									level_detail = driver_level_json["level_detail_th"]

								level_image = driver_level_json["level_image"]

						member_age = None
						if member_json[i]['member_birthday'] is not None:
							member_age = get_member_age(member_json[i]['member_birthday'])

						if member_lang == "en":
							member_fullname = member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']

							if member_json[i]['member_gender'] == "female":
								member_gender_text = "Female"
							else:
								member_gender_text = "Male"

							car_gear_text = member_json[i]['car_gear_en']
							communication_text = member_json[i]['communication_en']
							service_area_text = member_json[i]['service_area_en']
							workday_text = member_json[i]['workday_en']
							special_skill_text = member_json[i]['special_skill_en']
							car_type_detail = []
							car_type_text = ""

							if member_json[i]['car_type_en'] is not None:
								car_type_split = member_json[i]['car_type_en'].split(" , ")

								for j in range(len(car_type_split)):
									if car_type_split[j] == "Sedan":
										car_type_text = car_type_split[j]+" "+str(member_json[i]['sedan_job'])+" times"
									elif car_type_split[j] == "SUV":
										car_type_text = car_type_split[j]+" "+str(member_json[i]['suv_job'])+" times"
									else:
										car_type_text = car_type_split[j]+" "+str(member_json[i]['van_job'])+" times"

									car_type_detail.append(car_type_text)
						else:
							member_fullname = member_json[i]['member_firstname_th']+" "+member_json[i]['member_lastname_th']

							if member_json[i]['member_gender'] == "female":
								member_gender_text = "หญิง"
							else:
								member_gender_text = "ชาย"

							car_gear_text = member_json[i]['car_gear_th']
							communication_text = member_json[i]['communication_th']
							service_area_text = member_json[i]['service_area_th']
							workday_text = member_json[i]['workday_th']
							special_skill_text = member_json[i]['special_skill_th']
							car_type_detail = []
							car_type_text = ""

							if member_json[i]['car_type_th'] is not None:
								car_type_split = member_json[i]['car_type_th'].split(" , ")

								for j in range(len(car_type_split)):
									if car_type_split[j] == "รถเก๋ง":
										car_type_text = car_type_split[j]+" "+str(member_json[i]['sedan_job'])+" ครั้ง"
									elif car_type_split[j] == "รถ SUV":
										car_type_text = car_type_split[j]+" "+str(member_json[i]['suv_job'])+" ครั้ง"
									else:
										car_type_text = car_type_split[j]+" "+str(member_json[i]['van_job'])+" ครั้ง"

									car_type_detail.append(car_type_text)

						communication_list = []

						for j in range(len(member_json[i]['communication'])):
							communication = db.communication.find_one({"_id": ObjectId(member_json[i]['communication'][j])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							communication_object = dumps(communication)
							communication_json = json.loads(communication_object)

							if member_lang == "en":
								lang_name = communication_json['lang_name_en']
							else:
								lang_name = communication_json['lang_name_th']

							communication_list.append({
								"communication_id" : communication_json['_id']['$oid'],
								"lang_name": lang_name,
								"lang_code": communication_json['lang_code'],
								"flag_image": communication_json['flag_image']
							})


						#เช็คการรับงานของคนขับจาก tb request_driver

						sd = datetime.strptime(request_driver_json['start_date'], '%Y-%m-%d').strftime('%Y-%m-%d')

						#2020-07-10 01:00:00
						start_datetime_obj = datetime.strptime(sd+" "+request_driver_json['start_time'], '%Y-%m-%d %H:%M:%S')
						end_datetime_obj = start_datetime_obj + timedelta(hours=int(request_driver_json['hour_amount']))

						#2020-07-10 13:00:00
						# end_datetime_obj = datetime.strptime(request_driver_json['end_date']+" "+request_driver_json['end_time'], '%Y-%m-%d %H:%M:%S')

						#2020-07-09 17:00:00
						before_start_datetime_obj = start_datetime_obj - timedelta(hours=8)
						#2020-07-10 21:00:00
						after_end_datetime_obj = end_datetime_obj + timedelta(hours=8)

						start_date = start_datetime_obj.strftime('%Y-%m-%d')
						start_time = start_datetime_obj.strftime('%H:%M:%S')
						end_date = end_datetime_obj.strftime('%Y-%m-%d')
						end_time = end_datetime_obj.strftime('%H:%M:%S')

						before_start_date = before_start_datetime_obj.strftime('%Y-%m-%d')
						before_start_time = before_start_datetime_obj.strftime('%H:%M:%S')
						after_end_date = after_end_datetime_obj.strftime('%Y-%m-%d')
						after_end_time = after_end_datetime_obj.strftime('%H:%M:%S')

						#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก ก่อนรับงานนี้ 8 ชม.
						check_before = db.request_driver.find_one({
																	"request_no": {"$ne": request_driver_json['request_no']},
																	"driver_id": member_json[i]['_id']['$oid'],
																	"start_date": before_start_date,
																	"start_time": {"$gte" : before_start_time},
																	"start_time": {"$lte" : start_time},
																	"request_status": {"$nin" : ["2","3"]}
																})

						#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก หลังจบงานนี้ 8 ชม.
						check_after = db.request_driver.find_one({
																	"request_no": {"$ne": request_driver_json['request_no']},
																	"driver_id": member_json[i]['_id']['$oid'],
																	"start_date": start_date,
																	"start_time": {"$gte" : end_time},
																	"start_time": {"$lte" : after_end_time},
																	"request_status": {"$nin" : ["2","3"]}
																})

						if member_json[i]['driver_rating'] is not None:
							driver_rating = round(float(member_json[i]['driver_rating']) , 1)
						else:
							driver_rating = float("0")

						#ถ้าไม่เจองาน ก่อนรับงานนี้ 8 ชม. และ หลังจบงานนี้ 8 ชม. จึงจะสามารถรับงานนี้ได้
						if check_before is None and check_after is None:
							member_list.append({
								"member_id" : member_json[i]['_id']['$oid'],
								"member_code": member_json[i]['member_code'],
								"member_username": member_json[i]['member_username'],
								"member_firstname_en": member_json[i]['member_firstname_en'],
								"member_lastname_en": member_json[i]['member_lastname_en'],
								"member_firstname_th": member_json[i]['member_firstname_th'],
								"member_lastname_th": member_json[i]['member_lastname_th'],
								"member_email": member_json[i]['member_email'],
								"member_tel": member_json[i]['member_tel'],
								"member_birthday": member_json[i]['member_birthday'],
								"member_gender" : member_json[i]['member_gender'],
								"member_gender_text" : member_gender_text,
								"member_type": member_json[i]['member_type'],
								"profile_image": member_json[i]['profile_image'],
								"driver_license_expire": member_json[i]['driver_license_expire'],
								"driver_license_no": member_json[i]['driver_license_no'],
								"car_type": member_json[i]['car_type'],
								"car_type_detail": car_type_detail,
								"car_gear": member_json[i]['car_gear'],
								"car_gear_text": car_gear_text,
								"service_area": member_json[i]['service_area'],
								"service_area_text": service_area_text,
								"communication": communication_list,
								"communication_text": communication_text,
								"workday": member_json[i]['workday'],
								"workday_text": workday_text,
								"special_skill": member_json[i]['special_skill'],
								"special_skill_text": special_skill_text,
								"driver_rating": driver_rating,
								"driver_level": member_json[i]['driver_level'],
								"level_name": level_name,
								"level_detail": level_detail,
								"level_image": level_image,
								"member_age" : member_age,
								"member_lang": member_json[i]['member_lang'],
								"member_token": member_json[i]['member_token'],
								"noti_key": member_json[i]['noti_key']
							})

				if len(member_list) > 0:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					check_before_object = dumps(check_before)
					check_before_json = json.loads(check_before_object)

					check_after_object = dumps(check_after)
					check_after_json = json.loads(check_after_object)

					result = {
								"status" : True,
								"msg" : get_api_message("edit_driver_request_list" , "get_edit_driver_request_list_success" , member_lang),
								"data" : member_list
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("edit_driver_request_list" , "driver_not_found" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "edit_driver_request_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def check_main_package_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params
	isset_start_date = "start_date" in params
	isset_start_time = "start_time" in params
	isset_hour_amount = "hour_amount" in params
	isset_same_location = "same_location" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id and isset_start_date and isset_start_time and isset_hour_amount and isset_same_location:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# ดึงเวลาปัจจุบัน
			current_date = datetime.now().strftime('%Y-%m-%d')

			#check start date
			current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
			add_date_obj = current_date_obj + timedelta(days=3)

			start_date = datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
			start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

			# ถ้าวันที่จองมากกว่า วันที่ปัจจุบัน+3 แสดงว่า สามารถจองได้ 
			if start_date_obj > add_date_obj:
				check_start_time_obj = datetime.strptime(params['start_time'], '%H:%M')

				#ถ้านาทีมากกว่า 30 ให้บวกชั่วโมงเพิ่ม 1 
				if int(check_start_time_obj.strftime('%M')) > 30:
					start_time_hour = int(check_start_time_obj.strftime('%H')) + 1
				else:
					start_time_hour = int(check_start_time_obj.strftime('%H'))

				if params['same_location'] == "1":
					check_hour_amount = int(params['hour_amount'])
				else:
					check_hour_amount = int(params['hour_amount']) + 1

				check_end_time = start_time_hour + int(params['hour_amount'])

				if check_end_time >= 24:
					result = { 
						"status" : False,
						"msg" : get_api_message("check_main_package_request" , "total_hours_amount_must_be_less_than_24" , member_lang)
					}
				else:
					member_package = db.member_package.find({
																"member_id": member_info['_id']['$oid'],
																"package_id": params['package_id'],
																"member_package_status": "1"
															}).sort([("end_date", 1),("updated_at", -1)])

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					main_package_type = member_package_json[0]['package_type']

					main_package_list = []
					use_amount = 0
					old_use_amount = 0
					start_overtime = '20:00'
					end_overtime = '05:00'
					start_overtime_int = 20
					end_overtime_int = 5
					sum_ot = 0
					count_member_package = len(member_package_json)

					if main_package_type == "hour":
						for i in range(len(member_package_json)):
							main_package_info = member_package_json[i]

							if member_lang == "en":
								main_package_name = main_package_info['package_name_en']
							else:
								main_package_name = main_package_info['package_name_th']

							if member_package_json[i]['package_usage_type'] == "share" and member_package_json[i]['company_package_id'] is not None:
								company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[i]['company_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								company_package_object = dumps(company_package)
								company_package_json = json.loads(company_package_object)

								remaining_amount = company_package_json['remaining_amount']
							else:
								remaining_amount = member_package_json[i]['remaining_amount']


							end_date = datetime.strptime(member_package_json[i]['end_date'], '%Y-%m-%d')
							today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
							
							delta = end_date - today
							remaining_date = delta.days

							#เช็คว่า member package ที่สามารถใช้งานได้ ต้องมี remaining_amount มากกว่า 0 และมี end_date น้อยกว่าหรือเท่ากับวันที่ปัจจุบัน
							if remaining_amount > 0 and remaining_date >= 0:
								old_use_amount = use_amount
								use_amount = use_amount + remaining_amount
								# 10 = 0 + 10
								# 20 = 10 + 10

								#ถ้ามากกว่าหรือเท่ากับแสดงว่าใช้งาน package นี้ได้
								if use_amount >= check_hour_amount:
									remainning_package = use_amount - check_hour_amount 
									usage_package = remaining_amount - remainning_package

									usage_amount_value = usage_package
									usage_hour_amount_value = usage_package

									#*****
									if i == 0:
										#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น
										hour_amount = check_hour_amount
										start_time_obj = datetime.strptime(params['start_time'], '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
									else:
										hour_amount = check_hour_amount
										#เซ็ตเวลา start_time ตั้งต้น
										st_obj = datetime.strptime(params['start_time'], '%H:%M')
										et_obj = st_obj + timedelta(hours=hour_amount)


										#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
										start_time_obj = st_obj + timedelta(hours=old_use_amount)
										end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)

									if int(start_time_obj.strftime('%M')) > 30:
										# + hour
										start_time_obj = start_time_obj + timedelta(hours=1)
										# - minute
										start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

										# + hour
										end_time_obj = end_time_obj + timedelta(hours=1)
										# - minute
										end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

									if int(end_time_obj.strftime('%H')) == 0:
										end_time_int = 24
									else:
										end_time_int = int(end_time_obj.strftime('%H'))

									if int(start_time_obj.strftime('%H')) == 0:
										start_time_int = 0
									else:
										start_time_int = int(start_time_obj.strftime('%H'))

									start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
									end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

									sum_normal_usage = 0
									sum_overtime_usage = 0
									ot_1 = 0
									case = 0
									normal_usage = 0
									overtime_usage = 0

									#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
									# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
									if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
										case = 1
										# if i == 0:
										# 	# 3 <= 5
										# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
										# 		overtime_usage = usage_hour_amount_value
										# 	# 6 > 5
										# 	else:
										# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

										# 	normal_usage = usage_hour_amount_value - overtime_usage
										# else:
										# 	# 3 <= 5
										# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
										# 		overtime_usage = usage_hour_amount_value
										# 	# 6 > 5
										# 	else:
										# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

										# 	normal_usage = usage_hour_amount_value - overtime_usage

										# 3 <= 5
										# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
										if (end_time_int <= end_overtime_int): 
											overtime_usage = usage_hour_amount_value
										# 6 > 5
										else:
											# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
											overtime_usage = end_overtime_int - start_time_int

										normal_usage = usage_hour_amount_value - overtime_usage

										sum_ot = sum_ot + overtime_usage
									#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
									# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
									elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
										# case = 2
										# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
										# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

										# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
										# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
										
										# overtime_usage = overtime_usage_1 + overtime_usage_2
										# normal_usage = hour_amount - overtime_usage

										case = 2
										if i == 0:
											# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
											check_usage = int(check_usage_obj.strftime('%H'))

											if check_usage > usage_hour_amount_value:
												normal_usage = usage_hour_amount_value
											else:
												normal_usage = check_usage

											overtime_usage = usage_hour_amount_value - normal_usage
										else:
											#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
											if sum_ot == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))

												if count_member_package == 0:
													# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
													overtime_usage = end_time_int - start_overtime_int
												else:
													overtime_usage = hour_amount - usage_hour_amount_value
											else:
												normal_usage = 0
												overtime_usage = usage_hour_amount_value

										sum_ot = sum_ot + overtime_usage
									#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
									# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
									elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
										case = 3
										# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
										normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
										normal_usage = int(normal_usage_obj.strftime('%H'))

										# overtime_usage = hour_amount - normal_usage

										overtime_usage = usage_hour_amount_value - normal_usage
										
									#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
									# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
									elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
										case = 4
										if i == 0:
											# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
											normal_usage = int(normal_usage_obj.strftime('%H'))
											# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
											overtime_usage = end_time_int - start_overtime_int
										else:
											#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage = 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
											if sum_ot == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))

												if hour_amount >= usage_hour_amount_value:
													# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
													overtime_usage = end_time_int - start_overtime_int
												else:
													overtime_usage = hour_amount - usage_hour_amount_value
													
											#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
											else:
												normal_usage = 0
												overtime_usage = usage_hour_amount_value
										
										sum_ot = sum_ot + overtime_usage

									normal_paid = normal_usage * main_package_info['normal_paid_rate']
									overtime_paid = overtime_usage * main_package_info['overtime_paid_rate']
									sum_paid = normal_paid + overtime_paid

									normal_received = normal_usage * main_package_info['normal_received_rate']
									overtime_received = overtime_usage * main_package_info['overtime_received_rate']
									sum_received = normal_received + overtime_received

									if member_package_json[0]['package_type'] == "hour":
										remaining_show = remaining_amount - (normal_usage + overtime_usage)
									else:
										remaining_show = remaining_amount - 1

									main_package_list.append({
										"member_package_id" : member_package_json[i]['_id']['$oid'],
										"package_id": member_package_json[i]['package_id'],
										"package_name": main_package_name,
										"package_type": member_package_json[i]['package_type'],
										"usage_amount": usage_amount_value,
										"usage_hour_amount": usage_hour_amount_value,
										"normal_usage": normal_usage,
										"overtime_usage": overtime_usage,
										"normal_paid_rate": main_package_info['normal_paid_rate'],
										"normal_received_rate": main_package_info['normal_received_rate'],
										"overtime_paid_rate": main_package_info['overtime_paid_rate'],
										"overtime_received_rate": main_package_info['overtime_received_rate'],
										
										"remaining_amount": remaining_show,
										
										# "sum_paid": sum_paid,
										# "sum_received": sum_received,

										# "case": case,
										# "i": i,
										# "end_time_obj": end_time_obj,
										# "start_time_obj": start_time_obj
									})

									break
								else:
									usage_amount_value = remaining_amount
									usage_hour_amount_value = remaining_amount

									#*****
									if i == 0:
										#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น
										hour_amount = check_hour_amount
										start_time_obj = datetime.strptime(params['start_time'], '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
									else:
										hour_amount = check_hour_amount
										#เซ็ตเวลา start_time ตั้งต้น
										st_obj = datetime.strptime(params['start_time'], '%H:%M')
										et_obj = st_obj + timedelta(hours=hour_amount)

										#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
										start_time_obj = st_obj + timedelta(hours=old_use_amount)
										end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)

									if int(start_time_obj.strftime('%M')) > 30:
										# + hour
										start_time_obj = start_time_obj + timedelta(hours=1)
										# - minute
										start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))
										# + hour
										end_time_obj = end_time_obj + timedelta(hours=1)
										# - minute
										end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

									if int(end_time_obj.strftime('%H')) == 0:
										end_time_int = 24
									else:
										end_time_int = int(end_time_obj.strftime('%H'))

									if int(start_time_obj.strftime('%H')) == 0:
										start_time_int = 0
									else:
										start_time_int = int(start_time_obj.strftime('%H'))

									start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
									end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

									sum_normal_usage = 0
									sum_overtime_usage = 0
									ot_1 = 0
									case = 0
									normal_usage = 0
									overtime_usage = 0

									#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
									# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
									if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
										# case = 1
										# normal_usage_obj = end_time_obj - timedelta(hours=end_overtime_int)
										# normal_usage = int(normal_usage_obj.strftime('%H'))
										# overtime_usage = hour_amount - normal_usage

										case = 1
										# if i == 0:
										# 	# 3 <= 5
										# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
										# 		overtime_usage = usage_hour_amount_value
										# 	# 6 > 5
										# 	else:
										# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

										# 	normal_usage = usage_hour_amount_value - overtime_usage
										# else:
										# 	# 3 <= 5
										# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
										# 		overtime_usage = usage_hour_amount_value
										# 	# 6 > 5
										# 	else:
										# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

										# 	normal_usage = usage_hour_amount_value - overtime_usage

										# 3 <= 5
										# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
										if (end_time_int <= end_overtime_int):
											overtime_usage = usage_hour_amount_value
										# 6 > 5
										else:
											# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
											overtime_usage = end_overtime_int - start_time_int

										normal_usage = usage_hour_amount_value - overtime_usage


										sum_ot = sum_ot + overtime_usage

									#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
									# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
									elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
										# case = 2
										# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
										# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

										# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
										# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
										
										# overtime_usage = overtime_usage_1 + overtime_usage_2
										# normal_usage = hour_amount - overtime_usage

										case = 2
										if i == 0:
											# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
											check_usage = int(check_usage_obj.strftime('%H'))

											if check_usage > usage_hour_amount_value:
												normal_usage = usage_hour_amount_value
											else:
												normal_usage = check_usage

											overtime_usage = usage_hour_amount_value - normal_usage
										else:
											#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
											if sum_ot == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))

												if count_member_package == 0:
													# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
													overtime_usage = end_time_int - start_overtime_int
												else:
													overtime_usage = hour_amount - usage_hour_amount_value
											else:
												normal_usage = 0
												overtime_usage = usage_hour_amount_value

										sum_ot = sum_ot + overtime_usage
									#case 3 : 10:00 >= 05:00 and 20:00 <= 20:00
									# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
									elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
										case = 3
										# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
										normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
										normal_usage = int(normal_usage_obj.strftime('%H'))

										overtime_usage = usage_hour_amount_value - normal_usage
									#case 4 : 10:00 >= 05:00 and 22:00 > 20:00 
									# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
									elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
										case = 4
										if i == 0:
											# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
											check_usage = int(check_usage_obj.strftime('%H'))

											if check_usage > usage_hour_amount_value:
												normal_usage = usage_hour_amount_value
											else:
												normal_usage = check_usage

											overtime_usage = usage_hour_amount_value - normal_usage
										else:
											#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
											if sum_ot == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))

												# if count_member_package == 0:
												# 	overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
												# else:
												# 	overtime_usage = hour_amount - usage_hour_amount_value

												# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
												overtime_usage = end_time_int - start_overtime_int
											else:
												normal_usage = 0
												overtime_usage = usage_hour_amount_value

										sum_ot = sum_ot + overtime_usage

									normal_paid = normal_usage * main_package_info['normal_paid_rate']
									overtime_paid = overtime_usage * main_package_info['overtime_paid_rate']
									sum_paid = normal_paid + overtime_paid

									normal_received = normal_usage * main_package_info['normal_received_rate']
									overtime_received = overtime_usage * main_package_info['overtime_received_rate']
									sum_received = normal_received + overtime_received

									if member_package_json[0]['package_type'] == "hour":
										remaining_show = remaining_amount - (normal_usage + overtime_usage)
									else:
										remaining_show = remaining_amount - 1

									main_package_list.append({
										"member_package_id" : member_package_json[i]['_id']['$oid'],
										"package_id": member_package_json[i]['package_id'],
										"package_name": main_package_name,
										"package_type": member_package_json[i]['package_type'],
										"usage_amount": usage_amount_value,
										"usage_hour_amount": usage_hour_amount_value,
										"normal_usage": normal_usage,
										"overtime_usage": overtime_usage,
										"normal_paid_rate": main_package_info['normal_paid_rate'],
										"normal_received_rate": main_package_info['normal_received_rate'],
										"overtime_paid_rate": main_package_info['overtime_paid_rate'],
										"overtime_received_rate": main_package_info['overtime_received_rate'],
										
										"remaining_amount": remaining_show,

										# "sum_paid": sum_paid,
										# "sum_received": sum_received,
										
										# "case": case,
										# "i": i,
										# "end_time_obj": end_time_obj,
										# "start_time_obj": start_time_obj
									})

								last_end_time_obj = end_time_obj

						if len(main_package_list) > 0:
							if use_amount >= check_hour_amount:
								result = {
											"status" : True,
											"msg" : get_api_message("check_main_package_request" , "you_can_use_this_package" , member_lang),
											"main_package_id" : params['package_id'],
											"main_package" : main_package_list
										}
							else:
								missing_amount = check_hour_amount - use_amount

								start_date_obj = datetime.strptime(params['start_date'], '%d/%m/%Y')
								start_workday = start_date_obj.strftime('%a')

								#weekend
								if start_workday == "Sun" or start_workday == "Sat":
									service_time_in = ["allday" , "weekend"]
								#weekday
								else:
									service_time_in = ["allday" , "weekday"]

								package = db.member_package.aggregate([
																		{
																			"$match": {
																				"package_id": {"$ne": params['package_id']},
																				"member_id": member_info['_id']['$oid'],
																				"package_type": "hour",
																				"service_time": {"$in": service_time_in},
																				"member_package_status": "1"
																			}
																		},
																		{
																			"$group" : {
																				"_id" : "$package_id"
																			}
																		}
																	])

								second_package_list = []
								
								if package is not None:
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									package_object = dumps(package)
									package_json = json.loads(package_object)

									all_remainning_amount = 0

									for i in range(len(package_json)):
										member_package = db.member_package.find({
																				"member_id": member_info['_id']['$oid'],
																				"package_id": package_json[i]['_id'],
																				"member_package_status": "1"
																			})

										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										member_package_object = dumps(member_package)
										member_package_json = json.loads(member_package_object)
										
										remaining_package_list = []

										for j in range(len(member_package_json)):
											end_date = datetime.strptime(member_package_json[j]['end_date'], '%Y-%m-%d')
											today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
											
											delta = end_date - today
											remaining_date = delta.days

											if remaining_date >= 0:
												#***#
												if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
													company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
													#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
													company_package_object = dumps(company_package)
													company_package_json = json.loads(company_package_object)

													second_package_remaining_amount = company_package_json['remaining_amount']
												else:
													second_package_remaining_amount = member_package_json[j]['remaining_amount']

												remaining_package_list.append({
													"remaining_date" : remaining_date,
													"remaining_amount" : second_package_remaining_amount
												})

												all_remainning_amount = all_remainning_amount + second_package_remaining_amount

										second_package_info = get_package_info(member_package_json[j]['package_id'])

										if member_lang == "en":
											second_package_name = second_package_info['package_name_en']
										else:
											second_package_name = second_package_info['package_name_th']

										if second_package_info['package_model'] == "special":
											package_model = "Special"
										else:
											package_model = "Normal"

										if second_package_info['package_type'] == "hour":
											if member_lang == "en":
												package_type_text = "Per Hour"
											else:
												package_type_text = "รายชั่วโมง"
											package_type_amount = second_package_info['hour_amount']
										else:
											if member_lang == "en":
												package_type_text = "Per Time"
											else:
												package_type_text = "รายครั้ง"
											package_type_amount = second_package_info['time_amount']

										if len(remaining_package_list) > 0:
											second_package_list.append({
												# "member_package_id" : member_package_json[j]['_id']['$oid'],
												# "company_package_id" : member_package_json[j]['company_package_id'],
												"package_id": member_package_json[j]['package_id'],
												"package_name": second_package_name,
												"package_model": package_model,
												"package_type": member_package_json[j]['package_type'],
												"package_type_text": package_type_text,
												"package_type_amount": package_type_amount,
												"total_usage_date": second_package_info['total_usage_date'],
												"package_image": second_package_info['package_image'],
												"remaining_package": remaining_package_list
											})

								#ถ้ามากกว่าให้ส่ง second package กลับไป
								if all_remainning_amount >= missing_amount:
									#ถ้าเป็น company user 
									if member_info['company_id'] is not None:
										start_overtime = '20:00'
										end_overtime = '05:00'
										start_overtime_int = 20
										end_overtime_int = 5
										hour_amount = missing_amount

										start_time = last_end_time_obj.strftime('%H:%M')

										start_time_obj = datetime.strptime(start_time, '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=hour_amount)

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0

										# 16 = 12 + 4
										if int(end_time_obj.strftime('%H')) == 0:
											st = 24
											end_time = 24
										else:
											st = int(start_time_obj.strftime('%H'))
											end_time = int(end_time_obj.strftime('%H'))

										# 16 < 20
										if end_time <= start_overtime_int:
											sum_normal_usage = missing_amount
											sum_overtime_usage = 0
										# 21 > 20
										else:
											# 1 = 22 - 21
											if st > start_overtime_int:
												sum_overtime_usage = end_time - st
												sum_normal_usage = missing_amount - sum_overtime_usage
											# 2 = 22 - 20
											else:
												sum_overtime_usage = end_time - start_overtime_int
												sum_normal_usage = missing_amount - sum_overtime_usage

										normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
										overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
										sum_paid = normal_paid + overtime_paid

										normal_received = sum_normal_usage * main_package_info['normal_received_rate']
										overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
										sum_received = normal_received + overtime_received



										billing = {
													"package_id": params['package_id'],
													"package_name": main_package_name,
													"package_type": "hour",
													"usage_hour_amount": missing_amount,
													"normal_usage": sum_normal_usage,
													"overtime_usage": sum_overtime_usage,
													"normal_paid_rate": main_package_info['normal_paid_rate'],
													"normal_received_rate": main_package_info['normal_received_rate'],
													"overtime_paid_rate": main_package_info['overtime_paid_rate'],
													"overtime_received_rate": main_package_info['overtime_received_rate'],
													"sum_paid": sum_paid,
													"sum_received": sum_received,
													"service_period": "normal",

													# "aaa": "aaa",
													# "st": st,
													# "missing_amount": missing_amount,
													# "sum_normal_usage": sum_normal_usage,
													# "sum_overtime_usage": sum_overtime_usage,
													# "end_time": end_time,
													# "last_end_time_obj": last_end_time_obj
												}
									#ถ้าเป็น normal user
									else:
										billing = []

									result = {
												"status" : False,
												"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_second_package" , member_lang),
												"main_package_id" : params['package_id'],
												"main_package" : main_package_list,
												"missing_amount": missing_amount,
												"second_package": second_package_list,
												"billing": billing
											}
								#ถ้าน้อยกว่า
								else:
									#ถ้าเป็น company user 
									if member_info['company_id'] is not None:
										start_overtime = '20:00'
										end_overtime = '05:00'
										start_overtime_int = 20
										end_overtime_int = 5
										hour_amount = missing_amount

										start_time = last_end_time_obj.strftime('%H:%M')

										start_time_obj = datetime.strptime(start_time, '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=hour_amount)

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0

										# 16 = 12 + 4
										if int(end_time_obj.strftime('%H')) == 0:
											st = 24
											end_time = 24
										else:
											st = int(start_time_obj.strftime('%H'))
											end_time = int(end_time_obj.strftime('%H'))

										# 16 < 20
										if end_time <= start_overtime_int:
											sum_normal_usage = missing_amount
											sum_overtime_usage = 0
										# 21 > 20
										else:
											# 1 = 22 - 21
											if st > start_overtime_int:
												sum_overtime_usage = end_time - st
												sum_normal_usage = missing_amount - sum_overtime_usage
											# 2 = 22 - 20
											else:
												sum_overtime_usage = end_time - start_overtime_int
												sum_normal_usage = missing_amount - sum_overtime_usage

										normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
										overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
										sum_paid = normal_paid + overtime_paid

										normal_received = sum_normal_usage * main_package_info['normal_received_rate']
										overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
										sum_received = normal_received + overtime_received

										billing = {
													"package_id": params['package_id'],
													"package_name": main_package_name,
													"package_type": "hour",
													"usage_hour_amount": missing_amount,
													"normal_usage": sum_normal_usage,
													"overtime_usage": sum_overtime_usage,
													"normal_paid_rate": main_package_info['normal_paid_rate'],
													"normal_received_rate": main_package_info['normal_received_rate'],
													"overtime_paid_rate": main_package_info['overtime_paid_rate'],
													"overtime_received_rate": main_package_info['overtime_received_rate'],
													"sum_paid": sum_paid,
													"sum_received": sum_received,
													"service_period": "normal",

													# "bbb": "bbb",
													# "st": st,
													# "missing_amount": missing_amount,
													# "sum_normal_usage": sum_normal_usage,
													# "sum_overtime_usage": sum_overtime_usage,
													# "end_time": end_time,
													# "last_end_time_obj": last_end_time_obj
												}

										result = {
													"status" : False,
													"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_billing" , member_lang),
													"main_package_id" : params['package_id'],
													"main_package" : main_package_list,
													"missing_amount": missing_amount,
													"second_package": [],
													"billing": billing
												}
									#ถ้าเป็น normal user
									else:
										result = {
													"status" : False,
													"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_other_main_package" , member_lang)
												}	
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_other_main_package" , member_lang)
									}	
					else:
						main_package_info = member_package_json[0]

						if member_lang == "en":
							main_package_name = main_package_info['package_name_en']
						else:
							main_package_name = main_package_info['package_name_th']

						if member_package_json[0]['package_usage_type'] == "share" and member_package_json[0]['company_package_id'] is not None:
							company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[0]['company_package_id'])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_package_object = dumps(company_package)
							company_package_json = json.loads(company_package_object)

							remaining_amount = company_package_json['remaining_amount']
						else:
							remaining_amount = member_package_json[0]['remaining_amount']


						end_date = datetime.strptime(member_package_json[0]['end_date'], '%Y-%m-%d')
						today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
						
						delta = end_date - today
						remaining_date = delta.days

						#เช็คว่า member package ที่สามารถใช้งานได้ ต้องมี remaining_amount มากกว่า 0 และมี end_date น้อยกว่าหรือเท่ากับวันที่ปัจจุบัน
						if remaining_amount > 0 and remaining_date >= 0:
							use_amount = 12

							#ถ้ามากกว่าหรือเท่ากับแสดงว่าใช้งาน package นี้ได้
							if use_amount >= check_hour_amount:
								remainning_package = use_amount - check_hour_amount 
								# 0 = 12 - 12
								usage_package = use_amount - remainning_package
								# 12 = 12 - 0

								usage_amount_value = 1
								usage_hour_amount_value = usage_package

								#*****
								#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น
								hour_amount = check_hour_amount
								start_time_obj = datetime.strptime(params['start_time'], '%H:%M')
								end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
								
								if int(start_time_obj.strftime('%M')) > 30:
									# + hour
									start_time_obj = start_time_obj + timedelta(hours=1)
									# - minute
									start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

									# + hour
									end_time_obj = end_time_obj + timedelta(hours=1)
									# - minute
									end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

								if int(end_time_obj.strftime('%H')) == 0:
									end_time_int = 24
								else:
									end_time_int = int(end_time_obj.strftime('%H'))

								if int(start_time_obj.strftime('%H')) == 0:
									start_time_int = 0
								else:
									start_time_int = int(start_time_obj.strftime('%H'))

								start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
								end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

								sum_normal_usage = 0
								sum_overtime_usage = 0
								ot_1 = 0
								case = 0
								normal_usage = 0
								overtime_usage = 0

								#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
								# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
								if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
									case = 1
									# if i == 0:
									# 	# 3 <= 5
									# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
									# 		overtime_usage = usage_hour_amount_value
									# 	# 6 > 5
									# 	else:
									# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

									# 	normal_usage = usage_hour_amount_value - overtime_usage
									# else:
									# 	# 3 <= 5
									# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
									# 		overtime_usage = usage_hour_amount_value
									# 	# 6 > 5
									# 	else:
									# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

									# 	normal_usage = usage_hour_amount_value - overtime_usage

									# 3 <= 5
									# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
									if (end_time_int <= end_overtime_int): 
										overtime_usage = usage_hour_amount_value
									# 6 > 5
									else:
										# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
										overtime_usage = end_overtime_int - start_time_int

									normal_usage = usage_hour_amount_value - overtime_usage

									sum_ot = sum_ot + overtime_usage
								#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
								# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
								elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
									# case = 2
									# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

									# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
									# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
									
									# overtime_usage = overtime_usage_1 + overtime_usage_2
									# normal_usage = hour_amount - overtime_usage

									case = 2
									# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									check_usage = int(check_usage_obj.strftime('%H'))

									if check_usage > usage_hour_amount_value:
										normal_usage = usage_hour_amount_value
									else:
										normal_usage = check_usage

									overtime_usage = usage_hour_amount_value - normal_usage
									sum_ot = sum_ot + overtime_usage
								#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
								# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
								elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
									case = 3
									# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									# overtime_usage = hour_amount - normal_usage

									overtime_usage = usage_hour_amount_value - normal_usage
									
								#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
								# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
								elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
									case = 4
									# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))
									# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
									overtime_usage = end_time_int - start_overtime_int
									sum_ot = sum_ot + overtime_usage

								normal_paid = normal_usage * main_package_info['normal_paid_rate']
								overtime_paid = overtime_usage * main_package_info['overtime_paid_rate']
								sum_paid = normal_paid + overtime_paid

								normal_received = normal_usage * main_package_info['normal_received_rate']
								overtime_received = overtime_usage * main_package_info['overtime_received_rate']
								sum_received = normal_received + overtime_received

								if member_package_json[0]['package_type'] == "hour":
									remaining_show = remaining_amount - (normal_usage + overtime_usage)
								else:
									remaining_show = remaining_amount - 1

								main_package_list.append({
									"member_package_id" : member_package_json[0]['_id']['$oid'],
									"package_id": member_package_json[0]['package_id'],
									"package_name": main_package_name,
									"package_type": member_package_json[0]['package_type'],
									"usage_amount": usage_amount_value,
									"usage_hour_amount": usage_hour_amount_value,
									"normal_usage": normal_usage,
									"overtime_usage": overtime_usage,
									"normal_paid_rate": float(main_package_info['normal_paid_rate']),
									"normal_received_rate": float(main_package_info['normal_received_rate']),
									"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
									"overtime_received_rate": float(main_package_info['overtime_received_rate']),
									
									"remaining_amount": remaining_show,

									# "sum_paid": sum_paid,
									# "sum_received": sum_received,

									# "case": case,
									# "end_time_obj": end_time_obj,
									# "start_time_obj": start_time_obj
								})

								result = {
											"status" : True,
											"msg" : get_api_message("check_main_package_request" , "you_can_use_this_package" , member_lang),
											"main_package_id" : params['package_id'],
											"main_package" : main_package_list
										}
							else:
								usage_amount_value = 1
								usage_hour_amount_value = use_amount

								#*****
								#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น
								hour_amount = check_hour_amount
								start_time_obj = datetime.strptime(params['start_time'], '%H:%M')
								end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)

								if int(start_time_obj.strftime('%M')) > 30:
									# + hour
									start_time_obj = start_time_obj + timedelta(hours=1)
									# - minute
									start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))
									# + hour
									end_time_obj = end_time_obj + timedelta(hours=1)
									# - minute
									end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

								if int(end_time_obj.strftime('%H')) == 0:
									end_time_int = 24
								else:
									end_time_int = int(end_time_obj.strftime('%H'))

								if int(start_time_obj.strftime('%H')) == 0:
									start_time_int = 0
								else:
									start_time_int = int(start_time_obj.strftime('%H'))

								start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
								end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

								sum_normal_usage = 0
								sum_overtime_usage = 0
								ot_1 = 0
								case = 0
								normal_usage = 0
								overtime_usage = 0

								#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
								# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
								if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
									# case = 1
									# normal_usage_obj = end_time_obj - timedelta(hours=end_overtime_int)
									# normal_usage = int(normal_usage_obj.strftime('%H'))
									# overtime_usage = hour_amount - normal_usage

									case = 1
									# if i == 0:
									# 	# 3 <= 5
									# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
									# 		overtime_usage = usage_hour_amount_value
									# 	# 6 > 5
									# 	else:
									# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

									# 	normal_usage = usage_hour_amount_value - overtime_usage
									# else:
									# 	# 3 <= 5
									# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
									# 		overtime_usage = usage_hour_amount_value
									# 	# 6 > 5
									# 	else:
									# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

									# 	normal_usage = usage_hour_amount_value - overtime_usage

									# 3 <= 5
									# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
									if (end_time_int <= end_overtime_int):
										overtime_usage = usage_hour_amount_value
									# 6 > 5
									else:
										# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
										overtime_usage = end_overtime_int - start_time_int

									normal_usage = usage_hour_amount_value - overtime_usage
									sum_ot = sum_ot + overtime_usage

								#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
								# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
								elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
									# case = 2
									# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

									# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
									# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
									
									# overtime_usage = overtime_usage_1 + overtime_usage_2
									# normal_usage = hour_amount - overtime_usage

									case = 2
									# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									check_usage = int(check_usage_obj.strftime('%H'))

									if check_usage > usage_hour_amount_value:
										normal_usage = usage_hour_amount_value
									else:
										normal_usage = check_usage

									overtime_usage = usage_hour_amount_value - normal_usage
									sum_ot = sum_ot + overtime_usage
								#case 3 : 10:00 >= 05:00 and 20:00 <= 20:00
								# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
								elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
									case = 3
									# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									overtime_usage = usage_hour_amount_value - normal_usage
								#case 4 : 10:00 >= 05:00 and 22:00 > 20:00 
								# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
								elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
									case = 4
									# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									check_usage = int(check_usage_obj.strftime('%H'))

									if check_usage > usage_hour_amount_value:
										normal_usage = usage_hour_amount_value
									else:
										normal_usage = check_usage

									overtime_usage = usage_hour_amount_value - normal_usage
									sum_ot = sum_ot + overtime_usage

								normal_paid = normal_usage * main_package_info['normal_paid_rate']
								overtime_paid = overtime_usage * main_package_info['overtime_paid_rate']
								sum_paid = normal_paid + overtime_paid

								normal_received = normal_usage * main_package_info['normal_received_rate']
								overtime_received = overtime_usage * main_package_info['overtime_received_rate']
								sum_received = normal_received + overtime_received

								if member_package_json[0]['package_type'] == "hour":
									remaining_show = remaining_amount - (normal_usage + overtime_usage)
								else:
									remaining_show = remaining_amount - 1

								main_package_list.append({
									"member_package_id" : member_package_json[0]['_id']['$oid'],
									"package_id": member_package_json[0]['package_id'],
									"package_name": main_package_name,
									"package_type": member_package_json[0]['package_type'],
									"usage_amount": usage_amount_value,
									"usage_hour_amount": usage_hour_amount_value,
									"normal_usage": normal_usage,
									"overtime_usage": overtime_usage,
									"normal_paid_rate": float(main_package_info['normal_paid_rate']),
									"normal_received_rate": float(main_package_info['normal_received_rate']),
									"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
									"overtime_received_rate": float(main_package_info['overtime_received_rate']),
									
									"remaining_amount": remaining_show,
									# "sum_paid": sum_paid,
									# "sum_received": sum_received,
									
									# "case": case,
									# "end_time_obj": end_time_obj,
									# "start_time_obj": start_time_obj
								})

								last_end_time_obj = end_time_obj
								missing_amount = check_hour_amount - use_amount

								start_date_obj = datetime.strptime(params['start_date'], '%d/%m/%Y')
								start_workday = start_date_obj.strftime('%a')

								#weekend
								if start_workday == "Sun" or start_workday == "Sat":
									service_time_in = ["allday" , "weekend"]
								#weekday
								else:
									service_time_in = ["allday" , "weekday"]

								package = db.member_package.aggregate([
																		{
																			"$match": {
																				"package_id": {"$ne": params['package_id']},
																				"member_id": member_info['_id']['$oid'],
																				"package_type": "hour",
																				"service_time": {"$in": service_time_in},
																				"member_package_status": "1"
																			}
																		},
																		{
																			"$group" : {
																				"_id" : "$package_id"
																			}
																		}
																	])

								second_package_list = []
								
								if package is not None:
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									package_object = dumps(package)
									package_json = json.loads(package_object)

									all_remainning_amount = 0

									for i in range(len(package_json)):
										member_package = db.member_package.find({
																				"member_id": member_info['_id']['$oid'],
																				"package_id": package_json[i]['_id'],
																				"member_package_status": "1"
																			})

										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										member_package_object = dumps(member_package)
										member_package_json = json.loads(member_package_object)
										
										remaining_package_list = []

										for j in range(len(member_package_json)):
											end_date = datetime.strptime(member_package_json[j]['end_date'], '%Y-%m-%d')
											today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
											
											delta = end_date - today
											remaining_date = delta.days

											if remaining_date >= 0:
												#***#
												if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
													company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
													#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
													company_package_object = dumps(company_package)
													company_package_json = json.loads(company_package_object)

													second_package_remaining_amount = company_package_json['remaining_amount']
												else:
													second_package_remaining_amount = member_package_json[j]['remaining_amount']

												remaining_package_list.append({
													"remaining_date" : remaining_date,
													"remaining_amount" : second_package_remaining_amount
												})

												all_remainning_amount = all_remainning_amount + second_package_remaining_amount

										second_package_info = get_package_info(member_package_json[j]['package_id'])

										if member_lang == "en":
											package_name = second_package_info['package_name_en']
										else:
											package_name = second_package_info['package_name_th']

										if second_package_info['package_model'] == "special":
											package_model = "Special"
										else:
											package_model = "Normal"

										if second_package_info['package_type'] == "hour":
											if member_lang == "en":
												package_type_text = "Per Hour"
											else:
												package_type_text = "รายชั่วโมง"
											package_type_amount = second_package_info['hour_amount']
										else:
											if member_lang == "en":
												package_type_text = "Per Time"
											else:
												package_type_text = "รายครั้ง"
											package_type_amount = second_package_info['time_amount']

										if len(remaining_package_list) > 0:
											second_package_list.append({
												# "member_package_id" : member_package_json[j]['_id']['$oid'],
												# "company_package_id" : member_package_json[j]['company_package_id'],
												"package_id": member_package_json[j]['package_id'],
												"package_name": package_name,
												"package_model": package_model,
												"package_type": member_package_json[j]['package_type'],
												"package_type_text": package_type_text,
												"package_type_amount": package_type_amount,
												"total_usage_date": second_package_info['total_usage_date'],
												"package_image": second_package_info['package_image'],
												"remaining_package": remaining_package_list
											})				

								#ถ้ามากกว่าให้ส่ง second package กลับไป
								if all_remainning_amount >= missing_amount:
									#ถ้าเป็น company user 
									if member_info['company_id'] is not None:
										start_overtime = '20:00'
										end_overtime = '05:00'
										start_overtime_int = 20
										end_overtime_int = 5
										hour_amount = missing_amount

										start_time = last_end_time_obj.strftime('%H:%M')

										start_time_obj = datetime.strptime(start_time, '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=hour_amount)

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0

										# 16 = 12 + 4
										if int(end_time_obj.strftime('%H')) == 0:
											st = 24
											end_time = 24
										else:
											st = int(start_time_obj.strftime('%H'))
											end_time = int(end_time_obj.strftime('%H'))

										# 16 < 20
										if end_time <= start_overtime_int:
											sum_normal_usage = missing_amount
											sum_overtime_usage = 0
										# 21 > 20
										else:
											# 1 = 22 - 21
											if st > start_overtime_int:
												sum_overtime_usage = end_time - st
												sum_normal_usage = missing_amount - sum_overtime_usage
											# 2 = 22 - 20
											else:
												sum_overtime_usage = end_time - start_overtime_int
												sum_normal_usage = missing_amount - sum_overtime_usage

										normal_paid = sum_normal_usage * float(main_package_info['normal_paid_rate'])
										overtime_paid = sum_overtime_usage * float(main_package_info['overtime_paid_rate'])
										sum_paid = normal_paid + overtime_paid

										normal_received = sum_normal_usage * float(main_package_info['normal_received_rate'])
										overtime_received = sum_overtime_usage * float(main_package_info['overtime_received_rate'])
										sum_received = normal_received + overtime_received

										billing = {
													"package_id": params['package_id'],
													"package_name": main_package_name,
													"package_type": "hour",
													"usage_hour_amount": missing_amount,
													"normal_usage": sum_normal_usage,
													"overtime_usage": sum_overtime_usage,
													"normal_paid_rate": float(main_package_info['normal_paid_rate']),
													"normal_received_rate": float(main_package_info['normal_received_rate']),
													"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
													"overtime_received_rate": float(main_package_info['overtime_received_rate']),
													"sum_paid": sum_paid,
													"sum_received": sum_received,
													"service_period": "normal",

													# "ccc": "ccc",
													# "st": st,
													# "missing_amount": missing_amount,
													# "sum_normal_usage": sum_normal_usage,
													# "sum_overtime_usage": sum_overtime_usage,
													# "end_time": end_time,
													# "last_end_time_obj": last_end_time_obj
												}
									#ถ้าเป็น normal user
									else:
										billing = []

									result = {
												"status" : False,
												"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_second_package" , member_lang),
												"main_package_id" : params['package_id'],
												"main_package" : main_package_list,
												"missing_amount": missing_amount,
												"second_package": second_package_list,
												"billing": billing,
												# "last_end_time_obj": last_end_time_obj
											}
								#ถ้าน้อยกว่า
								else:
									#ถ้าเป็น company user 
									if member_info['company_id'] is not None:
										start_overtime = '20:00'
										end_overtime = '05:00'
										start_overtime_int = 20
										end_overtime_int = 5
										hour_amount = missing_amount

										start_time = last_end_time_obj.strftime('%H:%M')

										start_time_obj = datetime.strptime(start_time, '%H:%M')
										end_time_obj = start_time_obj + timedelta(hours=hour_amount)

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0

										# 16 = 12 + 4
										if int(end_time_obj.strftime('%H')) == 0:
											st = 24
											end_time = 24
										else:
											st = int(start_time_obj.strftime('%H'))
											end_time = int(end_time_obj.strftime('%H'))

										# 16 < 20
										if end_time <= start_overtime_int:
											sum_normal_usage = missing_amount
											sum_overtime_usage = 0
										# 21 > 20
										else:
											# 1 = 22 - 21
											if st > start_overtime_int:
												sum_overtime_usage = end_time - st
												sum_normal_usage = missing_amount - sum_overtime_usage
											# 2 = 22 - 20
											else:
												sum_overtime_usage = end_time - start_overtime_int
												sum_normal_usage = missing_amount - sum_overtime_usage

										normal_paid = sum_normal_usage * float(main_package_info['normal_paid_rate'])
										overtime_paid = sum_overtime_usage * float(main_package_info['overtime_paid_rate'])
										sum_paid = normal_paid + overtime_paid

										normal_received = sum_normal_usage * float(main_package_info['normal_received_rate'])
										overtime_received = sum_overtime_usage * float(main_package_info['overtime_received_rate'])
										sum_received = normal_received + overtime_received


										billing = {
													"package_id": params['package_id'],
													"package_name": main_package_name,
													"package_type": "hour",
													"usage_hour_amount": missing_amount,
													"normal_usage": sum_normal_usage,
													"overtime_usage": sum_overtime_usage,
													"normal_paid_rate": float(main_package_info['normal_paid_rate']),
													"normal_received_rate": float(main_package_info['normal_received_rate']),
													"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
													"overtime_received_rate": float(main_package_info['overtime_received_rate']),
													"sum_paid": sum_paid,
													"sum_received": sum_received,
													"service_period": "normal",

													# "ddd": "ddd",
													# "st": st,
													# "missing_amount": missing_amount,
													# "sum_normal_usage": sum_normal_usage,
													# "sum_overtime_usage": sum_overtime_usage,
													# "end_time": end_time,
													# "last_end_time_obj": last_end_time_obj
												}

										result = {
													"status" : False,
													"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_billing" , member_lang),
													"main_package_id" : params['package_id'],
													"main_package" : main_package_list,
													"missing_amount": missing_amount,
													"second_package": [],
													"billing": billing
												}
									#ถ้าเป็น normal user
									else:
										result = {
													"status" : False,
													"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_other_main_package" , member_lang)
												}	
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("check_main_package_request" , "this_package_is_not_enough_please_select_other_main_package" , member_lang)
									}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("check_main_package_request" , "the_start_date_must_be_3_days_more_than_the_current_date" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "check_main_package_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def check_second_package_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_second_package = "second_package" in params
	isset_missing_amount = "missing_amount" in params,
	isset_hour_amount = "hour_amount" in params
	isset_start_time = "start_time" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_second_package and isset_missing_amount and isset_hour_amount and isset_start_time:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			second_package_list = []
			use_amount = 0
			old_use_amount = 0
			start_overtime = '20:00'
			end_overtime = '05:00'
			start_overtime_int = 20
			end_overtime_int = 5
			sum_ot = 0

			member_package_in = []

			#วน loop เอา member_package_id มาใส่ array เพื่อนำไป orderby อีกครั้ง
			for i in range(len(params['second_package'])):
				# package_info = get_package_info(params['second_package'][i])

				mp = db.member_package.find({
												"member_id": member_info['_id']['$oid'],
												"package_id": params['second_package'][i],
												"package_type": "hour"
											})

				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				mp_object = dumps(mp)
				mp_json = json.loads(mp_object)

				for j in range(len(mp_json)):
					if mp_json[j]['package_usage_type'] == "share" and mp_json[j]['company_package_id'] is not None:
						company_package = db.company_package.find_one({"_id": ObjectId(mp_json[j]['company_package_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						company_package_object = dumps(company_package)
						company_package_json = json.loads(company_package_object)

						remaining_amount = company_package_json['remaining_amount']
					else:
						remaining_amount = mp_json[j]['remaining_amount']

					end_date = datetime.strptime(mp_json[j]['end_date'], '%Y-%m-%d')
					today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
					
					delta = end_date - today
					remaining_date = delta.days

					#เช็คว่า member package ที่สามารถใช้งานได้ ต้องมี remaining_amount มากกว่า 0 และมี end_date น้อยกว่าหรือเท่ากับวันที่ปัจจุบัน
					if remaining_amount > 0 and remaining_date >= 0:
						mp_id = mp_json[j]['_id']['$oid']
						member_package_in.append(ObjectId(mp_id))

			# ดึง member_package อีกรอบเพื่อเอาข้อมูลที่เหลือวันใช้งานน้อยมาใช้ก่อน
			member_package = db.member_package.find({
														"_id": {"$in" : member_package_in} 
													}).sort([("end_date", 1)])

			if member_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("check_second_package_request" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_package_object = dumps(member_package)
				member_package_json = json.loads(member_package_object)

				member_package_list = []

				for j in range(len(member_package_json)):
					# second_package_info = get_package_info(member_package_json[j]['package_id'])

					second_package_info = member_package_json[j]
					
					if member_lang == "en":
						package_name = second_package_info['package_name_en']
					else:
						package_name = second_package_info['package_name_th']

					if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
						company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						company_package_object = dumps(company_package)
						company_package_json = json.loads(company_package_object)

						remaining_amount = company_package_json['remaining_amount']
					else:
						remaining_amount = member_package_json[j]['remaining_amount']

					old_use_amount = use_amount
					use_amount = use_amount + remaining_amount
					#0 = 0 + 3

					#3 >= 1 
					#ถ้ามากกว่าหรือเท่ากับแสดงว่าใช้งาน package นี้ได้
					if use_amount >= params['missing_amount']:
						remainning_package = use_amount - params['missing_amount'] 
						usage_package = remaining_amount - remainning_package

						usage_amount_value = usage_package
						usage_hour_amount_value = usage_package

						if j == 0:
							#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น

							#start_time = 06:00 , end_time = 19:00 , hour_amount = 13
							#missing_amount = 1
							#new_start_time = end_time_int - missing_amount
							#18 = 19 - 1
							#new_hour_amount = missing_amount

							hour_amount = params['missing_amount']
							start_time = params['start_time']

							#เซ็ตเวลา start_time ตั้งต้นจาก package หลัก
							st_obj = datetime.strptime(start_time, '%H:%M')
							et_obj = st_obj + timedelta(hours=params['hour_amount'])

							#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
							start_time_obj = et_obj - timedelta(hours=hour_amount)
							end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
						else:
							hour_amount = usage_hour_amount_value
							start_time = last_end_time_obj.strftime('%H:%M')

							#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
							start_time_obj = datetime.strptime(start_time, '%H:%M')
							end_time_obj = start_time_obj + timedelta(hours=hour_amount)

						if int(start_time_obj.strftime('%M')) > 30:
							# + hour
							start_time_obj = start_time_obj + timedelta(hours=1)
							# - minute
							start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

							# + hour
							end_time_obj = end_time_obj + timedelta(hours=1)
							# - minute
							end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

						if int(end_time_obj.strftime('%H')) == 0:
							end_time_int = 24
						else:
							end_time_int = int(end_time_obj.strftime('%H'))

						if int(start_time_obj.strftime('%H')) == 0:
							start_time_int = 0
						else:
							start_time_int = int(start_time_obj.strftime('%H'))

						start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
						end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

						sum_normal_usage = 0
						sum_overtime_usage = 0
						ot_1 = 0
						case = 0
						normal_usage = 0
						overtime_usage = 0

						#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
						# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
						if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
							case = 1
							# if i == 0:
							# 	# 3 <= 5
							# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
							# 		overtime_usage = usage_hour_amount_value
							# 	# 6 > 5
							# 	else:
							# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

							# 	normal_usage = usage_hour_amount_value - overtime_usage
							# else:
							# 	# 3 <= 5
							# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
							# 		overtime_usage = usage_hour_amount_value
							# 	# 6 > 5
							# 	else:
							# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

							# 	normal_usage = usage_hour_amount_value - overtime_usage

							# 3 <= 5
							# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
							if (end_time_int <= end_overtime_int): 
								overtime_usage = usage_hour_amount_value
							# 6 > 5
							else:
								# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
								overtime_usage = end_overtime_int - start_time_int

							normal_usage = usage_hour_amount_value - overtime_usage

							sum_ot = sum_ot + overtime_usage
						#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
						# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
						elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
							# case = 2
							# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
							# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

							# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
							# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
							
							# overtime_usage = overtime_usage_1 + overtime_usage_2
							# normal_usage = hour_amount - overtime_usage

							case = 2
							if j == 0:
								# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
								check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
								check_usage = int(check_usage_obj.strftime('%H'))

								if check_usage > usage_hour_amount_value:
									normal_usage = usage_hour_amount_value
								else:
									normal_usage = check_usage

								overtime_usage = usage_hour_amount_value - normal_usage
							else:
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								if sum_ot == 0:
									# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									if count_member_package == 0:
										# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
										overtime_usage = end_time_int - start_overtime_int
									else:
										overtime_usage = hour_amount - usage_hour_amount_value
								else:
									normal_usage = 0
									overtime_usage = usage_hour_amount_value

							sum_ot = sum_ot + overtime_usage
						#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
						# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
						elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
							case = 3
							# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
							normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
							normal_usage = int(normal_usage_obj.strftime('%H'))

							# overtime_usage = hour_amount - normal_usage

							overtime_usage = usage_hour_amount_value - normal_usage
							
						#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
						# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
						elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
							case = 4
							if j == 0:
								# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
								normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
								normal_usage = int(normal_usage_obj.strftime('%H'))
								# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
								overtime_usage = end_time_int - start_overtime_int
							else:
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage = 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								if sum_ot == 0:
									# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									if hour_amount >= usage_hour_amount_value:
										# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
										overtime_usage = end_time_int - start_overtime_int
									else:
										overtime_usage = hour_amount - usage_hour_amount_value
										
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								else:
									normal_usage = 0
									overtime_usage = usage_hour_amount_value
							
							sum_ot = sum_ot + overtime_usage

						normal_paid = normal_usage * float(second_package_info['normal_paid_rate'])
						overtime_paid = overtime_usage * float(second_package_info['overtime_paid_rate'])
						sum_paid = normal_paid + overtime_paid

						normal_received = normal_usage * float(second_package_info['normal_received_rate'])
						overtime_received = overtime_usage * float(second_package_info['overtime_received_rate'])
						sum_received = normal_received + overtime_received
						remaining_show = remaining_amount - (normal_usage + overtime_usage)

						second_package_list.append({
							"member_package_id" : member_package_json[j]['_id']['$oid'],
							"package_id": member_package_json[j]['package_id'],
							"package_name": package_name,
							"package_type": member_package_json[j]['package_type'],
							"usage_amount": usage_amount_value,
							"usage_hour_amount": usage_hour_amount_value,

							"normal_usage": normal_usage,
							"overtime_usage": overtime_usage,
							"normal_paid_rate": float(second_package_info['normal_paid_rate']),
							"normal_received_rate": float(second_package_info['normal_received_rate']),
							"overtime_paid_rate": float(second_package_info['overtime_paid_rate']),
							"overtime_received_rate": float(second_package_info['overtime_received_rate']),
							
							"remaining_amount": remaining_show,

							# "sum_paid": sum_paid,
							# "sum_received": sum_received,

							# "case": case,
							# "j": j,
							# "end_time_obj": end_time_obj,
							# "start_time_obj": start_time_obj,

							# "st_obj": st_obj,
							# "et_obj": et_obj,
						})
						break
					else:
						usage_amount_value = remaining_amount
						usage_hour_amount_value = remaining_amount

						if j == 0:
							#เซ็ตเวลา start_time ตั้งต้น และเวลา end_time ล่าสุดตอนนั้น

							#start_time = 06:00 , end_time = 19:00 , hour_amount = 13
							#missing_amount = 1
							#new_start_time = end_time_int - missing_amount
							#18 = 19 - 1
							#new_hour_amount = missing_amount

							hour_amount = params['missing_amount']
							start_time = params['start_time']

							#เซ็ตเวลา start_time ตั้งต้นจาก package หลัก
							st_obj = datetime.strptime(start_time, '%H:%M')
							et_obj = st_obj + timedelta(hours=params['hour_amount'])

							#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
							start_time_obj = et_obj - timedelta(hours=hour_amount)
							end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
						else:
							hour_amount = usage_hour_amount_value
							start_time = last_end_time_obj.strftime('%H:%M')

							#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
							start_time_obj = datetime.strptime(start_time, '%H:%M')
							end_time_obj = start_time_obj + timedelta(hours=hour_amount)




						if int(start_time_obj.strftime('%M')) > 30:
							# + hour
							start_time_obj = start_time_obj + timedelta(hours=1)
							# - minute
							start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

							# + hour
							end_time_obj = end_time_obj + timedelta(hours=1)
							# - minute
							end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

						if int(end_time_obj.strftime('%H')) == 0:
							end_time_int = 24
						else:
							end_time_int = int(end_time_obj.strftime('%H'))

						if int(start_time_obj.strftime('%H')) == 0:
							start_time_int = 0
						else:
							start_time_int = int(start_time_obj.strftime('%H'))

						start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
						end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

						sum_normal_usage = 0
						sum_overtime_usage = 0
						ot_1 = 0
						case = 0
						normal_usage = 0
						overtime_usage = 0

						#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
						# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
						if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
							case = 1
							# if i == 0:
							# 	# 3 <= 5
							# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
							# 		overtime_usage = usage_hour_amount_value
							# 	# 6 > 5
							# 	else:
							# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

							# 	normal_usage = usage_hour_amount_value - overtime_usage
							# else:
							# 	# 3 <= 5
							# 	if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))): 
							# 		overtime_usage = usage_hour_amount_value
							# 	# 6 > 5
							# 	else:
							# 		overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))

							# 	normal_usage = usage_hour_amount_value - overtime_usage

							# 3 <= 5
							# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
							if (end_time_int <= end_overtime_int): 
								overtime_usage = usage_hour_amount_value
							# 6 > 5
							else:
								# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
								overtime_usage = end_overtime_int - start_time_int

							normal_usage = usage_hour_amount_value - overtime_usage

							sum_ot = sum_ot + overtime_usage
						#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
						# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
						elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
							# case = 2
							# overtime_usage_1_obj = end_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
							# overtime_usage_1 = int(overtime_usage_1_obj.strftime('%H'))

							# overtime_usage_2_obj = end_time_obj - timedelta(hours=start_overtime_int)
							# overtime_usage_2 = int(overtime_usage_2_obj.strftime('%H'))
							
							# overtime_usage = overtime_usage_1 + overtime_usage_2
							# normal_usage = hour_amount - overtime_usage

							case = 2
							if j == 0:
								# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
								check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
								check_usage = int(check_usage_obj.strftime('%H'))

								if check_usage > usage_hour_amount_value:
									normal_usage = usage_hour_amount_value
								else:
									normal_usage = check_usage

								overtime_usage = usage_hour_amount_value - normal_usage
							else:
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								if sum_ot == 0:
									# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									if count_member_package == 0:
										# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
										overtime_usage = end_time_int - start_overtime_int
									else:
										overtime_usage = hour_amount - usage_hour_amount_value
								else:
									normal_usage = 0
									overtime_usage = usage_hour_amount_value

							sum_ot = sum_ot + overtime_usage
						#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
						# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
						elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
							case = 3
							# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
							normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
							normal_usage = int(normal_usage_obj.strftime('%H'))

							# overtime_usage = hour_amount - normal_usage

							overtime_usage = usage_hour_amount_value - normal_usage
							
						#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
						# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
						elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
							case = 4
							if j == 0:
								# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
								normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
								normal_usage = int(normal_usage_obj.strftime('%H'))
								# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
								overtime_usage = end_time_int - start_overtime_int
							else:
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage = 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								if sum_ot == 0:
									# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
									normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
									normal_usage = int(normal_usage_obj.strftime('%H'))

									if hour_amount >= usage_hour_amount_value:
										# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
										overtime_usage = end_time_int - start_overtime_int
									else:
										overtime_usage = hour_amount - usage_hour_amount_value
										
								#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
								else:
									normal_usage = 0
									overtime_usage = usage_hour_amount_value
							
							sum_ot = sum_ot + overtime_usage

						normal_paid = normal_usage * float(second_package_info['normal_paid_rate'])
						overtime_paid = overtime_usage * float(second_package_info['overtime_paid_rate'])
						sum_paid = normal_paid + overtime_paid

						normal_received = normal_usage * float(second_package_info['normal_received_rate'])
						overtime_received = overtime_usage * float(second_package_info['overtime_received_rate'])
						sum_received = normal_received + overtime_received
						remaining_show = remaining_amount - (normal_usage + overtime_usage)

						second_package_list.append({
							"member_package_id" : member_package_json[j]['_id']['$oid'],
							"package_id": member_package_json[j]['package_id'],
							"package_name": package_name,
							"package_type": member_package_json[j]['package_type'],
							"usage_amount": usage_amount_value,
							"usage_hour_amount": usage_hour_amount_value,

							"normal_usage": normal_usage,
							"overtime_usage": overtime_usage,
							"normal_paid_rate": float(second_package_info['normal_paid_rate']),
							"normal_received_rate": float(second_package_info['normal_received_rate']),
							"overtime_paid_rate": float(second_package_info['overtime_paid_rate']),
							"overtime_received_rate": float(second_package_info['overtime_received_rate']),
							
							"remaining_amount": remaining_show,

							# "sum_paid": sum_paid,
							# "sum_received": sum_received,

							# "case": case,
							# "j": j,
							# "end_time_obj": end_time_obj,
							# "start_time_obj": start_time_obj,

							# "aaaaaa": use_amount

							# "st_obj": st_obj,
							# "et_obj": et_obj,
							
						})

					last_end_time_obj = end_time_obj

				if use_amount >= params['missing_amount']:
					result = {
								"status" : True,
								"msg" : get_api_message("check_second_package_request" , "you_can_use_this_package" , member_lang),
								"second_package_list" : second_package_list
							}
				else:
					missing_amount = params['missing_amount'] - use_amount

					result = {
								"status" : False,
								"msg" : get_api_message("check_second_package_request" , "this_package_is_not_enough_please_select_other_second_package" , member_lang),
								"second_package_list" : second_package_list,
								"missing_amount" : missing_amount
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "check_second_package_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def get_special_request_form(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_id = "package_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			package = db.package.find_one({
											"_id": ObjectId(params['package_id']),
											"package_status": "1"
										})
			if package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_special_request_form" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_object = dumps(package)
				package_json = json.loads(package_object)

				communication_list = []
				for i in range(len(package_json['communication'])):
					communication = db.communication.find_one({"_id": ObjectId(package_json['communication'][i])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					communication_object = dumps(communication)
					communication_json = json.loads(communication_object)

					if member_lang == "en":
						lang_name = communication_json['lang_name_en']
					else:
						lang_name = communication_json['lang_name_th']

					communication_list.append({
						"communication_id" : communication_json['_id']['$oid'],
						"lang_name": lang_name,
						"lang_code": communication_json['lang_code'],
						"flag_image": communication_json['flag_image']
					})

				driver_gender_list = [
										{"code": "male","name": "ชาย"},
										{"code": "female","name": "หญิง"}
									]

				driver_age_range = db.driver_age_range.find()
				driver_age_range_list = []

				if driver_age_range is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					driver_age_range_object = dumps(driver_age_range)
					driver_age_range_json = json.loads(driver_age_range_object)

					for i in range(len(driver_age_range_json)):
						driver_age_range_list.append({
							"id" : driver_age_range_json[i]['_id']['$oid'],
							"range": driver_age_range_json[i]['age_range']
						})

				special_skill = db.special_skill.find({"skill_status": "1"})
				special_skill_list = []

				if special_skill is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					special_skill_object = dumps(special_skill)
					special_skill_json = json.loads(special_skill_object)

					for i in range(len(special_skill_json)):
						if member_lang == "en":
							skill_name = special_skill_json[i]['skill_en']
						else:
							skill_name = special_skill_json[i]['skill_th']

						special_skill_list.append({
							"skill_id" : special_skill_json[i]['_id']['$oid'],
							"skill_name": skill_name
						})

				result = {
							"status" : True,
							"msg" : get_api_message("get_special_request_form" , "get_special_request_form_success" , member_lang),
							"driver_gender" : driver_gender_list,
							"driver_age_range" : driver_age_range_list,
							"communication" : communication_list,
							"special_skill" : special_skill_list
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_special_request_form"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def check_completed_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if company_id is None:
				#เช็คว่ามีงานที่จองโดย member_id นี้และมีสถานะเป็น กำลังเดินทาง และจบงานไม่สำเร็จ อยู่หรือไม่ 
				#ถ้ามีสถานะเป็น กำลังเดินทาง และจบงานไม่สำเร็จ จะไม่สามารถจองคนขับได้
				check_request_driver = db.request_driver.find({
																"member_id": member_id,
																"job_status": {"$in" : ["5","6","7","9","11"]}
															}).count()
			else: #company_id != null
				check_request_driver = 0
			
			if check_request_driver == 0:
				result = {
							"status" : True,
							"msg" : get_api_message("check_completed_request" , "request_completed" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("check_completed_request" , "please_book_another_time_after_the_current_request_is_over" , member_lang)
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "check_completed_request"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def add_driver_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_start_date = "start_date" in params
	isset_start_time = "start_time" in params
	isset_hour_amount = "hour_amount" in params
	isset_from_location_name = "from_location_name" in params
	isset_from_location_address = "from_location_address" in params
	isset_to_location_name = "to_location_name" in params
	isset_to_location_address = "to_location_address" in params
	isset_from_latitude = "from_latitude" in params
	isset_from_longitude = "from_longitude" in params
	isset_to_latitude = "to_latitude" in params
	isset_to_longitude = "to_longitude" in params
	isset_main_package_id = "main_package_id" in params
	isset_main_package = "main_package" in params
	isset_second_package_type = "second_package_type" in params
	isset_second_package = "second_package" in params
	isset_billing = "billing" in params
	isset_request_to = "request_to" in params
	isset_passenger_id = "passenger_id" in params
	isset_car_id = "car_id" in params
	isset_car_group = "car_group" in params
	isset_driver_gender = "driver_gender" in params
	isset_driver_age_range = "driver_age_range" in params
	isset_communication = "communication" in params
	isset_special_skill = "special_skill" in params
	isset_driver_list = "driver_list" in params
	isset_driver_note = "driver_note" in params

	#if isset_accept and isset_content_type and isset_token and isset_app_version and isset_start_date and isset_start_time and isset_hour_amount and isset_from_location_name and isset_from_location_address and isset_to_location_name and isset_to_location_address and isset_main_package_id and isset_main_package and isset_second_package_type and isset_second_package and isset_billing and isset_request_to and isset_passenger_id and isset_car_id and isset_car_group and isset_driver_gender and isset_driver_age_range and isset_communication and isset_driver_list and isset_driver_note:
	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_start_date and isset_start_time and isset_hour_amount and isset_from_location_name and isset_from_location_address and isset_to_location_name and isset_to_location_address and isset_main_package_id and isset_main_package and isset_second_package_type and isset_second_package and isset_billing and isset_request_to and isset_passenger_id and isset_car_id and isset_car_group and isset_driver_gender and isset_driver_age_range and isset_communication and isset_special_skill and isset_driver_list and isset_driver_note:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']
			billing_receiver_email = member_info['member_email']
			percent_check_package = 10
	
			if company_id is not None:
				company = db.company.find_one({"_id": ObjectId(company_id)})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				billing_receiver_email = company_json['billing_receiver_email']

			validate = []

			#check required
			if params['start_date']=="" or params['start_date'] is None:
				validate.append({"error_param" : "start_date","msg" : get_api_message("add_driver_request" , "start_date_is_required" , member_lang)})
			if params['start_time']=="" or params['start_time'] is None:
				validate.append({"error_param" : "start_time","msg" : get_api_message("add_driver_request" , "start_time_is_required" , member_lang)})
			if params['hour_amount']=="" or params['hour_amount'] is None:
				validate.append({"error_param" : "hour_amount","msg" : get_api_message("add_driver_request" , "hour_amount_is_required" , member_lang)})
			else:
				try:
					hour_amount = int(params['hour_amount'])
				except ValueError:
					validate.append({"error_param" : "hour_amount","msg" : get_api_message("add_driver_request" , "hour_amount_is_not_a_number" , member_lang)})
			if params['from_location_name']=="" or params['from_location_name'] is None:
				validate.append({"error_param" : "from_location_name","msg" : get_api_message("add_driver_request" , "from_location_name_is_required" , member_lang)})
			if params['from_location_address']=="" or params['from_location_address'] is None:
				validate.append({"error_param" : "from_location_address","msg" : get_api_message("add_driver_request" , "from_location_address_is_required" , member_lang)})
			if params['to_location_name']=="" or params['to_location_name'] is None:
				validate.append({"error_param" : "to_location_name","msg" : get_api_message("add_driver_request" , "to_location_name_is_required" , member_lang)})
			if params['to_location_address']=="" or params['to_location_address'] is None:
				validate.append({"error_param" : "to_location_address","msg" : get_api_message("add_driver_request" , "to_location_address_is_required" , member_lang)})
			
			if params['from_latitude']=="" or params['from_latitude'] is None:
				validate.append({"error_param" : "from_latitude","msg" : get_api_message("add_driver_request" , "from_latitude_is_required" , member_lang)})
			if params['from_longitude']=="" or params['from_longitude'] is None:
				validate.append({"error_param" : "from_longitude","msg" : get_api_message("add_driver_request" , "from_longitude_is_required" , member_lang)})
			if params['to_latitude']=="" or params['to_latitude'] is None:
				validate.append({"error_param" : "to_latitude","msg" : get_api_message("add_driver_request" , "to_latitude_is_required" , member_lang)})
			if params['to_longitude']=="" or params['to_longitude'] is None:
				validate.append({"error_param" : "to_longitude","msg" : get_api_message("add_driver_request" , "to_longitude_is_required" , member_lang)})

			if params['main_package_id']=="" or params['main_package_id'] is None:
				validate.append({"error_param" : "main_package_id","msg" : get_api_message("add_driver_request" , "main_package_id_is_required" , member_lang)})
			if len(params['main_package'])==0:
				validate.append({"error_param" : "main_package","msg" : get_api_message("add_driver_request" , "main_package_is_required" , member_lang)})
			if params['second_package_type']=="":
				validate.append({"error_param" : "second_package_type","msg" : get_api_message("add_driver_request" , "second_package_type_is_required" , member_lang)})
			elif params['second_package_type']=="package" and len(params['second_package'])==0:
				validate.append({"error_param" : "second_package","msg" : get_api_message("add_driver_request" , "second_package_is_required" , member_lang)})
			elif params['second_package_type']=="billing" and len(params['billing'])==0:
				validate.append({"error_param" : "billing","msg" : "Billing is required."})
			if params['request_to']=="" or params['request_to'] is None:
				validate.append({"error_param" : "request_to","msg" : "Request to is required."})
			elif params['request_to']=="another" and (params['passenger_id']=="" or params['passenger_id'] is None):
				validate.append({"error_param" : "passenger_id","msg" : get_api_message("add_driver_request" , "passenger_id_is_required" , member_lang)})
			if params['car_id']=="" or params['car_id'] is None:
				validate.append({"error_param" : "car_id","msg" : get_api_message("add_driver_request" , "car_id_is_required" , member_lang)})
			if params['car_group']=="" or params['car_group'] is None:
				validate.append({"error_param" : "car_group","msg" : get_api_message("add_driver_request" , "car_group_is_required" , member_lang)})
			elif params['car_group']!="personal" and params['car_group']!="company":
				validate.append({"error_param" : "car_group","msg" : get_api_message("add_driver_request" , "car_group_value_is_not_personal_and_company" , member_lang)})
			if len(params['driver_list'])==0:
				validate.append({"error_param" : "driver_list","msg" : get_api_message("add_driver_request" , "driver_list_is_required" , member_lang)})

			second_package_list = []
			#set second_package_id
			if params['second_package_type']=="package" and len(params['second_package'])>0:
				for i in range(len(params['second_package'])):
					second_package_list.append(params['second_package'][i]['package_id'])
			
			#ถ้า validate ผ่าน
			if len(validate) == 0:
				#ดึง package_code ล่าสุดจาก tb package แล้วเอามา +1
				request_driver = db.request_driver.find_one(sort=[("request_no", -1)])
				rdid = 1

				if request_driver is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					rdid = int(request_driver_json["request_no"][1:8])+1

				request_no = "R"+"%07d" % rdid

				if params['request_to']=="another":
					passenger_id = params['passenger_id']
				else:
					passenger_id = member_info['_id']['$oid']

				#แปลง format วันที่
				start_date = datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
				start_datetime_obj = datetime.strptime(start_date+" "+params['start_time']+":00", '%Y-%m-%d %H:%M:%S')
				end_datetime_obj = start_datetime_obj + timedelta(hours=int(params['hour_amount']))
				# int(end_time_obj.strftime('%H'))
				start_time = start_datetime_obj.strftime('%H:%M:%S')
				end_date = end_datetime_obj.strftime('%Y-%m-%d')
				end_time = end_datetime_obj.strftime('%H:%M:%S')

				#เซ็ตวันเวลาที่สามารถตอบรับงานได้
				created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				create_datetime_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
				end_accept_datetime_obj = create_datetime_obj + timedelta(minutes=45)
				end_accept_at = end_accept_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

				#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
				request_id = ObjectId()
				driver_list_id = ObjectId()
				#แปลง ObjectId ให้เป็น string
				request_id_string = str(request_id)
				driver_list_id_string = str(driver_list_id)

				billing_array = []
				if params['billing'] is not None:
					#แปลง format วันที่
					billing_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 

					#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
					billing_id = ObjectId()
					#แปลง ObjectId ให้เป็น string
					billing_id_string = str(billing_id)

					billing_data = { 
										"_id": billing_id,
										"request_id": request_id_string,
										"request_no": request_no,
										"company_id": company_id,
										"package_id": params['billing']['package_id'],
										"package_type": params['billing']['package_type'],
										"usage_hour_amount": params['billing']['usage_hour_amount'],
										"normal_usage": params['billing']['normal_usage'],
										"overtime_usage": params['billing']['overtime_usage'],
										"normal_paid_rate": float(params['billing']['normal_paid_rate']),
										"normal_received_rate": float(params['billing']['normal_received_rate']),
										"overtime_paid_rate": float(params['billing']['overtime_paid_rate']),
										"overtime_received_rate": float(params['billing']['overtime_received_rate']),
										"sum_paid": params['billing']['sum_paid'],
										"sum_received": params['billing']['sum_received'],
										"service_period": "normal",
										"billing_status": "0",
										"billing_date_int": billing_date_int,
										"created_at": created_at,
										"updated_at": created_at
									}

					#insert billing
					if db.billing.insert_one(billing_data):
						#ส่ง noti หา master admin ของ company นั้นๆ
						master_admin = db.member.find({
														"company_id": company_id,
														"company_user_type": "2"
													})

						if master_admin is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							master_admin_object = dumps(master_admin)
							master_admin_json = json.loads(master_admin_object)
							
							noti_type = "add_billing"
							billing_amount = '{:,.2f}'.format(round(float(params['billing']['sum_paid']) , 2))

							send_email_list = []

							for k in range(len(master_admin_json)):
								#sent noti to member
								customer_info = get_member_info_by_id(master_admin_json[k]['_id']['$oid'])
								member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']

								noti_title_en = member_info['member_firstname_en']+" "+member_info['member_lastname_en']+" has used exceed packages"
								noti_title_th = member_info['member_firstname_th']+" "+member_info['member_lastname_th']+" มีการใช้งานเกิน package"
								noti_message_en = "with job number "+request_no+" and amount "+billing_amount+" baht."
								noti_message_th = "โดยมีการวางบิลงาน "+request_no+" เป็นจำนวนเงิน "+billing_amount+" บาท"

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

								#-----------------------------------------------------------------#

								send_noti_key = customer_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "request_id": request_id_string , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"company_id": company_id,
													"request_id": request_id_string,
													"request_no": request_no
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

								email_type = "add_billing"
								subject = "VR Driver : วางบิลงาน "+request_no+" สำเร็จ"
								to_email = master_admin_json[k]['member_email'].lower()
								template_html = "add_billing.html"
								data_detail = { "member_fullname" : member_fullname, "request_no" : request_no, "billing_amount" : billing_amount }

								#put email ใส่ array 
								send_email_list.append(master_admin_json[k]['member_email'])

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
								email_type = "add_billing"
								subject = "VR Driver : วางบิลงาน "+request_no+" สำเร็จ"
								to_email = billing_receiver_email.lower()
								template_html = "add_billing.html"
								data_detail = { "member_fullname" : member_fullname, "request_no" : request_no, "billing_amount" : billing_amount }

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


						#เซ็ตค่า billing_array
						billing_array.append(billing_id_string)


				#เซ็ตค่า special_request
				special_request = {
										"driver_gender": params['driver_gender'],
										"driver_age_range": params['driver_age_range'],
										"communication": params['communication'],
										"special_skill": params['special_skill']
									}

				driver_list = []
				for i in range(len(params['driver_list'])):
					driver_list.append({
						"driver_id" : params['driver_list'][i],
						"driver_request_status": "0"
					})

				#insert driver_list
				driver_list_data = { 
							"_id": driver_list_id,
							"request_id": request_id_string,
							"driver_list": driver_list,
							"driver_list_status": "1",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

				if company_id is None:
					company_name = None
				else:
					company = db.company.find_one({"_id": ObjectId(company_id)})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)
					company_name = company_json['company_name']

				member_info = get_member_info_by_id(member_info['_id']['$oid'])
				member_name = member_info['member_firstname_th']+" "+member_info['member_lastname_th']

				passenger_info = get_member_info_by_id(passenger_id)
				passenger_name = passenger_info['member_firstname_th']+" "+passenger_info['member_lastname_th']

				start_date_int = int(datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')) 
				create_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

				start_time_int = int(datetime.strptime(start_time, '%H:%M:%S').strftime('%H%M%S'))
				end_time_int = int(datetime.strptime(end_time, '%H:%M:%S').strftime('%H%M%S'))

				#เก็บข้อมูลรถเพิ่มเติม
				car = db.car.find_one({"_id": ObjectId(params['car_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				car_type = db.car_type.find_one({"_id": ObjectId(car_json['car_type_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				car_brand = db.car_brand.find_one({"_id": ObjectId(car_json['car_brand_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_brand_object = dumps(car_brand)
				car_brand_json = json.loads(car_brand_object)

				car_type_code = car_type_json['car_type_code']
				car_brand_name = car_brand_json['brand_name']
				license_plate = car_json['license_plate']
				
				if db.driver_list.insert_one(driver_list_data):
					#insert request_driver
					data_request = { 
										"_id": request_id,
										"request_no": request_no,
										"company_id": member_info['company_id'],
										"company_name": company_name,
										"member_id": member_info['_id']['$oid'],
										"member_name": member_name,
										"passenger_id": passenger_id,
										"passenger_name": passenger_name,
										"request_to": params['request_to'],
										"start_date": start_date,
										"end_date": end_date,
										"start_time": start_time,
										"end_time": end_time,
										"start_date_int": start_date_int,
										"start_time_int": start_time_int,
										"end_time_int": end_time_int,
										"hour_amount": int(params['hour_amount']),
										"from_location_name": params['from_location_name'],
										"from_location_address": params['from_location_address'],
										"to_location_name": params['to_location_name'],
										"to_location_address": params['to_location_address'],
										"from_latitude": params['from_latitude'],
										"from_longitude": params['from_longitude'],
										"to_latitude": params['to_latitude'],
										"to_longitude": params['to_longitude'],
										"main_package_id": params['main_package_id'],
										"main_package": params['main_package'],
										"second_package_id": second_package_list,
										"second_package": params['second_package'],
										"overtime_package_id": None,
										"overtime_package": [],
										"billing_id": billing_array, 
										"car_id": params['car_id'],
										"car_group": params['car_group'],
										"car_type_code": car_type_code,
										"car_brand_name": car_brand_name,
										"license_plate": license_plate,
										"special_request": special_request,
										"driver_list_id": driver_list_id_string,
										"driver_id": None,
										"driver_note": params['driver_note'],
										"request_status": "0",
										"job_status": None,
										"check_status": None,
										"confirm_start_job_at": None,
										"accept_start_request": None,
										"end_accept_at": end_accept_at,
										"delay_minute": int("0"),
										"delay_end_date": end_date,
										"delay_end_time": end_time,
										"start_at": start_date+" "+start_time,
										"created_at": created_at,
										"updated_at": created_at,
										"create_date_int": create_date_int,
										"end_job_at": None,
										"remark_id": None,
										"admin_remark": None
									}

					if db.request_driver.insert_one(data_request):
						#หักโควตาการใช้งาน
						#ถ้าเป็น normal user อัพเดตโควตาใน tb member_package
						if member_info['company_id'] is None:
							#เอา main_package มาวน loop เช็ค
							for i in range(len(params['main_package'])):
								#ดึงข้อมูล member_package จาก member_package_id
								member_package = db.member_package.find_one({"_id": ObjectId(params['main_package'][i]['member_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								member_package_object = dumps(member_package)
								member_package_json = json.loads(member_package_object)				

								last_usage_amount = member_package_json['usage_amount']
								last_remaining_amount = member_package_json['remaining_amount']

								#ถ้า package_type = "hour" และ package_usage_type = "quota"
								if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
									# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
									# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_hour_amount']
									last_remaining_amount = member_package_json['remaining_amount'] - params['main_package'][i]['usage_hour_amount']
								#ถ้า package_type = "time" และ package_usage_type = "quota"
								elif member_package_json['package_type'] == "time" and member_package_json['package_usage_type'] == "quota":
									# last_usage_amount = usage_amount (member_package) + usage_amount (main_package) 
									# last_remaining_amount = remaining_amount (member_package) - usage_amount (main_package)
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_amount']
									last_remaining_amount = member_package_json['remaining_amount'] - params['main_package'][i]['usage_amount']

								if last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota":
									member_package_status = "0"
								else:
									member_package_status = "1"

								#update tb member_package
								where_param = { "_id": ObjectId(params['main_package'][i]['member_package_id']) }
								value_param = {
												"$set":
													{
														"usage_amount": last_usage_amount,
														"remaining_amount": last_remaining_amount,
														"member_package_status": member_package_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
								db.member_package.update(where_param , value_param)

								#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
								check_amount = float((member_package_json['total_amount'] / 100) * percent_check_package)

								if last_remaining_amount <= check_amount:
									#ส่ง noti หา ตัวเอง
									noti_type = "quota_less_than"
									member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									
									noti_title_en = member_fullname+"'s "+member_package_json['package_name_en']+" package"
									noti_title_th = "แพ็คเกจ "+member_package_json['package_name_th']+" ของ "+member_fullname
									noti_message_en = "has less than 10%"+" "+"usage quota"
									noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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

									#ส่ง noti
									send_noti_key = member_info['noti_key']
									send_noti_title = noti_title
									send_noti_message = noti_message
									send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "member_package_id": member_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
									send_noti_badge = 1

									#insert member_notification
									noti_detail = {
														"member_package_id": member_package_json['_id']['$oid']
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

							#ถ้ามี second_package ให้เอา second_package มาวน loop เช็ค
							if len(params['second_package']) > 0:
								for i in range(len(params['second_package'])):
									#ดึงข้อมูล member_package จาก member_package_id
									member_package = db.member_package.find_one({"_id": ObjectId(params['second_package'][i]['member_package_id'])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									member_package_object = dumps(member_package)
									member_package_json = json.loads(member_package_object)

									last_usage_amount = member_package_json['usage_amount']
									last_remaining_amount = member_package_json['remaining_amount']

									#ถ้า package_type = "hour" และ package_usage_type = "quota"
									if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
										# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
										# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
										last_usage_amount = member_package_json['usage_amount'] + params['second_package'][i]['usage_hour_amount']
										last_remaining_amount = member_package_json['remaining_amount'] - params['second_package'][i]['usage_hour_amount']

									if last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota":
										member_package_status = "0"
									else:
										member_package_status = "1"

									#update tb member_package
									where_param = { "_id": ObjectId(params['second_package'][i]['member_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": last_usage_amount,
															"remaining_amount": last_remaining_amount,
															"member_package_status": member_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.member_package.update(where_param , value_param)

									#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
									check_amount = float((member_package_json['total_amount'] / 100) * percent_check_package)

									if last_remaining_amount <= check_amount:
										#ส่ง noti หา ตัวเอง
										noti_type = "quota_less_than"
										member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']
										
										noti_title_en = member_fullname+"'s "+member_package_json['package_name_en']+" package"
										noti_title_th = "แพ็คเกจ "+member_package_json['package_name_th']+" ของ "+member_fullname
										noti_message_en = "has less than 10%"+" "+"usage quota"
										noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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

										#ส่ง noti
										send_noti_key = member_info['noti_key']
										send_noti_title = noti_title
										send_noti_message = noti_message
										send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "member_package_id": member_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
										send_noti_badge = 1

										#insert member_notification
										noti_detail = {
															"member_package_id": member_package_json['_id']['$oid']
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

						#ถ้าเป็น company user อัพเดตโควตาใน tb company_package และ member_package
						else:
							#เอา main_package มาวน loop เช็ค
							for i in range(len(params['main_package'])):
								#ดึงข้อมูล member_package จาก member_package_id
								member_package = db.member_package.find_one({"_id": ObjectId(params['main_package'][i]['member_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								member_package_object = dumps(member_package)
								member_package_json = json.loads(member_package_object)

								#ดึงข้อมูล company_package จาก company_package_id
								company_package = db.company_package.find_one({"_id": ObjectId(member_package_json['company_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								company_package_object = dumps(company_package)
								company_package_json = json.loads(company_package_object)

								last_usage_amount = member_package_json['usage_amount']
								last_remaining_amount = member_package_json['remaining_amount']
								last_usage_amount_company = company_package_json['usage_amount']
								last_remaining_amount_company = company_package_json['remaining_amount']

								#ถ้า package_type = "hour" และ package_usage_type = "quota"
								if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
									# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
									# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_hour_amount']
									last_remaining_amount = member_package_json['remaining_amount'] - params['main_package'][i]['usage_hour_amount']
									last_usage_amount_company = company_package_json['usage_amount'] + params['main_package'][i]['usage_hour_amount']
									last_remaining_amount_company = company_package_json['remaining_amount'] - params['main_package'][i]['usage_hour_amount']
								#ถ้า package_type = "hour" และ package_usage_type = "share"
								if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "share":
									# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_hour_amount']
									last_remaining_amount = member_package_json['remaining_amount']
									last_usage_amount_company = company_package_json['usage_amount'] + params['main_package'][i]['usage_hour_amount']
									last_remaining_amount_company = company_package_json['remaining_amount'] - params['main_package'][i]['usage_hour_amount']
								#ถ้า package_type = "time" และ package_usage_type = "quota"
								if member_package_json['package_type'] == "time" and member_package_json['package_usage_type'] == "quota":	
									# last_usage_amount = usage_amount (member_package) + usage_amount (main_package) 
									# last_remaining_amount = remaining_amount (member_package) - usage_amount (main_package)
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_amount']
									last_remaining_amount = member_package_json['remaining_amount'] - params['main_package'][i]['usage_amount']
									last_usage_amount_company = company_package_json['usage_amount'] + params['main_package'][i]['usage_amount']
									last_remaining_amount_company = company_package_json['remaining_amount'] - params['main_package'][i]['usage_amount']
								#ถ้า package_type = "time" และ package_usage_type = "share"
								if member_package_json['package_type'] == "time" and member_package_json['package_usage_type'] == "share":
									# last_usage_amount = usage_amount (member_package) + usage_amount (main_package) 
									last_usage_amount = member_package_json['usage_amount'] + params['main_package'][i]['usage_amount']
									last_remaining_amount = member_package_json['remaining_amount']
									last_usage_amount_company = company_package_json['usage_amount'] + params['main_package'][i]['usage_amount']
									last_remaining_amount_company = company_package_json['remaining_amount'] - params['main_package'][i]['usage_amount']

								if last_remaining_amount_company == 0:
									company_package_status = "0"
								else:
									company_package_status = "1"

								if (last_remaining_amount_company == 0 and member_package_json['package_usage_type'] == "share") or (last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota"):
									member_package_status = "0"
								else:
									member_package_status = "1"

								#update tb company_package
								where_param = { "_id": ObjectId(member_package_json['company_package_id']) }
								value_param = {
												"$set":
													{
														"usage_amount": last_usage_amount_company,
														"remaining_amount": last_remaining_amount_company,
														"company_package_status": company_package_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
								db.company_package.update(where_param , value_param)

								#update tb member_package
								where_param = { "_id": ObjectId(params['main_package'][i]['member_package_id']) }
								value_param = {
												"$set":
													{
														"usage_amount": last_usage_amount,
														"remaining_amount": last_remaining_amount,
														"member_package_status": member_package_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
								db.member_package.update(where_param , value_param)

								#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
								check_amount = float((company_package_json['total_amount'] / 100) * percent_check_package)

								if last_remaining_amount_company <= check_amount:
									#ส่ง noti หา master admin ของ company นั้นๆ
									master_admin = db.member.find({
																	"company_id": company_id,
																	"company_user_type": "2"
																})

									if master_admin is not None:
										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										master_admin_object = dumps(master_admin)
										master_admin_json = json.loads(master_admin_object)
										
										noti_type = "quota_less_than"

										send_email_list = []

										for i in range(len(master_admin_json)):
											#sent noti to member
											customer_info = get_member_info_by_id(master_admin_json[i]['_id']['$oid'])
											member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']
											
											noti_title_en = member_fullname+"'s "+company_package_json['package_name_en']+" package"
											noti_title_th = "แพ็คเกจ "+company_package_json['package_name_th']+" ของ "+member_fullname
											noti_message_en = "has less than 10%"+" "+"usage quota"
											noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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
											send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "company_package_id": company_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
											send_noti_badge = 1

											#insert member_notification
											noti_detail = {
																"company_id": company_id,
																"company_package_id": company_package_json['_id']['$oid']
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

							#ถ้ามี second_package ให้เอา second_package มาวน loop เช็ค
							if len(params['second_package']) > 0:
								# aaa = []
								for i in range(len(params['second_package'])):
									#ดึงข้อมูล member_package จาก member_package_id
									member_package = db.member_package.find_one({"_id": ObjectId(params['second_package'][i]['member_package_id'])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									member_package_object = dumps(member_package)
									member_package_json = json.loads(member_package_object)

									#ดึงข้อมูล company_package จาก company_package_id
									company_package = db.company_package.find_one({"_id": ObjectId(member_package_json['company_package_id'])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									company_package_object = dumps(company_package)
									company_package_json = json.loads(company_package_object)

									last_usage_amount = int(member_package_json['usage_amount'])
									last_remaining_amount = int(member_package_json['remaining_amount'])
									last_usage_amount_company = int(company_package_json['usage_amount']) + int(params['second_package'][i]['usage_hour_amount'])
									last_remaining_amount_company = int(company_package_json['remaining_amount']) - int(params['second_package'][i]['usage_hour_amount'])

									#ถ้า package_type = "hour" และ package_usage_type = "quota"
									if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
										# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
										# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
										last_usage_amount = int(member_package_json['usage_amount']) + int(params['second_package'][i]['usage_hour_amount'])
										last_remaining_amount = int(member_package_json['remaining_amount']) - int(params['second_package'][i]['usage_hour_amount'])
									#ถ้า package_type = "hour" และ package_usage_type = "share"
									if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "share":
										# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
										last_usage_amount = int(member_package_json['usage_amount']) + int(params['second_package'][i]['usage_hour_amount'])
										last_remaining_amount = int(member_package_json['remaining_amount'])
									
									if last_remaining_amount_company == 0:
										company_package_status = "0"
									else:
										company_package_status = "1"

									if (last_remaining_amount_company == 0 and member_package_json['package_usage_type'] == "share") or (last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota"):
										member_package_status = "0"
									else:
										member_package_status = "1"

									#update tb company_package
									where_param = { "_id": ObjectId(member_package_json['company_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": last_usage_amount_company,
															"remaining_amount": last_remaining_amount_company,
															"company_package_status": company_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.company_package.update(where_param , value_param)

									#update tb member_package
									where_param = { "_id": ObjectId(params['second_package'][i]['member_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": last_usage_amount,
															"remaining_amount": last_remaining_amount,
															"member_package_status": member_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.member_package.update(where_param , value_param)

									#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
									check_amount = float((company_package_json['total_amount'] / 100) * percent_check_package)

									if last_remaining_amount_company <= check_amount:
										#ส่ง noti หา master admin ของ company นั้นๆ
										master_admin = db.member.find({
																		"company_id": company_id,
																		"company_user_type": "2"
																	})

										if master_admin is not None:
											#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
											master_admin_object = dumps(master_admin)
											master_admin_json = json.loads(master_admin_object)
											
											noti_type = "quota_less_than"

											send_email_list = []

											for i in range(len(master_admin_json)):
												#sent noti to member
												customer_info = get_member_info_by_id(master_admin_json[i]['_id']['$oid'])
												member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']
												
												noti_title_en = member_fullname+"'s "+company_package_json['package_name_en']+" package"
												noti_title_th = "แพ็คเกจ "+company_package_json['package_name_th']+" ของ "+member_fullname
												noti_message_en = "has less than 10%"+" "+"usage quota"
												noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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
												send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "company_package_id": company_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
												send_noti_badge = 1

												#insert member_notification
												noti_detail = {
																	"company_id": company_id,
																	"company_package_id": company_package_json['_id']['$oid']
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

						#วน loop ส่ง noti
						for i in range(len(params['driver_list'])):
							driver_info = get_member_info_by_id(params['driver_list'][i])

							start_date_show = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
							start_time_show = datetime.strptime(start_time, '%H:%M:%S').strftime('%H:%M')

							noti_title_en = "VR Driver would remind you that a new job"
							noti_title_th = "VR Driver ขอแจ้งเตือนว่าคุณมีงานใหม่"
							noti_message_en = request_no+" , departure date "+start_date_show+" , "+start_time_show
							noti_message_th = request_no+" เดินทางวันที่ "+start_date_show+" , "+start_time_show

							if driver_info['member_lang'] == "en":
								member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
								noti_title = noti_title_en
								noti_message = noti_message_en
								show_noti = noti_title_en+" "+noti_message_en
							else:
								member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
								noti_title = noti_title_th
								noti_message = noti_message_th
								show_noti = noti_title_th+" "+noti_message_th

							#แปลง format วันที่
							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							#ส่ง noti
							noti_type = "request_driver"
							send_noti_key = driver_info['noti_key']
							send_noti_title = noti_title
							send_noti_message = noti_message
							send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": request_id_string ,"created_datetime" : created_datetime }
							send_noti_badge = 1

							#insert member_notification
							noti_detail = {
												"request_id": request_id_string,
												"request_no": request_no,
												"request_date": start_date,
												"start_time": start_time,
												"end_time": end_time,
												"time_amount": int(params['hour_amount'])
											}

							data = { 
										"member_id": driver_info['_id']['$oid'],
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
									"msg" : get_api_message("add_driver_request" , "add_request_driver_success" , member_lang),
									"request_id" : request_id_string
								}
					else:
						result = {
								"status" : False,
								"msg" : get_api_message("add_driver_request" , "request_driver_insert_failed" , member_lang)
								}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("add_driver_request" , "driver_list_insert_failed" , member_lang)
							}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("all" , "please_check_your_parameters_value"),
							"error_list" : validate
						}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "add_driver_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_driver_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_driver_list = "driver_list" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_driver_list:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("edit_driver_request" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				current_driver_list_id = request_driver_json['driver_list_id']
				start_date = request_driver_json['start_date']
				start_time = request_driver_json['start_time']
				end_time = request_driver_json['end_time']
				request_no = request_driver_json['request_no']
				hour_amount = request_driver_json['hour_amount']

				#เซ็ตวันเวลาที่สามารถตอบรับงานได้
				created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				create_datetime_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
				end_accept_datetime_obj = create_datetime_obj + timedelta(minutes=45)
				end_accept_at = end_accept_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
			
				#ถ้าค่า driver_list เป็น [] จะถือว่าให้ admin backend เป็นคนเลือกคนขับ
				if len(params['driver_list']) == 0:
					# update current driver_list
					where_param = { "_id": ObjectId(current_driver_list_id) }
					value_param = {
									"$set":
										{
											"driver_list_status": "0",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.driver_list.update(where_param , value_param):
						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"driver_list_id": None,
												"request_status": "0",
												"end_accept_at": end_accept_at,
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.request_driver.update(where_param , value_param):
							noti_title_en = "มีการแจ้งขอ Request Driver"
							noti_title_th = "มีการแจ้งขอ Request Driver"
							noti_message_en = "งาน "+request_no+" ส่งคำร้องให้แอดมิน Assign คนขับให้ใหม่"
							noti_message_th = "งาน "+request_no+" ส่งคำร้องให้แอดมิน Assign คนขับให้ใหม่"

							#insert admin_notification
							noti_type = "assign_driver"
							noti_detail = {
												"request_id": params['request_id'],
												"request_no": request_no,
												"request_date": start_date,
												"start_time": start_time,
												"end_time": end_time,
												"time_amount": int(hour_amount)
											}

							data_admin = { 
											"noti_type": noti_type,
											"noti_title_en": noti_title_en,
											"noti_title_th": noti_title_th,
											"noti_message_en": noti_message_en,
											"noti_message_th": noti_message_th,
											"noti_detail": noti_detail,
											"noti_status": "0",
											"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
							db.admin_notification.insert_one(data_admin)

							result = {
										"status" : True,
										"msg" : get_api_message("edit_driver_request" , "edit_request_driver_success" , member_lang),
										"request_id" : params['request_id']
									}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("edit_driver_request" , "request_driver_update_failed" , member_lang)
									}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_driver_request" , "driver_list_update_failed" , member_lang)
								}
				#ถ้าค่า driver_list ไม่ใช่ [] 
				else:
					driver_list = []
					for i in range(len(params['driver_list'])):
						driver_list.append({
							"driver_id" : params['driver_list'][i],
							"driver_request_status": "0"
						})

					# update current driver_list
					where_param = { "_id": ObjectId(current_driver_list_id) }
					value_param = {
									"$set":
										{
											"driver_list_status": "0",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.driver_list.update(where_param , value_param):
						driver_list_id = ObjectId()
						#แปลง ObjectId ให้เป็น string
						driver_list_id_string = str(driver_list_id)

						#insert new driver_list
						driver_list_data = { 
												"_id": driver_list_id,
												"request_id": params['request_id'],
												"driver_list": driver_list,
												"driver_list_status": "1",
												"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
						
						if db.driver_list.insert_one(driver_list_data):
							# update request_driver
							where_param = { "_id": ObjectId(params['request_id']) }
							value_param = {
											"$set":
												{
													"driver_list_id": driver_list_id_string,
													"request_status": "0",
													"end_accept_at": end_accept_at,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.request_driver.update(where_param , value_param):
								#วน loop ส่ง noti
								for i in range(len(params['driver_list'])):
									driver_info = get_member_info_by_id(params['driver_list'][i])
									start_date_show = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
									start_time_show = datetime.strptime(start_time, '%H:%M:%S').strftime('%H:%M')

									noti_title_en = "VR Driver would remind you that a new job"
									noti_title_th = "VR Driver ขอแจ้งเตือนว่าคุณมีงานใหม่"
									noti_message_en = request_no+" , departure date "+start_date_show+" , "+start_time_show
									noti_message_th = request_no+" เดินทางวันที่ "+start_date_show+" , "+start_time_show

									if driver_info['member_lang'] == "en":
										member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
										noti_title = noti_title_en
										noti_message = noti_message_en
										show_noti = noti_title_en+" "+noti_message_en
									else:
										member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
										noti_title = noti_title_th
										noti_message = noti_message_th
										show_noti = noti_title_th+" "+noti_message_th

									#แปลง format วันที่
									created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

									#ส่ง noti
									noti_type = "request_driver"
									send_noti_key = driver_info['noti_key']
									send_noti_title = noti_title
									send_noti_message = noti_message
									send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
									send_noti_badge = 1

									#insert member_notification
									noti_detail = {
														"request_id": params['request_id'],
														"request_no": request_no,
														"request_date": start_date,
														"start_time": start_time,
														"end_time": end_time,
														"time_amount": int(hour_amount)
													}

									data = { 
												"member_id": driver_info['_id']['$oid'],
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
											"msg" : get_api_message("edit_driver_request" , "edit_request_driver_success" , member_lang),
											"request_id" : params['request_id']
										}
							else:
								result = {
										"status" : False,
										"msg" : get_api_message("edit_driver_request" , "request_driver_update_failed" , member_lang)
										}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("edit_driver_request" , "driver_list_insert_failed" , member_lang)
									}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_driver_request" , "driver_list_update_failed" , member_lang)
								}

		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "edit_driver_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def cancel_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("cancel_request" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				request_no = request_driver_json['request_no']
				main_package = request_driver_json['main_package']
				second_package = request_driver_json['second_package']
				billing_id = request_driver_json['billing_id']
				start_datetime = request_driver_json['start_date']+" "+request_driver_json['start_time']
				passenger_id = request_driver_json['passenger_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if member_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				#เช็คเวลาปัจจุบันว่ามากกว่าหรือเท่ากับ 48 ชั่วโมงก่อนเริ่มงาน หรือไม่
				start_datetime_obj = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
				before_48hr_datetime_obj = start_datetime_obj - timedelta(hours=48)
				current_datetime_obj = datetime.now()

				today = datetime.now().strftime('%Y-%m-%d')
				today_int = int(datetime.strptime(today, '%Y-%m-%d').strftime('%Y%m%d')) 

				if current_datetime_obj <= before_48hr_datetime_obj:
					if request_driver_json['request_status'] == "0" or request_driver_json['request_status'] == "1" or request_driver_json['request_status'] == "3":
						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"request_status": "2",
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.request_driver.update(where_param , value_param):
							#คืนค่า package ให้กับลูกค้า
							#วน loop main_package
							for i in range(len(main_package)):
								#เอา member_package_id ไปดึงข้อมูลใน tb member_package
								member_package = db.member_package.find_one({"_id": ObjectId(main_package[i]['member_package_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								member_package_object = dumps(member_package)
								member_package_json = json.loads(member_package_object)

								#ถ้า company_package_id จาก tb member_package เป็น null แสดงว่าเป็น request จาก normal user
								if member_package_json['company_package_id'] is None:
									#ถ้า member_package.package_type = hour
									if member_package_json['package_type'] == "hour":
										#ให้ update new_usage_amount = member_package.usage_amount - main_package.usage_hour_amount
										#ให้ update new_remaining_amount = member_package.remaining_amount + main_package.usage_hour_amount
										new_usage_amount = member_package_json['usage_amount'] - main_package[i]['usage_hour_amount']
										new_remaining_amount = member_package_json['remaining_amount'] + main_package[i]['usage_hour_amount']
									#ถ้า member_package.package_type = time
									else:
										#ให้ update new_usage_amount = member_package.usage_amount - 1
										#ให้ update new_remaining_amount = member_package.remaining_amount + 1
										new_usage_amount = member_package_json['usage_amount'] - 1
										new_remaining_amount = member_package_json['remaining_amount'] + 1

									#ถ้า member_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
									if member_package_json['member_package_status'] == "0" and member_package_json['end_date_int'] >= today_int:
										member_package_status = "1"
									else:
										member_package_status = member_package_json['member_package_status']

									#update ข้อมูลใน tb member_package
									where_param = { "_id": ObjectId(main_package[i]['member_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": new_usage_amount,
															"remaining_amount": new_remaining_amount,
															"member_package_status": member_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.member_package.update(where_param , value_param)
										
								#ถ้า company_package_id จาก tb member_package ไม่ใช่ null แสดงว่าเป็น request จาก company user
								else:
									company_package = db.company_package.find_one({"_id": ObjectId(member_package_json['company_package_id'])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									company_package_object = dumps(company_package)
									company_package_json = json.loads(company_package_object)

									#ถ้า member_package.package_usage_type = quota
									if member_package_json['package_usage_type'] == "quota":
										#ถ้า member_package.package_type = hour
										if member_package_json['package_type'] == "hour":
											#ให้ update new_usage_amount = member_package.usage_amount - main_package.usage_hour_amount
											#ให้ update new_remaining_amount = member_package.remaining_amount + main_package.usage_hour_amount
											new_usage_amount = member_package_json['usage_amount'] - main_package[i]['usage_hour_amount']
											new_remaining_amount = member_package_json['remaining_amount'] + main_package[i]['usage_hour_amount']
											new_company_usage_amount = company_package_json['usage_amount'] - main_package[i]['usage_hour_amount']
											new_company_remaining_amount = company_package_json['remaining_amount'] + main_package[i]['usage_hour_amount']
										#ถ้า member_package.package_type = time
										else:
											#ให้ update new_usage_amount = member_package.usage_amount - 1
											#ให้ update new_remaining_amount = member_package.remaining_amount + 1
											new_usage_amount = member_package_json['usage_amount'] - 1
											new_remaining_amount = member_package_json['remaining_amount'] + 1
											new_company_usage_amount = company_package_json['usage_amount'] - 1
											new_company_remaining_amount = company_package_json['remaining_amount'] + 1
										
									#ถ้า member_package.package_usage_type = share
									else:
										#ถ้า member_package.package_type = hour
										if member_package_json['package_type'] == "hour":
											#ให้ update new_usage_amount = member_package.usage_amount - main_package.usage_hour_amount
											new_usage_amount = member_package_json['usage_amount'] - main_package[i]['usage_hour_amount']
											new_remaining_amount = 0
											new_company_usage_amount = company_package_json['usage_amount'] - main_package[i]['usage_hour_amount']
											new_company_remaining_amount = company_package_json['remaining_amount'] + main_package[i]['usage_hour_amount']

										#ถ้า member_package.package_type = time
										else:
											#ให้ update new_usage_amount = member_package.usage_amount - 1
											new_usage_amount = member_package_json['usage_amount'] - 1
											new_remaining_amount = 0
											new_company_usage_amount = company_package_json['usage_amount'] - 1
											new_company_remaining_amount = company_package_json['remaining_amount'] + 1

									#ถ้า member_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
									if member_package_json['member_package_status'] == "0" and member_package_json['end_date_int'] >= today_int:
										member_package_status = "1"
									else:
										member_package_status = member_package_json['member_package_status']

									#ถ้า company_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
									if company_package_json['company_package_status'] == "0" and company_package_json['end_date_int'] >= today_int:
										company_package_status = "1"
									else:
										company_package_status = company_package_json['company_package_status']

									#update ข้อมูลใน tb member_package
									where_param = { "_id": ObjectId(main_package[i]['member_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": new_usage_amount,
															"remaining_amount": new_remaining_amount,
															"member_package_status": member_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.member_package.update(where_param , value_param)

									#update ข้อมูลใน tb company_package
									where_param = { "_id": ObjectId(member_package_json['company_package_id']) }
									value_param = {
													"$set":
														{
															"usage_amount": new_company_usage_amount,
															"remaining_amount": new_company_remaining_amount,
															"company_package_status": company_package_status,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									db.company_package.update(where_param , value_param)

							#ถ้า len(second_package) > 0
							if len(second_package) > 0:
								#วน loop second_package
								for i in range(len(second_package)):
									#เอา member_package_id ไปดึงข้อมูลใน tb member_package
									member_package = db.member_package.find_one({"_id": ObjectId(second_package[i]['member_package_id'])})
							
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									member_package_object = dumps(member_package)
									member_package_json = json.loads(member_package_object)

									#ถ้า company_package_id จาก tb member_package เป็น null แสดงว่าเป็น request จาก normal user
									if member_package_json['company_package_id'] is None:
										#ให้ update new_usage_amount = member_package.usage_amount - second_package.usage_hour_amount
										#ให้ update new_remaining_amount = member_package.remaining_amount + second_package.usage_hour_amount
										new_usage_amount = member_package_json['usage_amount'] - second_package[i]['usage_hour_amount']
										new_remaining_amount = member_package_json['remaining_amount'] + second_package[i]['usage_hour_amount']

										#ถ้า member_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
										if member_package_json['member_package_status'] == "0" and member_package_json['end_date_int'] >= today_int:
											member_package_status = "1"
										else:
											member_package_status = member_package_json['member_package_status']

										#update ข้อมูลใน tb member_package
										where_param = { "_id": ObjectId(second_package[i]['member_package_id']) }
										value_param = {
														"$set":
															{
																"usage_amount": new_usage_amount,
																"remaining_amount": new_remaining_amount,
																"member_package_status": member_package_status,
																"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
															}
													}
										db.member_package.update(where_param , value_param)
										
									#ถ้า company_package_id จาก tb member_package ไม่ใช่ null แสดงว่าเป็น request จาก company user
									else:
										company_package = db.company_package.find_one({"_id": ObjectId(member_package_json['company_package_id'])})
										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										company_package_object = dumps(company_package)
										company_package_json = json.loads(company_package_object)

										#ถ้า member_package.package_usage_type = quota
										if member_package_json['package_usage_type'] == "quota":
											#ให้ update new_usage_amount = member_package.usage_amount - second_package.usage_hour_amount
											#ให้ update new_remaining_amount = member_package.remaining_amount + second_package.usage_hour_amount
											new_usage_amount = member_package_json['usage_amount'] - second_package[i]['usage_hour_amount']
											new_remaining_amount = member_package_json['remaining_amount'] + second_package[i]['usage_hour_amount']
											new_company_usage_amount = company_package_json['usage_amount'] - second_package[i]['usage_hour_amount']
											new_company_remaining_amount = company_package_json['remaining_amount'] + second_package[i]['usage_hour_amount']
											
										#ถ้า member_package.package_usage_type = share
										else:
											#ให้ update new_usage_amount = member_package.usage_amount - second_package.usage_hour_amount
											#ให้ update new_remaining_amount = 0
											new_usage_amount = member_package_json['usage_amount'] - second_package[i]['usage_hour_amount']
											new_remaining_amount = 0
											new_company_usage_amount = company_package_json['usage_amount'] - second_package[i]['usage_hour_amount']
											new_company_remaining_amount = company_package_json['remaining_amount'] + second_package[i]['usage_hour_amount']

										#ถ้า member_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
										if member_package_json['member_package_status'] == "0" and member_package_json['end_date_int'] >= today_int:
											member_package_status = "1"
										else:
											member_package_status = member_package_json['member_package_status']

										#ถ้า company_package_status = 0 และ end_date มากกว่าหรือเท่ากับวันที่ปัจจุบัน ให้อัพเดตกลับมาเป็น 1
										if company_package_json['company_package_status'] == "0" and company_package_json['end_date_int'] >= today_int:
											company_package_status = "1"
										else:
											company_package_status = company_package_json['company_package_status']

										#update ข้อมูลใน tb member_package
										where_param = { "_id": ObjectId(second_package[i]['member_package_id']) }
										value_param = {
														"$set":
															{
																"usage_amount": new_usage_amount,
																"remaining_amount": new_remaining_amount,
																"member_package_status": member_package_status,
																"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
															}
													}
										db.member_package.update(where_param , value_param)

										#update ข้อมูลใน tb company_package
										where_param = { "_id": ObjectId(member_package_json['company_package_id']) }
										value_param = {
														"$set":
															{
																"usage_amount": new_company_usage_amount,
																"remaining_amount": new_company_remaining_amount,
																"company_package_status": company_package_status,
																"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
															}
													}
										db.company_package.update(where_param , value_param)		

							#ถ้า len(billing_id) > 0
							if len(billing_id) > 0:
								#update ข้อมูลใน tb billing
								where_param = { "_id": ObjectId(billing_id[0]) }
								value_param = {
												"$set":
													{
														"billing_status": "2",
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
								db.billing.update(where_param , value_param)

							#ถ้า driver_list_id ไม่ใช่ null
							if request_driver_json['driver_list_id'] is not None:
								#เอา driver_list_id ไปดึงข้อมูลใน tb driver_list
								driver_list = db.driver_list.find_one({"_id": ObjectId(request_driver_json['driver_list_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								driver_list_object = dumps(driver_list)
								driver_list_json = json.loads(driver_list_object)
								driver_list = driver_list_json['driver_list']

								#วน loop ส่ง noti
								for i in range(len(driver_list)):
									driver_info = get_member_info_by_id(driver_list[i]['driver_id'])

									noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
									noti_message_en = "cancel request : "+request_no
									noti_message_th = "ยกเลิกงาน "+request_no

									if driver_info['member_lang'] == "en":
										member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
										noti_title = noti_title_en
										noti_message = noti_message_en
										show_noti = noti_title_en+" "+noti_message_en
									else:
										member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
										noti_title = noti_title_th
										noti_message = noti_message_th
										show_noti = noti_title_th+" "+noti_message_th

									#แปลง format วันที่
									created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

									#ส่ง noti
									noti_type = "cancel_request"
									send_noti_key = driver_info['noti_key']
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
												"member_id": driver_info['_id']['$oid'],
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
										"msg" : get_api_message("cancel_request" , "cancel_request_success" , member_lang)
									}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("cancel_request" , "request_update_failed" , member_lang)
									}		
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("cancel_request" , "can_not_cancel_request_because_request_status_is_invalid" , member_lang)
								}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("cancel_request" , "can_not_cancel_request_because_you_cancel_the_request_more_than_the_specified_time" , member_lang)
							}	
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "cancel_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def accept_start_request(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("accept_start_request" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				passenger_id = request_driver_json['passenger_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if member_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				if request_driver_json['request_status'] == "4" and request_driver_json['job_status'] == "5":
					# update request_driver
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"request_status": "5",
											"job_status": "6",
											"check_status": "0",
											"accept_start_request": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.request_driver.update(where_param , value_param):
						#เพิ่มข้อมูลการตรวจสภาพรถ
						data = { 
							"request_id": params['request_id'],
							"outside_inspection": [],
							"inspection_before_use": [],
							"inspection_before_use_comment": None,
							"inspection_before_use_image": [],
							"start_mileage": None,
							"end_mileage": None,
							"start_mileage_at": None,
							"end_mileage_at": None,
							"check_status": "0",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}

						if db.car_inspection.insert_one(data):
							driver_info = get_member_info_by_id(request_driver_json['driver_id'])
							noti_type = "start_job"
							request_no = request_driver_json['request_no']

							noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
							noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
							noti_message_en = "accept to start job : "+request_no
							noti_message_th = "ยอมรับการเริ่มงาน "+request_no

							if driver_info['member_lang'] == "en":
								member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
								noti_title = noti_title_en
								noti_message = noti_message_en
								show_noti = noti_title_en+" "+noti_message_en
							else:
								member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
								noti_title = noti_title_th
								noti_message = noti_message_th
								show_noti = noti_title_th+" "+noti_message_th

							#แปลง format วันที่
							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							#ส่ง noti The passenger accept to start job : R0000005
							send_noti_key = driver_info['noti_key']
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
										"member_id": driver_info['_id']['$oid'],
										"member_fullname": member_fullname,
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
										"msg" : get_api_message("accept_start_request" , "accept_start_request_success" , member_lang)
									}
						else:
							result = {
								"status" : False,
								"msg" : get_api_message("accept_start_request" , "car_inspection_insert_failed" , member_lang)
							}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("accept_start_request" , "request_update_failed" , member_lang)
								}	
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("accept_start_request" , "can_not_accept_start_request_because_request_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "accept_start_request"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def accept_car_inspection(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("accept_car_inspection" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				passenger_id = request_driver_json['passenger_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if member_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_inspection_object = dumps(car_inspection)
				car_inspection_json = json.loads(car_inspection_object)

				if request_driver_json['request_status'] == "5" and (request_driver_json['job_status'] == "6" or request_driver_json['job_status'] == "7") and car_inspection_json['check_status'] == "2":
					# update car_inspection
					where_param = { "request_id": params['request_id'] }
					value_param = {
									"$set":
										{
											"check_status": "4",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.car_inspection.update(where_param , value_param):
						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"check_status": "4",
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						db.request_driver.update(where_param , value_param)

						driver_info = get_member_info_by_id(request_driver_json['driver_id'])
						noti_type = "accept_car_inspection"
						request_no = request_driver_json['request_no']

						noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
						noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						noti_message_en = "accept car inspection : "+request_no
						noti_message_th = "ยอมรับการตรวจสภาพรถงาน "+request_no

						if driver_info['member_lang'] == "en":
							member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
							noti_title = noti_title_en
							noti_message = noti_message_en
							show_noti = noti_title_en+" "+noti_message_en
						else:
							member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
							noti_title = noti_title_th
							noti_message = noti_message_th
							show_noti = noti_title_th+" "+noti_message_th

						#แปลง format วันที่
						created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

						#ส่ง noti
						send_noti_key = driver_info['noti_key']
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
									"member_id": driver_info['_id']['$oid'],
									"member_fullname": member_fullname,
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
									"msg" : get_api_message("accept_car_inspection" , "accept_car_inspection_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("accept_car_inspection" , "car_inspection_update_failed" , member_lang)
								}	
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("accept_car_inspection" , "can_not_accept_car_inspection_because_check_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "accept_car_inspection"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def reject_car_inspection(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("reject_car_inspection" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				passenger_id = request_driver_json['passenger_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if member_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_inspection_object = dumps(car_inspection)
				car_inspection_json = json.loads(car_inspection_object)

				if request_driver_json['request_status'] == "5" and request_driver_json['job_status'] == "6" and car_inspection_json['check_status'] == "2":
					# update car_inspection
					where_param = { "request_id": params['request_id'] }
					value_param = {
									"$set":
										{
											"check_status": "3",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.car_inspection.update(where_param , value_param):
						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"check_status": "3",
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						db.request_driver.update(where_param , value_param)

						driver_info = get_member_info_by_id(request_driver_json['driver_id'])
						noti_type = "reject_car_inspection"
						request_no = request_driver_json['request_no']

						noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
						noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						noti_message_en = "reject car inspection : "+request_no+" , please car inspection again."
						noti_message_th = "ปฏิเสธการตรวจสภาพรถงาน "+request_no+" กรุณาตรวจสภาพรถอีกครั้ง"

						if driver_info['member_lang'] == "en":
							member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
							noti_title = noti_title_en
							noti_message = noti_message_en
							show_noti = noti_title_en+" "+noti_message_en
						else:
							member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
							noti_title = noti_title_th
							noti_message = noti_message_th
							show_noti = noti_title_th+" "+noti_message_th

						#แปลง format วันที่
						created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

						#ส่ง noti
						send_noti_key = driver_info['noti_key']
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
									"member_id": driver_info['_id']['$oid'],
									"member_fullname": member_fullname,
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
									"msg" : get_api_message("reject_car_inspection" , "reject_car_inspection_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("reject_car_inspection" , "car_inspection_update_failed" , member_lang)
								}	
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("reject_car_inspection" , "can_not_reject_car_inspection_because_check_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "reject_car_inspection"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def delay_job(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_delay_minute = "delay_minute" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_delay_minute:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("delay_job" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				passenger_id = request_driver_json['passenger_id']
				mem_id = request_driver_json['member_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if mem_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				if request_driver_json['request_status'] == "5" and request_driver_json['job_status'] == "7":
					#เช็ค member_package ของคนที่จองว่ามีพอให้หักหรือไม่
					today_date = datetime.now().strftime('%Y-%m-%d')
					today_time = datetime.now().strftime('%H:%M:%S')

					member_package = db.member_package.find({
																"member_id": mem_id,
																"package_type": "hour",
																"end_date": {"$gte" : today_date}
															})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)

					remaining_minute = 0

					for i in range(len(member_package_json)):
						#normal user
						if member_package_json[i]['company_package_id'] is None:
							remaining_minute = remaining_minute + (int(member_package_json[i]['remaining_amount']) * 60)
						#company user
						else:
							#ดึงข้อมูล company_package จาก company_package_id
							company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[i]['company_package_id'])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_package_object = dumps(company_package)
							company_package_json = json.loads(company_package_object)

							#ถ้า package_usage_type = "share"
							if member_package_json[i]['package_usage_type'] == "share":
								remaining_amount = company_package_json['remaining_amount']
							#ถ้า package_usage_type = "quota"
							else:
								remaining_amount = member_package_json[i]['remaining_amount']

							remaining_minute = remaining_minute + (int(remaining_amount) * 60)

					# result = { 
					# 			"status" : False,
					# 			"msg" : "aaa",
					# 			"remaining_minute" : remaining_minute,
					# 			"delay_minute" : params['delay_minute'],
					# 			"len" : len(member_package_json)
					# 		}

					#ถ้ามีพอ จะสามารถเลื่อนเวลาได้
					if remaining_minute >= params['delay_minute']:
						#ถ้า delay_minute เท่ากับ 0 แสดงว่ายังไม่เคยกดเลื่อนเวลา
						if request_driver_json['delay_minute'] == 0:
							#update request_driver_json.delay_minute = params['delay_minute']
							delay_minute = int(params['delay_minute'])
							end_datetime = request_driver_json['end_date']+" "+request_driver_json['end_time']
							
						#ถ้า delay_minute มากกว่าหรือเท่ากับ 30 แสดงว่าเคยมีการกดเลื่อนเวลาแล้ว
						else:
							delay_minute = request_driver_json['delay_minute'] + int(params['delay_minute'])
							end_datetime = request_driver_json['delay_end_date']+" "+request_driver_json['delay_end_time']

						end_datetime_obj = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')
						delay_end_datetime_obj = end_datetime_obj + timedelta(minutes=int(params['delay_minute']))

						delay_end_date = delay_end_datetime_obj.strftime('%Y-%m-%d')
						delay_end_time = delay_end_datetime_obj.strftime('%H:%M:%S')
						delay_end_time_noti = delay_end_datetime_obj.strftime('%H:%M')

						#insert delay_request
						data = { 
									"request_id": params['request_id'],
									"delay_minute": int(params['delay_minute']),
									"delay_end_date": delay_end_date,
									"delay_end_time": delay_end_time,
									"delay_status": "1", #1 = เลื่อน , 0 = ไม่เลื่อน
									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}

						if db.delay_request.insert_one(data):
							# update request_driver
							where_param = { "_id": ObjectId(params['request_id']) }
							value_param = {
											"$set":
												{
													"job_status": "6",
													"delay_minute": delay_minute,
													"delay_end_date": delay_end_date,
													"delay_end_time": delay_end_time,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.request_driver.update(where_param , value_param):
								driver_info = get_member_info_by_id(request_driver_json['driver_id'])
								noti_type = "delay_job"
								request_no = request_driver_json['request_no']

								noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
								noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
								noti_message_en = "postpone arrival time to "+delay_end_time_noti+" for job : "+request_no
								noti_message_th = "เลื่อนเวลาจบงานเป็นเวลา "+delay_end_time_noti+" สำหรับงาน "+request_no

								if driver_info['member_lang'] == "en":
									member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
									noti_title = noti_title_en
									noti_message = noti_message_en
									show_noti = noti_title_en+" "+noti_message_en
								else:
									member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
									noti_title = noti_title_th
									noti_message = noti_message_th
									show_noti = noti_title_th+" "+noti_message_th

								#แปลง format วันที่
								created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

								#ส่ง noti The passenger postpone arrival time to 19:00 p.m.
								send_noti_key = driver_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"request_id": params['request_id'],
													"request_no": request_no,
													"delay_minute": delay_minute,
													"delay_end_date": delay_end_date,
													"delay_end_time": delay_end_time_noti
												}

								data = { 
											"member_id": driver_info['_id']['$oid'],
											"member_fullname": member_fullname,
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
											"msg" : get_api_message("delay_job" , "delay_job_success" , member_lang)
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("delay_job" , "request_update_failed" , member_lang)
										}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("delay_job" , "delay_request_insert_failed" , member_lang)
									}
					#ถ้าไม่พอ จะไม่สามารถเลื่อนเวลาได้
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("delay_job" , "can_not_delay_job_because_you_do_not_have_enough_package" , member_lang)
								}	
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("delay_job" , "can_not_delay_job_because_request_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "delay_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def not_delay_job(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("not_delay_job" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				passenger_id = request_driver_json['passenger_id']

				#ถ้าคนจองเป็นคนทำรายการ จะดึงข้อมูลของผู้โดยสารมาแสดงผลแทน
				if member_id != passenger_id:
					member_info = get_member_info_by_id(passenger_id)

				if request_driver_json['request_status'] == "5" and request_driver_json['job_status'] == "7":
					delay_end_date = request_driver_json['delay_end_date']
					delay_end_time = request_driver_json['delay_end_time']
					delay_end_time_noti = datetime.strptime(delay_end_time, '%H:%M:%S').strftime('%H:%M')

					#insert delay_request
					data = { 
								"request_id": params['request_id'],
								"delay_minute": 0,
								"delay_end_date": delay_end_date,
								"delay_end_time": delay_end_time,
								"delay_status": "0", #1 = เลื่อน , 0 = ไม่เลื่อน
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

					if db.delay_request.insert_one(data):
						driver_info = get_member_info_by_id(request_driver_json['driver_id'])
						noti_type = "not_delay_job"
						request_no = request_driver_json['request_no']

						noti_title_en = "Passenger : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
						noti_title_th = "ผู้โดยสาร "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						noti_message_en = "confirm job end time at "+delay_end_time_noti+" for job : "+request_no+" if you can't finish the job right now , please contact passenger"
						noti_message_th = "ยืนยันเวลาจบงานที่เวลา "+delay_end_time_noti+" สำหรับงาน "+request_no+" หากไม่สามารถจบงานเวลานี้ได้ กรุณาติดต่อผู้โดยสาร"

						if driver_info['member_lang'] == "en":
							member_fullname = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
							noti_title = noti_title_en
							noti_message = noti_message_en
							show_noti = noti_title_en+" "+noti_message_en
						else:
							member_fullname = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
							noti_title = noti_title_th
							noti_message = noti_message_th
							show_noti = noti_title_th+" "+noti_message_th

						#แปลง format วันที่
						created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

						#ส่ง noti
						send_noti_key = driver_info['noti_key']
						send_noti_title = noti_title
						send_noti_message = noti_message
						send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": params['request_id'] , "created_datetime" : created_datetime }
						send_noti_badge = 1

						#insert member_notification
						noti_detail = {
											"request_id": params['request_id'],
											"request_no": request_no,
											"delay_minute": 0,
											"delay_end_date": delay_end_date,
											"delay_end_time": delay_end_time_noti
										}

						data = { 
									"member_id": driver_info['_id']['$oid'],
									"member_fullname": member_fullname,
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
									"msg" : get_api_message("not_delay_job" , "confirm_job_end_time_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("not_delay_job" , "delay_request_insert_failed" , member_lang)
								}	
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("not_delay_job" , "can_not_confirm_job_end_time_because_request_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "not_delay_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_overtime_package(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			
			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_overtime_package" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				main_package_id = request_driver_json['main_package_id']
				main_package_info = request_driver_json['main_package'][0]
				end_date = request_driver_json['end_date']
				end_time = request_driver_json['end_time']
				delay_end_date = request_driver_json['delay_end_date']
				delay_end_time = request_driver_json['delay_end_time']

				if int(request_driver_json['delay_minute']) <= 30:
					delay_hour = 0
					delay_minute = int(request_driver_json['delay_minute'])
				else:
					delay_hour = int(request_driver_json['delay_minute']) // 60 
					delay_minute = int(request_driver_json['delay_minute']) % 60 

				overtime_amount = delay_hour

				start_date_obj = datetime.strptime(request_driver_json['start_date'], '%Y-%m-%d')
				start_workday = start_date_obj.strftime('%a')

				#weekend
				if start_workday == "Sun" or start_workday == "Sat":
					service_time_in = ["allday" , "weekend"]
				#weekday
				else:
					service_time_in = ["allday" , "weekday"]

				package = db.member_package.aggregate([
														{
															"$match": {
																"member_id": member_info['_id']['$oid'],
																"package_type": "hour",
																"service_time": {"$in": service_time_in},
																"member_package_status": "1"
															}
														},
														{
															"$group" : {
																"_id" : "$package_id"
															}
														}
													])

				overtime_package_list = []
				
				if package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					package_object = dumps(package)
					package_json = json.loads(package_object)

					all_remainning_amount = 0

					for i in range(len(package_json)):
						member_package = db.member_package.find({
																"member_id": member_info['_id']['$oid'],
																"package_id": package_json[i]['_id'],
																"member_package_status": "1"
															})

						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						member_package_object = dumps(member_package)
						member_package_json = json.loads(member_package_object)
						
						remaining_package_list = []

						for j in range(len(member_package_json)):
							end_date = datetime.strptime(member_package_json[j]['end_date'], '%Y-%m-%d')
							today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
							
							delta = end_date - today
							remaining_date = delta.days

							if remaining_date >= 0:
								#***#
								if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
									company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									company_package_object = dumps(company_package)
									company_package_json = json.loads(company_package_object)

									overtime_package_remaining_amount = company_package_json['remaining_amount']
								else:
									overtime_package_remaining_amount = member_package_json[j]['remaining_amount']

								remaining_package_list.append({
									"remaining_date" : remaining_date,
									"remaining_amount" : overtime_package_remaining_amount
								})

								all_remainning_amount = all_remainning_amount + overtime_package_remaining_amount

						overtime_package_info = get_package_info(member_package_json[j]['package_id'])

						if member_lang == "en":
							overtime_package_name = overtime_package_info['package_name_en']
						else:
							overtime_package_name = overtime_package_info['package_name_th']

						if overtime_package_info['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if overtime_package_info['package_type'] == "hour":
							if member_lang == "en":
								package_type_text = "Per Hour"
							else:
								package_type_text = "รายชั่วโมง"
							package_type_amount = overtime_package_info['hour_amount']
						else:
							if member_lang == "en":
								package_type_text = "Per Time"
							else:
								package_type_text = "รายครั้ง"
							package_type_amount = overtime_package_info['time_amount']

						if len(remaining_package_list) > 0:
							overtime_package_list.append({
								# "member_package_id" : member_package_json[j]['_id']['$oid'],
								# "company_package_id" : member_package_json[j]['company_package_id'],
								"package_id": member_package_json[j]['package_id'],
								"package_name": overtime_package_name,
								"package_model": package_model,
								"package_type": member_package_json[j]['package_type'],
								"package_type_text": package_type_text,
								"package_type_amount": package_type_amount,
								"total_usage_date": overtime_package_info['total_usage_date'],
								"package_image": overtime_package_info['package_image'],
								"remaining_package": remaining_package_list
							})

				if (all_remainning_amount >= overtime_amount) and len(overtime_package_list) > 0:
					#ถ้าเป็น company user 
					if member_info['company_id'] is not None:
						start_overtime = '20:00'
						end_overtime = '05:00'
						start_overtime_int = 20
						end_overtime_int = 5
						hour_amount = overtime_amount

						start_time = datetime.strptime(end_time, '%H:%M:%S').strftime('%H:%M')

						start_time_obj = datetime.strptime(start_time, '%H:%M')
						end_time_obj = start_time_obj + timedelta(hours=hour_amount)

						start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
						end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

						sum_normal_usage = 0
						sum_overtime_usage = 0
						ot_1 = 0

						#เวลาจบงานจริง > 24 และวันที่จบงานที่จอง ต้องเป็นคนละวันกับ วันที่จบงานจริง
						if int(end_time_obj.strftime('%H')) >= 0 and request_driver_json['end_date'] != request_driver_json['delay_end_date']:
							st = int(start_time_obj.strftime('%H'))
							end_time = 24 + int(end_time_obj.strftime('%H'))
						else:
							st = int(start_time_obj.strftime('%H'))
							end_time = int(end_time_obj.strftime('%H'))

						# 16 < 20
						if end_time <= start_overtime_int:
							sum_normal_usage = overtime_amount
							sum_overtime_usage = 0
						# 21 > 20
						else:
							# 1 = 21 - 20
							# sum_overtime_usage = end_time - start_overtime_int
							# 3 = 4 - 1
							# sum_normal_usage = overtime_amount - sum_overtime_usage

							#end_time 21 - 29
							if end_time > start_overtime_int and end_time < 30:
								# 1 = 22 - 21
								sum_overtime_usage = end_time - st
								# 0 = 1 - 1
								sum_normal_usage = overtime_amount - sum_overtime_usage
							#end_time 30+
							else:
								# 9
								sum_overtime_usage = 9
								# 2 = 11 - 9
								sum_normal_usage = overtime_amount - sum_overtime_usage

						normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
						overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
						sum_paid = normal_paid + overtime_paid

						normal_received = sum_normal_usage * main_package_info['normal_received_rate']
						overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
						sum_received = normal_received + overtime_received

						billing = {
									"package_id": main_package_id,
									"package_name": main_package_info['package_name'],
									"package_type": main_package_info['package_type'],
									"usage_hour_amount": overtime_amount,
									"normal_usage": sum_normal_usage,
									"overtime_usage": sum_overtime_usage,
									"normal_paid_rate": main_package_info['normal_paid_rate'],
									"normal_received_rate": main_package_info['normal_received_rate'],
									"overtime_paid_rate": main_package_info['overtime_paid_rate'],
									"overtime_received_rate": main_package_info['overtime_received_rate'],
									"sum_paid": sum_paid,
									"sum_received": sum_received
								}
					#ถ้าเป็น normal user
					else:
						billing = []

					result = {
								"status" : True,
								"msg" : get_api_message("get_overtime_package" , "get_overtime_package_success" , member_lang),
								"overtime_amount": overtime_amount,
								"delay_hour": delay_hour,
								"delay_minute": delay_minute,
								"overtime_package": overtime_package_list,
								"billing": billing
							}
				else:
					#ถ้าเป็น company user 
					if member_info['company_id'] is not None:
						start_overtime = '20:00'
						end_overtime = '05:00'
						start_overtime_int = 20
						end_overtime_int = 5
						hour_amount = overtime_amount

						start_time = datetime.strptime(end_time, '%H:%M:%S').strftime('%H:%M')

						start_time_obj = datetime.strptime(start_time, '%H:%M')
						end_time_obj = start_time_obj + timedelta(hours=hour_amount)

						start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
						end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

						sum_normal_usage = 0
						sum_overtime_usage = 0
						ot_1 = 0

						#เวลาจบงานจริง > 24 และวันที่จบงานที่จอง ต้องเป็นคนละวันกับ วันที่จบงานจริง
						if int(end_time_obj.strftime('%H')) >= 0 and request_driver_json['end_date'] != request_driver_json['delay_end_date']:
							st = int(start_time_obj.strftime('%H'))
							end_time = 24 + int(end_time_obj.strftime('%H'))
						else:
							st = int(start_time_obj.strftime('%H'))
							end_time = int(end_time_obj.strftime('%H'))

						# 16 < 20
						if end_time <= start_overtime_int:
							sum_normal_usage = overtime_amount
							sum_overtime_usage = 0
						# 21 > 20
						else:
							# 1 = 21 - 20
							# sum_overtime_usage = end_time - start_overtime_int
							# 3 = 4 - 1
							# sum_normal_usage = overtime_amount - sum_overtime_usage

							#end_time 21 - 29
							if end_time > start_overtime_int and end_time < 30:
								# 1 = 22 - 21
								sum_overtime_usage = end_time - st
								# 0 = 1 - 1
								sum_normal_usage = overtime_amount - sum_overtime_usage
							#end_time 30+
							else:
								# 9
								sum_overtime_usage = 9
								# 2 = 11 - 9
								sum_normal_usage = overtime_amount - sum_overtime_usage

						normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
						overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
						sum_paid = normal_paid + overtime_paid

						normal_received = sum_normal_usage * main_package_info['normal_received_rate']
						overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
						sum_received = normal_received + overtime_received

						billing = {
									"package_id": main_package_id,
									"package_name": main_package_info['package_name'],
									"package_type": main_package_info['package_type'],
									"usage_hour_amount": overtime_amount,
									"normal_usage": sum_normal_usage,
									"overtime_usage": sum_overtime_usage,
									"normal_paid_rate": main_package_info['normal_paid_rate'],
									"normal_received_rate": main_package_info['normal_received_rate'],
									"overtime_paid_rate": main_package_info['overtime_paid_rate'],
									"overtime_received_rate": main_package_info['overtime_received_rate'],
									"sum_paid": sum_paid,
									"sum_received": sum_received
								}

						result = {
									"status" : False,
									"msg" : get_api_message("get_overtime_package" , "can_not_get_overtime_package_please_select_billing" , member_lang),
									"overtime_amount": overtime_amount,
									"delay_hour": delay_hour,
									"delay_minute": delay_minute,
									"overtime_package": [],
									"billing": billing
								}
					#ถ้าเป็น normal user
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("get_overtime_package" , "can_not_get_overtime_package_please_contact_your_driver" , member_lang)
								}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_overtime_package"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def pay_overtime(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_overtime_package_type = "overtime_package_type" in params
	isset_overtime_package = "overtime_package" in params
	isset_billing = "billing" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_overtime_package_type and isset_overtime_package and isset_billing:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']
			billing_receiver_email = member_info['member_email']
			percent_check_package = 10

			if company_id is not None:
				company = db.company.find_one({"_id": ObjectId(company_id)})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_object = dumps(company)
				company_json = json.loads(company_object)
				billing_receiver_email = company_json['billing_receiver_email']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("pay_overtime" , "request_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				mem_id = request_driver_json['member_id']
				billing_array = request_driver_json['billing_id']
				request_no = request_driver_json['request_no']

				#ถ้าผู้โดยสารเป็นคนทำรายการ จะดึงข้อมูลของคนจองมาแสดงผลแทน
				if member_id != mem_id:
					member_info = get_member_info_by_id(mem_id)

				if request_driver_json['request_status'] == "6" and request_driver_json['job_status'] == "9":
					if params['overtime_package_type'] == "billing":
						if params['billing'] is not None:
							billing = request_driver_json['billing_id']

							#แปลง format วันที่
							created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							billing_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 

							#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
							billing_id = ObjectId()
							#แปลง ObjectId ให้เป็น string
							billing_id_string = str(billing_id)

							billing_data = { 
												"_id": billing_id,
												"request_id": params['request_id'],
												"request_no": request_no,
												"company_id": company_id,
												"package_id": params['billing']['package_id'],
												"package_type": params['billing']['package_type'],
												"usage_hour_amount": params['billing']['usage_hour_amount'],
												"normal_usage": params['billing']['normal_usage'],
												"overtime_usage": params['billing']['overtime_usage'],
												"normal_paid_rate": float(params['billing']['normal_paid_rate']),
												"normal_received_rate": float(params['billing']['normal_received_rate']),
												"overtime_paid_rate": float(params['billing']['overtime_paid_rate']),
												"overtime_received_rate": float(params['billing']['overtime_received_rate']),
												"sum_paid": params['billing']['sum_paid'],
												"sum_received": params['billing']['sum_received'],
												"service_period": "overtime",
												"billing_status": "0",
												"billing_date_int": billing_date_int,
												"created_at": created_at,
												"updated_at": created_at
											}

							#insert billing
							if db.billing.insert_one(billing_data):
								#update summary data
								payment_amount = float(request_driver_json['payment_amount']) + float(params['billing']['sum_received'])
								normal_payment_amount = request_driver_json['normal_payment_amount'] + params['billing']['normal_received_rate']
								overtime_payment_amount = request_driver_json['overtime_payment_amount'] + params['billing']['overtime_received_rate']
								total_normal_usage = request_driver_json['total_normal_usage'] + params['billing']['normal_usage']
								total_overtime_usage = request_driver_json['total_overtime_usage'] + params['billing']['overtime_usage']

								#ส่ง noti หา master admin ของ company นั้นๆ
								master_admin = db.member.find({
																"company_id": company_id,
																"company_user_type": "2"
															})

								if master_admin is not None:
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									master_admin_object = dumps(master_admin)
									master_admin_json = json.loads(master_admin_object)
									
									noti_type = "add_billing"
									billing_amount = '{:,.2f}'.format(round(float(params['billing']['sum_paid']) , 2))

									send_email_list = []

									for k in range(len(master_admin_json)):
										#sent noti to member
										customer_info = get_member_info_by_id(master_admin_json[k]['_id']['$oid'])
										member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']

										noti_title_en = member_info['member_firstname_en']+" "+member_info['member_lastname_en']+" has used exceed packages"
										noti_title_th = member_info['member_firstname_th']+" "+member_info['member_lastname_th']+" มีการใช้งานเกิน package"
										noti_message_en = "with job number "+request_no+" and amount "+billing_amount+" baht."
										noti_message_th = "โดยมีการวางบิลงาน "+request_no+" เป็นจำนวนเงิน "+billing_amount+" บาท"

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

										#-----------------------------------------------------------------#

										send_noti_key = customer_info['noti_key']
										send_noti_title = noti_title
										send_noti_message = noti_message
										send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "request_id": params['request_id'] , "created_datetime" : created_datetime }
										send_noti_badge = 1

										#insert member_notification
										noti_detail = {
															"company_id": company_id,
															"request_id": params['request_id'],
															"request_no": request_no
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

										email_type = "add_billing"
										subject = "VR Driver : วางบิลงาน "+request_no+" สำเร็จ"
										to_email = master_admin_json[k]['member_email'].lower()
										template_html = "add_billing.html"
										data_detail = { "member_fullname" : member_fullname, "request_no" : request_no, "billing_amount" : billing_amount }

										#put email ใส่ array 
										send_email_list.append(master_admin_json[k]['member_email'])

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
										email_type = "add_billing"
										subject = "VR Driver : วางบิลงาน "+request_no+" สำเร็จ"
										to_email = billing_receiver_email.lower()
										template_html = "add_billing.html"
										data_detail = { "member_fullname" : member_fullname, "request_no" : request_no, "billing_amount" : billing_amount }

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

								#เซ็ตค่า billing
								billing_array.append(billing_id_string)

							#update tb request_driver.billing_id
							where_param = { "_id": ObjectId(params['request_id']) }
							value_param = {
											"$set":
												{
													"billing_id": billing_array,
													"job_status": "10",

													"payment_amount": payment_amount,
													"normal_payment_amount": normal_payment_amount,
													"overtime_payment_amount": overtime_payment_amount,
													"total_normal_usage": total_normal_usage,
													"total_overtime_usage": total_overtime_usage,
													"payment_status": "1",
													"payment_date": datetime.now().strftime('%Y-%m-%d'),
													"payment_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}	

							if db.request_driver.update(where_param , value_param):
								result = {
											"status" : True,
											"msg" : get_api_message("pay_overtime" , "pay_overtime_success" , member_lang)
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("pay_overtime" , "request_update_failed" , member_lang)
										}		
					else:
						if len(params['overtime_package']) > 0:
							overtime_package_list = []
							op_list = []
							use_amount = 0
							old_use_amount = 0
							start_overtime = '20:00'
							end_overtime = '05:00'
							start_overtime_int = 20
							end_overtime_int = 5
							sum_ot = 0

							member_package_in = []

							#วน loop เอา member_package_id มาใส่ array เพื่อนำไป orderby อีกครั้ง
							for i in range(len(params['overtime_package'])):
								mp = db.member_package.find({
																"member_id": member_info['_id']['$oid'],
																"package_id": params['overtime_package'][i],
																"package_type": "hour"
															})

								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								mp_object = dumps(mp)
								mp_json = json.loads(mp_object)

								for j in range(len(mp_json)):
									if mp_json[j]['package_usage_type'] == "share" and mp_json[j]['company_package_id'] is not None:
										company_package = db.company_package.find_one({"_id": ObjectId(mp_json[j]['company_package_id'])})
										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										company_package_object = dumps(company_package)
										company_package_json = json.loads(company_package_object)

										remaining_amount = company_package_json['remaining_amount']
									else:
										remaining_amount = mp_json[j]['remaining_amount']

									end_date = datetime.strptime(mp_json[j]['end_date'], '%Y-%m-%d')
									today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
									
									delta = end_date - today
									remaining_date = delta.days

									#เช็คว่า member package ที่สามารถใช้งานได้ ต้องมี remaining_amount มากกว่า 0 และมี end_date น้อยกว่าหรือเท่ากับวันที่ปัจจุบัน
									if remaining_amount > 0 and remaining_date >= 0:
										mp_id = mp_json[j]['_id']['$oid']
										member_package_in.append(ObjectId(mp_id))

							# ดึง member_package อีกรอบเพื่อเอาข้อมูลที่เหลือวันใช้งานน้อยมาใช้ก่อน
							member_package = db.member_package.find({
																		"_id": {"$in" : member_package_in} 
																	}).sort([("end_date", 1)])

							if member_package is None:
								result = { 
											"status" : False,
											"msg" : get_api_message("pay_overtime" , "member_package_not_found" , member_lang)
										}
							else:
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								member_package_object = dumps(member_package)
								member_package_json = json.loads(member_package_object)

								member_package_list = []

								for j in range(len(member_package_json)):
									overtime_package_info = member_package_json[j]
									
									if member_lang == "en":
										package_name = overtime_package_info['package_name_en']
									else:
										package_name = overtime_package_info['package_name_th']

									if member_package_json[j]['package_usage_type'] == "share" and member_package_json[j]['company_package_id'] is not None:
										company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[j]['company_package_id'])})
										#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
										company_package_object = dumps(company_package)
										company_package_json = json.loads(company_package_object)

										remaining_amount = company_package_json['remaining_amount']
									else:
										remaining_amount = member_package_json[j]['remaining_amount']

									old_use_amount = use_amount
									use_amount = use_amount + remaining_amount
									#0 = 0 + 3

									#3 >= 1 
									#ถ้ามากกว่าหรือเท่ากับแสดงว่าใช้งาน package นี้ได้

									if int(request_driver_json['delay_minute']) <= 30:
										delay_hour = 0
										delay_minute = int(request_driver_json['delay_minute'])
									else:
										delay_hour = int(request_driver_json['delay_minute']) // 60 
										delay_minute = int(request_driver_json['delay_minute']) % 60

									overtime_amount = delay_hour

									if delay_minute > 30:
										overtime_amount = overtime_amount + 1

									if use_amount >= overtime_amount:
										remainning_package = use_amount - overtime_amount 
										usage_package = remaining_amount - remainning_package

										usage_amount_value = usage_package
										usage_hour_amount_value = usage_package

										if j == 0:
											hour_amount = overtime_amount
											start_time = datetime.strptime(request_driver_json['end_time'], '%H:%M:%S').strftime('%H:%M')

											#เซ็ตเวลา start_time ตั้งต้นจาก package หลัก
											st_obj = datetime.strptime(start_time, '%H:%M')
											et_obj = st_obj + timedelta(hours=hour_amount)

											#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
											start_time_obj = et_obj - timedelta(hours=hour_amount)
											end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
										else:
											hour_amount = usage_hour_amount_value
											start_time = last_end_time_obj.strftime('%H:%M')

											#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
											start_time_obj = datetime.strptime(start_time, '%H:%M')
											end_time_obj = start_time_obj + timedelta(hours=hour_amount)

										if int(start_time_obj.strftime('%M')) > 30:
											# + hour
											start_time_obj = start_time_obj + timedelta(hours=1)
											# - minute
											start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

											# + hour
											end_time_obj = end_time_obj + timedelta(hours=1)
											# - minute
											end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

										if int(end_time_obj.strftime('%H')) == 0:
											end_time_int = 24
										else:
											end_time_int = int(end_time_obj.strftime('%H'))

										if int(start_time_obj.strftime('%H')) == 0:
											start_time_int = 0
										else:
											start_time_int = int(start_time_obj.strftime('%H'))

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0
										case = 0
										normal_usage = 0
										overtime_usage = 0

										#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
										# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
										if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
											case = 1
											# 3 <= 5
											# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
											if (end_time_int <= end_overtime_int): 
												overtime_usage = usage_hour_amount_value
											# 6 > 5
											else:
												# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
												overtime_usage = end_overtime_int - start_time_int

											normal_usage = usage_hour_amount_value - overtime_usage

											sum_ot = sum_ot + overtime_usage
										#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
										# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
										elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
											case = 2
											if j == 0:
												# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												check_usage = int(check_usage_obj.strftime('%H'))

												if check_usage > usage_hour_amount_value:
													normal_usage = usage_hour_amount_value
												else:
													normal_usage = check_usage

												overtime_usage = usage_hour_amount_value - normal_usage
											else:
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												if sum_ot == 0:
													# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
													normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
													normal_usage = int(normal_usage_obj.strftime('%H'))

													if count_member_package == 0:
														# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
														overtime_usage = end_time_int - start_overtime_int
													else:
														overtime_usage = hour_amount - usage_hour_amount_value
												else:
													normal_usage = 0
													overtime_usage = usage_hour_amount_value

											sum_ot = sum_ot + overtime_usage
										#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
										# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
										elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
											case = 3
											# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
											normal_usage = int(normal_usage_obj.strftime('%H'))

											# overtime_usage = hour_amount - normal_usage

											overtime_usage = usage_hour_amount_value - normal_usage
											
										#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
										# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
										elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
											case = 4
											if j == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))
												# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
												overtime_usage = end_time_int - start_overtime_int
											else:
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage = 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												if sum_ot == 0:
													# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
													normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
													normal_usage = int(normal_usage_obj.strftime('%H'))

													if hour_amount >= usage_hour_amount_value:
														# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
														overtime_usage = end_time_int - start_overtime_int
													else:
														overtime_usage = hour_amount - usage_hour_amount_value
														
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												else:
													normal_usage = 0
													overtime_usage = usage_hour_amount_value
											
											sum_ot = sum_ot + overtime_usage

										normal_paid = normal_usage * float(overtime_package_info['normal_paid_rate'])
										overtime_paid = overtime_usage * float(overtime_package_info['overtime_paid_rate'])
										sum_paid = normal_paid + overtime_paid

										normal_received = normal_usage * float(overtime_package_info['normal_received_rate'])
										overtime_received = overtime_usage * float(overtime_package_info['overtime_received_rate'])
										sum_received = normal_received + overtime_received
										remaining_show = remaining_amount - (normal_usage + overtime_usage)

										if j == 0:
											op_list.append(member_package_json[j]['package_id'])
										else:
											i = j - 1
											if member_package_json[i]['package_id'] != member_package_json[j]['package_id']:
												op_list.append(member_package_json[j]['package_id'])

										overtime_package_list.append({
											"member_package_id" : member_package_json[j]['_id']['$oid'],
											"package_id": member_package_json[j]['package_id'],
											# "package_name": package_name,
											"package_type": member_package_json[j]['package_type'],
											"usage_amount": usage_amount_value,
											"usage_hour_amount": usage_hour_amount_value,

											"normal_usage": normal_usage,
											"overtime_usage": overtime_usage,
											"normal_paid_rate": float(overtime_package_info['normal_paid_rate']),
											"normal_received_rate": float(overtime_package_info['normal_received_rate']),
											"overtime_paid_rate": float(overtime_package_info['overtime_paid_rate']),
											"overtime_received_rate": float(overtime_package_info['overtime_received_rate']),
											
											# "remaining_amount": remaining_show,
										})

										break
									else:
										usage_amount_value = remaining_amount
										usage_hour_amount_value = remaining_amount

										if j == 0:
											hour_amount = overtime_amount
											start_time = datetime.strptime(request_driver_json['end_time'], '%H:%M:%S').strftime('%H:%M')

											#เซ็ตเวลา start_time ตั้งต้นจาก package หลัก
											st_obj = datetime.strptime(start_time, '%H:%M')
											et_obj = st_obj + timedelta(hours=hour_amount)

											#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
											start_time_obj = et_obj - timedelta(hours=hour_amount)
											end_time_obj = start_time_obj + timedelta(hours=usage_hour_amount_value)
										else:
											hour_amount = usage_hour_amount_value
											start_time = last_end_time_obj.strftime('%H:%M')

											#เซ็ตเวลา start_time และ end_time ล่าสุดตอนนั้น
											start_time_obj = datetime.strptime(start_time, '%H:%M')
											end_time_obj = start_time_obj + timedelta(hours=hour_amount)


										if int(start_time_obj.strftime('%M')) > 30:
											# + hour
											start_time_obj = start_time_obj + timedelta(hours=1)
											# - minute
											start_time_obj = start_time_obj - timedelta(minutes=int(start_time_obj.strftime('%M')))

											# + hour
											end_time_obj = end_time_obj + timedelta(hours=1)
											# - minute
											end_time_obj = end_time_obj - timedelta(minutes=int(end_time_obj.strftime('%M')))

										if int(end_time_obj.strftime('%H')) == 0:
											end_time_int = 24
										else:
											end_time_int = int(end_time_obj.strftime('%H'))

										if int(start_time_obj.strftime('%H')) == 0:
											start_time_int = 0
										else:
											start_time_int = int(start_time_obj.strftime('%H'))

										start_overtime_obj = datetime.strptime(start_overtime, '%H:%M')
										end_overtime_obj = datetime.strptime(end_overtime, '%H:%M')

										sum_normal_usage = 0
										sum_overtime_usage = 0
										ot_1 = 0
										case = 0
										normal_usage = 0
										overtime_usage = 0

										#case 1 : 01:00 <= 05:00 and 10:00 <= 20:00
										# if (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
										if (start_time_int <= end_overtime_int) and (end_time_int <= start_overtime_int):
											case = 1
											# 3 <= 5
											# if (int(end_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))):
											if (end_time_int <= end_overtime_int): 
												overtime_usage = usage_hour_amount_value
											# 6 > 5
											else:
												# overtime_usage = end_overtime_int - int(start_time_obj.strftime('%H'))
												overtime_usage = end_overtime_int - start_time_int

											normal_usage = usage_hour_amount_value - overtime_usage

											sum_ot = sum_ot + overtime_usage
										#case 2 : 01:00 <= 05:00 and 23:00 > 20:00
										# elif (int(start_time_obj.strftime('%H')) <= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
										elif (start_time_int <= end_overtime_int) and (end_time_int > start_overtime_int):
											case = 2
											if j == 0:
												# check_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												check_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												check_usage = int(check_usage_obj.strftime('%H'))

												if check_usage > usage_hour_amount_value:
													normal_usage = usage_hour_amount_value
												else:
													normal_usage = check_usage

												overtime_usage = usage_hour_amount_value - normal_usage
											else:
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												if sum_ot == 0:
													# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
													normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
													normal_usage = int(normal_usage_obj.strftime('%H'))

													if count_member_package == 0:
														# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
														overtime_usage = end_time_int - start_overtime_int
													else:
														overtime_usage = hour_amount - usage_hour_amount_value
												else:
													normal_usage = 0
													overtime_usage = usage_hour_amount_value

											sum_ot = sum_ot + overtime_usage
										#case 3 : 10:00 >= 04:59 and 20:00 <= 20:00
										# elif (int(start_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H'))) and (int(end_time_obj.strftime('%H')) <= int(start_overtime_obj.strftime('%H'))):
										elif (start_time_int >= end_overtime_int) and (end_time_int <= start_overtime_int):
											case = 3
											# normal_usage_obj = end_time_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
											normal_usage_obj = end_time_obj - timedelta(hours=start_time_int)
											normal_usage = int(normal_usage_obj.strftime('%H'))

											# overtime_usage = hour_amount - normal_usage

											overtime_usage = usage_hour_amount_value - normal_usage
											
										#case 4 : 10:00 >= 04:59 and 22:00 > 20:00 
										# elif (int(end_time_obj.strftime('%H')) >= int(end_overtime_obj.strftime('%H')) and int(end_time_obj.strftime('%H')) > int(start_overtime_obj.strftime('%H'))):
										elif (end_time_int >= end_overtime_int) and (end_time_int > start_overtime_int):
											case = 4
											if j == 0:
												# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
												normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
												normal_usage = int(normal_usage_obj.strftime('%H'))
												# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
												overtime_usage = end_time_int - start_overtime_int
											else:
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage = 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												if sum_ot == 0:
													# normal_usage_obj = start_overtime_obj - timedelta(hours=int(start_time_obj.strftime('%H')))
													normal_usage_obj = start_overtime_obj - timedelta(hours=start_time_int)
													normal_usage = int(normal_usage_obj.strftime('%H'))

													if hour_amount >= usage_hour_amount_value:
														# overtime_usage = int(end_time_obj.strftime('%H')) - start_overtime_int
														overtime_usage = end_time_int - start_overtime_int
													else:
														overtime_usage = hour_amount - usage_hour_amount_value
														
												#ถ้าข้อมูลก่อนหน้านี้มี overtime_usage > 0 จะถือว่า usage ที่เหลือเป็น overtime_usage ทั้งหมด
												else:
													normal_usage = 0
													overtime_usage = usage_hour_amount_value
											
											sum_ot = sum_ot + overtime_usage

										normal_paid = normal_usage * float(overtime_package_info['normal_paid_rate'])
										overtime_paid = overtime_usage * float(overtime_package_info['overtime_paid_rate'])
										sum_paid = normal_paid + overtime_paid

										normal_received = normal_usage * float(overtime_package_info['normal_received_rate'])
										overtime_received = overtime_usage * float(overtime_package_info['overtime_received_rate'])
										sum_received = normal_received + overtime_received
										remaining_show = remaining_amount - (normal_usage + overtime_usage)

										if j == 0:
											op_list.append(member_package_json[j]['package_id'])
										else:
											i = j - 1
											if member_package_json[i]['package_id'] != member_package_json[j]['package_id']:
												op_list.append(member_package_json[j]['package_id'])

										overtime_package_list.append({
											"member_package_id" : member_package_json[j]['_id']['$oid'],
											"package_id": member_package_json[j]['package_id'],
											# "package_name": package_name,
											"package_type": member_package_json[j]['package_type'],
											"usage_amount": usage_amount_value,
											"usage_hour_amount": usage_hour_amount_value,

											"normal_usage": normal_usage,
											"overtime_usage": overtime_usage,
											"normal_paid_rate": float(overtime_package_info['normal_paid_rate']),
											"normal_received_rate": float(overtime_package_info['normal_received_rate']),
											"overtime_paid_rate": float(overtime_package_info['overtime_paid_rate']),
											"overtime_received_rate": float(overtime_package_info['overtime_received_rate']),
											
											# "remaining_amount": remaining_show,											
										})

									last_end_time_obj = end_time_obj

								if use_amount >= overtime_amount:
									#update summary data
									payment_amount = float(request_driver_json['payment_amount']) + float(sum_received)
									normal_payment_amount = request_driver_json['normal_payment_amount'] + normal_received
									overtime_payment_amount = request_driver_json['overtime_payment_amount'] + overtime_received
									total_normal_usage = request_driver_json['total_normal_usage'] + normal_usage
									total_overtime_usage = request_driver_json['total_overtime_usage'] + overtime_usage

									# update tb request_driver.billing_id
									where_param = { "_id": ObjectId(params['request_id']) }
									value_param = {
													"$set":
														{
															"overtime_package_id": op_list,
															"overtime_package": overtime_package_list,
															"job_status": "10",

															"payment_amount": payment_amount,
															"normal_payment_amount": normal_payment_amount,
															"overtime_payment_amount": overtime_payment_amount,
															"total_normal_usage": total_normal_usage,
															"total_overtime_usage": total_overtime_usage,
															"payment_status": "1",
															"payment_date": datetime.now().strftime('%Y-%m-%d'),
															"payment_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}

									if db.request_driver.update(where_param , value_param):
										#หักโควตาการใช้งาน
										#ถ้าเป็น normal user อัพเดตโควตาใน tb member_package
										if member_info['company_id'] is None:
											#ถ้ามี overtime_package ให้เอา overtime_package มาวน loop เช็ค
											if len(overtime_package_list) > 0:
												for i in range(len(overtime_package_list)):
													#ดึงข้อมูล member_package จาก member_package_id
													member_package = db.member_package.find_one({"_id": ObjectId(overtime_package_list[i]['member_package_id'])})
													#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
													member_package_object = dumps(member_package)
													member_package_json = json.loads(member_package_object)

													last_usage_amount = member_package_json['usage_amount']
													last_remaining_amount = member_package_json['remaining_amount']

													#ถ้า package_type = "hour" และ package_usage_type = "quota"
													if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
														# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
														# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
														last_usage_amount = member_package_json['usage_amount'] + overtime_package_list[i]['usage_hour_amount']
														last_remaining_amount = member_package_json['remaining_amount'] - overtime_package_list[i]['usage_hour_amount']

													if last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota":
														member_package_status = "0"
													else:
														member_package_status = "1"

													#update tb member_package
													where_param = { "_id": ObjectId(overtime_package_list[i]['member_package_id']) }
													value_param = {
																	"$set":
																		{
																			"usage_amount": last_usage_amount,
																			"remaining_amount": last_remaining_amount,
																			"member_package_status": member_package_status,
																			"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
																		}
																}
													db.member_package.update(where_param , value_param)

													#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
													check_amount = float((member_package_json['total_amount'] / 100) * percent_check_package)

													if last_remaining_amount <= check_amount:
														#ส่ง noti หา ตัวเอง
														noti_type = "quota_less_than"
														member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']
														
														noti_title_en = member_fullname+"'s "+member_package_json['package_name_en']+" package"
														noti_title_th = "แพ็คเกจ "+member_package_json['package_name_th']+" ของ "+member_fullname
														noti_message_en = "has less than 10%"+" "+"usage quota"
														noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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

														#ส่ง noti
														send_noti_key = member_info['noti_key']
														send_noti_title = noti_title
														send_noti_message = noti_message
														send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "member_package_id": member_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
														send_noti_badge = 1

														#insert member_notification
														noti_detail = {
																			"member_package_id": member_package_json['_id']['$oid']
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

										#ถ้าเป็น company user อัพเดตโควตาใน tb company_package และ member_package
										else:
											#ถ้ามี overtime_package ให้เอา overtime_package มาวน loop เช็ค
											if len(overtime_package_list) > 0:
												# aaa = []
												for i in range(len(overtime_package_list)):
													#ดึงข้อมูล member_package จาก member_package_id
													member_package = db.member_package.find_one({"_id": ObjectId(overtime_package_list[i]['member_package_id'])})
													#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
													member_package_object = dumps(member_package)
													member_package_json = json.loads(member_package_object)

													#ดึงข้อมูล company_package จาก company_package_id
													company_package = db.company_package.find_one({"_id": ObjectId(member_package_json['company_package_id'])})
													#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
													company_package_object = dumps(company_package)
													company_package_json = json.loads(company_package_object)

													last_usage_amount = int(member_package_json['usage_amount'])
													last_remaining_amount = int(member_package_json['remaining_amount'])
													last_usage_amount_company = int(company_package_json['usage_amount']) + int(overtime_package_list[i]['usage_hour_amount'])
													last_remaining_amount_company = int(company_package_json['remaining_amount']) - int(overtime_package_list[i]['usage_hour_amount'])

													#ถ้า package_type = "hour" และ package_usage_type = "quota"
													if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "quota":
														# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
														# last_remaining_amount = remaining_amount (member_package) - usage_hour_amount (main_package)
														last_usage_amount = int(member_package_json['usage_amount']) + int(overtime_package_list[i]['usage_hour_amount'])
														last_remaining_amount = int(member_package_json['remaining_amount']) - int(overtime_package_list[i]['usage_hour_amount'])
													#ถ้า package_type = "hour" และ package_usage_type = "share"
													if member_package_json['package_type'] == "hour" and member_package_json['package_usage_type'] == "share":
														# last_usage_amount = usage_amount (member_package) + usage_hour_amount (main_package) 
														last_usage_amount = int(member_package_json['usage_amount']) + int(overtime_package_list[i]['usage_hour_amount'])
														last_remaining_amount = int(member_package_json['remaining_amount'])
													
													if last_remaining_amount_company == 0:
														company_package_status = "0"
													else:
														company_package_status = "1"

													if (last_remaining_amount_company == 0 and member_package_json['package_usage_type'] == "share") or (last_remaining_amount == 0 and member_package_json['package_usage_type'] == "quota"):
														member_package_status = "0"
													else:
														member_package_status = "1"

													#update tb company_package
													where_param = { "_id": ObjectId(member_package_json['company_package_id']) }
													value_param = {
																	"$set":
																		{
																			"usage_amount": last_usage_amount_company,
																			"remaining_amount": last_remaining_amount_company,
																			"company_package_status": company_package_status,
																			"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
																		}
																}
													db.company_package.update(where_param , value_param)

													#update tb member_package
													where_param = { "_id": ObjectId(overtime_package_list[i]['member_package_id']) }
													value_param = {
																	"$set":
																		{
																			"usage_amount": last_usage_amount,
																			"remaining_amount": last_remaining_amount,
																			"member_package_status": member_package_status,
																			"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
																		}
																}
													db.member_package.update(where_param , value_param)

													#ส่ง noti แจ้งเตือนกรณี package เหลือน้อยกว่า 10 % ของโควตาทั้งหมด 
													check_amount = float((company_package_json['total_amount'] / 100) * percent_check_package)

													if last_remaining_amount_company <= check_amount:
														#ส่ง noti หา master admin ของ company นั้นๆ
														master_admin = db.member.find({
																						"company_id": company_id,
																						"company_user_type": "2"
																					})

														if master_admin is not None:
															#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
															master_admin_object = dumps(master_admin)
															master_admin_json = json.loads(master_admin_object)
															
															noti_type = "quota_less_than"

															send_email_list = []

															for i in range(len(master_admin_json)):
																#sent noti to member
																customer_info = get_member_info_by_id(master_admin_json[i]['_id']['$oid'])
																member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']
																
																noti_title_en = member_fullname+"'s "+company_package_json['package_name_en']+" package"
																noti_title_th = "แพ็คเกจ "+company_package_json['package_name_th']+" ของ "+member_fullname
																noti_message_en = "has less than 10%"+" "+"usage quota"
																noti_message_th = "เหลือโควตาใช้งานน้อยกว่า 10%"

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
																send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "company_package_id": company_package_json['_id']['$oid'] , "created_datetime" : created_datetime }
																send_noti_badge = 1

																#insert member_notification
																noti_detail = {
																					"company_id": company_id,
																					"company_package_id": company_package_json['_id']['$oid']
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

										result = {
													"status" : True,
													"msg" : get_api_message("pay_overtime" , "pay_overtime_success" , member_lang)
												}
									else:
										result = {
													"status" : False,
													"msg" : get_api_message("pay_overtime" , "request_update_failed" , member_lang)
												}
								else:
									result = {
												"status" : False,
												"msg" : get_api_message("pay_overtime" , "this_package_is_not_enough_please_select_other_overtime_package" , member_lang)
											}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("pay_overtime" , "can_not_pay_overtime_because_request_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "pay_overtime"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def customer_noti_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_noti_start_at = "noti_start_at" in params
	isset_noti_length = "noti_length" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_noti_start_at and isset_noti_length:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

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
						"msg" : get_api_message("customer_noti_list" , "notification_start_at_is_not_a_number" , member_lang)
					}
			elif not check_noti_length:
				result = { 
						"status" : False,
						"msg" : get_api_message("customer_noti_list" , "notification_length_is_not_a_number" , member_lang)
					}
			else:
				if member_info['member_type'] == "customer":
					notification = db.member_notification.find({
																	"member_id" : member_info['_id']['$oid'],
																	"noti_status" : {"$in" : ["0","1"]}
																}).sort([("created_at", -1)]).skip(noti_start_at).limit(noti_length)
				
					total_data = db.member_notification.find({
																"member_id" : member_info['_id']['$oid'],
																"noti_status" : {"$in" : ["0","1"]}
															}).count()

					if notification is None:
						result = { 
									"status" : False,
									"msg" : get_api_message("customer_noti_list" , "data_not_found" , member_lang)
								}
					else:
						noti = db.member_notification.find({
																"member_id" : member_info['_id']['$oid'],
																"noti_status" : {"$in" : ["0","1"]}
															})

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

						for i in range(len(notification_json)):
							if member_lang == "en":
								noti_message = notification_json[i]['noti_message_en']
							else:
								noti_message = notification_json[i]['noti_message_th']

							if notification_json[i]['noti_type'] == "add_billing_statement":
								noti_code = notification_json[i]['noti_detail']['billing_statement_code']
							elif notification_json[i]['noti_type'] == "news_promotion":
								noti_code = None
							elif notification_json[i]['noti_type'] == "change_customer_name":
								noti_code = None
							elif notification_json[i]['noti_type'] == "approve_package_purchase":
								noti_code = notification_json[i]['noti_detail']['order_no']
							elif notification_json[i]['noti_type'] == "not_approve_package_purchase":
								noti_code = notification_json[i]['noti_detail']['order_no']
							elif notification_json[i]['noti_type'] == "quota_less_than":
								noti_code = None
							elif notification_json[i]['noti_type'] == "nearby_end_date_member_package":
								noti_code = None
							elif notification_json[i]['noti_type'] == "nearby_end_date_company_package":
								noti_code = None
							elif notification_json[i]['noti_type'] == "welcome_to_vrdriver":
								noti_code = None
							else:
								noti_code = notification_json[i]['noti_detail']['request_no']

							#แปลง format วันที่
							created_datetime = datetime.strptime(notification_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							noti_list.append({
								"noti_id" : notification_json[i]['_id']['$oid'],
								"member_id" : notification_json[i]['member_id'],
								"noti_message": noti_message,
								"noti_code": noti_code,
								"noti_type": notification_json[i]['noti_type'],
								"noti_detail": notification_json[i]['noti_detail'],
								"noti_status": notification_json[i]['noti_status'],
								"created_datetime": created_datetime
							})

						result = {
									"status" : True,
									"msg" : get_api_message("customer_noti_list" , "get_customer_notification_list_success" , member_lang),
									"noti_list" : noti_list,
									"badge" : count_badge,
									"total_data" : total_data
								}
				else:
					result = { 
						"status" : False,
						"msg" : get_api_message("customer_noti_list" , "member_type_is_invalid" , member_lang)
					}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "customer_noti_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def set_read_noti(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member_notification = db.member_notification.find({
																"member_id": member_info['_id']['$oid'], 
																"noti_status": "0"
															})
			
			if member_notification is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("set_read_noti" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_notification_object = dumps(member_notification)
				member_notification_json = json.loads(member_notification_object)
				update_status = 1

				for i in range(len(member_notification_json)):
					# update member_notification
					where_param = { "_id": ObjectId(member_notification_json[i]['_id']['$oid']) }
					value_param = {
									"$set":
										{
											"noti_status": "1",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.member_notification.update(where_param , value_param):
						update_status = 1
					else:
						update_status = 0
						break
						
				if update_status == 1:
					result = {
								"status" : True,
								"msg" : get_api_message("set_read_noti" , "set_read_noti_success" , member_lang)
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("set_read_noti" , "member_noti_update_failed" , member_lang)
							}	
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "set_read_noti"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_driver_rating_question(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			service_rating_question = db.service_rating_question.find()
			
			if service_rating_question is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_driver_rating_question" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				service_rating_question_object = dumps(service_rating_question)
				service_rating_question_json = json.loads(service_rating_question_object)

				service_rating_question_list = []

				for i in range(len(service_rating_question_json)):
					if member_lang == "en":
						question_name = service_rating_question_json[i]['question_en']
					else:
						question_name = service_rating_question_json[i]['question_th']

					service_rating_question_list.append({
						"question_id" : service_rating_question_json[i]['_id']['$oid'],
						"question_name": question_name
					})
						
				result = {
							"status" : True,
							"msg" : get_api_message("get_driver_rating_question" , "get_driver_rating_question_success" , member_lang),
							"question" : service_rating_question_list
						}	
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_driver_rating_question"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def send_driver_rating(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_rating = "rating" in params
	isset_recommend = "recommend" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_rating and isset_recommend:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id']),
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("send_driver_rating" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['request_status'] == "6" and (request_driver_json['job_status'] == "8" or request_driver_json['job_status'] == "9" or request_driver_json['job_status'] == "10" or request_driver_json['job_status'] == "11"):
					passenger_id = request_driver_json['passenger_id']
					member_id = request_driver_json['member_id']
					driver_id = request_driver_json['driver_id']

					service_rating = db.service_rating.find_one({"request_id": params['request_id']})
					
					if service_rating is None:
						#เพิ่มข้อมูลคะแนนการใช้บริการ
						data = { 
									"request_id": params['request_id'],
									"driver_id": request_driver_json['driver_id'],
									"passenger_id": request_driver_json['passenger_id'],
									"rating": [],
									"average_rating": "0",
									"recommend": None,
									"rating_status": "0",
									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						db.service_rating.insert_one(data)	

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					service_rating_object = dumps(service_rating)
					service_rating_json = json.loads(service_rating_object)

					if service_rating_json['rating_status'] == "0":
						if len(params['rating']) > 0:
							all_rating = 0
							for i in range(len(params['rating'])):
								all_rating = all_rating + int(params['rating'][i]['question_rating'])

							average_rating = all_rating / len(params['rating'])

							if params['recommend'] is None:
								recommend = ""
							else:
								recommend = params['recommend']

							where_param = { "request_id": params['request_id'] }
							value_param = {
											"$set":
												{
													"rating": params['rating'],
													"average_rating": average_rating,
													"recommend": recommend,
													"rating_status": "1",
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.service_rating.update(where_param , value_param):
								#คำนวณ rating ล่าสุดของคนขับ
								service_rating = db.service_rating.find({"driver_id": request_driver_json['driver_id']})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								service_rating_object = dumps(service_rating)
								service_rating_json = json.loads(service_rating_object)

								all_average_rating = 0

								for i in range(len(service_rating_json)):
									all_average_rating = all_average_rating + float(service_rating_json[i]['average_rating'])

								driver_average_rating = all_average_rating / len(service_rating_json)

								#update ข้อมูล rating ล่าสุดของคนขับ ลง table member
								where_param = { "_id": ObjectId(request_driver_json['driver_id']) }
								value_param = {
												"$set": {
															"driver_rating": driver_average_rating,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
								db.member.update(where_param , value_param)

								result = {
											"status" : True,
											"msg" : get_api_message("send_driver_rating" , "send_driver_rating_success" , member_lang)
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("send_driver_rating" , "service_rating_update_failed" , member_lang)
										}	
						else:
							result = { 
										"status" : False,
										"msg" : get_api_message("send_driver_rating" , "please_check_your_rating" , member_lang)
									}
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("send_driver_rating" , "can_not_send_driver_rating_because_you_have_already_sended" , member_lang)
								}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("send_driver_rating" , "can_not_send_driver_rating_because_request_status_is_invalid" , member_lang)
							}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "send_driver_rating"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def set_job_1_hour(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_no = "request_no" in params
	isset_start_date = "start_date" in params

	if isset_accept and isset_content_type and isset_app_version and isset_request_no and isset_start_date:
		request_driver = db.request_driver.find_one({"request_no": params['request_no']})
		
		if request_driver is None:
			result = { 
						"status" : False,
						"msg" : "Request not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			request_driver_object = dumps(request_driver)
			request_driver_json = json.loads(request_driver_object)

			if request_driver_json['request_status'] == "1" or request_driver_json['request_status'] == "4":
				start_date = params['start_date']
				end_date = params['start_date']
				start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
				delay_end_date = params['start_date']
				request_status = "4"
				job_status = "2"

				where_param = { "request_no": params['request_no'] }
				value_param = {
								"$set": {
											"start_date": start_date,
											"end_date": end_date,
											"start_date_int": start_date_int,
											"delay_end_date": delay_end_date,
											"start_at": request_driver_json['start_date']+" "+request_driver_json['start_time'],
											"request_status": request_status,
											"job_status": job_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

				if db.request_driver.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Set job 1 hour success."
							}
				else:
					result = {
								"status" : False,
								"msg" : "Request update failed."
							}
			else:
				result = {
							"status" : False,
							"msg" : "Can't set job 1 hour because request status is invalid."
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "set_job_1_hour"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def set_job_time(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_no = "request_no" in params
	isset_start_time = "start_time" in params
	isset_end_time = "end_time" in params

	if isset_accept and isset_content_type and isset_app_version and isset_request_no:
		request_driver = db.request_driver.find_one({"request_no": params['request_no']})
		
		if request_driver is None:
			result = { 
						"status" : False,
						"msg" : "Request not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			request_driver_object = dumps(request_driver)
			request_driver_json = json.loads(request_driver_object)
	
			if params['start_time'] != "":
				start_time = params['start_time']
			else:
				start_time = request_driver_json['start_time']

			if params['end_time'] != "":
				delay_end_time = params['end_time']
			else:
				delay_end_time = request_driver_json['delay_end_time']

			if request_driver_json['delay_minute'] > 0:
				delay_end_time_obj = datetime.strptime(params['end_time'], '%H:%M:%S')
				check_datetime_obj = delay_end_time_obj - timedelta(minutes=request_driver_json['delay_minute'])
				end_time = check_datetime_obj.strftime('%H:%M:%S')
			else:
				end_time = params['end_time']

			where_param = { "request_no": params['request_no'] }
			value_param = {
							"$set": {
										"start_time": start_time,
										"end_time": end_time,
										"start_at": request_driver_json['start_date']+" "+end_time,
										"delay_end_time": delay_end_time,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

			if db.request_driver.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Set job time success."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Request update failed."
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "set_job_time"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

