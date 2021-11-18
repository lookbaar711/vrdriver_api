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

#edit -- add special skill
def get_driver_profile(mem_id,request):
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

			driver = db.member.find_one({
											"member_token": token,
											"member_type": "driver"
										})
			
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			driver_object = dumps(driver)
			driver_json = json.loads(driver_object)

			member = db.member.find_one({
											"_id": ObjectId(mem_id),
											"member_type": "driver"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_driver_profile" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				level_name = None
				level_detail = None
				level_image = None

				if member_json['driver_level'] is not None:
					driver_level = db.driver_level.find_one({"_id": ObjectId(member_json['driver_level'])})
					
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

				if member_lang == "en":
					car_gear_text = member_json['car_gear_en']
					service_area_text = member_json['service_area_en']
					communication_text = member_json['communication_en']
					workday_text = member_json['workday_en']
					special_skill_text = member_json['special_skill_en']
					car_type_detail = []
					car_type_text = ""

					if member_json['car_type_en'] is not None:
						car_type_split = member_json['car_type_en'].split(" , ")

						for i in range(len(car_type_split)):
							if car_type_split[i] == "Sedan":
								car_type_text = car_type_split[i]+" "+str(member_json['sedan_job'])+" times"
							elif car_type_split[i] == "SUV":
								car_type_text = car_type_split[i]+" "+str(member_json['suv_job'])+" times"
							else:
								car_type_text = car_type_split[i]+" "+str(member_json['van_job'])+" times"

							car_type_detail.append(car_type_text)
				else:
					car_gear_text = member_json['car_gear_th']
					service_area_text = member_json['service_area_th']
					communication_text = member_json['communication_th']
					workday_text = member_json['workday_th']
					special_skill_text = member_json['special_skill_th']
					car_type_detail = []
					car_type_text = ""

					if member_json['car_type_th'] is not None:
						car_type_split = member_json['car_type_th'].split(" , ")

						for i in range(len(car_type_split)):
							if car_type_split[i] == "รถเก๋ง":
								car_type_text = car_type_split[i]+" "+str(member_json['sedan_job'])+" times"
							elif car_type_split[i] == "รถ SUV":
								car_type_text = car_type_split[i]+" "+str(member_json['suv_job'])+" times"
							else:
								car_type_text = car_type_split[i]+" "+str(member_json['van_job'])+" times"

							car_type_detail.append(car_type_text)
						
				member_birthday = None
				driver_license_expire = None

				if member_json['member_birthday'] is not None:
					member_birthday = datetime.strptime(member_json['member_birthday'], '%Y-%m-%d').strftime('%d/%m/%Y')

				if member_json['driver_license_expire'] is not None:
					driver_license_expire = datetime.strptime(member_json['driver_license_expire'], '%Y-%m-%d').strftime('%d/%m/%Y')

				emergency_call = db.emergency_call.find_one()
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				emergency_call_object = dumps(emergency_call)
				emergency_call_json = json.loads(emergency_call_object)

				if member_json['driver_rating'] is not None:
					driver_rating = round(float(member_json['driver_rating']) , 1)
				else:
					driver_rating = float("0")

				driver_profile = {
									"member_id" : member_json['_id']['$oid'],
									"member_code": member_json['member_code'],
									"member_username": member_json['member_username'],
									"member_firstname_en": member_json['member_firstname_en'],
									"member_lastname_en": member_json['member_lastname_en'],
									"member_firstname_th": member_json['member_firstname_th'],
									"member_lastname_th": member_json['member_lastname_th'],
									"member_email": member_json['member_email'],
									"member_tel": member_json['member_tel'],
									"member_birthday": member_birthday,
									"member_gender": member_json['member_gender'],
									"member_type": member_json['member_type'],
									"profile_image": member_json['profile_image'],
									"driver_license_expire": driver_license_expire,
									"driver_license_no": member_json['driver_license_no'],
									"car_type": member_json['car_type'],
									"car_type_detail": car_type_detail,
									"car_gear": member_json['car_gear'],
									"car_gear_text": car_gear_text,
									"service_area": member_json['service_area'],
									"service_area_text": service_area_text,
									"communication": member_json['communication'],
									"communication_text": communication_text,
									"workday": member_json['workday'],
									"workday_text": workday_text,
									"special_skill": member_json['special_skill'],
									"special_skill_text": special_skill_text,
									"driver_rating": driver_rating,
									"driver_level": member_json['driver_level'],
									"level_name": level_name,
									"level_detail": level_detail,
									"level_image": level_image,
									"member_lang": member_json['member_lang'],
									"member_token": member_json['member_token'],
									"noti_key": member_json['noti_key'],
									"member_status": member_json['member_status'],
									"driver_emergency" : emergency_call_json['call_driver_admin']
								}

				result = {
							"status" : True,
							"msg" : get_api_message("get_driver_profile" , "get_driver_profile_success" , member_lang),
							"driver_profile" : driver_profile
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
	user_type = "driver"
	function_name = "get_driver_profile"
	request_headers = request.headers
	params_get = {"member_id" : mem_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def get_my_driver_profile(request):
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
											"member_type": "driver"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_my_driver_profile" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				level_name = None
				level_detail = None
				level_image = None

				if member_json['driver_level'] is not None:
					driver_level = db.driver_level.find_one({"_id": ObjectId(member_json['driver_level'])})
					
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

				if member_lang == "en":
					car_gear_text = member_json['car_gear_en']
					service_area_text = member_json['service_area_en']
					communication_text = member_json['communication_en']
					workday_text = member_json['workday_en']
					special_skill_text = member_json['special_skill_en']
					car_type_detail = []
					car_type_text = ""

					if member_json['car_type_en'] is not None:
						car_type_split = member_json['car_type_en'].split(" , ")

						for i in range(len(car_type_split)):
							if car_type_split[i] == "Sedan":
								car_type_text = car_type_split[i]+" "+str(member_json['sedan_job'])+" times"
							elif car_type_split[i] == "SUV":
								car_type_text = car_type_split[i]+" "+str(member_json['suv_job'])+" times"
							else:
								car_type_text = car_type_split[i]+" "+str(member_json['van_job'])+" times"

							car_type_detail.append(car_type_text)
				else:
					car_gear_text = member_json['car_gear_th']
					service_area_text = member_json['service_area_th']
					communication_text = member_json['communication_th']
					workday_text = member_json['workday_th']
					special_skill_text = member_json['special_skill_th']
					car_type_detail = []
					car_type_text = ""

					if member_json['car_type_en'] is not None:
						car_type_split = member_json['car_type_th'].split(" , ")

						for i in range(len(car_type_split)):
							if car_type_split[i] == "รถเก๋ง":
								car_type_text = car_type_split[i]+" "+str(member_json['sedan_job'])+" times"
							elif car_type_split[i] == "รถ SUV":
								car_type_text = car_type_split[i]+" "+str(member_json['suv_job'])+" times"
							else:
								car_type_text = car_type_split[i]+" "+str(member_json['van_job'])+" times"

							car_type_detail.append(car_type_text)

				member_birthday = None
				driver_license_expire = None

				if member_json['member_birthday'] is not None:
					member_birthday = datetime.strptime(member_json['member_birthday'], '%Y-%m-%d').strftime('%d/%m/%Y')

				if member_json['driver_license_expire'] is not None:
					driver_license_expire = datetime.strptime(member_json['driver_license_expire'], '%Y-%m-%d').strftime('%d/%m/%Y')
				
				emergency_call = db.emergency_call.find_one()
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				emergency_call_object = dumps(emergency_call)
				emergency_call_json = json.loads(emergency_call_object)

				if member_json['driver_rating'] is not None:
					driver_rating = round(float(member_json['driver_rating']) , 1)
				else:
					driver_rating = float("0")

				driver_profile = {
									"member_id" : member_json['_id']['$oid'],
									"member_code": member_json['member_code'],
									"member_username": member_json['member_username'],
									"member_firstname_en": member_json['member_firstname_en'],
									"member_lastname_en": member_json['member_lastname_en'],
									"member_firstname_th": member_json['member_firstname_th'],
									"member_lastname_th": member_json['member_lastname_th'],
									"member_email": member_json['member_email'],
									"member_tel": member_json['member_tel'],
									"member_birthday": member_birthday,
									"member_gender": member_json['member_gender'],
									"member_type": member_json['member_type'],
									"profile_image": member_json['profile_image'],
									"driver_license_expire": driver_license_expire,
									"driver_license_no": member_json['driver_license_no'],
									"car_type": member_json['car_type'],
									"car_type_detail": car_type_detail,
									"car_gear": member_json['car_gear'],
									"car_gear_text": car_gear_text,
									"service_area": member_json['service_area'],
									"service_area_text": service_area_text,
									"communication": member_json['communication'],
									"communication_text": communication_text,
									"workday": member_json['workday'],
									"workday_text": workday_text,
									"special_skill": member_json['special_skill'],
									"special_skill_text": special_skill_text,
									"driver_rating": driver_rating,
									"driver_level": member_json['driver_level'],
									"level_name": level_name,
									"level_detail": level_detail,
									"level_image": level_image,
									"member_lang": member_json['member_lang'],
									"member_token": member_json['member_token'],
									"noti_key": member_json['noti_key'],
									"member_status": member_json['member_status'],
									"driver_emergency" : emergency_call_json['call_driver_admin']
								}

				result = {
							"status" : True,
							"msg" : get_api_message("get_my_driver_profile" , "get_driver_profile_success" , member_lang),
							"driver_profile" : driver_profile
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
	user_type = "driver"
	function_name = "get_my_driver_profile"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def driver_news_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
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
						"msg" : get_api_message("driver_news_list" , "news_start_at_is_not_a_number" , member_lang)
					}
		elif not check_news_length:
			result = { 
						"status" : False,
						"msg" : get_api_message("driver_news_list" , "news_length_is_not_a_number" , member_lang)
					}
		else:
			news = db.news.find({
									"display" : {"$in" : ["all","driver"]},
									"news_status" : "1"
								}).sort([("pin", -1),("updated_at", -1)]).skip(news_start_at).limit(news_length)

			if news is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("driver_news_list" , "data_not_found" , member_lang)
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
							"msg" : get_api_message("driver_news_list" , "get_driver_news_list_success" , member_lang),
							"news_list" : news_list
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "driver_news_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def main_driver_guest(request):
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
		check_version = check_update_version("driver" , params['app_version'] , params['os_type'])

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
						"msg" : get_api_message("main_driver_guest" , "number_news_is_not_a_number" , member_lang)
					}
		else:
			news = db.news.find({
									"display" : {"$in" : ["all","driver"]},
									"news_status": "1"
								}).sort([("pin", -1),("updated_at", -1)]).limit(number_news)
			
			news_list = []
			job_list = []

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

			lang_code_en = "en"
			lang_code_th = "th"

			if member_lang == "en":
				gender_name = "Male"
				lang_name_en = "EN"
				lang_name_th = "TH"
				request_status_text = "Finish"
			else:
				gender_name = "ชาย"
				lang_name_en = "อังกฤษ"
				lang_name_th = "ไทย"
				request_status_text = "สำเร็จ"
			
			job_list = [
							{
								"hour_amount": 7,
								"from_location_name": "SPACE 48 BUILDING",
								"from_location_address": "โครงการปรีชา คอมเพล็กซ์ อาคารสเปซ 48 ถนนรัชดาภิเษก แขวงสามเสนนอก เขตห้วยขวาง กรุงเทพมหานคร 10310",
								"to_location_name": "Q HOUSE PLOENCHIT",
								"to_location_address": "598 ถนนเพลินจิต แขวงลุมพินี เขตปทุมวัน กรุงเทพมหานคร 10330",
								"car_brand_name": "Toyota",
								"driver_note": "ต้องการคนขับที่ช่วยยกของได้ เพราะมีของที่ต้องขนไปด้วย",
								"driver_gender": [
									{
										"code": "male",
										"name": gender_name
									}
								],
								"driver_gender_text": gender_name,
								"communication": [
									{
										"communication_id": "5ea11dfc1d9c7d3aac00762d",
										"flag_image": "flag_th.png",
										"lang_code": lang_code_th, #th
										"lang_name": lang_name_th #TH or ไทย
									},
									{
										"communication_id": "5ea11e011d9c7d3aac00762e",
										"flag_image": "flag_en.png",
										"lang_code": lang_code_en, #en
										"lang_name": lang_name_en #EN or อังกฤษ
									}
								],
								"request_status": "6",
								"request_status_text": request_status_text,
								"payment_amount": "2,100"
							},
							{
								"hour_amount": 6,
								"from_location_name": "OLYMPIA TOWER",
								"from_location_address": "444 อาคารโอลิมเปียไทยทาวเวอร์ ถนนรัชดาภิเษก สามเสนนอก ห้วยขวาง กรุงเทพฯ 10310",
								"to_location_name": "SPACE 48 BUILDING",
								"to_location_address": "โครงการปรีชา คอมเพล็กซ์ อาคารสเปซ 48 ถนนรัชดาภิเษก แขวงสามเสนนอก เขตห้วยขวาง กรุงเทพมหานคร 10310",
								"car_brand_name": "Honda",
								"driver_note": "ขอแวะที่ปั้มก่อนถึงที่หมาย",
								"driver_gender": [
									{
										"code": "male",
										"name": gender_name
									}
								],
								"driver_gender_text": gender_name,
								"communication": [
									{
										"communication_id": "5ea11dfc1d9c7d3aac00762d",
										"flag_image": "flag_th.png",
										"lang_code": lang_code_th, #th
										"lang_name": lang_name_th #TH or ไทย
									},
									{
										"communication_id": "5ea11e011d9c7d3aac00762e",
										"flag_image": "flag_en.png",
										"lang_code": lang_code_en, #en
										"lang_name": lang_name_en #EN or อังกฤษ
									}
								],
								"request_status": "6",
								"request_status_text": request_status_text,
								"payment_amount": "1,800"
							}
						]

			result = {
						"status" : True,
						"msg" : get_api_message("main_driver_guest" , "get_main_driver_guest_success" , member_lang),
						"news" : news_list,
						"job" : job_list,
						"check_version" : check_version
				}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "main_driver_guest"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def main_driver(request):
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
			check_version = check_update_version("driver" , params['app_version'] , params['os_type'])
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member = db.member.find_one({
											"member_token": token,
											"member_type": "driver"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("main_driver" , "data_not_found" , member_lang)
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
								"msg" : get_api_message("main_driver" , "number_news_is_not_a_number" , member_lang)
							}
				else:
					news_list = []
					job_list = []

					news = db.news.find({
											"display" : {"$in" : ["all","driver"]},
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
																"driver_id": member_json['_id']['$oid'],
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

							job_list.append({
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
								"request_status_text": request_status_text,
								"check_status": request_driver_json[i]['check_status']
							})

					result = {
								"status" : True,
								"msg" : get_api_message("main_driver" , "get_main_driver_success" , member_lang),
								"news" : news_list,
								"job" : job_list,
								"check_version" : check_version,
								"len" : len(request_driver_json)
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
	user_type = "driver"
	function_name = "main_driver"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_driver_register(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
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

		car_type = db.car_type.find()
		car_gear = db.car_gear.find()
		service_area = db.service_area.find()
		communication = db.communication.find()
		workday = db.workday.find()

		if car_type is None or car_gear is None or service_area is None or communication is None or workday is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("get_driver_register" , "please_check_your_master_data_in_database" , member_lang)
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

			car_type_list = []
			car_gear_list = []
			service_area_list = []
			communication_list = []
			workday_list = []

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

			for k in range(len(service_area_json)):
				if member_lang == "en":
					service_area_name = service_area_json[k]['service_area_name_en']
				else:
					service_area_name = service_area_json[k]['service_area_name_th']

				service_area_list.append({
					"service_area_id" : service_area_json[k]['_id']['$oid'],
					"service_area_name": service_area_name,
					"is_bangkok": service_area_json[k]['is_bangkok'],
					"all_bangkok": service_area_json[k]['all_bangkok']
				})

			for l in range(len(communication_json)):
				if member_lang == "en":
					lang_name = communication_json[l]['lang_name_en']
				else:
					lang_name = communication_json[l]['lang_name_th']

				communication_list.append({
					"communication_id" : communication_json[l]['_id']['$oid'],
					"lang_name": lang_name,
					"lang_code": communication_json[l]['lang_code'],
					"flag_image": communication_json[l]['flag_image']
				})

			for m in range(len(workday_json)):
				if member_lang == "en":
					short_name = workday_json[m]['short_name_en']
				else:
					short_name = workday_json[m]['short_name_th']

				workday_list.append({
					"workday_id" : workday_json[m]['_id']['$oid'],
					"short_name": short_name
				})

			if member_lang == "en":
				male = "Male"
				female = "Female"
			else:
				male = "ชาย"
				female = "หญิง"

			gender_list = [
							{"code": "male","name": male},
							{"code": "female","name": female}
						]

			result = {
						"status" : True,
						"msg" : get_api_message("get_driver_register" , "get_driver_register_success" , member_lang),
						"car_type" : car_type_list,
						"car_gear" : car_gear_list,
						"service_area" : service_area_list,
						"communication" : communication_list,
						"workday" : workday_list,
						"gender" : gender_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "get_driver_register"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def send_driver_register(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_firstname_en = "member_firstname_en" in params
	isset_lastname_en = "member_lastname_en" in params
	isset_firstname_th = "member_firstname_th" in params
	isset_lastname_th = "member_lastname_th" in params
	isset_email = "member_email" in params
	isset_tel = "member_tel" in params
	isset_username = "member_username" in params
	isset_password = "member_password" in params

	isset_birthday = "member_birthday" in params
	isset_gender = "member_gender" in params
	isset_license_expire = "driver_license_expire" in params
	isset_license_no = "driver_license_no" in params
	isset_car_type = "car_type" in params
	isset_car_gear = "car_gear" in params
	isset_service_area = "service_area" in params
	isset_communication = "communication" in params
	isset_workday = "workday" in params
	isset_profile_image = "profile_image" in params
	isset_member_lang = "member_lang" in params
	isset_os_type = "os_type" in params

	if isset_accept and isset_content_type and isset_app_version and isset_firstname_en and isset_lastname_en and isset_firstname_th and isset_lastname_th and isset_email and isset_tel and isset_username and isset_password and isset_birthday and isset_gender and isset_license_expire and isset_license_no and isset_car_type and isset_car_gear and isset_service_area and isset_communication and isset_workday and isset_profile_image and isset_member_lang and isset_os_type:
		if params['member_lang'] == "en":
			member_lang = "en"
		else:
			member_lang = "th"

		validate = []

		#check required
		if params['member_firstname_en']=="" or params['member_firstname_en'] is None:
			validate.append({"error_param" : "member_firstname_en","msg" : get_api_message("send_driver_register" , "firstname_en_is_required" , member_lang)}) 
		if params['member_lastname_en']=="" or params['member_lastname_en'] is None:
			validate.append({"error_param" : "member_lastname_en","msg" : get_api_message("send_driver_register" , "lastname_en_is_required" , member_lang)}) 
		if params['member_firstname_th']=="" or params['member_firstname_th'] is None:
			validate.append({"error_param" : "member_firstname_th","msg" : get_api_message("send_driver_register" , "firstname_th_is_required" , member_lang)}) 
		if params['member_lastname_th']=="" or params['member_lastname_th'] is None:
			validate.append({"error_param" : "member_lastname_th","msg" : get_api_message("send_driver_register" , "lastname_th_is_required" , member_lang)}) 

		if params['member_email']=="" or params['member_email'] is None:
			validate.append({"error_param" : "member_email","msg" : get_api_message("send_driver_register" , "email_is_required" , member_lang)}) 
		if params['member_tel']=="" or params['member_tel'] is None:
			validate.append({"error_param" : "member_tel","msg" : get_api_message("send_driver_register" , "tel_is_required" , member_lang)})
		if params['member_username']=="" or params['member_username'] is None:
			validate.append({"error_param" : "member_username","msg" : get_api_message("send_driver_register" , "username_is_required" , member_lang)}) 
		if params['member_password']=="" or params['member_password'] is None:
			validate.append({"error_param" : "member_password","msg" : get_api_message("send_driver_register" , "password_is_required" , member_lang)}) 
		
		if params['member_birthday']=="" or params['member_birthday'] is None:
			validate.append({"error_param" : "member_birthday","msg" : get_api_message("send_driver_register" , "birthday_is_required" , member_lang)}) 
		if params['member_gender']=="" or params['member_gender'] is None:
			validate.append({"error_param" : "member_gender","msg" : get_api_message("send_driver_register" , "gender_is_required" , member_lang)}) 
		if params['driver_license_expire']=="":
			validate.append({"error_param" : "driver_license_expire","msg" : get_api_message("send_driver_register" , "driver_license_expire_is_required" , member_lang)}) 
		if params['driver_license_no']=="" or params['driver_license_no'] is None:
			validate.append({"error_param" : "driver_license_no","msg" : get_api_message("send_driver_register" , "driver_license_no_is_required" , member_lang)})
		if params['car_type']=="" or params['car_type'] is None:
			validate.append({"error_param" : "car_type","msg" : get_api_message("send_driver_register" , "car_type_is_required" , member_lang)}) 
		if params['car_gear']=="" or params['car_gear'] is None:
			validate.append({"error_param" : "car_gear","msg" : get_api_message("send_driver_register" , "car_gear_is_required" , member_lang)}) 
		if params['service_area']=="" or params['service_area'] is None:
			validate.append({"error_param" : "service_area","msg" : get_api_message("send_driver_register" , "service_area_is_required" , member_lang)}) 
		if params['communication']=="" or params['communication'] is None:
			validate.append({"error_param" : "communication","msg" : get_api_message("send_driver_register" , "communication_is_required" , member_lang)}) 
		if params['workday']=="" or params['workday'] is None:
			validate.append({"error_param" : "workday","msg" : get_api_message("send_driver_register" , "workday_is_required" , member_lang)}) 
		if params['member_lang']=="" or params['member_lang'] is None:
			validate.append({"error_param" : "member_lang","msg" : get_api_message("send_driver_register" , "language_is_required" , member_lang)}) 

		#check already customer name
		if (params['member_firstname_en']!="" and params['member_firstname_en'] is not None) and (params['member_lastname_en']!="" and params['member_lastname_en'] is not None):
			check_customer_name = db.member.find({
													"member_type": "driver",
													"member_firstname_en": params['member_firstname_en'].strip().title(),
													"member_lastname_en": params['member_lastname_en'].strip().title()
												}).count()
			if check_customer_name > 0:
				validate.append({"error_param" : "member_firstname_en","msg" : get_api_message("send_driver_register" , "firstname_en_and_lastname_en_has_been_used" , member_lang)}) 

		if (params['member_firstname_th']!="" and params['member_firstname_th'] is not None) and (params['member_lastname_th']!="" and params['member_lastname_th'] is not None):
			check_customer_name = db.member.find({
													"member_type": "driver",
													"member_firstname_th": params['member_firstname_th'].strip().title(),
													"member_lastname_th": params['member_lastname_th'].strip().title()
												}).count()
			if check_customer_name > 0:
				validate.append({"error_param" : "member_firstname_th","msg" : get_api_message("send_driver_register" , "firstname_th_and_lastname_th_has_been_used" , member_lang)}) 
		
		#check already email
		if params['member_email']!="" and params['member_email'] is not None:
			#check email format
			pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
			regex = re.compile(pattern)
			check_format_email = regex.findall(params['member_email'])

			if len(check_format_email) > 0:
				check_email = db.member.find({
												"member_type": "driver",
												"member_email": params['member_email'].strip().lower()
											}).count()
				if check_email > 0:
					validate.append({"error_param" : "member_email","msg" : get_api_message("send_driver_register" , "email_has_been_used" , member_lang)})
			else:
				validate.append({"error_param" : "member_email","msg" : get_api_message("send_driver_register" , "invalid_email_format" , member_lang)})		

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
				validate.append({"error_param" : "member_tel","msg" : get_api_message("send_driver_register" , "invalid_tel_format" , member_lang)}) 

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
				validate.append({"error_param" : "driver_license_no","msg" : get_api_message("send_driver_register" , "invalid_driver_license_no_format" , member_lang)})

		#check already username
		if params['member_username']!="" and params['member_username'] is not None:
			#check username format
			pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
			regex = re.compile(pattern)
			check_format_username = regex.findall(params['member_username'])

			if len(check_format_username) > 0:
				check_username = db.member.find({
													"member_type": "driver",
													"member_username": params['member_username'].strip().lower()
												}).count()
				if check_username > 0:
					validate.append({"error_param" : "member_username","msg" : get_api_message("send_driver_register" , "username_has_been_used" , member_lang)}) 
			else:
				validate.append({"error_param" : "member_username","msg" : get_api_message("send_driver_register" , "invalid_username_format" , member_lang)})		

		#check password format
		if params['member_password']!="" and params['member_password'] is not None:
			count_password = len(params['member_password'])

			if count_password < 6:
				validate.append({"error_param" : "member_password","msg" : get_api_message("send_driver_register" , "password_less_than_6_character" , member_lang)}) 

		#set car_type_en & car_type_th
		car_type_in = []
		for i in range(len(params['car_type'])):
			car_type_in.append(ObjectId(params['car_type'][i]))

		car_type = db.car_type.find({"_id" : {"$in" : car_type_in}})

		if car_type is None or car_type.count() == 0:
			validate.append({"error_param" : "car_type","msg" : get_api_message("send_driver_register" , "please_check_your_car_type_value" , member_lang)})
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

		#set car_gear_en & car_gear_th
		car_gear_in = []
		for i in range(len(params['car_gear'])):
			car_gear_in.append(ObjectId(params['car_gear'][i]))

		car_gear = db.car_gear.find({"_id" : {"$in" : car_gear_in}})

		if car_gear is None or car_gear.count() == 0:
			validate.append({"error_param" : "car_gear","msg" : get_api_message("send_driver_register" , "please_check_your_car_gear_value" , member_lang)})
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

		#set communication_en & communication_th
		communication_in = []
		for i in range(len(params['communication'])):
			communication_in.append(ObjectId(params['communication'][i]))

		communication = db.communication.find({"_id" : {"$in" : communication_in}})

		if communication is None or communication.count() == 0:
			validate.append({"error_param" : "communication","msg" : get_api_message("send_driver_register" , "please_check_your_communication_value" , member_lang)}) 
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

		#set service_area_en & service_area_th
		service_area_in = []
		for i in range(len(params['service_area'])):
			service_area_in.append(ObjectId(params['service_area'][i]))

		service_area = db.service_area.find({"_id" : {"$in" : service_area_in}})

		if service_area is None or service_area.count() == 0:
			validate.append({"error_param" : "service_area","msg" : get_api_message("send_driver_register" , "please_check_your_service_area_value" , member_lang)}) 
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

		#set workday_en & workday_th
		workday_in = []
		for i in range(len(params['workday'])):
			workday_in.append(ObjectId(params['workday'][i]))

		workday = db.workday.find({"_id" : {"$in" : workday_in}})

		if workday is None or workday.count() == 0:
			validate.append({"error_param" : "workday","msg" : get_api_message("send_driver_register" , "please_check_your_workday_value" , member_lang)}) 
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

			#เอา password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(params['member_password'].encode())
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

			member_age = 0
			#แปลง format วันที่
			if params['member_birthday'] is not None:
				member_birthday = datetime.strptime(params['member_birthday'], '%d/%m/%Y').strftime('%Y-%m-%d')
				member_age = get_member_age(member_birthday)

			driver_license_expire = None

			if params['driver_license_expire'] is not None:
				driver_license_expire = datetime.strptime(params['driver_license_expire'], '%d/%m/%Y').strftime('%Y-%m-%d')				

			register_date_int = int(datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

			data = { 
						"member_code": member_code,
						"member_username": params['member_username'].strip().lower(),
						"member_password": hash_pass,
						"member_firstname_en": params['member_firstname_en'].strip().title(),
						"member_lastname_en": params['member_lastname_en'].strip().title(),
						"member_firstname_th": params['member_firstname_th'].strip().title(),
						"member_lastname_th": params['member_lastname_th'].strip().title(),
						"member_email": params['member_email'].strip().lower(),
						"member_tel": params['member_tel'].strip(),
						"member_type": "driver",

						"member_birthday": member_birthday,
						"member_gender": params['member_gender'],
						"driver_license_expire": driver_license_expire,
						"driver_license_no": params['driver_license_no'].strip(),
						"car_type": params['car_type'],
						"car_type_en": car_type_en,
						"car_type_th": car_type_th,
						"car_gear": params['car_gear'],
						"car_gear_en": car_gear_en,
						"car_gear_th": car_gear_th,
						"service_area": params['service_area'],
						"service_area_en": service_area_en,
						"service_area_th": service_area_th,
						"communication": params['communication'],
						"communication_en": communication_en,
						"communication_th": communication_th,
						"workday": params['workday'],
						"workday_en": workday_en,
						"workday_th": workday_th,
						"special_skill": [],
						"special_skill_en": None,
						"special_skill_th": None,
						"driver_level": None,
						"driver_level_text": None,
						"driver_level_priority": 0,
						"driver_rating": float("0"),
						"profile_image": image_name,
						"member_lang": member_lang,
						"member_status": "0",
						"break_start_date": None,
						"break_end_date": None,
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"register_date_int": register_date_int,
						"approved_at": None,
						"member_token": None,
						"noti_key": None,
						"os_type": params['os_type'],
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
				username = params['member_username'].strip().lower()
				password = params['member_password']
				android_link = "https://play.google.com/store"
				ios_link = "https://www.apple.com/th/ios/app-store/"

				email_type = "register_success_driver"
				subject = "VR Driver : สมัครสมาชิกคนขับสำเร็จ"
				to_email = params['member_email'].strip().lower()
				template_html = "register_success_driver.html"
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
							"msg" : get_api_message("send_driver_register" , "register_succes" , member_lang) 
						}
			else:
				result = {
						"status" : False,
						"msg" : get_api_message("send_driver_register" , "data_insert_failed" , member_lang) 
					}
		else:
			result = {
						"status" : False,
						"msg" : get_api_message("send_driver_register" , "please_check_your_parameters_value" , member_lang), 
						"error_list" : validate
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "send_driver_register"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_my_driver_profile(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_firstname_en = "member_firstname_en" in params
	isset_lastname_en = "member_lastname_en" in params
	isset_firstname_th = "member_firstname_th" in params
	isset_lastname_th = "member_lastname_th" in params
	isset_email = "member_email" in params
	isset_tel = "member_tel" in params

	isset_birthday = "member_birthday" in params
	isset_gender = "member_gender" in params
	isset_license_expire = "driver_license_expire" in params
	isset_license_no = "driver_license_no" in params
	isset_car_type = "car_type" in params
	isset_car_gear = "car_gear" in params
	isset_service_area = "service_area" in params
	isset_communication = "communication" in params
	isset_workday = "workday" in params
	isset_profile_image = "profile_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_firstname_en and isset_lastname_en and isset_firstname_th and isset_lastname_th and isset_email and isset_tel and isset_birthday and isset_gender and isset_license_expire and isset_license_no and isset_car_type and isset_car_gear and isset_service_area and isset_communication and isset_workday and isset_profile_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check required
			if params['member_firstname_en']=="" or params['member_firstname_en'] is None:
				validate.append({"error_param" : "member_firstname_en","msg" : get_api_message("edit_my_driver_profile" , "firstname_en_is_required" , member_lang)}) 
			if params['member_lastname_en']=="" or params['member_lastname_en'] is None:
				validate.append({"error_param" : "member_lastname_en","msg" : get_api_message("edit_my_driver_profile" , "lastname_en_is_required" , member_lang)})
			if params['member_firstname_th']=="" or params['member_firstname_th'] is None:
				validate.append({"error_param" : "member_firstname_th","msg" : get_api_message("edit_my_driver_profile" , "firstname_th_is_required" , member_lang)}) 
			if params['member_lastname_th']=="" or params['member_lastname_th'] is None:
				validate.append({"error_param" : "member_lastname_th","msg" : get_api_message("edit_my_driver_profile" , "lastname_th_is_required" , member_lang)}) 

			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_driver_profile" , "email_is_required" , member_lang)}) 
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_driver_profile" , "tel_is_required" , member_lang)}) 
			
			if params['member_birthday']=="" or params['member_birthday'] is None:
				validate.append({"error_param" : "member_birthday","msg" : get_api_message("edit_my_driver_profile" , "birthday_is_required" , member_lang)}) 
			if params['member_gender']=="" or params['member_gender'] is None:
				validate.append({"error_param" : "member_gender","msg" : get_api_message("edit_my_driver_profile" , "gender_is_required" , member_lang)}) 
			if params['driver_license_expire']=="":
				validate.append({"error_param" : "driver_license_expire","msg" : get_api_message("edit_my_driver_profile" , "driver_license_expire_is_required" , member_lang)}) 
			if params['driver_license_no']=="" or params['driver_license_no'] is None:
				validate.append({"error_param" : "driver_license_no","msg" : get_api_message("edit_my_driver_profile" , "driver_license_no_is_required" , member_lang)}) 
			if params['car_type']=="" or params['car_type'] is None:
				validate.append({"error_param" : "car_type","msg" : get_api_message("edit_my_driver_profile" , "car_type_is_required" , member_lang)}) 
			if params['car_gear']=="" or params['car_gear'] is None:
				validate.append({"error_param" : "car_gear","msg" : get_api_message("edit_my_driver_profile" , "car_gear_is_required" , member_lang)}) 
			if params['service_area']=="" or params['service_area'] is None:
				validate.append({"error_param" : "service_area","msg" : get_api_message("edit_my_driver_profile" , "service_area_is_required" , member_lang)}) 
			if params['communication']=="" or params['communication'] is None:
				validate.append({"error_param" : "communication","msg" : get_api_message("edit_my_driver_profile" , "communication_is_required" , member_lang)}) 
			if params['workday']=="" or params['workday'] is None:
				validate.append({"error_param" : "workday","msg" : get_api_message("edit_my_driver_profile" , "workday_is_required" , member_lang)}) 

			#check already customer name
			if (params['member_firstname_en']!="" and params['member_firstname_en'] is not None) and (params['member_lastname_en']!="" and params['member_lastname_en'] is not None):
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_customer_name = db.member.find({
														"member_token": {"$ne": token},
														"member_type": "driver",
														"member_firstname_en": params['member_firstname_en'].strip().title(),
														"member_lastname_en": params['member_lastname_en'].strip().title()
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname_en","msg" : get_api_message("edit_my_driver_profile" , "firstname_en_and_lastname_en_has_been_used" , member_lang)})

			if (params['member_firstname_th']!="" and params['member_firstname_th'] is not None) and (params['member_lastname_th']!="" and params['member_lastname_th'] is not None):
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_customer_name = db.member.find({
														"member_token": {"$ne": token},
														"member_type": "driver",
														"member_firstname_th": params['member_firstname_th'].strip().title(),
														"member_lastname_th": params['member_lastname_th'].strip().title()
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname_th","msg" : get_api_message("edit_my_driver_profile" , "firstname_th_and_lastname_th_has_been_used" , member_lang)}) 
			
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
													"member_type": "driver",
													"member_email": params['member_email'].strip().lower()
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_driver_profile" , "email_has_been_used" , member_lang)}) 
				else:
					validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_driver_profile" , "invalid_email_format" , member_lang)})

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
					validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_driver_profile" , "invalid_tel_format" , member_lang)}) 

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
					validate.append({"error_param" : "driver_license_no","msg" : get_api_message("edit_my_driver_profile" , "invalid_driver_license_no_format" , member_lang)}) 

			#set car_type_en & car_type_th
			car_type_in = []
			for i in range(len(params['car_type'])):
				car_type_in.append(ObjectId(params['car_type'][i]))

			car_type = db.car_type.find({"_id" : {"$in" : car_type_in}})

			if car_type is None or car_type.count() == 0:
				validate.append({"error_param" : "car_type","msg" : get_api_message("edit_my_driver_profile" , "please_check_your_car_type_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)
				car_type_en = ""
				car_type_th = ""

				for i in range(len(car_type_json)):
					if i == 0:
						car_type_en = car_type_json[i]['car_type_name_en']
						car_type_th = car_type_json[i]['car_type_name_th']
					else:
						car_type_en = car_type_en+" , "+car_type_json[i]['car_type_name_en']
						car_type_th = car_type_th+" , "+car_type_json[i]['car_type_name_th']

			#set car_gear_en & car_gear_th
			car_gear_in = []
			for i in range(len(params['car_gear'])):
				car_gear_in.append(ObjectId(params['car_gear'][i]))

			car_gear = db.car_gear.find({"_id" : {"$in" : car_gear_in}})

			if car_gear is None or car_gear.count() == 0:
				validate.append({"error_param" : "car_gear","msg" : get_api_message("edit_my_driver_profile" , "please_check_your_car_gear_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_gear_object = dumps(car_gear)
				car_gear_json = json.loads(car_gear_object)
				car_gear_en = ""
				car_gear_th = ""

				for i in range(len(car_gear_json)):
					if i == 0:
						car_gear_en = car_gear_json[i]['car_gear_en']
						car_gear_th = car_gear_json[i]['car_gear_th']
					else:
						car_gear_en = car_gear_en+" , "+car_gear_json[i]['car_gear_en']
						car_gear_th = car_gear_th+" , "+car_gear_json[i]['car_gear_th']

			#set communication_en & communication_th
			communication_in = []
			for i in range(len(params['communication'])):
				communication_in.append(ObjectId(params['communication'][i]))

			communication = db.communication.find({"_id" : {"$in" : communication_in}})

			if communication is None or communication.count() == 0:
				validate.append({"error_param" : "communication","msg" : get_api_message("edit_my_driver_profile" , "please_check_your_communication_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				communication_object = dumps(communication)
				communication_json = json.loads(communication_object)
				communication_en = ""
				communication_th = ""

				for i in range(len(communication_json)):
					if i == 0:
						communication_en = communication_json[i]['lang_name_en']
						communication_th = communication_json[i]['lang_name_th']
					else:
						communication_en = communication_en+" , "+communication_json[i]['lang_name_en']
						communication_th = communication_th+" , "+communication_json[i]['lang_name_th']

			#set service_area_en & service_area_th
			service_area_in = []
			for i in range(len(params['service_area'])):
				service_area_in.append(ObjectId(params['service_area'][i]))

			service_area = db.service_area.find({"_id" : {"$in" : service_area_in}})

			if service_area is None or service_area.count() == 0:
				validate.append({"error_param" : "service_area","msg" : get_api_message("edit_my_driver_profile" , "please_check_your_service_area_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				service_area_object = dumps(service_area)
				service_area_json = json.loads(service_area_object)
				service_area_en = ""
				service_area_th = ""

				for i in range(len(service_area_json)):
					if i == 0:
						service_area_en = service_area_json[i]['service_area_name_en']
						service_area_th = service_area_json[i]['service_area_name_th']
					else:
						service_area_en = service_area_en+" , "+service_area_json[i]['service_area_name_en']
						service_area_th = service_area_th+" , "+service_area_json[i]['service_area_name_th']

			#set workday_en & workday_th
			workday_in = []
			for i in range(len(params['workday'])):
				workday_in.append(ObjectId(params['workday'][i]))

			workday = db.workday.find({"_id" : {"$in" : workday_in}})

			if workday is None or workday.count() == 0:
				validate.append({"error_param" : "workday","msg" : get_api_message("edit_my_driver_profile" , "please_check_your_workday_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				workday_object = dumps(workday)
				workday_json = json.loads(workday_object)
				workday_en = ""
				workday_th = ""

				for i in range(len(workday_json)):
					if i == 0:
						workday_en = workday_json[i]['short_name_en']
						workday_th = workday_json[i]['short_name_th']
					else:
						workday_en = workday_en+" , "+workday_json[i]['short_name_en']
						workday_th = workday_th+" , "+workday_json[i]['short_name_th']


			#ถ้า validate ผ่าน
			if len(validate) == 0:
				member = db.member.find_one({
												"member_token": token,
												"member_type": "driver"
											})
				if member is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("edit_my_driver_profile" , "data_not_found" , member_lang)
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

					member_age = 0
					#แปลง format วันที่
					if params['member_birthday'] is not None:
						member_birthday = datetime.strptime(params['member_birthday'], '%d/%m/%Y').strftime('%Y-%m-%d')
						member_age = get_member_age(member_birthday)

					driver_license_expire = None

					if params['driver_license_expire'] is not None:
						driver_license_expire = datetime.strptime(params['driver_license_expire'], '%d/%m/%Y').strftime('%Y-%m-%d')

					where_param = { "member_token": token }
					value_param = {
									"$set": {
												"member_firstname_en": params['member_firstname_en'].strip().title(),
												"member_lastname_en": params['member_lastname_en'].strip().title(),
												"member_firstname_th": params['member_firstname_th'].strip().title(),
												"member_lastname_th": params['member_lastname_th'].strip().title(),
												"member_email": params['member_email'].strip().lower(),
												"member_tel": params['member_tel'].strip(),
												"profile_image": image_name,
												"member_birthday": member_birthday,
												"member_gender": params['member_gender'],
												"driver_license_expire": driver_license_expire,
												"driver_license_no": params['driver_license_no'].strip(),
												"car_type": params['car_type'],
												"car_type_en": car_type_en,
												"car_type_th": car_type_th,
												"car_gear": params['car_gear'],
												"car_gear_en": car_gear_en,
												"car_gear_th": car_gear_th,
												"service_area": params['service_area'],
												"service_area_en": service_area_en,
												"service_area_th": service_area_th,
												"communication": params['communication'],
												"communication_en": communication_en,
												"communication_th": communication_th,
												"workday": params['workday'],
												"workday_en": workday_en,
												"workday_th": workday_th,
												"member_age": int(member_age),
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

					if db.member.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : get_api_message("edit_my_driver_profile" , "edit_profile_success" , member_lang) 
								}
					else:
						result = {
								"status" : False,
								"msg" : get_api_message("edit_my_driver_profile" , "data_update_failed" , member_lang) 
								}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("edit_my_driver_profile" , "please_check_your_parameters_value" , member_lang), 
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
	user_type = "driver"
	function_name = "edit_my_driver_profile"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def job_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_job_tab = "job_tab" in params
	isset_request_status = "request_status" in params
	isset_job_start_at = "job_start_at" in params
	isset_job_length = "job_length" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_job_tab and isset_request_status and isset_job_start_at and isset_job_length:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			try:
				job_start_at = int(params['job_start_at'])
				check_job_start_at = True
			except ValueError:
				check_job_start_at = False

			try:
				job_length = int(params['job_length'])
				check_job_length = True
			except ValueError:
				check_job_length = False


			if not check_job_start_at:
				result = { 
							"status" : False,
							"msg" : get_api_message("job_list" , "job_start_at_is_not_a_number" , member_lang) 
						}
			elif not check_job_length:
				result = { 
							"status" : False,
							"msg" : get_api_message("job_list" , "job_length_is_not_a_number" , member_lang) 
						}
			else:
				if params['job_tab'] == "3":
					dl = db.driver_list.find({
												"driver_list.driver_id": member_info['_id']['$oid'],
												"driver_list_status": "1"
											})

					if dl is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						dl_in = []
						for i in range(len(dl_json)):
							for j in range(len(dl_json[i]['driver_list'])):
								#driver_id ในข้อมูลต้องตรงกับ member_id ของคนขับที่เรียก api และ driver_request_status ต้องเท่ากับ 0 หรือ 1 หรือ 4
								if ((dl_json[i]['driver_list'][j]['driver_id'] == member_info['_id']['$oid']) and (dl_json[i]['driver_list'][j]['driver_request_status'] == "0" or dl_json[i]['driver_list'][j]['driver_request_status'] == "1" or dl_json[i]['driver_list'][j]['driver_request_status'] == "4")):
									dl_in.append(dl_json[i]['_id']['$oid'])

						if "0" in params['request_status']:
							params['request_status'].remove("0")
						if "6" in params['request_status']:
							params['request_status'].remove("6")

						if len(params['request_status']) == 0:
							request_driver = db.request_driver.find({
																		"driver_list_id": {"$in" : dl_in},
																		"request_status": {"$nin" : ["0" , "6"]}
																	}).sort([("created_at", -1)]).skip(job_start_at).limit(job_length)
						else:
							#ถ้าเลือกสถานะ ตอบรับแล้ว
							if "1" in params['request_status']:
								#ถ้าไม่ได้เลือกสถานะ งานที่ใกล้จะถึง ให้ดึงข้อมูลงานสถานะ งานที่ใกล้จะถึง มาแสดงด้วย 
								if "4" not in params['request_status']:
									params['request_status'].append("4")

							request_driver = db.request_driver.find({
																		"driver_list_id": {"$in" : dl_in},
																		"request_status": {"$in" : params['request_status']}
																	}).sort([("created_at", -1)]).skip(job_start_at).limit(job_length)
							
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

								if (request_driver_json[i]['request_status'] == "3" or request_driver_json[i]['request_status'] == "4" or request_driver_json[i]['request_status'] == "5" or request_driver_json[i]['request_status'] == "6") and member_info['_id']['$oid'] == request_driver_json[i]['driver_id']:
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
										"request_status_text": request_status_text,
										"check_status": request_driver_json[i]['check_status']
									})
								elif (request_driver_json[i]['request_status'] == "0" or request_driver_json[i]['request_status'] == "1" or request_driver_json[i]['request_status'] == "2"):
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
										"request_status_text": request_status_text,
										"check_status": request_driver_json[i]['check_status']
									})

						result = {
									"status" : True,
									"msg" : get_api_message("job_list" , "get_job_list_success" , member_lang), 
									"data" : request_driver_list
								}
				elif params['job_tab'] == "2":
					dl = db.driver_list.find({
												"driver_list.driver_id": member_info['_id']['$oid'],
												"driver_list_status": "1"
											})

					if dl is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						dl_in = []
						for i in range(len(dl_json)):
							for j in range(len(dl_json[i]['driver_list'])):
								#driver_id ในข้อมูลต้องตรงกับ member_id ของคนขับที่เรียก api และ driver_request_status ต้องเท่ากับ 0
								if ((dl_json[i]['driver_list'][j]['driver_id'] == member_info['_id']['$oid']) and (dl_json[i]['driver_list'][j]['driver_request_status'] == "0")):
									dl_in.append(dl_json[i]['_id']['$oid'])

						request_driver = db.request_driver.find({
																	"driver_list_id": {"$in" : dl_in},
																	"request_status": "0"
																}).sort([("created_at", -1)]).skip(job_start_at).limit(job_length)

						request_driver_list = []

						if request_driver is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							request_driver_object = dumps(request_driver)
							request_driver_json = json.loads(request_driver_object)

							for i in range(len(request_driver_json)):
								package_info = get_package_info(request_driver_json[i]['main_package_id'])

								if member_lang == "en":
									main_package_name = package_info['package_name_en']
									request_status_text = "Waiting for reply"
								else:
									main_package_name = package_info['package_name_th']
									request_status_text = "รอตอบรับ"
								

								start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
								start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')
								start_datetime = start_date+" "+start_time

								if (request_driver_json[i]['request_status'] == "3" or request_driver_json[i]['request_status'] == "4" or request_driver_json[i]['request_status'] == "5" or request_driver_json[i]['request_status'] == "6") and member_info['_id']['$oid'] == request_driver_json[i]['driver_id']:
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
										"request_status_text": request_status_text,
										"job_status": request_driver_json[i]['job_status']
									})
								elif (request_driver_json[i]['request_status'] == "0" or request_driver_json[i]['request_status'] == "1" or request_driver_json[i]['request_status'] == "2"):
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
										"request_status_text": request_status_text,
										"job_status": request_driver_json[i]['job_status']
									})

						result = {
									"status" : True,
									"msg" : get_api_message("job_list" , "get_job_list_success" , member_lang),
									"data" : request_driver_list
								}
				else:
					dl = db.driver_list.find({
												"driver_list.driver_id": member_info['_id']['$oid'],
												"driver_list_status": "1"
											})

					if dl is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						dl_in = []
						for i in range(len(dl_json)):
							for j in range(len(dl_json[i]['driver_list'])):
								if ((dl_json[i]['driver_list'][j]['driver_id'] == member_info['_id']['$oid']) and (dl_json[i]['driver_list'][j]['driver_request_status'] == "0" or dl_json[i]['driver_list'][j]['driver_request_status'] == "1" or dl_json[i]['driver_list'][j]['driver_request_status'] == "4")):
									dl_in.append(dl_json[i]['_id']['$oid'])

						#ถ้า request_status = null ให้ดึงสถานะทั้งหมดมาแสดง
						if len(params['request_status']) == 0:
							request_driver = db.request_driver.find({
																		"driver_list_id": {"$in" : dl_in},
																	}).sort([("created_at", -1)]).skip(job_start_at).limit(job_length)
						#ถ้า request_status != null ให้ดึงเฉพาะสถานะที่เลือกมาแสดง
						else:
							#ถ้าเลือกสถานะ ตอบรับแล้ว
							if "1" in params['request_status']:
								#ถ้าไม่ได้เลือกสถานะ งานที่ใกล้จะถึง ให้ดึงข้อมูลงานสถานะ งานที่ใกล้จะถึง มาแสดงด้วย 
								if "4" not in params['request_status']:
									params['request_status'].append("4")

							request_driver = db.request_driver.find({
																		"driver_list_id": {"$in" : dl_in},
																		"request_status": {"$in" : params['request_status']}
																	}).sort([("updated_at", -1)]).skip(job_start_at).limit(job_length)
							
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

								if (request_driver_json[i]['request_status'] == "3" or request_driver_json[i]['request_status'] == "4" or request_driver_json[i]['request_status'] == "5" or request_driver_json[i]['request_status'] == "6") and member_info['_id']['$oid'] == request_driver_json[i]['driver_id']:
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
										"request_status_text": request_status_text,
										"job_status": request_driver_json[i]['job_status'],
										"check_status": request_driver_json[i]['check_status']
									})
								elif (request_driver_json[i]['request_status'] == "0" or request_driver_json[i]['request_status'] == "1" or request_driver_json[i]['request_status'] == "2"):
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
										"request_status_text": request_status_text,
										"job_status": request_driver_json[i]['job_status'],
										"check_status": request_driver_json[i]['check_status']
									})

						result = {
									"status" : True,
									"msg" : get_api_message("job_list" , "get_job_list_success" , member_lang),
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
	user_type = "driver"
	function_name = "job_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def job_detail(request):
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
															"_id": ObjectId(params['request_id'])
														})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("job_detail" , "data_not_found" , member_lang),
							"msg_code" : "0"
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				mem_info = get_member_info_by_id(request_driver_json['member_id'])
				member_fullname = mem_info['member_firstname_en']+" "+mem_info['member_lastname_en']

				passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])
				passenger_fullname = passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en']

				driver_request_status = None
				driver_request_status_text = None

				if request_driver_json['driver_list_id'] is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("job_detail" , "do_not_have_permission_to_access_the_data" , member_lang),
								"msg_code" : "1"
							}
				else:
					dl = db.driver_list.find_one({
													"_id": ObjectId(request_driver_json['driver_list_id']),
													"driver_list_status": "1",
													"driver_list.driver_id": member_id
												})
					if dl is None:
						result = { 
									"status" : False,
									"msg" : get_api_message("job_detail" , "do_not_have_permission_to_access_the_data" , member_lang),
									"msg_code" : "1"
								}
					else:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						dl_in = []
						
						for j in range(len(dl_json['driver_list'])):
							if dl_json['driver_list'][j]['driver_id'] == member_info['_id']['$oid']:
								driver_request_status = dl_json['driver_list'][j]['driver_request_status']

								if driver_request_status == "4":
									if member_lang == "en":
										driver_request_status_text = "Reject job"
									else:
										driver_request_status_text = "ปฏิเสธงาน"
								elif driver_request_status == "3":
									if member_lang == "en":
										driver_request_status_text = "Canceled by driver"
									else:
										driver_request_status_text = "ยกเลิกโดยคนขับ"
								elif driver_request_status == "2":
									if member_lang == "en":
										driver_request_status_text = "Canceled by customer"
									else:
										driver_request_status_text = "ยกเลิกโดยลูกค้า"
								elif driver_request_status == "1":
									if member_lang == "en":
										driver_request_status_text = "Accepted"
									else:
										driver_request_status_text = "ตอบรับแล้ว"
								else:
									if member_lang == "en":
										driver_request_status_text = "Waiting for reply"
									else:
										driver_request_status_text = "รอตอบรับ"


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

						customer_detail = None
						if request_driver_json['member_id'] is not None:
							customer_info = get_member_info_by_id(request_driver_json['member_id'])
							customer_detail = {
												"customer_id": customer_info['_id']['$oid'],
												"customer_code": customer_info['member_code'],
												"customer_fullname": customer_info['member_firstname_en']+" "+customer_info['member_lastname_en'],
												"customer_tel": customer_info['member_tel'],
												"customer_image": customer_info['profile_image']
											}

						package_info = get_package_info(request_driver_json['main_package_id'])
						normal_received_rate = int(package_info['normal_received_rate'])
						overtime_received_rate = int(package_info['overtime_received_rate'])
						all_received = 0

						package_detail_list = []

						for i in range(len(request_driver_json['main_package'])):
							main_package_info = get_package_info(request_driver_json['main_package'][i]['package_id'])
							
							if member_lang == "en":
								package_name = main_package_info['package_name_en']

								if request_driver_json['main_package'][i]['package_type'] == "hour":
									usage_text = "use "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" hour"
								else:
									usage_text = "use "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" time"
							else:
								package_name = main_package_info['package_name_th']

								if request_driver_json['main_package'][i]['package_type'] == "hour":
									usage_text = "ใช้ "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" ชั่วโมง"
								else:
									usage_text = "ใช้ "+str(int(request_driver_json['main_package'][i]['usage_amount']))+" ครั้ง"

							package_detail_list.append({
								"package_name": package_name,
								"usage_text": usage_text
							})

							normal_received = request_driver_json['main_package'][i]['normal_usage'] * normal_received_rate
							overtime_received = request_driver_json['main_package'][i]['overtime_usage'] * overtime_received_rate

							all_received = all_received + (normal_received + overtime_received)

						for i in range(len(request_driver_json['second_package'])):
							second_package_info = get_package_info(request_driver_json['second_package'][i]['package_id'])
							
							if member_lang == "en":
								package_name = second_package_info['package_name_en']

								if request_driver_json['second_package'][i]['package_type'] == "hour":
									usage_text = "use "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" hour"
								else:
									usage_text = "use "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" time"
							else:
								package_name = second_package_info['package_name_th']

								if request_driver_json['second_package'][i]['package_type'] == "hour":
									usage_text = "ใช้ "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" ชั่วโมง"
								else:
									usage_text = "ใช้ "+str(int(request_driver_json['second_package'][i]['usage_amount']))+" ครั้ง"

							package_detail_list.append({
								"package_name": package_name,
								"usage_text": usage_text
							})
						
							normal_received = request_driver_json['second_package'][i]['normal_usage'] * normal_received_rate
							overtime_received = request_driver_json['second_package'][i]['overtime_usage'] * overtime_received_rate

							all_received = all_received + (normal_received + overtime_received)
						
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


						if request_driver_json['job_status'] == "9":
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

								billing_package_info = get_package_info(billing_json['package_id'])
							
								if member_lang == "en":
									package_name = billing_package_info['package_name_en']
									usage_text = "use "+str(int(billing_json['usage_hour_amount']))+" hour"
								else:
									package_name = billing_package_info['package_name_th']
									usage_text = "ใช้ "+str(int(billing_json['usage_hour_amount']))+" ชั่วโมง"

								billing_detail_list.append({
									"package_name": package_name,
									"usage_text": usage_text,
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

						data = {
									"request_id" : request_driver_json['_id']['$oid'],
									"request_no": request_driver_json['request_no'],
									"company_id": request_driver_json['company_id'],
									"driver_id": request_driver_json['driver_id'],
									"member_id": request_driver_json['member_id'],
									"passenger_id": request_driver_json['passenger_id'],
									"member_fullname": member_fullname,
									"passenger_fullname": passenger_fullname,
									"request_to": request_driver_json['request_to'],
									"overtime_received_rate": overtime_received_rate,
									"all_received": all_received,
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
									"driver_age_range": driver_age_range_list,
									"driver_age_range_text": driver_age_range_text,
									"communication": communication_list,
									"special_skill": special_skill_list,
									"special_skill_text": special_skill_text,
									"package_detail": package_detail_list,
									"billing_detail": billing_detail_list,
									"customer_detail": customer_detail,
									"driver_request_status": driver_request_status,
									"driver_request_status_text": driver_request_status_text,
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

									"accept_start_date": accept_start_date,
									"accept_start_time": accept_start_time,
									"end_job_date": end_job_date,
									"end_job_time": end_job_time
								}

						result = {
									"status" : True,
									"msg" : get_api_message("job_detail" , "get_job_detail_success" , member_lang),
									"data" : data
								}
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized"),
						"msg_code" : "0"
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters"),
					"msg_code" : "0"
				}
	
	#set log detail
	# user_type = "driver"
	# function_name = "job_detail"
	# request_headers = request.headers
	# params_get = None
	# params_post = params
	# set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def accept_job(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("accept_job" , "job_not_found" , member_lang),
							"msg_code" : "0"
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				#เช็คเวลารับงานว่าเกิน 45 นาทีหลังจาก request หรือไม่
				create_datetime_obj = datetime.strptime(request_driver_json['created_at'], '%Y-%m-%d %H:%M:%S')
				end_accept_datetime_obj = datetime.strptime(request_driver_json['end_accept_at'], '%Y-%m-%d %H:%M:%S')
				current_datetime_obj = datetime.now()

				if ((current_datetime_obj.strftime('%Y-%m-%d') == create_datetime_obj.strftime('%Y-%m-%d')) and (current_datetime_obj <= end_accept_datetime_obj)):
					if request_driver_json['driver_list_id'] is None:
						result = {
								"status" : False,
								"msg" : get_api_message("accept_job" , "driver_list_not_found" , member_lang),
								"msg_code" : "1"
							}
					else:
						dl = db.driver_list.find_one({
														"_id": ObjectId(request_driver_json['driver_list_id'])
													})

						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						driver_list = []
						for i in range(len(dl_json['driver_list'])):
							#แก้ไข driver_request_status เฉพาะคนที่มี driver_id ตรงกับ driver_id ที่ส่งเข้ามาเท่านั้น
							if dl_json['driver_list'][i]['driver_id'] == member_info['_id']['$oid']:
								driver_request_status = "1" #รับงาน
							else:
								driver_request_status = "4" #ปฏิเสธงาน

							driver_list.append({
								"driver_id" : dl_json['driver_list'][i]['driver_id'],
								"driver_request_status": driver_request_status
							})

						if request_driver_json['request_status'] == "0":
							#2020-07-10 01:00:00
							start_datetime_obj = datetime.strptime(request_driver_json['start_date']+" "+request_driver_json['start_time'], '%Y-%m-%d %H:%M:%S')
							#2020-07-10 13:00:00
							end_datetime_obj = datetime.strptime(request_driver_json['end_date']+" "+request_driver_json['end_time'], '%Y-%m-%d %H:%M:%S')

							#2020-07-09 17:00:00
							before_start_datetime_obj = start_datetime_obj - timedelta(hours=8)
							#2020-07-10 21:00:00
							after_end_datetime_obj = end_datetime_obj + timedelta(hours=8)

							start_date = start_datetime_obj.strftime('%Y-%m-%d')
							end_date = end_datetime_obj.strftime('%Y-%m-%d')

							before_start_date = before_start_datetime_obj.strftime('%Y-%m-%d')
							before_start_time = before_start_datetime_obj.strftime('%H:%M:%S')
							after_end_date = after_end_datetime_obj.strftime('%Y-%m-%d')
							after_end_time = after_end_datetime_obj.strftime('%H:%M:%S')

							#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก ก่อนรับงานนี้ 8 ชม.
							check_before = db.request_driver.find_one({
																		"_id": {"$ne": ObjectId(params['request_id'])},
																		"driver_id": member_info['_id']['$oid'],
																		"end_date": before_start_date,
																		"end_time": {"$gte" : before_start_time},
																		"request_status": {"$nin" : ["2","3"]}
																	})

							#เช็คเวลาที่เคยรับงานว่าต้องห่างจาก หลังจบงานนี้ 8 ชม.
							check_after = db.request_driver.find_one({
																		"_id": {"$ne": ObjectId(params['request_id'])},
																		"driver_id": member_info['_id']['$oid'],
																		"start_date": after_end_date,
																		"start_time": {"$lte" : after_end_time},
																		"request_status": {"$nin" : ["2","3"]}
																	})

							#ถ้าไม่เจองาน ก่อนรับงานนี้ 8 ชม. และ หลังจบงานนี้ 8 ชม. จึงจะสามารถรับงานนี้ได้
							if check_before is None and check_after is None:
								driver_info = get_member_info_by_id(member_info['_id']['$oid'])
								driver_name_en = driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
								driver_name_th = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
								driver_code = driver_info['member_code']

								# update request_driver
								where_param = { "_id": ObjectId(params['request_id']) }
								value_param = {
												"$set":
													{
														"driver_id": member_info['_id']['$oid'],
														"driver_name_en": driver_name_en,
														"driver_name_th": driver_name_th,
														"driver_code": driver_code,
														"request_status": "1",
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.request_driver.update(where_param , value_param):
									# update driver_list
									where_param = { "_id": ObjectId(request_driver_json['driver_list_id']) }
									value_param = {
													"$set":
														{
															"driver_list": driver_list,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}

									if db.driver_list.update(where_param , value_param):
										noti_type = "accept_job"
										request_no = request_driver_json['request_no']

										#sent noti to member
										customer_info = get_member_info_by_id(request_driver_json['member_id'])
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
													"msg" : get_api_message("accept_job" , "accept_job_success" , member_lang)
												}
									else:
										result = {
													"status" : False,
													"msg" : get_api_message("accept_job" , "driver_list_update_failed" , member_lang), 
													"msg_code" : "2"
												}
								else:
									result = {
												"status" : False,
												"msg" : get_api_message("accept_job" , "job_update_failed" , member_lang), 
												"msg_code" : "3"
											}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("accept_job" , "can_not_accept_job_because_you_have_job_during_this_time" , member_lang),
											"msg_code" : "4"
										}
						else:
							result = { 
										"status" : False,
										"msg" : get_api_message("accept_job" , "can_not_accept_job_because_someone_already_accepted_this_job" , member_lang),
										"msg_code" : "5"
									}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("accept_job" , "can_not_accept_job_because_you_accepted_the_job_more_than_the_specified_time" , member_lang),
								"msg_code" : "6"
							}	
		else:
			result = { 
						"status" : False,
						"error_code" : 401,
						"msg" : get_api_message("all" , "unauthorized"),
						"msg_code" : "7"
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters"),
					"msg_code" : "8"
				}

	#set log detail
	user_type = "driver"
	function_name = "accept_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def reject_job(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("reject_job" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				#เช็คเวลารับงานว่าเกิน 45 นาทีหลังจาก request หรือไม่
				create_datetime_obj = datetime.strptime(request_driver_json['created_at'], '%Y-%m-%d %H:%M:%S')
				after_create_datetime_obj = create_datetime_obj + timedelta(minutes=45)
				current_datetime_obj = datetime.now()

				if current_datetime_obj <= after_create_datetime_obj:
					if request_driver_json['driver_list_id'] is None:
						result = {
								"status" : False,
								"msg" : get_api_message("reject_job" , "driver_list_not_found" , member_lang)
							}
					else:
						dl = db.driver_list.find_one({
														"_id": ObjectId(request_driver_json['driver_list_id'])
													})

						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						driver_list = []
						for i in range(len(dl_json['driver_list'])):
							#แก้ไข driver_request_status เฉพาะคนที่มี driver_id ตรงกับ driver_id ที่ส่งเข้ามาเท่านั้น
							if dl_json['driver_list'][i]['driver_id'] == member_info['_id']['$oid']:
								driver_request_status = "4" #ปฏิเสธงาน
							else:
								driver_request_status = dl_json['driver_list'][i]['driver_request_status']

							driver_list.append({
								"driver_id" : dl_json['driver_list'][i]['driver_id'],
								"driver_request_status": driver_request_status
							})

						if request_driver_json['request_status'] == "0":
							check_request_info = check_request_status(params['request_id'])

							#จำนวนคนที่ปฏิเสธงาน เท่ากับ จำนวนคนขับที่ request ทั้งหมด
							if check_request_info['all_driver'] == (int(check_request_info['count_reject'])+1):
								driver_list_status = "0"
							else:
								driver_list_status = "1"

							# update driver_list
							where_param = { "_id": ObjectId(request_driver_json['driver_list_id']) }
							value_param = {
											"$set":
												{
													"driver_list": driver_list,
													"driver_list_status": driver_list_status,
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.driver_list.update(where_param , value_param):
								noti_type = "reject_job"
								request_no = request_driver_json['request_no']

								#sent noti to member
								customer_info = get_member_info_by_id(request_driver_json['member_id'])
								noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
								noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
								noti_message_en = "reject job : "+request_no
								noti_message_th = "ปฏิเสธงาน "+request_no

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

								check_request_info = check_request_status(params['request_id'])

								#จำนวนคนที่ปฏิเสธงาน เท่ากับ จำนวนคนขับที่ request ทั้งหมด
								if check_request_info['all_driver'] == check_request_info['count_reject']:
									# update request_driver
									where_param = { "_id": ObjectId(params['request_id']) }
									value_param = {
													"$set":
														{
															"driver_list_id": None,
															"request_status": "0",
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
									
									db.request_driver.update(where_param , value_param)

									noti_type = "reject_job_all"
									request_id = params['request_id']
									request_no = request_driver_json['request_no']

									noti_title_en = "All driver reject job : "+request_no
									noti_title_th = "คนขับทุกคนปฏิเสธงาน "+request_no
									noti_message_en = "please select driver again."
									noti_message_th = "กรุณาเลือกคนขับอีกครั้ง"

									#-----------------------------------------------------------------#

									#sent noti to member
									customer_info = get_member_info_by_id(request_driver_json['member_id'])
									
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
									send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": request_id , "created_datetime" : created_datetime }
									send_noti_badge = 1

									#insert member_notification
									noti_detail = {
														"request_id": request_id,
														"request_no": request_no
													}

									data = { 
												"member_id": customer_info['_id']['$oid'],
												"member_fullname": customer_info['member_firstname_en']+" "+customer_info['member_lastname_en'],
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

									#-----------------------------------------------------------------#

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
										send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": request_id , "created_datetime" : created_datetime }
										send_noti_badge = 1

										#insert member_notification
										noti_detail = {
															"request_id": request_id,
															"request_no": request_no
														}

										data = { 
													"member_id": passenger_info['_id']['$oid'],
													"member_fullname": passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en'],
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
											"msg" : get_api_message("reject_job" , "reject_job_success" , member_lang) 
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("reject_job" , "driver_list_update_failed" , member_lang)
										}
						else:
							result = { 
										"status" : False,
										"msg" : get_api_message("reject_job" , "can_not_reject_job_because_someone_already_accepted_this_job" , member_lang)
									}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("reject_job" , "can_not_reject_job_because_you_reject_the_job_more_than_the_specified_time" , member_lang) 
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
	user_type = "driver"
	function_name = "reject_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def cancel_job(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("cancel_job" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				start_datetime = request_driver_json['start_date']+" "+request_driver_json['start_time']

				#เช็คเวลาปัจจุบันว่ามากกว่าหรือเท่ากับ 48 ชั่วโมงก่อนเริ่มงาน หรือไม่
				start_datetime_obj = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
				before_48hr_datetime_obj = start_datetime_obj - timedelta(hours=48)
				current_datetime_obj = datetime.now()

				if current_datetime_obj <= before_48hr_datetime_obj:
					if request_driver_json['driver_list_id'] is None:
						result = {
								"status" : False,
								"msg" : get_api_message("cancel_job" , "driver_list_not_found" , member_lang)
							}
					else:
						dl = db.driver_list.find_one({
														"_id": ObjectId(request_driver_json['driver_list_id'])
													})

						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						dl_object = dumps(dl)
						dl_json = json.loads(dl_object)

						driver_list = []
						for i in range(len(dl_json['driver_list'])):
							#แก้ไข driver_request_status เฉพาะคนที่มี driver_id ตรงกับ driver_id ที่ส่งเข้ามาเท่านั้น
							if dl_json['driver_list'][i]['driver_id'] == member_info['_id']['$oid']:
								driver_request_status = "3" #รับงาน
							else:
								driver_request_status = "4" #ปฏิเสธงาน

							driver_list.append({
								"driver_id" : dl_json['driver_list'][i]['driver_id'],
								"driver_request_status": driver_request_status
							})

						if request_driver_json['request_status'] == "1" or request_driver_json['request_status'] == "4":
							# update request_driver
							where_param = { "_id": ObjectId(params['request_id']) }
							value_param = {
											"$set":
												{
													"request_status": "3",
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.request_driver.update(where_param , value_param):
								# update driver_list
								where_param = { "_id": ObjectId(request_driver_json['driver_list_id']) }
								value_param = {
												"$set":
													{
														"driver_list": driver_list,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.driver_list.update(where_param , value_param):
									noti_type = "cancel_job"
									request_no = request_driver_json['request_no']

									#sent noti to member
									customer_info = get_member_info_by_id(request_driver_json['member_id'])
									noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
									noti_message_en = "cancel job : "+request_no+" please select driver again."
									noti_message_th = "ยกเลิกงาน "+request_no+" กรุณาเลือกคนขับอีกครั้ง"

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
												"msg" : get_api_message("cancel_job" , "cancel_job_success" , member_lang) 
											}
								else:
									result = {
												"status" : False,
												"msg" : get_api_message("cancel_job" , "driver_list_update_failed" , member_lang) 
											}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("cancel_job" , "job_update_failed" , member_lang) 
										}
							
						else:
							result = { 
										"status" : False,
										"msg" : get_api_message("cancel_job" , "can_not_cancel_job_because_job_status_is_invalid" , member_lang) 
									}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("cancel_job" , "can_not_cancel_job_because_you_cancel_the_job_more_than_the_specified_time" , member_lang) 
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
	user_type = "driver"
	function_name = "cancel_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def coming_soon_job_form(request):
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

			coming_soon_remark = db.coming_soon_remark.find()
			
			if coming_soon_remark is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("coming_soon_job_form" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				coming_soon_remark_object = dumps(coming_soon_remark)
				coming_soon_remark_json = json.loads(coming_soon_remark_object)

				coming_soon_remark_list = []

				for i in range(len(coming_soon_remark_json)):
					if member_lang == "en":
						remark = coming_soon_remark_json[i]['remark_en']
					else:
						remark = coming_soon_remark_json[i]['remark_th']

					coming_soon_remark_list.append({
						"id" : coming_soon_remark_json[i]['_id']['$oid'],
						"name": remark
					})

				if member_lang == "en":
					time_0 = "Arrived"
					time_15 = "15 minutes"
					time_30 = "30 minutes"
					time_45 = "45 minutes"
				else:
					time_0 = "ถึงแล้ว"
					time_15 = "15 นาที"
					time_30 = "30 นาที"
					time_45 = "45 นาที"

				coming_soon_time_list = [
											{"code": 0,"name": time_0},
											{"code": 15,"name": time_15},
											{"code": 30,"name": time_30},
											{"code": 45,"name": time_45}
										]

				result = {
							"status" : True,
							"msg" : get_api_message("coming_soon_job_form" , "get_coming_soon_job_form_success" , member_lang),
							"coming_soon_time": coming_soon_time_list,
							"coming_soon_remark": coming_soon_remark_list
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
	user_type = "driver"
	function_name = "coming_soon_job_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def coming_soon_job(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_coming_soon_time_code = "coming_soon_time_code" in params
	isset_coming_soon_remark_id = "coming_soon_remark_id" in params
	isset_other_remark = "other_remark" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_coming_soon_time_code and isset_coming_soon_remark_id and isset_other_remark:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("coming_soon_job" , "job_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['driver_list_id'] is None:
					result = {
								"status" : False,
								"msg" : get_api_message("coming_soon_job" , "driver_list_not_found" , member_lang)
							}
				else:
					if request_driver_json['request_status'] == "4" and (request_driver_json['job_status'] == "2" or request_driver_json['job_status'] == "3" or request_driver_json['job_status'] == "4"):
						# update request_driver
						where_param = { "_id": ObjectId(params['request_id']) }
						value_param = {
										"$set":
											{
												"job_status": "3",
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						if db.request_driver.update(where_param , value_param):
							noti_type = "coming_soon_job"
							request_no = request_driver_json['request_no']
							coming_soon_time_code = str(params['coming_soon_time_code'])

							#sent noti to member
							customer_info = get_member_info_by_id(request_driver_json['member_id'])
							noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']+" for job "+request_no
							noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']+" งาน "+request_no
							
							if params['other_remark'] is None or params['other_remark'] == "":
								if params['coming_soon_remark_id'] is not None:
									coming_soon_remark = db.coming_soon_remark.find_one({"_id": ObjectId(params['coming_soon_remark_id'])})
		
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									coming_soon_remark_object = dumps(coming_soon_remark)
									coming_soon_remark_json = json.loads(coming_soon_remark_object)
									
									noti_message_en = "will arrive within "+coming_soon_time_code+" minutes because "+coming_soon_remark_json['remark_en'].lower()+"."
									noti_message_th = "กำลังจะถึงภายในเวลา "+coming_soon_time_code+" นาที เนื่องจาก"+coming_soon_remark_json['remark_th']
							else:
								noti_message_en = "will arrive within "+coming_soon_time_code+" minutes because "+params['other_remark'].lower()+"."
								noti_message_th = "กำลังจะถึงภายในเวลา "+coming_soon_time_code+" นาที เนื่องจาก"+params['other_remark']


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
										"msg" : get_api_message("coming_soon_job" , "confirm_coming_soon_job_success" , member_lang)
									}
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("coming_soon_job" , "job_update_failed" , member_lang) 
									}	
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("coming_soon_job" , "can_not_confirm_coming_soon_job_because_job_status_is_invalid" , member_lang)
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
	user_type = "driver"
	function_name = "coming_soon_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def confirm_start_job(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("confirm_start_job" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['request_status'] == "4" and (request_driver_json['job_status'] == "2" or request_driver_json['job_status'] == "3" or request_driver_json['job_status'] == "4"):
					# update request_driver
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"job_status": "5",
											"confirm_start_job_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.request_driver.update(where_param , value_param):
						noti_type = "confirm_start_job"
						request_no = request_driver_json['request_no']

						#sent noti to member
						customer_info = get_member_info_by_id(request_driver_json['member_id'])
						noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
						noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						noti_message_en = "confirm to start job :  "+request_no
						noti_message_th = "ยืนยันการเริ่มงาน "+request_no

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
									"msg" : get_api_message("confirm_start_job" , "confirm_start_job_success" , member_lang) 
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("confirm_start_job" , "job_update_failed" , member_lang) 
								}	
				else:
					if request_driver_json['job_status'] == "5":
						result = { 
									"status" : False,
									"msg" : get_api_message("confirm_start_job" , "can_not_confirm_start_job_because_you_have_already_confirmed" , member_lang)
								}
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("confirm_start_job" , "can_not_confirm_start_job_because_job_status_is_invalid" , member_lang)
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
	user_type = "driver"
	function_name = "confirm_start_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_inspection_form(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_car_inspection_form" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)
				car_id = request_driver_json['car_id']


				car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})

				start_mileage = 0

				if car_inspection is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_inspection_object = dumps(car_inspection)
					car_inspection_json = json.loads(car_inspection_object)
					start_mileage = car_inspection_json['start_mileage']
				
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

				if member_lang == "en":
					car_type_name = car_type_json['car_type_name_en']
					car_gear_name = car_gear_json['car_gear_en']
					car_engine_name = car_engine_json['car_engine_en']

				else:
					car_type_name = car_type_json['car_type_name_th']
					car_gear_name = car_gear_json['car_gear_th']
					car_engine_name = car_engine_json['car_engine_th']
				
				outside_inspection = db.outside_inspection.find({"car_type_code": car_type_code})
				inspection_before_use = db.inspection_before_use.find({"check_status": "1"})

				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				outside_inspection_object = dumps(outside_inspection)
				outside_inspection_json = json.loads(outside_inspection_object)

				inspection_before_use_object = dumps(inspection_before_use)
				inspection_before_use_json = json.loads(inspection_before_use_object)

				outside_inspection_list = []
				inspection_before_use_list = []

				for i in range(len(outside_inspection_json)):
					if member_lang == "en":
						point_name = outside_inspection_json[i]['point_name_en']
					else:
						point_name = outside_inspection_json[i]['point_name_th']

					part_list = []

					for j in range(len(outside_inspection_json[i]['part'])):
						if member_lang == "en":
							part_name = outside_inspection_json[i]['part'][j]['part_name_en']
						else:
							part_name = outside_inspection_json[i]['part'][j]['part_name_th']

						part_list.append({
							"part_code": outside_inspection_json[i]['part'][j]['part_code'],
							"part_name": part_name,
							"check_result": "1",
							"check_remark": None,
							"check_image": []
						})

					outside_inspection_list.append({
						"outside_inspection_id" : outside_inspection_json[i]['_id']['$oid'],
						"car_type_id": outside_inspection_json[i]['car_type_id'],
						"car_type_code": outside_inspection_json[i]['car_type_code'],
						"point_name": point_name,
						"part": part_list,
						"point_number": outside_inspection_json[i]['point_number']
					})

				for i in range(len(inspection_before_use_json)):
					if member_lang == "en":
						check_name = inspection_before_use_json[i]['check_name_en']
					else:
						check_name = inspection_before_use_json[i]['check_name_th']
				
					inspection_before_use_list.append({
						"inspection_before_use_id" : inspection_before_use_json[i]['_id']['$oid'],
						"check_name": check_name,
						"check_result": "1",
						"check_remark": None
					})

				result = {
							"status" : True,
							"msg" : get_api_message("get_car_inspection_form" , "get_car_inspection_form_success" , member_lang),
							"request_id": params['request_id'],
							"car_id": car_id,
							"car_brand_name": car_brand_name,
							"license_plate": license_plate,
							"car_type_code": car_type_code,
							"car_type_name": car_type_name,
							"car_gear_name": car_gear_name,
							"car_engine_name": car_engine_name,
							"start_mileage": start_mileage,
							"end_mileage": None,
							"outside_inspection": outside_inspection_list,
							"inspection_before_use": inspection_before_use_list
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
	user_type = "driver"
	function_name = "get_car_inspection_form"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def confirm_car_inspection(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_outside_inspection = "outside_inspection" in params
	isset_inspection_before_use = "inspection_before_use" in params
	isset_inspection_before_use_comment = "inspection_before_use_comment" in params
	isset_inspection_before_use_image = "inspection_before_use_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_outside_inspection and isset_inspection_before_use and isset_inspection_before_use_comment and isset_inspection_before_use_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("confirm_car_inspection" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				outside_inspection_list = []
				inspection_before_use_list = []
				inspection_before_use_image_list = []

				if len(params['outside_inspection']) > 0:
					for i in range(len(params['outside_inspection'])):
						outside_inspection = db.outside_inspection.find_one({"_id": ObjectId(params['outside_inspection'][i]['outside_inspection_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						outside_inspection_object = dumps(outside_inspection)
						outside_inspection_json = json.loads(outside_inspection_object)	

						point_name_en = outside_inspection_json['point_name_en']
						point_name_th = outside_inspection_json['point_name_th']

						part_list = []

						for j in range(len(params['outside_inspection'][i]['part'])):
							for k in range(len(outside_inspection_json['part'])):
								if params['outside_inspection'][i]['part'][j]['part_code'] == outside_inspection_json['part'][k]['part_code']:
									check_image_list = []

									if len(params['outside_inspection'][i]['part'][j]['check_image']) <= 0:
										image_name = None
									else:
										for l in range(len(params['outside_inspection'][i]['part'][j]['check_image'])):
											#generate token
											generate_token = get_random_token(40)
											check_upload_image = upload_outside_inspection_image(params['outside_inspection'][i]['part'][j]['check_image'][l], generate_token)

											if check_upload_image is None:
												image_name = None
											else:
												image_name = check_upload_image

											check_image_list.append(image_name)

									part_list.append({
										"part_code": params['outside_inspection'][i]['part'][j]['part_code'],
										"part_name_en": outside_inspection_json['part'][k]['part_name_en'],
										"part_name_th": outside_inspection_json['part'][k]['part_name_th'],
										"check_result": params['outside_inspection'][i]['part'][j]['check_result'],
										"check_remark": params['outside_inspection'][i]['part'][j]['check_remark'],
										"check_image": check_image_list
									})

						outside_inspection_list.append({
							"outside_inspection_id" : params['outside_inspection'][i]['outside_inspection_id'],
							"part" : part_list,
							"point_name_en" : point_name_en,
							"point_name_th" : point_name_th,
							"point_number" : params['outside_inspection'][i]['point_number']
						})

				if len(params['inspection_before_use']) > 0:
					for i in range(len(params['inspection_before_use'])):
						inspection_before_use = db.inspection_before_use.find_one({"_id": ObjectId(params['inspection_before_use'][i]['inspection_before_use_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						inspection_before_use_object = dumps(inspection_before_use)
						inspection_before_use_json = json.loads(inspection_before_use_object)	

						check_name_en = inspection_before_use_json['check_name_en']
						check_name_th = inspection_before_use_json['check_name_th']

						inspection_before_use_list.append({
							"inspection_before_use_id" : params['inspection_before_use'][i]['inspection_before_use_id'],
							"check_name_en" : check_name_en,
							"check_name_th" : check_name_th,
							"check_result" : params['inspection_before_use'][i]['check_result'],
							"check_remark" : params['inspection_before_use'][i]['check_remark']
						})

				if len(params['inspection_before_use_image']) <= 0:
					image_name = None
				else:
					for i in range(len(params['inspection_before_use_image'])):
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_inspection_before_use_image(params['inspection_before_use_image'][i], generate_token)

						if check_upload_image is None:
							image_name = None
						else:
							image_name = check_upload_image

						inspection_before_use_image_list.append(image_name)

				# update car_inspection
				where_param = { "request_id": params['request_id'] }
				value_param = {
								"$set":
									{
										"outside_inspection": outside_inspection_list,
										"inspection_before_use": inspection_before_use_list,
										"inspection_before_use_comment": params['inspection_before_use_comment'],
										"inspection_before_use_image": inspection_before_use_image_list,
										"check_status": "2",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.car_inspection.update(where_param , value_param):
					# update request_driver
					where_param = { "_id": ObjectId(params['request_id']) }
					value_param = {
									"$set":
										{
											"check_status": "2",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.request_driver.update(where_param , value_param):
						noti_type = "confirm_car_inspection"
						request_no = request_driver_json['request_no']

						#sent noti to member
						customer_info = get_member_info_by_id(request_driver_json['member_id'])
						noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
						noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
						noti_message_en = "confirm to vehicle inspections : "+request_no
						noti_message_th = "ยืนยันการตรวจสภาพรถงาน "+request_no

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
						send_noti_message = noti_message_th
						send_noti_data = { "action" : noti_type , "noti_message" : noti_message , "request_id": params['request_id'] , "created_datetime" : created_datetime }
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
							send_noti_message = noti_message_th
							send_noti_data = { "action" : noti_type , "noti_message" : noti_message , "request_id": params['request_id'] , "created_datetime" : created_datetime }
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
									"msg" : get_api_message("confirm_car_inspection" , "confirm_car_inspection_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("confirm_car_inspection" , "job_update_failed" , member_lang)
								}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("confirm_car_inspection" , "car_inspection_update_failed" , member_lang)
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
	user_type = "driver"
	function_name = "confirm_car_inspection"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_start_mileage(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_check_status = "check_status" in params
	isset_start_mileage = "start_mileage" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_check_status and isset_start_mileage:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			request_driver_object = dumps(request_driver)
			request_driver_json = json.loads(request_driver_object)

			# update car_inspection
			where_param = { "request_id": params['request_id'] }
			value_param = {
							"$set":
								{
									"start_mileage": int(params['start_mileage']),
									"start_mileage_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"check_status": params['check_status'],
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.car_inspection.update(where_param , value_param):
				# update request_driver
				where_param = { "_id": ObjectId(params['request_id']) }
				value_param = {
								"$set":
									{
										"check_status": params['check_status'],
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				db.request_driver.update(where_param , value_param)

				result = {
							"status" : True,
							"msg" : get_api_message("add_start_mileage" , "add_start_mileage_success" , member_lang)
						}
			else:
				result = {
						"status" : False,
						"msg" : get_api_message("add_start_mileage" , "data_update_failed" , member_lang) 
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
	user_type = "driver"
	function_name = "add_start_mileage"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_inspection_detail(request):
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

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_car_inspection_detail" , "job_not_found" , member_lang) 
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

				if member_lang == "en":
					car_type_name = car_type_json['car_type_name_en']
					car_gear_name = car_gear_json['car_gear_en']
					car_engine_name = car_engine_json['car_engine_en']

				else:
					car_type_name = car_type_json['car_type_name_th']
					car_gear_name = car_gear_json['car_gear_th']
					car_engine_name = car_engine_json['car_engine_th']
				
				# outside_inspection = db.outside_inspection.find({"car_type_code": car_type_code})
				# inspection_before_use = db.inspection_before_use.find({"check_status": "1"})

				car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})

				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_inspection_object = dumps(car_inspection)
				car_inspection_json = json.loads(car_inspection_object)

				outside_inspection_json = car_inspection_json['outside_inspection']
				inspection_before_use_json = car_inspection_json['inspection_before_use']

				outside_inspection_list = []
				inspection_before_use_list = []

				for i in range(len(outside_inspection_json)):
					if member_lang == "en":
						point_name = outside_inspection_json[i]['point_name_en']
					else:
						point_name = outside_inspection_json[i]['point_name_th']

					part_list = []

					for j in range(len(outside_inspection_json[i]['part'])):
						if member_lang == "en":
							part_name = outside_inspection_json[i]['part'][j]['part_name_en']
						else:
							part_name = outside_inspection_json[i]['part'][j]['part_name_th']

						part_list.append({
							"part_code": outside_inspection_json[i]['part'][j]['part_code'],
							"part_name": part_name,
							"check_result": outside_inspection_json[i]['part'][j]['check_result'],
							"check_remark": outside_inspection_json[i]['part'][j]['check_remark'],
							"check_image": outside_inspection_json[i]['part'][j]['check_image'],
						})

					outside_inspection_list.append({
						"outside_inspection_id" : outside_inspection_json[i]['outside_inspection_id'],
						"car_type_id": car_json['car_type_id'],
						"car_type_code": car_type_code,
						"point_name": point_name,
						"part": part_list,
						"point_number": outside_inspection_json[i]['point_number']
					})

				for i in range(len(inspection_before_use_json)):
					if member_lang == "en":
						check_name = inspection_before_use_json[i]['check_name_en']
					else:
						check_name = inspection_before_use_json[i]['check_name_th']
				
					inspection_before_use_list.append({
						"inspection_before_use_id" : inspection_before_use_json[i]['inspection_before_use_id'],
						"check_name": check_name,
						"check_result": inspection_before_use_json[i]['check_result'],
						"check_remark": inspection_before_use_json[i]['check_remark']
					})

				result = {
							"status" : True,
							"msg" : get_api_message("get_car_inspection_detail" , "get_car_inspection_detail_success" , member_lang),
							"request_id": params['request_id'],
							"car_id": car_id,
							"car_brand_name": car_brand_name,
							"license_plate": license_plate,
							"car_type_code": car_type_code,
							"car_type_name": car_type_name,
							"car_gear_name": car_gear_name,
							"car_engine_name": car_engine_name,
							"start_mileage": car_inspection_json['start_mileage'],
							"end_mileage": car_inspection_json['end_mileage'],
							"outside_inspection": outside_inspection_list,
							"inspection_before_use": inspection_before_use_list,
							"inspection_before_use_comment": car_inspection_json['inspection_before_use_comment'],
							"inspection_before_use_image": car_inspection_json['inspection_before_use_image'],
							"check_status": car_inspection_json['check_status']
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
	user_type = "driver"
	function_name = "get_car_inspection_detail"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def driver_noti_list(request):
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
							"msg" : get_api_message("driver_noti_list" , "notification_start_at_is_not_a_number" , member_lang) 
						}
			elif not check_noti_length:
				result = { 
							"status" : False,
							"msg" : get_api_message("driver_noti_list" , "notification_length_is_not_a_number" , member_lang) 
						}
			else:
				if member_info['member_type'] == "driver":
					notification = db.member_notification.find({
																	"member_id" : member_info['_id']['$oid'],
																	"noti_status" : {"$in" : ["0","1"]}
																}).sort([("created_at", -1)]).skip(noti_start_at).limit(noti_length)
				
					if notification is None:
						result = { 
									"status" : False,
									"msg" : get_api_message("driver_noti_list" , "data_not_found" , member_lang) 
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

							#แปลง format วันที่
							created_datetime = datetime.strptime(notification_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

							noti_list.append({
								"noti_id" : notification_json[i]['_id']['$oid'],
								"member_id" : notification_json[i]['member_id'],
								"noti_message": noti_message,
								"noti_type": notification_json[i]['noti_type'],
								"noti_detail": notification_json[i]['noti_detail'],
								"noti_status": notification_json[i]['noti_status'],
								"created_datetime": created_datetime
							})

						result = {
									"status" : True,
									"msg" : get_api_message("driver_noti_list" , "get_driver_notification_list_success" , member_lang), 
									"noti_list" : noti_list,
									"badge" : count_badge
								}
				else:
					result = { 
						"status" : False,
						"msg" : get_api_message("driver_noti_list" , "member_type_is_invalid" , member_lang) 
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
	user_type = "driver"
	function_name = "driver_noti_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def end_job(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_end_mileage = "end_mileage" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_end_mileage:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({"_id": ObjectId(params['request_id'])})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("end_job" , "job_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				#กำลังเดินทาง
				if request_driver_json['request_status'] == "5":
					#ลูกค้าตอบรับการเริ่มงาน หรือ 15 นาทีก่อนถึงเวลาจบงาน
					if request_driver_json['job_status'] == "6" or request_driver_json['job_status'] == "7":
						#ตรวจสภาพรถผ่าน
						if request_driver_json['check_status'] == "4":
							#อัพเดต requset_status เป็น 6

							delay_end_time_obj = datetime.strptime(request_driver_json['delay_end_date']+" "+request_driver_json['delay_end_time'], '%Y-%m-%d %H:%M:%S')
							end_time_obj = datetime.strptime(request_driver_json['end_date']+" "+request_driver_json['end_time'], '%Y-%m-%d %H:%M:%S')
							end_time_30_obj = end_time_obj + timedelta(minutes=30)

							
							main_package_info = request_driver_json['main_package'][0]

							#จบงานเกินเวลาจอง
							if delay_end_time_obj > end_time_30_obj:
								#ถ้าเวลาจบงานล่าสุด มากกว่า เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 9
								job_status = "9"
							#จบงานตามเวลาจอง
							else:
								#ถ้าเวลาจบงานล่าสุด น้อยกว่าหรือเท่ากับ เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 8
								job_status = "8"

							#คำนวณรายรับทั้งหมดของคนขับ
							main_package_normal_received = 0
							main_package_overtime_received = 0
							main_package_received = 0

							second_package_normal_received = 0
							second_package_overtime_received = 0
							second_package_received = 0

							overtime_package_normal_received = 0
							overtime_package_overtime_received = 0
							overtime_package_received = 0

							billing_normal_received = 0
							billing_overtime_received = 0
							billing_received = 0
							
							payment_amount = 0
							normal_payment_amount = 0
							overtime_payment_amount = 0
							total_normal_usage = 0
							total_overtime_usage = 0

							for i in range(len(request_driver_json['main_package'])):
								main_package_normal_received = main_package_normal_received + (request_driver_json['main_package'][i]['normal_usage'] * main_package_info['normal_received_rate'])
								main_package_overtime_received = main_package_overtime_received + (request_driver_json['main_package'][i]['overtime_usage'] * main_package_info['overtime_received_rate'])

								total_normal_usage = total_normal_usage + request_driver_json['main_package'][i]['normal_usage']
								total_overtime_usage = total_overtime_usage + request_driver_json['main_package'][i]['overtime_usage']

							main_package_received = main_package_normal_received + main_package_overtime_received

							if len(request_driver_json['second_package']) > 0:
								for j in range(len(request_driver_json['second_package'])):
									second_package_normal_received = second_package_normal_received + (request_driver_json['second_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
									second_package_overtime_received = second_package_overtime_received + (request_driver_json['second_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

									total_normal_usage = total_normal_usage + request_driver_json['second_package'][j]['normal_usage']
									total_overtime_usage = total_overtime_usage + request_driver_json['second_package'][j]['overtime_usage']

								second_package_received = second_package_normal_received + second_package_overtime_received

							if len(request_driver_json['overtime_package']) > 0:
								for j in range(len(request_driver_json['overtime_package'])):
									overtime_package_normal_received = overtime_package_normal_received + (request_driver_json['overtime_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
									overtime_package_overtime_received = overtime_package_overtime_received + (request_driver_json['overtime_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

									total_normal_usage = total_normal_usage + request_driver_json['overtime_package'][j]['normal_usage']
									total_overtime_usage = total_overtime_usage + request_driver_json['overtime_package'][j]['overtime_usage']

								overtime_package_received = overtime_package_normal_received + overtime_package_overtime_received

							if len(request_driver_json['billing_id']) > 0:
								for k in range(len(request_driver_json['billing_id'])):
									billing = db.billing.find_one({"_id": ObjectId(request_driver_json['billing_id'][k])})
									#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
									billing_object = dumps(billing)
									billing_json = json.loads(billing_object)

									billing_normal_received = billing_normal_received + (billing_json['normal_usage'] * main_package_info['normal_received_rate'])
									billing_overtime_received = billing_overtime_received + (billing_json['overtime_usage'] * main_package_info['overtime_received_rate'])

									total_normal_usage = total_normal_usage + billing_json['normal_usage']
									total_overtime_usage = total_overtime_usage + billing_json['overtime_usage']

								billing_received = billing_normal_received + billing_overtime_received

							payment_amount = float(main_package_received + second_package_received + overtime_package_received + billing_received)	
							normal_payment_amount = float(main_package_normal_received + second_package_normal_received + overtime_package_normal_received + billing_normal_received)
							overtime_payment_amount = float(main_package_overtime_received + second_package_overtime_received + overtime_package_overtime_received + billing_overtime_received)

							# update request_driver
							where_param = { "_id": ObjectId(params['request_id']) }
							value_param = {
											"$set":
												{
													"request_status": "6",
													"job_status": job_status,
													"payment_amount": payment_amount,
													"normal_payment_amount": normal_payment_amount,
													"overtime_payment_amount": overtime_payment_amount,
													"total_normal_usage": total_normal_usage,
													"total_overtime_usage": total_overtime_usage,
													"payment_status": "0",
													"payment_date": None,
													"payment_at": None,
													"end_job_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.request_driver.update(where_param , value_param):
								car = db.car.find_one({"_id": ObjectId(request_driver_json['car_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								car_object = dumps(car)
								car_json = json.loads(car_object)

								car_type = db.car_type.find_one({"_id": ObjectId(car_json['car_type_id'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								car_type_object = dumps(car_type)
								car_type_json = json.loads(car_type_object)
								car_type_code = car_type_json['car_type_code']

								driver_info = get_member_info_by_id(request_driver_json['driver_id'])
								
								if car_type_code == "sedan":
									sedan_job = int(driver_info['sedan_job']) + 1
									suv_job = int(driver_info['suv_job'])
									van_job = int(driver_info['van_job'])
								elif car_type_code == "suv":
									sedan_job = int(driver_info['sedan_job'])
									suv_job = int(driver_info['suv_job']) + 1
									van_job = int(driver_info['van_job'])
								else:
									sedan_job = int(driver_info['sedan_job'])
									suv_job = int(driver_info['suv_job'])
									van_job = int(driver_info['van_job']) + 1

								# update จำนวนประเภทรถที่รับงานสำเร็จ
								where_param = { "_id": ObjectId(request_driver_json['driver_id']) }
								value_param = {
												"$set":
													{
														"sedan_job": sedan_job,
														"suv_job": suv_job,
														"van_job": van_job,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}
								db.member.update(where_param , value_param)

								#อัพเดตข้อมูล end_mileage
								where_param = { "request_id": params['request_id'] }
								value_param = {
												"$set":
													{
														"end_mileage": int(params['end_mileage']),
														"end_mileage_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								db.car_inspection.update(where_param , value_param)

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


								#sent noti to member
								customer_info = get_member_info_by_id(request_driver_json['member_id'])

								#จบงานเกินเวลาจอง
								if delay_end_time_obj > end_time_30_obj:
									#ถ้าเวลาจบงานล่าสุด มากกว่า เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 9
									noti_type = "end_job_overtime"
									request_no = request_driver_json['request_no']

									noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
									noti_message_en = "end overbooking job : "+request_no+" please choose paymemt method for excess charges."
									noti_message_th = "จบงาน "+request_no+" เกินเวลา กรุณาเลือกช่องทางชำระค่าใช้จ่ายส่วนเกิน"
								#จบงานตามเวลาจอง
								else:
									#ถ้าเวลาจบงานล่าสุด น้อยกว่าหรือเท่ากับ เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 8
									noti_type = "end_job_normal"
									request_no = request_driver_json['request_no']

									noti_title_en = "Driver : "+member_info['member_firstname_en']+" "+member_info['member_lastname_en']
									noti_title_th = "คนขับ "+member_info['member_firstname_th']+" "+member_info['member_lastname_th']
									noti_message_en = "end job :  "+request_no+" , please rate the service."
									noti_message_th = "จบงาน "+request_no+" กรุณาให้คะแนนการบริการ"

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
											"msg" : get_api_message("end_job" , "end_job_success" , member_lang) 
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("end_job" , "data_update_failed" , member_lang)
										}	
						#ตรวจสภาพรถไม่ผ่าน
						elif request_driver_json['check_status'] == "3":
							#ไม่ต้องอัพเดต ให้ฟ้องกลับไปว่า กรุณาตรวจสภาพรถอีกครั้ง
							result = {
										"status" : False,
										"msg" : get_api_message("end_job" , "please_car_inspection_again" , member_lang)
									}
						#ยืนยันการตรวจสภาพรถ
						elif request_driver_json['check_status'] == "2":
							#ไม่ต้องอัพเดต ให้ฟ้องกลับไปว่า ไม่สามารถจบงานได้ กรุณารอการยืนยันการตรวจสภาพรถจากผู้โดยสาร
							result = {
										"status" : False,
										"msg" : get_api_message("end_job" , "can_not_end_job_please_wait_for_confirmation_of_the_vehicle_inspection_from_the_passenger" , member_lang)
									}
						#ยังไม่ได้ตรวจสภาพรถ (0) หรือ ข้ามการตรวจสภาพรถ (1)
						else:
							#ไม่ต้องอัพเดต ให้ฟ้องกลับไปว่า กรุณาตรวจสภาพรถก่อนการจบงาน
							result = {
										"status" : False,
										"msg" : get_api_message("end_job" , "please_car_inspection" , member_lang) 
									}
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("end_job" , "can_not_end_job_because_job_status_is_invalid" , member_lang)
								}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("end_job" , "can_not_end_job_because_job_status_is_invalid" , member_lang)
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
	user_type = "driver"
	function_name = "end_job"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_driver_rating_summary(request):
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

			all_job = 0
			success_job = 0
			failed_job = 0
			in_progress_job = 0

			request_driver = db.request_driver.find({"driver_id": member_info['_id']['$oid']})
			
			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_driver_rating_summary" , "job_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				for i in range(len(request_driver_json)):
					#success
					if request_driver_json[i]['request_status'] == "6":
						success_job = success_job + 1
					#failed
					elif request_driver_json[i]['request_status'] == "2" or request_driver_json[i]['request_status'] == "3":
						failed_job = failed_job + 1
					else:
						in_progress_job = in_progress_job + 1

					all_job = all_job + 1


				service_rating = db.service_rating.find({"driver_id": member_info['_id']['$oid']})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				service_rating_object = dumps(service_rating)
				service_rating_json = json.loads(service_rating_object)

				all_rating_1 = 0
				all_rating_2 = 0
				all_rating_3 = 0
				all_rating_4 = 0
				all_rating_5 = 0
				count_service_rating = len(service_rating_json)

				#วน loop รวมคะแนนของคำถามแต่ละข้อ
				for i in range(count_service_rating):
					for j in range(len(service_rating_json[i]['rating'])):
						if j == 4:
							all_rating_5 = all_rating_5 + service_rating_json[i]['rating'][j]['question_rating']
						elif j == 3:
							all_rating_4 = all_rating_4 + service_rating_json[i]['rating'][j]['question_rating']
						elif j == 2:
							all_rating_3 = all_rating_3 + service_rating_json[i]['rating'][j]['question_rating']
						elif j == 1:
							all_rating_2 = all_rating_2 + service_rating_json[i]['rating'][j]['question_rating']
						else:
							all_rating_1 = all_rating_1 + service_rating_json[i]['rating'][j]['question_rating']

				if count_service_rating > 0:
					#หาค่าเฉลี่ยคะแนนของคำถามแต่ละข้อ
					average_rating_5 = '%.1f' % (all_rating_5 / count_service_rating)
					average_rating_4 = '%.1f' % (all_rating_4 / count_service_rating)
					average_rating_3 = '%.1f' % (all_rating_3 / count_service_rating)
					average_rating_2 = '%.1f' % (all_rating_2 / count_service_rating)
					average_rating_1 = '%.1f' % (all_rating_1 / count_service_rating)
				else:
					#หาค่าเฉลี่ยคะแนนของคำถามแต่ละข้อ
					average_rating_5 = 0
					average_rating_4 = 0
					average_rating_3 = 0
					average_rating_2 = 0
					average_rating_1 = 0

				service_rating_question = db.service_rating_question.find()
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				service_rating_question_object = dumps(service_rating_question)
				service_rating_question_json = json.loads(service_rating_question_object)

				average_rating_list = []

				for i in range(len(service_rating_question_json)):
					if member_lang == "en":
						question_name = service_rating_question_json[i]['question_en']
					else:
						question_name = service_rating_question_json[i]['question_th']

					if i == 4:
						question_rating = average_rating_5
					elif i == 3:
						question_rating = average_rating_4
					elif i == 2:
						question_rating = average_rating_3
					elif i == 1:
						question_rating = average_rating_2
					else:
						question_rating = average_rating_1

					average_rating_list.append({
						"question_id" : service_rating_question_json[i]['_id']['$oid'],
						"question_name": question_name,
						"question_rating": question_rating
					})

			result = {
						"status" : True,
						"msg" : get_api_message("get_driver_rating_summary" , "get_driver_rating_summary_success" , member_lang),
						"driver_rating" : round(float(member_info['driver_rating']) , 1),
						"all_job" : all_job,
						"success_job" : success_job,
						"failed_job" : failed_job,
						"in_progress_job" : in_progress_job,
						"average_rating" : average_rating_list
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
	user_type = "driver"
	function_name = "get_driver_rating_summary"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def update_driver_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_last_latitude = "last_latitude" in params
	isset_last_longitude = "last_longitude" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_last_latitude and isset_last_longitude:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# update request_driver
			where_param = { "_id": ObjectId(member_info['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"last_latitude": params['last_latitude'],
									"last_longitude": params['last_longitude'],
									"last_location_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.member.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("update_driver_location" , "update_driver_location_success" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("update_driver_location" , "data_update_failed" , member_lang) 
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
	user_type = "driver"
	function_name = "update_driver_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_income_summary(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_month = "month" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_month:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			total_year_income = 0
			total_year_received = 0
			total_year_pending = 0
			total_year_cancel = 0
			total_month_received = 0
			total_month_pending = 0
			total_month_cancel = 0

			current_year = datetime.now().strftime('%Y')
			current_month = datetime.now().strftime('%m')

			if current_month == "02":
				end_date_of_month = "29"
			elif current_month == "04" or current_month == "06" or current_month == "09" or current_month == "11":
				end_date_of_month = "30"
			else:
				end_date_of_month = "31"

			#ข้อมูลรายรับทั้งหมดของปีที่เลือก
			rd = db.request_driver.find({
											"driver_id": member_id,
											"start_date": {"$regex": current_year},
											"request_status": "6",
											"job_status" : {"$in" : ["8","10"]}
										})

			if rd is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				rd_object = dumps(rd)
				rd_json = json.loads(rd_object)

				for i in range(len(rd_json)):
					total_year_income = total_year_income + rd_json[i]['payment_amount']

					if rd_json[i]['payment_status'] == "1":
						total_year_received = total_year_received + rd_json[i]['payment_amount']
					else:
						total_year_pending = total_year_pending + rd_json[i]['payment_amount']

			#ข้อมูลรายรับจากงานที่ถูกยกเลิกของปีที่เลือก
			rd = db.request_driver.find({
											"driver_id": member_id,
											"start_date": {"$regex": current_year},
											"request_status": {"$in" : ["2","3"]}
										})

			if rd is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				rd_object = dumps(rd)
				rd_json = json.loads(rd_object)

				for i in range(len(rd_json)):
					main_package_info = rd_json[i]['main_package'][0]

					#คำนวณรายรับทั้งหมดของคนขับ
					main_package_normal_received = 0
					main_package_overtime_received = 0
					main_package_received = 0

					second_package_normal_received = 0
					second_package_overtime_received = 0
					second_package_received = 0

					overtime_package_normal_received = 0
					overtime_package_overtime_received = 0
					overtime_package_received = 0

					billing_normal_received = 0
					billing_overtime_received = 0
					billing_received = 0

					for j in range(len(rd_json[i]['main_package'])):
						main_package_normal_received = main_package_normal_received + (rd_json[i]['main_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
						main_package_overtime_received = main_package_overtime_received + (rd_json[i]['main_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

					main_package_received = main_package_normal_received + main_package_overtime_received

					if len(rd_json[i]['second_package']) > 0:
						for j in range(len(rd_json[i]['second_package'])):
							second_package_normal_received = second_package_normal_received + (rd_json[i]['second_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
							second_package_overtime_received = second_package_overtime_received + (rd_json[i]['second_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

						second_package_received = second_package_normal_received + second_package_overtime_received

					if len(rd_json[i]['overtime_package']) > 0:
						for j in range(len(rd_json[i]['overtime_package'])):
							overtime_package_normal_received = overtime_package_normal_received + (rd_json[i]['overtime_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
							overtime_package_overtime_received = overtime_package_overtime_received + (rd_json[i]['overtime_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

						overtime_package_received = overtime_package_normal_received + overtime_package_overtime_received

					if len(rd_json[i]['billing_id']) > 0:
						for j in range(len(rd_json[i]['billing_id'])):
							billing = db.billing.find_one({"_id": ObjectId(rd_json[i]['billing_id'][j])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							billing_object = dumps(billing)
							billing_json = json.loads(billing_object)

							billing_normal_received = billing_normal_received + (billing_json['normal_usage'] * main_package_info['normal_received_rate'])
							billing_overtime_received = billing_overtime_received + (billing_json['overtime_usage'] * main_package_info['overtime_received_rate'])

						billing_received = billing_normal_received + billing_overtime_received

					total_year_cancel = total_year_cancel + float(main_package_received + second_package_received + overtime_package_received + billing_received)
			

			#---------------------------------------------------------------------------------------#

			end_year = current_year
			end_month = current_month

			if params['month'] == "1":
				start_year = current_year
				start_month = current_month
			elif params['month'] == "3":
				#เดือนปัจจุบันน้อยกว่าเดือน 3 
				if current_month == "01" or current_month == "02":
					start_year = str(int(current_year)-1)
					
					if current_month == "01":
						start_month = "11"
					elif current_month == "02":
						start_month = "12"
				#เดือนปัจจุบันมากกว่าเดือน 3 
				else:
					start_year = current_year
					start_month = int(current_month)-2

					if start_month < 10:
						start_month = "0"+str(start_month)
					else:
						start_month = str(start_month)
			elif params['month'] == "6":
				#เดือนปัจจุบันน้อยกว่าเดือน 6 
				if current_month == "01" or current_month == "02" or current_month == "03" or current_month == "04" or current_month == "05":
					start_year = str(int(current_year)-1)
					start_month = int(current_month)-5

					if current_month == "01":
						start_month = "08"
					elif current_month == "02":
						start_month = "09"
					elif current_month == "03":
						start_month = "10"
					elif current_month == "04":
						start_month = "11"
					elif current_month == "05":
						start_month = "12"
				#เดือนปัจจุบันมากกว่าเดือน 6 
				else:
					start_year = current_year
					start_month = int(current_month)-5

					if start_month < 10:
						start_month = "0"+str(start_month)
					else:
						start_month = str(start_month)
			else:
				#เดือนปัจจุบันน้อยกว่าเดือน 12 
				if current_month == "01" or current_month == "02" or current_month == "03" or current_month == "04" or current_month == "05" or current_month == "06" or current_month == "07" or current_month == "08" or current_month == "09" or current_month == "10" or current_month == "11":
					start_year = str(int(current_year)-1)
					start_month = int(current_month)-11

					if current_month == "01":
						start_month = "02"
					elif current_month == "02":
						start_month = "03"
					elif current_month == "03":
						start_month = "04"
					elif current_month == "04":
						start_month = "05"
					elif current_month == "05":
						start_month = "06"
					elif current_month == "06":
						start_month = "07"
					elif current_month == "07":
						start_month = "08"
					elif current_month == "08":
						start_month = "09"
					elif current_month == "09":
						start_month = "10"
					elif current_month == "10":
						start_month = "11"
					elif current_month == "11":
						start_month = "12"
				#เดือนปัจจุบันเท่ากับเดือน 12 
				else:
					start_year = current_year
					start_month = int(current_month)-11

					start_month = "01"
					
			start_date_int = int(start_year+""+start_month+"01")
			end_date_int = int(end_year+""+end_month+""+end_date_of_month)

			#ข้อมูลรายรับทั้งหมดของเดือนและปีที่เลือก
			request_driver = db.request_driver.find({
														"driver_id": member_id,
														"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int},
														"request_status": "6",
														"job_status" : {"$in" : ["8","10"]}
													}).sort([("start_date", -1)])

			if request_driver is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				payment_driver_list = []

				for i in range(len(request_driver_json)):
					main_package_info = request_driver_json[i]['main_package'][0]
					create_datetime_obj = datetime.strptime(request_driver_json[i]['created_at'], '%Y-%m-%d %H:%M:%S')
					create_date = create_datetime_obj.strftime('%Y-%m-%d')
					create_time = create_datetime_obj.strftime('%H:%M')
					start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
					start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')

					payment_date = None
					if request_driver_json[i]['payment_date'] is not None:
						payment_datetime_obj = datetime.strptime(request_driver_json[i]['payment_date'], '%Y-%m-%d')
						payment_date = payment_datetime_obj.strftime('%Y-%m-%d')

					driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
					driver_code = driver_info['member_code']
					driver_name = driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']

					if request_driver_json[i]['payment_status'] == "1":
						payment_status_text = "จ่ายแล้ว"
						total_month_received = total_month_received + request_driver_json[i]['payment_amount']
					else:
						payment_status_text = "รอดำเนินการ"
						total_month_pending = total_month_pending + request_driver_json[i]['payment_amount']

					payment_driver_list.append({
						"request_no": request_driver_json[i]['request_no'],
						"start_date": start_date,
						"start_time": start_time,
						"total_receive_amount": request_driver_json[i]['payment_amount'],
						"normal_receive_amount": request_driver_json[i]['normal_payment_amount'],
						"overtime_receive_amount": request_driver_json[i]['overtime_payment_amount'],
						"payment_status": request_driver_json[i]['payment_status'],
						"payment_status_text": payment_status_text
					})

			#ข้อมูลรายรับจากงานที่ถูกยกเลิกของเดือนและปีที่เลือก
			request_driver = db.request_driver.find({
														"driver_id": member_id,
														"start_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int},
														"request_status": {"$in" : ["2","3"]}
													})

			if request_driver is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				for i in range(len(request_driver_json)):
					main_package_info = request_driver_json[i]['main_package'][0]

					#คำนวณรายรับทั้งหมดของคนขับ
					main_package_normal_received = 0
					main_package_overtime_received = 0
					main_package_received = 0

					second_package_normal_received = 0
					second_package_overtime_received = 0
					second_package_received = 0

					overtime_package_normal_received = 0
					overtime_package_overtime_received = 0
					overtime_package_received = 0

					billing_normal_received = 0
					billing_overtime_received = 0
					billing_received = 0

					for j in range(len(request_driver_json[i]['main_package'])):
						main_package_normal_received = main_package_normal_received + (request_driver_json[i]['main_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
						main_package_overtime_received = main_package_overtime_received + (request_driver_json[i]['main_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

					main_package_received = main_package_normal_received + main_package_overtime_received

					if len(request_driver_json[i]['second_package']) > 0:
						for j in range(len(request_driver_json[i]['second_package'])):
							second_package_normal_received = second_package_normal_received + (request_driver_json[i]['second_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
							second_package_overtime_received = second_package_overtime_received + (request_driver_json[i]['second_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

						second_package_received = second_package_normal_received + second_package_overtime_received

					if len(request_driver_json[i]['overtime_package']) > 0:
						for j in range(len(request_driver_json[i]['overtime_package'])):
							overtime_package_normal_received = overtime_package_normal_received + (request_driver_json[i]['overtime_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
							overtime_package_overtime_received = overtime_package_overtime_received + (request_driver_json[i]['overtime_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

						overtime_package_received = overtime_package_normal_received + overtime_package_overtime_received

					if len(request_driver_json[i]['billing_id']) > 0:
						for j in range(len(request_driver_json[i]['billing_id'])):
							billing = db.billing.find_one({"_id": ObjectId(request_driver_json[i]['billing_id'][j])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							billing_object = dumps(billing)
							billing_json = json.loads(billing_object)

							billing_normal_received = billing_normal_received + (billing_json['normal_usage'] * main_package_info['normal_received_rate'])
							billing_overtime_received = billing_overtime_received + (billing_json['overtime_usage'] * main_package_info['overtime_received_rate'])

						billing_received = billing_normal_received + billing_overtime_received

					total_month_cancel = total_month_cancel + float(main_package_received + second_package_received + overtime_package_received + billing_received)

			result = {
						"status" : True,
						"msg" : get_api_message("get_income_summary" , "get_income_summary_success" , member_lang),
						"month" : params['month'],
						"total_year_income": total_year_income,
						"total_year_received": total_year_received,
						"total_year_pending": total_year_pending,
						"total_year_cancel": total_year_cancel,
						"total_month_received": total_month_received,
						"total_month_pending": total_month_pending,
						"total_month_cancel": total_month_cancel,
						"payment_driver" : payment_driver_list
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
	user_type = "driver"
	function_name = "get_income_summary"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def change_request_status(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_request_status = "request_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_request_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# update data
			where_param = { "_id": ObjectId(params['request_id']) }
			value_param = {
							"$set":
								{
									"request_status": params['request_status'],
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.request_driver.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : "Change request status success."
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
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "driver"
	function_name = "change_request_status"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def change_driver_request_status(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_id = "request_id" in params
	isset_driver_id = "driver_id" in params
	isset_driver_request_status = "driver_request_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_id and isset_driver_id and isset_driver_request_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info_by_id(params['driver_id'])
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			request_driver = db.request_driver.find_one({
															"_id": ObjectId(params['request_id'])
														})

			if request_driver is None:
				result = { 
							"status" : False,
							"msg" : "Job not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				if request_driver_json['driver_list_id'] is None:
					result = {
								"status" : False,
								"msg" : "Driver list not found."
							}
				else:
					dl = db.driver_list.find_one({
													"_id": ObjectId(request_driver_json['driver_list_id'])
												})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					dl_object = dumps(dl)
					dl_json = json.loads(dl_object)

					driver_list = []
					for i in range(len(dl_json['driver_list'])):
						#แก้ไข driver_request_status เฉพาะคนที่มี driver_id ตรงกับ driver_id ที่ส่งเข้ามาเท่านั้น
						if dl_json['driver_list'][i]['driver_id'] == member_info['_id']['$oid']:
							driver_request_status = params['driver_request_status']
						else:
							driver_request_status = dl_json['driver_list'][i]['driver_request_status']

						driver_list.append({
							"driver_id" : dl_json['driver_list'][i]['driver_id'],
							"driver_request_status": driver_request_status
						})

					# update data
					where_param = { "_id": ObjectId(request_driver_json['driver_list_id']) , "driver_list.driver_id": member_info['_id']['$oid'] }
					value_param = {
									"$set":
										{
											"driver_list": driver_list,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.driver_list.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : "Change driver request status success."
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
						"msg" : get_api_message("all" , "unauthorized")
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "driver"
	function_name = "change_driver_request_status"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def last_location_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	if isset_accept and isset_content_type:
		location = db.test.find().sort([("updated_at", -1)]).skip(0).limit(10)

		if location is None:
			result = { 
						"status" : False,
						"msg" : "Data not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			location_object = dumps(location)
			location_json = json.loads(location_object)

			location_list = []

			for i in range(len(location_json)):
				location_list.append({
					"last_latitude": location_json[i]['last_latitude'],
					"last_longitude": location_json[i]['last_longitude'],
					"updated_at": location_json[i]['updated_at']
				})

			result = {
						"status" : True,
						"msg" : "Get location list success.",
						"location" : location_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "last_location_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#api test
def update_location(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_last_latitude = "last_latitude" in params
	isset_last_longitude = "last_longitude" in params

	if isset_accept and isset_content_type and isset_app_version and isset_last_latitude and isset_last_longitude:
		data = { 
					"last_latitude": params['last_latitude'],
					"last_longitude": params['last_longitude'],
					"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				}

		if db.test.insert_one(data):
			result = {
						"status" : True,
						"msg" : "Update location success."
					}
		else:
			result = {
						"status" : False,
						"msg" : "Job update failed."
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}
	
	#set log detail
	user_type = "driver"
	function_name = "update_location"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result
