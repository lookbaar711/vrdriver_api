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

def company_dashboard(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_start_date and isset_end_date:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			member = db.member.find_one({
											"member_token": token,
											"member_type": "customer"
										})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("company_dashboard" , "data_not_found" , member_lang)
						}
			else:
				request_driver_list = []

				if params['start_date'] is None and params['end_date'] is None:
					today_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

					company_member = db.member.find({
														"company_id": company_id,
														"created_at": {
															"$lt": today_datetime
														},
														"member_status": "1"
													})

					count_request_driver = db.request_driver.find({
																	"company_id": company_id,
																	"created_at": {
																		"$lt": today_datetime
																	}
																}).count()

				else:
					sd = datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
					ed = datetime.strptime(params['end_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
					start_date = sd + " 00:00:00"
					end_date = ed + " 23:59:59"

					company_member = db.member.find({
														"company_id": company_id,
														"created_at": {
															"$gte": start_date,
															"$lt": end_date
														},
														"member_status": "1"
													})

					count_request_driver = db.request_driver.find({
																	"company_id": company_id,
																	"created_at": {
																		"$gte": start_date,
																		"$lt": end_date
																	}
																}).count()

				if company_member is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("company_dashboard" , "data_not_found" , member_lang)
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_member_object = dumps(company_member)
					company_member_json = json.loads(company_member_object)
					count_master_admin = 0
					count_admin_company = 0
					count_user_company = 0
					count_billing_amount = 0

					for i in range(len(company_member_json)):
						if company_member_json[i]['company_user_type'] == "2":
							count_master_admin = count_master_admin + 1
						elif company_member_json[i]['company_user_type'] == "1":
							count_admin_company = count_admin_company + 1
						else:
							count_user_company = count_user_company + 1

					today_date = datetime.now().strftime('%Y-%m-%d')
					today_time = datetime.now().strftime('%H:%M:%S')

					request_driver = db.request_driver.find({
																"member_id": member_id,
																"start_date": {"$gte" : today_date},
																"request_status" : {"$in" : ["1","4","5"]}
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

					where_param = { 
									"company_id" : company_id,
									"billing_status": {"$in" : ["0","1"]}
								}

					if params['start_date'] is not None and params['start_date'] != "" and params['end_date'] is not None and params['end_date'] != "":
						start_billing_date_int = int(datetime.strptime(params['start_date'], '%d/%m/%Y').strftime('%Y%m%d')) 
						end_billing_date_int = int(datetime.strptime(params['end_date'], '%d/%m/%Y').strftime('%Y%m%d')) 
					
						add_params = {"billing_date_int" : {"$gte" : start_billing_date_int , "$lte" : end_billing_date_int}}
						where_param.update(add_params)

					billing_list = []

					billing = db.billing.find(where_param)

					if billing is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						billing_object = dumps(billing)
						billing_json = json.loads(billing_object)

						for i in range(len(billing_json)):
							count_billing_amount = count_billing_amount + int(billing_json[i]['sum_paid'])

					result = {
								"status" : True,
								"msg" : get_api_message("company_dashboard" , "get_company_dashboard_success" , member_lang),
								"count_request_driver" : count_request_driver,
								"count_billing_amount" : count_billing_amount,
								"count_master_admin" : count_master_admin,
								"count_admin_company" : count_admin_company,
								"count_user_company" : count_user_company,
								"request" : request_driver_list
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
	function_name = "company_dashboard"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_contact_us(request):
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

		contact_us = db.contact_us.find_one()

		if contact_us is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("get_contact_us" , "data_not_found" , member_lang) 
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			contact_us_object = dumps(contact_us)
			contact_us_json = json.loads(contact_us_object)

			contact_topic = db.contact_topic.find({"topic_status": "1"})

			if contact_topic is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				contact_topic_object = dumps(contact_topic)
				contact_topic_json = json.loads(contact_topic_object)

				if member_lang == "en":
					contact_address = contact_us_json['contact_address_en']
				else:
					contact_address = contact_us_json['contact_address_th']

				contact_topic_list = []

				for i in range(len(contact_topic_json)):
					if member_lang == "en":
						topic_name = contact_topic_json[i]['topic_en']
					else:
						topic_name = contact_topic_json[i]['topic_th']

					contact_topic_list.append({
						"topic_id" : contact_topic_json[i]['_id']['$oid'],
						"topic_name": topic_name
					})

			result = {
						"status" : True,
						"msg" : get_api_message("get_contact_us" , "get_contact_us_success" , member_lang),
						"contact_address" : contact_address,
						"contact_email" : contact_us_json['contact_email'],
						"contact_tel" : contact_us_json['contact_tel'],
						"contact_topic" : contact_topic_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "get_contact_us"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_my_web_profile(request):
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
	isset_current_password = "current_password" in params
	isset_new_password = "new_password" in params
	isset_confirm_password = "confirm_password" in params
	isset_profile_image = "profile_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_firstname and isset_lastname and isset_email and isset_tel and isset_current_password and isset_new_password and isset_confirm_password  and isset_profile_image:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check required
			if params['member_firstname']=="" or params['member_firstname'] is None:
				validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_my_web_profile" , "firstname_is_required" , member_lang)})
			if params['member_lastname']=="" or params['member_lastname'] is None:
				validate.append({"error_param" : "member_lastname","msg" : get_api_message("edit_my_web_profile" , "lastname_is_required" , member_lang)})
			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_web_profile" , "email_is_required" , member_lang)})
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_web_profile" , "tel_is_required" , member_lang)})

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
					validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_my_web_profile" , "firstname_and_lastname_has_been_used" , member_lang)}) 
			
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
						validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_web_profile" , "email_has_been_used" , member_lang)})
				else:
					validate.append({"error_param" : "member_email","msg" : get_api_message("edit_my_web_profile" , "invalid_email_format" , member_lang)})		

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
					validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_my_web_profile" , "invalid_tel_format" , member_lang)}) 

			#check current password
			if params['current_password']!="" and params['current_password'] is not None:
				#เอา current password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(params['current_password'].encode())
				current_password = hash_input_pass.hexdigest()

				#เช็คว่ารหัสผ่านตรงกันหรือไม่
				check_password = db.member.find({
													"member_token": token,
													"member_password": current_password
												}).count()
				if check_password == 0:
					validate.append({"error_param" : "current_password","msg" : get_api_message("edit_my_web_profile" , "current_password_is_incorrect" , member_lang)}) 

			#check new password & confirm password
			if (params['new_password']!="" and params['new_password'] is not None) and (params['confirm_password']!="" and params['confirm_password'] is not None):
				if params['new_password']!=params['confirm_password']:
					validate.append({"error_param" : "new_password","msg" : get_api_message("edit_my_web_profile" , "new_password_do_not_match" , member_lang)}) 
				else:
					count_password = len(params['new_password'])
					if count_password < 6:
						validate.append({"error_param" : "new_password","msg" : get_api_message("edit_my_web_profile" , "new_password_less_than_6_character" , member_lang)}) 


			#ถ้า validate ผ่าน
			if len(validate) == 0:
				member = db.member.find_one({
												"member_token": token,
												"member_type": "customer"
											})
				if member is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("edit_my_web_profile" , "data_not_found" , member_lang) 
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

					if params['new_password'] is None:
						new_password = member_json['member_password']
					else:
						#เอา new_password ที่รับมาเข้ารหัส
						hash_input_pass = hashlib.md5(params['new_password'].encode())
						new_password = hash_input_pass.hexdigest()

					where_param = { "member_token": token }
					value_param = {
									"$set": {
												"member_password": new_password,
												"member_firstname_en": params['member_firstname'].strip().title(),
												"member_lastname_en": params['member_lastname'].strip().title(),
												"member_firstname_th": params['member_firstname'].strip().title(),
												"member_lastname_th": params['member_lastname'].strip().title(),
												"member_email": params['member_email'].strip().lower(),
												"member_tel": params['member_tel'].strip(),
												"profile_image": image_name
											}
									}

					if db.member.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : get_api_message("edit_my_web_profile" , "edit_profile_success" , member_lang) 
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_my_web_profile" , "data_update_failed" , member_lang) 
								}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("edit_my_web_profile" , "please_check_your_parameters_value" , member_lang), 
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
	function_name = "edit_my_web_profile"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def activate_user(mem_id,request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None
	
	if isset_accept and isset_content_type:
		member = db.member.find_one({
										"_id": ObjectId(mem_id),
										"member_type": "customer"
									})
		if member is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("activate_user" , "data_not_found" , member_lang)
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			member_object = dumps(member)
			member_json = json.loads(member_object)
			member_lang = member_json['member_lang']

			#ถ้าเคย activate ไปแล้ว ให้ฟ้องว่าเคย activate ไปแล้ว
			if member_json['activated_at'] is not None:
				result = { 
							"status" : False,
							"msg" : get_api_message("activate_user" , "already_activated" , member_lang)
						}
			else:
				#update member
				where_param = { "_id": ObjectId(mem_id) }
				value_param = {
								"$set": {
											"activated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

				if db.member.update(where_param , value_param):
					#ถ้าเป็นบุคคลทั่วไป
					if member_json['company_id'] is None:
						android_link = "https://play.google.com/store"
						ios_link = "https://www.apple.com/th/ios/app-store/"

						#send email
						email_type = "register_success_normal"
						subject = "VR Driver : สมัครสมาชิกสำเร็จ"
						to_email = member_json['member_email'].strip().lower()
						template_html = "register_success_normal.html"
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
					#ถ้าเป็นนิติบุคคล
					else:
						#ส่งเมล์หลังจากสมัครสมาชิกนิติบุคคลสำเร็จ
						web_link = "https://play.google.com/store"

						#send email
						email_type = "register_success_company"
						subject = "VR Driver : สมัครสมาชิกนิติบุคคลสำเร็จ"
						to_email = member_json['member_email'].strip().lower()
						template_html = "register_success_company.html"
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

					#ส่ง noti welcome หา user
					noti_title_en = "Welcome "+member_json['member_firstname_en']+" "+member_json['member_lastname_en']
					noti_title_th = "ยินดีต้อนรับคุณ "+member_json['member_firstname_th']+" "+member_json['member_lastname_th']
					noti_message_en = "to VR Driver"
					noti_message_th = "เข้าสู่ VR Driver"

					if member_json['member_lang'] == "en":
						member_fullname = member_json['member_firstname_en']+" "+member_json['member_lastname_en']
						noti_title = noti_title_en
						noti_message = noti_message_en
						show_noti = noti_title_en+" "+noti_message_en
					else:
						member_fullname = member_json['member_firstname_th']+" "+member_json['member_lastname_th']
						noti_title = noti_title_th
						noti_message = noti_message_th
						show_noti = noti_title_th+" "+noti_message_th

					#แปลง format วันที่
					created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')

					#ส่ง noti
					noti_type = "welcome_to_vrdriver"
					send_noti_key = member_json['noti_key']
					send_noti_title = noti_title
					send_noti_message = noti_message
					send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "created_datetime" : created_datetime }
					send_noti_badge = 1

					#insert member_notification
					noti_detail = {}

					data = { 
								"member_id": member_json['_id']['$oid'],
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
								"msg" : get_api_message("activate_user" , "activate_user_success" , member_lang)
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("activate_user" , "data_update_failed" , member_lang)
							}	
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "activate_user"
	request_headers = request.headers
	params_get = {"member_id" : mem_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)
	
	return result

def get_company_info(request):
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

			#ถ้าเป็น normal user
			if member_info['company_id'] is None:
				result = { 
						"status" : False,
						"msg" : get_api_message("get_company_info" , "this_user_is_not_company_user" , member_lang) 
					}
			else:
				company = db.company.find_one({"_id": ObjectId(member_info['company_id'])})
				if company is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("get_company_info" , "data_not_found" , member_lang) 
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)

					if member_lang == "en":
						company_province_name = company_json['company_province_en']
						company_district_name = company_json['company_district_en']
						company_sub_district_name = company_json['company_sub_district_en']

						billing_province_name = company_json['billing_province_en']
						billing_district_name = company_json['billing_district_en']
						billing_sub_district_name = company_json['billing_sub_district_en']
					else:
						company_province_name = company_json['company_province_th']
						company_district_name = company_json['company_district_th']
						company_sub_district_name = company_json['company_sub_district_th']

						billing_province_name = company_json['billing_province_th']
						billing_district_name = company_json['billing_district_th']
						billing_sub_district_name = company_json['billing_sub_district_th']

					data = {
								"id": company_json['_id']['$oid'],
								"company_name": company_json['company_name'],
								"company_tax_id": company_json['company_tax_id'],
								"company_email": company_json['company_email'],
								"company_tel": company_json['company_tel'],

								"company_address": company_json['company_address'],
								"company_postcode": company_json['company_postcode'],
								"company_province_name": company_province_name,
								"company_province_code": company_json['company_province_code'],
								"company_district_name": company_district_name,
								"company_district_code": company_json['company_district_code'],
								"company_sub_district_name": company_sub_district_name,
								"company_sub_district_code": company_json['company_sub_district_code'],

								"billing_date": company_json['billing_date'],
								"billing_receiver_firstname": company_json['billing_receiver_firstname'],
								"billing_receiver_lastname": company_json['billing_receiver_lastname'],
								"billing_receiver_email": company_json['billing_receiver_email'],
								"billing_receiver_tel": company_json['billing_receiver_tel'],
								"same_company_address": company_json['same_company_address'],

								"billing_address": company_json['billing_address'],
								"billing_postcode": company_json['billing_postcode'],
								"billing_province_name": billing_province_name,
								"billing_province_code": company_json['billing_province_code'],
								"billing_district_name": billing_district_name,
								"billing_district_code": company_json['billing_district_code'],
								"billing_sub_district_name": billing_sub_district_name,
								"billing_sub_district_code": company_json['billing_sub_district_code'],

								"vat_registration_doc": company_json['vat_registration_doc'],
								"vat_registration_doc_type": company_json['vat_registration_doc_type'],
								"vat_registration_doc_name": company_json['vat_registration_doc_name'],
								"company_certificate_doc": company_json['company_certificate_doc'],
								"company_certificate_doc_type": company_json['company_certificate_doc_type'],
								"company_certificate_doc_name": company_json['company_certificate_doc_name'],
								"company_logo": company_json['company_logo'],
								"company_status": company_json['company_status']
							}

					result = {
								"status" : True,
								"msg" : get_api_message("get_company_info" , "get_company_info_success" , member_lang), 
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
	function_name = "get_company_info"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_company(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_id = "company_id" in params
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
	isset_vat_registration_doc = "vat_registration_doc" in params
	isset_vat_registration_doc_type = "vat_registration_doc_type" in params
	isset_vat_registration_doc_name = "vat_registration_doc_name" in params
	isset_company_certificate_doc = "company_certificate_doc" in params
	isset_company_certificate_doc_type = "company_certificate_doc_type" in params
	isset_company_certificate_doc_name = "company_certificate_doc_name" in params
	isset_company_logo = "company_logo" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_id and isset_company_name and isset_company_tax_id and isset_company_email and isset_company_tel and isset_company_address and isset_company_postcode and isset_company_province_code and isset_company_district_code and isset_company_sub_district_code and isset_billing_date and isset_billing_receiver_firstname and isset_billing_receiver_lastname and isset_billing_receiver_email and isset_billing_receiver_tel and isset_company_id and isset_company_name and isset_billing_postcode and isset_billing_province_code and isset_billing_district_code and isset_billing_sub_district_code and isset_vat_registration_doc and isset_vat_registration_doc_type and isset_vat_registration_doc_name and isset_company_certificate_doc and isset_company_certificate_doc_type and isset_company_certificate_doc_name and isset_company_logo:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			same_company_address = str(params['same_company_address'])

			#check required
			if params['company_name']=="" or params['company_name'] is None:
				validate.append({"error_param" : "company_name","msg" : get_api_message("edit_company" , "company_name_is_required" , member_lang)}) 
			if params['company_tax_id']=="" or params['company_tax_id'] is None:
				validate.append({"error_param" : "company_tax_id","msg" : get_api_message("edit_company" , "company_tax_id_is_required" , member_lang)}) 
			if params['company_email']=="" or params['company_email'] is None:
				validate.append({"error_param" : "company_email","msg" : get_api_message("edit_company" , "company_email_is_required" , member_lang)}) 
			if params['company_tel']=="" or params['company_tel'] is None:
				validate.append({"error_param" : "company_tel","msg" : get_api_message("edit_company" , "company_tel_is_required" , member_lang)}) 

			if params['company_address']=="" or params['company_address'] is None:
				validate.append({"error_param" : "company_address","msg" : get_api_message("edit_company" , "company_address_is_required" , member_lang)}) 
			if params['company_postcode']=="" or params['company_postcode'] is None:
				validate.append({"error_param" : "company_postcode","msg" : get_api_message("edit_company" , "company_postcode_is_required" , member_lang)}) 
			if params['company_province_code']=="" or params['company_province_code'] is None:
				validate.append({"error_param" : "company_province_code","msg" : get_api_message("edit_company" , "company_province_is_required" , member_lang)}) 
			if params['company_district_code']=="" or params['company_district_code'] is None:
				validate.append({"error_param" : "company_district_code","msg" : get_api_message("edit_company" , "company_district_is_required" , member_lang)}) 
			if params['company_sub_district_code']=="" or params['company_sub_district_code'] is None:
				validate.append({"error_param" : "company_sub_district_code","msg" : get_api_message("edit_company" , "company_sub_district_is_required" , member_lang)}) 
			
			if params['billing_date']=="" or params['billing_date'] is None:
				validate.append({"error_param" : "billing_date","msg" : get_api_message("edit_company" , "billing_date_is_required" , member_lang)}) 
			if params['billing_receiver_firstname']=="" or params['billing_receiver_firstname'] is None:
				validate.append({"error_param" : "billing_receiver_firstname","msg" : get_api_message("edit_company" , "billing_receiver_firstname_is_required" , member_lang)}) 
			if params['billing_receiver_lastname']=="" or params['billing_receiver_lastname'] is None:
				validate.append({"error_param" : "billing_receiver_lastname","msg" : get_api_message("edit_company" , "billing_receiver_lastname_is_required" , member_lang)}) 
			if params['billing_receiver_email']=="" or params['billing_receiver_email'] is None:
				validate.append({"error_param" : "billing_receiver_email","msg" : get_api_message("edit_company" , "billing_receiver_email_is_required" , member_lang)}) 
			if params['billing_receiver_tel']=="" or params['billing_receiver_tel'] is None:
				validate.append({"error_param" : "billing_receiver_tel","msg" : get_api_message("edit_company" , "billing_receiver_tel_is_required" , member_lang)}) 

			if same_company_address=="0" and (params['billing_address']=="" or params['billing_address'] is None):
				validate.append({"error_param" : "billing_address","msg" : get_api_message("edit_company" , "billing_address_is_required" , member_lang)}) 
			if same_company_address=="0" and (params['billing_postcode']=="" or params['billing_postcode'] is None):
				validate.append({"error_param" : "billing_postcode","msg" : get_api_message("edit_company" , "billing_postcode_is_required" , member_lang)}) 
			if same_company_address=="0" and (params['billing_province_code']=="" or params['billing_province_code'] is None):
				validate.append({"error_param" : "billing_province","msg" : get_api_message("edit_company" , "billing_province_is_required" , member_lang)}) 
			if same_company_address=="0" and (params['billing_district_code']=="" or params['billing_district_code'] is None):
				validate.append({"error_param" : "billing_district_code","msg" : get_api_message("edit_company" , "billing_district_is_required" , member_lang)}) 
			if same_company_address=="0" and (params['billing_sub_district_code']=="" or params['billing_sub_district_code'] is None):
				validate.append({"error_param" : "billing_sub_district_code","msg" : get_api_message("edit_company" , "billing_sub_district_is_required" , member_lang)}) 

			#check already company name
			if params['company_name']!="" and params['company_name'] is not None:
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_company_name = db.company.find({
												"_id": {"$ne": ObjectId(params['company_id'])},
												"company_name": params['company_name'].strip(),
												"company_status": "1"
											}).count()
				if check_company_name > 0:
					validate.append({"error_param" : "company_name","msg" : get_api_message("edit_company" , "company_name_has_been_used" , member_lang)}) 

			#check already tax id
			if params['company_tax_id']!="" and params['company_tax_id'] is not None:
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_company_tax_id = db.company.find({
												"_id": {"$ne": ObjectId(params['company_id'])},
												"company_tax_id": params['company_tax_id'].strip(),
												"company_status": "1"
											}).count()
				if check_company_tax_id > 0:
					validate.append({"error_param" : "company_tax_id","msg" : get_api_message("edit_company" , "company_tax_id_has_been_used" , member_lang)}) 

			#check already company email
			if params['company_email']!="" and params['company_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['company_email'])

				if len(check_format_email) > 0:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_email = db.company.find({
													"_id": {"$ne": ObjectId(params['company_id'])},
													"company_email": params['company_email'].strip().lower(),
													"company_status": "1"
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "company_email","msg" : get_api_message("edit_company" , "company_email_has_been_used" , member_lang)}) 
				else:
					validate.append({"error_param" : "company_email","msg" : get_api_message("edit_company" , "invalid_email_format" , member_lang)})

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
					validate.append({"error_param" : "company_tel","msg" : get_api_message("edit_company" , "invalid_company_tel_format" , member_lang)}) 

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
					validate.append({"error_param" : "billing_receiver_tel","msg" : get_api_message("edit_company" , "invalid_billing_tel_format" , member_lang)}) 

			#check company postcode format
			if params['company_postcode']!="" and params['company_postcode'] is not None:
				count_postcode = len(params['company_postcode'])

				if count_postcode != 5:
					validate.append({"error_param" : "company_postcode","msg" : get_api_message("edit_company" , "invalid_company_postcode_format" , member_lang)}) 
			
			#check billing postcode format
			if same_company_address=="0" and (params['billing_postcode']!="" and params['billing_postcode'] is not None):
				count_postcode = len(params['billing_postcode'])

				if count_postcode != 5:
					validate.append({"error_param" : "billing_postcode","msg" : get_api_message("edit_company" , "invalid_billing_postcode_format" , member_lang)}) 


			#set company_province_en & company_province_th
			province = db.province.find_one({"province_code" : params['company_province_code']})

			if province is None:
				validate.append({"error_param" : "company_province_code","msg" : get_api_message("edit_company" , "please_check_your_company_province_code_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				province_object = dumps(province)
				province_json = json.loads(province_object)

				company_province_en = province_json['province_en']
				company_province_th = province_json['province_th']

			#set company_district_en & company_district_th
			district = db.district.find_one({"district_code" : params['company_district_code']})

			if district is None:
				validate.append({"error_param" : "company_district_code","msg" : get_api_message("edit_company" , "please_check_your_company_district_code_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				district_object = dumps(district)
				district_json = json.loads(district_object)

				company_district_en = district_json['district_en']
				company_district_th = district_json['district_th']

			#set company_sub_district_en & company_sub_district_th
			sub_district = db.sub_district.find_one({"sub_district_code" : params['company_sub_district_code']})

			if sub_district is None:
				validate.append({"error_param" : "company_sub_district_code","msg" : get_api_message("edit_company" , "please_check_your_company_sub_district_code_value" , member_lang)}) 
			else:
				# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				sub_district_object = dumps(sub_district)
				sub_district_json = json.loads(sub_district_object)

				company_sub_district_en = sub_district_json['sub_district_en']
				company_sub_district_th = sub_district_json['sub_district_th']

			#คนละที่อยู่
			if same_company_address=="0":
				#set billing_province_en & billing_province_th
				billing_province = db.province.find_one({"province_code" : params['billing_province_code']})

				if billing_province is None:
					validate.append({"error_param" : "billing_province_code","msg" : get_api_message("edit_company" , "please_check_your_billing_province_code_value" , member_lang)}) 
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
					validate.append({"error_param" : "billing_district_code","msg" : get_api_message("edit_company" , "please_check_your_billing_district_code_value" , member_lang)}) 
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
					validate.append({"error_param" : "billing_sub_district_code","msg" : get_api_message("edit_company" , "please_check_your_billing_sub_district_code_value" , member_lang)}) 
				else:
					# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					billing_sub_district_object = dumps(billing_sub_district)
					billing_sub_district_json = json.loads(billing_sub_district_object)

					billing_sub_district_en = billing_sub_district_json['sub_district_en']
					billing_sub_district_th = billing_sub_district_json['sub_district_th']
					billing_sub_district_code = billing_sub_district_json['sub_district_code']
			#ที่อยู่เดียวกัน
			else:
				billing_province_en = province_json['province_en']
				billing_province_th = province_json['province_th']
				billing_province_code = params['company_province_code']

				billing_district_en = district_json['district_en']
				billing_district_th = district_json['district_th']
				billing_district_code = params['company_district_code']

				billing_sub_district_en = sub_district_json['sub_district_en']
				billing_sub_district_th = sub_district_json['sub_district_th']
				billing_sub_district_code = params['company_sub_district_code']



			#ถ้า validate ผ่าน
			if len(validate) == 0:
				company = db.company.find_one({"_id": ObjectId(member_info['company_id'])})

				if company is None:
					result = { 
								"status" : False,
								"msg" : get_api_message("edit_company" , "data_not_found" , member_lang) 
							}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)

					#ถ้าไม่มีการแก้ไขรูป logo (company_logo เป็น null) ไม่ต้องอัพเดตรูป  
					if params['company_logo'] is None:
						company_logo = company_json['company_logo']
					else:
						#เช็ค path และลบรูปเก่า
						if company_json['company_logo'] is not None:
							if os.path.exists("static/images/company/logo/"+company_json['company_logo']):
								os.remove("static/images/company/logo/"+company_json['company_logo'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_company_logo(params['company_logo'], generate_token)

						if check_upload_image is None:
							company_logo = None
						else:
							company_logo = check_upload_image

					#ถ้าไม่มีการแก้ไข doc (vat_registration_doc เป็น null) ไม่ต้องอัพเดต  
					if params['vat_registration_doc'] is None:
						vat_registration_doc = company_json['vat_registration_doc']
					else:
						#เช็ค path และลบรูปเก่า
						if company_json['vat_registration_doc'] is not None:
							if os.path.exists("static/images/company/vat_registration/"+company_json['vat_registration_doc']):
								os.remove("static/images/company/vat_registration/"+company_json['vat_registration_doc'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_vat_registration(params['vat_registration_doc'], generate_token, params['vat_registration_doc_type'])

						if check_upload_image is None:
							vat_registration_doc = None
						else:
							vat_registration_doc = check_upload_image

					#ถ้าไม่มีการแก้ไข doc (company_certificate_doc เป็น null) ไม่ต้องอัพเดต 
					if params['company_certificate_doc'] is None:
						company_certificate_doc = company_json['company_certificate_doc']
					else:
						#เช็ค path และลบรูปเก่า
						if company_json['company_certificate_doc'] is not None:
							if os.path.exists("static/images/company/company_certificate/"+company_json['company_certificate_doc']):
								os.remove("static/images/company/company_certificate/"+company_json['company_certificate_doc'])
			
						#generate token
						generate_token = get_random_token(40)
						check_upload_image = upload_company_certificate(params['company_certificate_doc'], generate_token, params['company_certificate_doc_type'])

						if check_upload_image is None:
							company_certificate_doc = None
						else:
							company_certificate_doc = check_upload_image

					#ถ้าเป็น 0 ให้อัพเดตเป็น 2
					if company_json['company_status'] == "0":
						company_status = "2"
					else:
						company_status = company_json['company_status']


					if same_company_address == "1":
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
					else:
						billing_address = params['billing_address']
						billing_postcode = params['billing_postcode']
						billing_province_en = billing_province_en
						billing_province_th = billing_province_th
						billing_province_code = params['billing_province_code']
						billing_district_en = billing_district_en
						billing_district_th = billing_district_th
						billing_district_code = params['billing_district_code']
						billing_sub_district_en = billing_sub_district_en
						billing_sub_district_th = billing_sub_district_th
						billing_sub_district_code = params['billing_sub_district_code']

					# update data to tb company
					where_param = { "_id": ObjectId(params['company_id']) }
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

											"vat_registration_doc": vat_registration_doc,
											"vat_registration_doc_type": params['vat_registration_doc_type'],
											"vat_registration_doc_name": params['vat_registration_doc_name'],
											"company_certificate_doc": company_certificate_doc,
											"company_certificate_doc_type": params['company_certificate_doc_type'],
											"company_certificate_doc_name": params['company_certificate_doc_name'],
											"company_logo": company_logo,
											"company_status": company_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.company.update(where_param , value_param):
						if company_json['company_status'] == "0":
							if company_json['os_type'] == "ios" or company_json['os_type'] == "android":
								register_channel = "app"
							else:
								register_channel = "web"
				
							# insert data to tb company_history
							data = { 
										"company_id": params['company_id'],
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

										"vat_registration_doc": vat_registration_doc,
										"vat_registration_doc_type": params['vat_registration_doc_type'],
										"vat_registration_doc_name": params['vat_registration_doc_name'],
										"company_certificate_doc": company_certificate_doc,
										"company_certificate_doc_type": params['company_certificate_doc_type'],
										"company_certificate_doc_name": params['company_certificate_doc_name'],
										"company_logo": company_logo,
										"os_type": company_json['os_type'],
										"register_channel": register_channel,
										"company_status": company_status,
										"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"approved_at": None
								}

							if db.company_history.insert_one(data):
								noti_title_en = "บริษัท "+params['company_name']
								noti_title_th = "บริษัท "+params['company_name']
								noti_message_en = "แจ้งอัพเดตข้อมูลนิติบุคคลแล้ว"
								noti_message_th = "แจ้งอัพเดตข้อมูลนิติบุคคลแล้ว"

								#insert admin_notification
								noti_type = "edit_company"
								noti_detail = {
													"company_id": params['company_id'],
													"company_name": params['company_name'].strip(),
													"company_tax_id": params['company_tax_id'].strip(),
													"company_email": params['company_email'].strip().lower(),
													"company_tel": params['company_tel'].strip()
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
											"msg" : get_api_message("edit_company" , "edit_company_success" , member_lang) 
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("edit_company" , "company_history_insert_failed" , member_lang) 
										}
						else:
							result = {
										"status" : True,
										"msg" : get_api_message("edit_company" , "edit_company_success" , member_lang) 
									}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_company" , "data_update_failed" , member_lang) 
								}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("edit_company" , "please_check_your_parameters_value" , member_lang), 
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
	function_name = "edit_company"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def province_list(request):
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

			province = db.province.find({"province_status": "1"})

			if province is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("province_list" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				province_object = dumps(province)
				province_json = json.loads(province_object)

				province_list = []

				for i in range(len(province_json)):
					if member_lang == "en":
						province_name = province_json[i]['province_en']
					else:
						province_name = province_json[i]['province_th']

					province_list.append({
						"id" : province_json[i]['_id']['$oid'],
						"province_code": province_json[i]['province_code'],
						"province_name": province_name
					})

				result = {
							"status" : True,
							"msg" : get_api_message("province_list" , "get_province_list_success" , member_lang),
							"data" : province_list
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
	function_name = "province_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def district_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_province_code = "province_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_province_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

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
							"msg" : get_api_message("district_list" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				district_object = dumps(district)
				district_json = json.loads(district_object)

				district_list = []

				for i in range(len(district_json)):
					if member_lang == "en":
						district_name = district_json[i]['district_en']
					else:
						district_name = district_json[i]['district_th']

					district_list.append({
						"id" : district_json[i]['_id']['$oid'],
						"district_code": district_json[i]['district_code'],
						"district_name": district_name
					})

				result = {
							"status" : True,
							"msg" : get_api_message("district_list" , "get_district_list_success" , member_lang), 
							"data" : district_list
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
	function_name = "district_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def sub_district_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_district_code = "district_code" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_district_code:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

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
							"msg" : get_api_message("sub_district_list" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				sub_district_object = dumps(sub_district)
				sub_district_json = json.loads(sub_district_object)

				sub_district_list = []

				for i in range(len(sub_district_json)):
					if member_lang == "en":
						sub_district_name = sub_district_json[i]['sub_district_en']
					else:
						sub_district_name = sub_district_json[i]['sub_district_th']

					sub_district_list.append({
						"sub_district_id" : sub_district_json[i]['_id']['$oid'],
						"sub_district_code": sub_district_json[i]['sub_district_code'],
						"sub_district_name": sub_district_name
					})

				result = {
							"status" : True,
							"msg" : get_api_message("sub_district_list" , "get_sub_district_list_success" , member_lang), 
							"data" : sub_district_list
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
	function_name = "sub_district_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_address_info(request):
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
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			
			postcode = db.postcode.find({
											"postcode": params['postcode'],
											"postcode_status": "1"
										})

			if postcode is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_address_info" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				postcode_object = dumps(postcode)
				postcode_json = json.loads(postcode_object)

				address_info_list = []

				for i in range(len(postcode_json)):
					if member_lang == "en":
						sub_district_name = postcode_json[i]['sub_district_en']
						district_name = postcode_json[i]['district_en']
						province_name = postcode_json[i]['province_en']
					else:
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
							"msg" : get_api_message("get_address_info" , "get_address_info_success" , member_lang), 
							"data" : address_info_list
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
	function_name = "get_address_info"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_user_list(request):
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
				result = { 
							"status" : False,
							"msg" : get_api_message("company_user_list" , "data_not_found" , member_lang) 
						}
			else:
				member = db.member.find({"member_type" : "customer","company_id" : member_info['company_id']}).sort([("updated_at", -1)])

				if member is None:
					result = { 
							"status" : False,
							"msg" : get_api_message("company_user_list" , "data_not_found" , member_lang) 
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_object = dumps(member)
					member_json = json.loads(member_object)

					member_list = []

					for i in range(len(member_json)):
						if member_json[i]['company_user_type'] == "2":
							company_user_type_show = "Master Admin"
						elif member_json[i]['company_user_type'] == "1":
							company_user_type_show = "Admin Company"
						else:
							company_user_type_show = "User Company"


						if member_json[i]['member_status'] == "1":
							if member_lang == "en":
								member_status_show = "Active"
							else:
								member_status_show = "เปิดใช้งาน"
						else:
							if member_lang == "en":
								member_status_show = "Inactive"
							else:
								member_status_show = "ปิดใช้งาน"

						member_list.append({
							"member_id" : member_json[i]['_id']['$oid'],
							"member_code": member_json[i]['member_code'],
							"member_fullname": member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en'],
							"member_tel": member_json[i]['member_tel'],
							"member_email": member_json[i]['member_email'],
							"company_user_type": member_json[i]['company_user_type'],
							"company_user_type_show": company_user_type_show,
							"member_status": member_json[i]['member_status'],
							"member_status_show": member_status_show
						})

				result = {
							"status" : True,
							"msg" : get_api_message("company_user_list" , "get_company_user_list_success" , member_lang), 
							"data" : member_list
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
	function_name = "company_user_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_user_form(request):
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

			company_user_type_list = [
										{"code": "2","name": "Master Admin"},
										{"code": "1","name": "Admin Company"},
										{"code": "0","name": "User Company"}
									]

			if member_lang == "en":
				member_status_1 = "Active"
				member_status_0 = "Inactive"
			else:
				member_status_1 = "เปิดใช้งาน"
				member_status_0 = "ปิดใช้งาน"

			member_status_list = [
									{"code": "1","name": member_status_1},
									{"code": "0","name": member_status_0}
								]

			result = {
						"status" : True,
						"msg" : get_api_message("get_company_user_form" , "get_company_user_form_success" , member_lang), 
						"company_user_type" : company_user_type_list,
						"member_status" : member_status_list
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
	function_name = "get_company_user_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_user_detail(mem_id,request):
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

			member = db.member.find_one({"_id": ObjectId(mem_id), "member_type" : "customer"})
			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_company_user_detail" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)	

				if member_lang == "en":
					member_firstname = member_json['member_firstname_en']
					member_lastname = member_json['member_lastname_en']
				else:
					member_firstname = member_json['member_firstname_th']
					member_lastname = member_json['member_lastname_th']

				if member_json['company_user_type'] == "2":
					company_user_type_show = "Master Admin"
				elif member_json['company_user_type'] == "1":
					company_user_type_show = "Admin Compamy"
				else:
					company_user_type_show = "User Company"

				if member_json['member_status'] == "1":
					if member_lang == "en":
						member_status_show = "Active"
					else:
						member_status_show = "เปิดใช้งาน"
				else:
					if member_lang == "en":
						member_status_show = "Inactive"
					else:
						member_status_show = "ปิดใช้งาน"

				data = {
							"member_id" : member_json['_id']['$oid'],
							"member_code": member_json['member_code'],
							"member_username": member_json['member_username'],
							"member_firstname": member_firstname,
							"member_lastname": member_lastname,
							"member_tel": member_json['member_tel'],
							"member_email": member_json['member_email'],
							"company_user_type": member_json['company_user_type'],
							"company_user_type_show": company_user_type_show,
							"member_status": member_json['member_status'],
							"member_status_show": member_status_show
						}

				result = {
							"status" : True,
							"msg" : get_api_message("get_company_user_detail" , "get_company_user_detail_success" , member_lang), 
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
	function_name = "get_company_user_detail"
	request_headers = request.headers
	params_get = {"member_id" : mem_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_company_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_username = "member_username" in params
	isset_member_firstname = "member_firstname" in params
	isset_member_lastname = "member_lastname" in params
	isset_member_email = "member_email" in params
	isset_member_tel = "member_tel" in params
	isset_company_user_type = "company_user_type" in params
	isset_member_status = "member_status" in params
	isset_os_type = "os_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_username and isset_member_firstname and isset_member_lastname and isset_member_email and isset_member_tel and isset_company_user_type and isset_member_status and isset_os_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check required
			if params['member_firstname']=="" or params['member_firstname'] is None:
				validate.append({"error_param" : "member_firstname","msg" : get_api_message("add_company_user" , "firstname_is_required" , member_lang)}) 
			if params['member_lastname']=="" or params['member_lastname'] is None:
				validate.append({"error_param" : "member_lastname","msg" : get_api_message("add_company_user" , "lastname_is_required" , member_lang)}) 
			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : get_api_message("add_company_user" , "email_is_required" , member_lang)}) 
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : get_api_message("add_company_user" , "tel_is_required" , member_lang)}) 
			if params['member_username']=="" or params['member_username'] is None:
				validate.append({"error_param" : "member_username","msg" : get_api_message("add_company_user" , "username_is_required" , member_lang)}) 
			if params['company_user_type']=="" or params['company_user_type'] is None:
				validate.append({"error_param" : "company_user_type","msg" : get_api_message("add_company_user" , "company_user_type_is_required" , member_lang)}) 

			#check already customer name
			if (params['member_firstname']!="" and params['member_firstname'] is not None) and (params['member_lastname']!="" and params['member_lastname'] is not None):
				check_customer_name = db.member.find({
														"member_type": "customer",
														"member_firstname_en": params['member_firstname'].strip().title(),
														"member_lastname_en": params['member_lastname'].strip().title()
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname","msg" : get_api_message("add_company_user" , "firstname_and_lastname_has_been_used" , member_lang)}) 
			
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
						validate.append({"error_param" : "member_email","msg" : get_api_message("add_company_user" , "email_has_been_used" , member_lang)}) 
				else:
					validate.append({"error_param" : "member_email","msg" : get_api_message("add_company_user" , "invalid_email_format" , member_lang)})		

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
					validate.append({"error_param" : "member_tel","msg" : get_api_message("add_company_user" , "invalid_tel_format" , member_lang)}) 

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
						validate.append({"error_param" : "member_username","msg" : get_api_message("add_company_user" , "username_has_been_used" , member_lang)}) 
				else:
					validate.append({"error_param" : "member_username","msg" : get_api_message("add_company_user" , "invalid_username_format" , member_lang)})

			#ถ้า validate ผ่าน
			if len(validate) == 0:
				#generate password
				generate_password = get_random_token(8)

				#เอา password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(generate_password.encode())
				hash_pass = hash_input_pass.hexdigest()

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
							"company_id": member_info['company_id'],
							"company_name": member_info['company_name'],
							"company_user_type": params['company_user_type'],
							"company_status": member_info['company_status'],
							"profile_image": None,
							"member_lang": member_lang,
							"member_status": params['member_status'],
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"approved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"member_token": None,
							"noti_key": None,
							"os_type": params['os_type'],
							"social_type": None,
							"social_id": None
						}

				if db.member.insert_one(data):
					# username = params['member_username'].lower()
					# password = generate_password
					# android_link = "https://play.google.com/store"
					# ios_link = "https://www.apple.com/th/ios/app-store/"

					# #send email
					# email_type = "register_success_normal"
					# subject = "VR Driver : สมัครสมาชิกสำเร็จ"
					# to_email = params['member_email'].lower()
					# template_html = "register_success_normal.html"
					# data_detail = { "username" : username, "password" : password, "android_link" : android_link , "ios_link" : ios_link }

					# data_email = { 
					# 				"email_type": email_type,
					# 				"data": data_detail,
					# 				"subject": subject,
					# 				"to_email": to_email,
					# 				"template_html": template_html,
					# 				"send_status": "0",
					# 				"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					# 				"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					# 			}
					# db.queue_email.insert_one(data_email)

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
								"msg" : get_api_message("add_company_user" , "add_customer_user_success" , member_lang) 
							}
				else:
					result = {
							"status" : False,
							"msg" : get_api_message("add_company_user" , "data_insert_failed" , member_lang) 
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("add_company_user" , "please_check_your_parameters_value" , member_lang), 
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
	function_name = "add_company_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_company_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_id = "member_id" in params
	isset_member_firstname = "member_firstname" in params
	isset_member_lastname = "member_lastname" in params
	isset_member_email = "member_email" in params
	isset_member_tel = "member_tel" in params
	isset_company_user_type = "company_user_type" in params
	isset_member_status = "member_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_id and isset_member_firstname and isset_member_lastname and isset_member_email and isset_member_tel and isset_company_user_type and isset_member_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			validate = []

			#check required
			if params['member_firstname']=="" or params['member_firstname'] is None:
				validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_company_user" , "firstname_is_required" , member_lang)}) 
			if params['member_lastname']=="" or params['member_lastname'] is None:
				validate.append({"error_param" : "member_lastname","msg" : get_api_message("edit_company_user" , "lastname_is_required" , member_lang)}) 
			if params['member_email']=="" or params['member_email'] is None:
				validate.append({"error_param" : "member_email","msg" : get_api_message("edit_company_user" , "email_is_required" , member_lang)}) 
			if params['member_tel']=="" or params['member_tel'] is None:
				validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_company_user" , "tel_is_required" , member_lang)}) 
			if params['company_user_type']=="" or params['company_user_type'] is None:
				validate.append({"error_param" : "company_user_type","msg" : get_api_message("edit_company_user" , "company_user_type_is_required" , member_lang)}) 

			#check already customer name
			if (params['member_firstname']!="" and params['member_firstname'] is not None) and (params['member_lastname']!="" and params['member_lastname'] is not None):
				#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
				check_customer_name = db.member.find({
														"_id": {"$ne": ObjectId(params['member_id'])},
														"member_token": {"$ne": token},
														"member_type": "customer",
														"member_firstname_en": params['member_firstname'].strip().title(),
														"member_lastname_en": params['member_lastname'].strip().title()
													}).count()
				if check_customer_name > 0:
					validate.append({"error_param" : "member_firstname","msg" : get_api_message("edit_company_user" , "firstname_and_lastname_has_been_used" , member_lang)}) 
			
			#check already email
			if params['member_email']!="" and params['member_email'] is not None:
				#check email format
				pattern = r'[a-z0-9._-]+@[a-z]+\.[a-z.]+'
				regex = re.compile(pattern)
				check_format_email = regex.findall(params['member_email'])

				if len(check_format_email) > 0:
					#เช็คค่าซ้ำที่ไม่ใช่ข้อมูลของตัวเอง
					check_email = db.member.find({
													"_id": {"$ne": ObjectId(params['member_id'])},
													"member_token": {"$ne": token},
													"member_type": "customer",
													"member_email": params['member_email'].strip().lower()
												}).count()
					if check_email > 0:
						validate.append({"error_param" : "member_email","msg" : get_api_message("edit_company_user" , "email_has_been_used" , member_lang)}) 
				else:
					validate.append({"error_param" : "member_email","msg" : get_api_message("edit_company_user" , "invalid_email_format" , member_lang)})

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
					validate.append({"error_param" : "member_tel","msg" : get_api_message("edit_company_user" , "invalid_tel_format" , member_lang)}) 

			
			#ถ้า validate ผ่าน
			if len(validate) == 0:
				# update data
				where_param = { "_id": ObjectId(params['member_id']) }
				value_param = {
								"$set":
									{
										"member_firstname_en": params['member_firstname'].strip().title(),
										"member_lastname_en": params['member_lastname'].strip().title(),
										"member_firstname_th": params['member_firstname'].strip().title(),
										"member_lastname_th": params['member_lastname'].strip().title(),
										"member_tel": params['member_tel'].strip(),
										"member_email": params['member_email'].strip().lower(),
										"company_user_type": params['company_user_type'],
										"member_status": params['member_status'],
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : get_api_message("edit_company_user" , "edit_customer_user_success" , member_lang) 
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("edit_company_user" , "data_update_failed" , member_lang) 
							}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("edit_company_user" , "please_check_your_parameters_value" , member_lang), 
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
	function_name = "edit_company_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def my_package_list_frontend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_type = "package_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if params['package_type'] == "all":
				member_package = db.member_package.find({
															"member_id": member_info['_id']['$oid'],
															"member_package_status": "1"
														})
			else:
				member_package = db.member_package.find({
															"member_id": member_info['_id']['$oid'],
															"package_type": params['package_type'],
															"member_package_status": "1"
														})

			member_package_list = []
			
			if member_package is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_package_object = dumps(member_package)
				member_package_json = json.loads(member_package_object)

				for i in range(len(member_package_json)):
					package_info = member_package_json[i]

					if member_lang == "en":
						package_name = member_package_json[i]['package_name_en']
					else:
						package_name = member_package_json[i]['package_name_th']

					if member_package_json[i]['package_model'] == "special":
						package_model = "Special"
					else:
						package_model = "Normal"

					if member_package_json[i]['package_type'] == "hour":
						if member_lang == "en":
							package_type_text = "Per Hour"
						else:
							package_type_text = "รายชั่วโมง"
					else:
						if member_lang == "en":
							package_type_text = "Per Time"
						else:
							package_type_text = "รายครั้ง"
					
					package_type_amount = member_package_json[i]['package_type_amount']

					if company_id is not None:
						package_admin = ""

						admin = db.package_admin.find_one({"company_package_id": member_package_json[i]['company_package_id']})
						
						if admin is not None:	
							# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							admin_object = dumps(admin)
							admin_json = json.loads(admin_object)

							if len(admin_json['package_admin']) > 0:
								for j in range(len(admin_json['package_admin'])):
									admin_info = get_member_info_by_id(admin_json['package_admin'][j])

									if j == 0:
										package_admin = admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']
									else:
										package_admin = package_admin+" , "+admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']

						package_usage_type = member_package_json[i]['package_usage_type']

						if package_usage_type == "quota":
							if member_lang == "en":
								package_usage_type_show = "Quota Package"
							else:
								package_usage_type_show = "Package แบ่ง"
						else:
							if member_lang == "en":
								package_usage_type_show = "Share Package"
							else:
								package_usage_type_show = "Package ร่วม"

					else:
						if member_lang == "en":
							package_usage_type_show = "Share Package"
						else:
							package_usage_type_show = "Package ร่วม"

						package_admin = ""
						package_usage_type = member_package_json[i]['package_usage_type']
						package_usage_type_show = package_usage_type_show

					end_date = datetime.strptime(member_package_json[i]['end_date'], '%Y-%m-%d')
					today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
					delta = end_date - today
					remaining_date = delta.days

					check_date = int((int(member_package_json[i]['total_usage_date']) * 10) / 100)

					if remaining_date >= check_date:
						remaining_date_10_percent = "1"
					else:
						remaining_date_10_percent = "0"

					if member_package_json[i]['package_usage_type'] == "share" and member_package_json[i]['company_package_id'] is not None:
						company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[i]['company_package_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						company_package_object = dumps(company_package)
						company_package_json = json.loads(company_package_object)

						remaining_amount = company_package_json['remaining_amount']
					else:
						remaining_amount = member_package_json[i]['remaining_amount']


					if remaining_date >= 0:
						member_package_list.append({
							"member_package_id" : member_package_json[i]['_id']['$oid'],
							"company_package_id" : member_package_json[i]['company_package_id'],
							"package_id": member_package_json[i]['package_id'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": member_package_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_type_amount": package_type_amount,
							"package_image": member_package_json[i]['package_image'],
							"remaining_date": remaining_date,
							"remaining_date_10_percent": remaining_date_10_percent,
							"remaining_amount": remaining_amount,
							"usage_amount": member_package_json[i]['usage_amount'],
							"total_amount": member_package_json[i]['total_amount'],
							"package_admin": package_admin,
							"package_usage_type": package_usage_type,
							"package_usage_type_show": package_usage_type_show
						})

				member_package_list.sort(key=lambda x: x.get('remaining_date'))

			result = {
						"status" : True,
						"msg" : get_api_message("my_package_list_frontend" , "get_my_package_list_success" , member_lang), 
						"data" : member_package_list
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
	function_name = "my_package_list_frontend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def package_list_frontend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_type = "package_type" in params
	isset_member_lang = "member_lang" in params

	if isset_accept and isset_content_type and isset_app_version and isset_package_type and isset_member_lang:
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

				if params['package_type'] == "hour":
					normal_package = db.package.find({
												"package_type": "hour",
												"package_status": "1",
												"special_company": {"$size": 0}
											}).sort([("created_at", -1)])
				elif params['package_type'] == "time":
					normal_package = db.package.find({
												"package_type": "time",
												"package_status": "1",
												"special_company": {"$size": 0}
											}).sort([("created_at", -1)])
				else:
					normal_package = db.package.find({
												"package_status": "1",
												"special_company": {"$size": 0}
											}).sort([("created_at", -1)])

				special_package = None

				#ถ้าเป็น company user
				if company_id is not None:
					if params['package_type'] == "hour":
						special_package = db.package.find({
															"package_type": "hour",
															"package_status": "1",
															"special_company": company_id
														}).sort([("created_at", -1)])
					elif params['package_type'] == "time":
						special_package = db.package.find({
															"package_type": "time",
															"package_status": "1",
															"special_company": company_id
														}).sort([("created_at", -1)])
					else:
						special_package = db.package.find({
															"package_status": "1",
															"special_company": company_id
														}).sort([("created_at", -1)])

				normal_package_list = []
				special_package_list = []
				
				if normal_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					normal_package_object = dumps(normal_package)
					normal_package_json = json.loads(normal_package_object)

					for i in range(len(normal_package_json)):
						if member_lang == "en":
							package_name = normal_package_json[i]['package_name_en']
						else:
							package_name = normal_package_json[i]['package_name_th']

						if normal_package_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if normal_package_json[i]['package_type'] == "hour":
							if member_lang == "en":
								package_type_text = "Per Hour"
							else:
								package_type_text = "รายชั่วโมง"
							package_type_amount = normal_package_json[i]['hour_amount']
						else:
							if member_lang == "en":
								package_type_text = "Per Time"
							else:
								package_type_text = "รายครั้ง"
							package_type_amount = normal_package_json[i]['time_amount']

						normal_package_list.append({
							"package_id" : normal_package_json[i]['_id']['$oid'],
							"package_code": normal_package_json[i]['package_code'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": normal_package_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_type_amount": package_type_amount,
							"package_price": "{:,}".format(int(normal_package_json[i]['package_price'])),
							"package_image": normal_package_json[i]['package_image']
						})

				if special_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					special_package_object = dumps(special_package)
					special_package_json = json.loads(special_package_object)

					for i in range(len(special_package_json)):
						if member_lang == "en":
							package_name = special_package_json[i]['package_name_en']
						else:
							package_name = special_package_json[i]['package_name_th']

						if special_package_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if special_package_json[i]['package_type'] == "hour":
							if member_lang == "en":
								package_type_text = "Per Hour"
							else:
								package_type_text = "รายชั่วโมง"
							package_type_amount = special_package_json[i]['hour_amount']
						else:
							if member_lang == "en":
								package_type_text = "Per Time"
							else:
								package_type_text = "รายครั้ง"
							package_type_amount = special_package_json[i]['time_amount']

						special_package_list.append({
							"package_id" : special_package_json[i]['_id']['$oid'],
							"package_code": special_package_json[i]['package_code'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": special_package_json[i]['package_type'],
							"package_type_text": package_type_text,
							"package_type_amount": package_type_amount,
							"package_price": "{:,}".format(int(special_package_json[i]['package_price'])),
							"package_image": special_package_json[i]['package_image']
						})

				result = {
							"status" : True,
							"msg" : get_api_message("package_list_frontend" , "get_package_list_success" , member_lang), 
							"normal_package" : normal_package_list,
							"special_package" : special_package_list
						}
			else:
				result = { 
							"status" : False,
							"error_code" : 401,
							"msg" : get_api_message("all" , "unauthorized")
						}	
		#guest
		else:
			if params['package_type'] == "hour":
				normal_package = db.package.find({
											"package_type": "hour",
											"package_status": "1",
											"special_company": {"$size": 0}
										}).sort([("created_at", -1)])
			elif params['package_type'] == "time":
				normal_package = db.package.find({
											"package_type": "time",
											"package_status": "1",
											"special_company": {"$size": 0}
										}).sort([("created_at", -1)])
			else:
				normal_package = db.package.find({
											"package_status": "1",
											"special_company": {"$size": 0}
										}).sort([("created_at", -1)])

			normal_package_list = []
			special_package_list = []
			
			if normal_package is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				normal_package_object = dumps(normal_package)
				normal_package_json = json.loads(normal_package_object)

				for i in range(len(normal_package_json)):
					if member_lang == "en":
						package_name = normal_package_json[i]['package_name_en']
					else:
						package_name = normal_package_json[i]['package_name_th']

					if normal_package_json[i]['package_model'] == "special":
						package_model = "Special"
					else:
						package_model = "Normal"

					if normal_package_json[i]['package_type'] == "hour":
						if member_lang == "en":
							package_type_text = "Per Hour"
						else:
							package_type_text = "รายชั่วโมง"
						package_type_amount = normal_package_json[i]['hour_amount']
					else:
						if member_lang == "en":
							package_type_text = "Per Time"
						else:
							package_type_text = "รายครั้ง"
						package_type_amount = normal_package_json[i]['time_amount']

					normal_package_list.append({
						"package_id" : normal_package_json[i]['_id']['$oid'],
						"package_code": normal_package_json[i]['package_code'],
						"package_name": package_name,
						"package_model": package_model,
						"package_type": normal_package_json[i]['package_type'],
						"package_type_text": package_type_text,
						"package_type_amount": package_type_amount,
						"package_price": "{:,}".format(int(normal_package_json[i]['package_price'])),
						"package_image": normal_package_json[i]['package_image']
					})

			result = {
						"status" : True,
						"msg" : get_api_message("package_list_frontend" , "get_package_list_success" , member_lang),
						"normal_package" : normal_package_list,
						"special_package" : special_package_list
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "package_list_frontend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_admin(request):
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

			member = db.member.find({
										"company_id": member_info['company_id'],
										"member_type": "customer",
										"company_user_type": {"$in" : ["1"]},
										"member_status": "1"
									})

			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_company_admin" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				member_list = []

				for i in range(len(member_json)):
					member_list.append({
						"value" : member_json[i]['_id']['$oid'],
						"label": member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']
					})

				result = {
							"status" : True,
							"msg" : get_api_message("get_company_admin" , "get_company_admin_success" , member_lang),
							"data" : member_list
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
	function_name = "get_company_admin"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_user(request):
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

			member = db.member.find({
										"company_id": member_info['company_id'],
										"member_type": "customer",
										"member_status": "1"
									})

			if member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_company_user" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)

				member_list = []

				for i in range(len(member_json)):
					member_list.append({
						"value" : member_json[i]['_id']['$oid'],
						"label": member_json[i]['member_firstname_en']+" "+member_json[i]['member_lastname_en']
					})

				result = {
							"status" : True,
							"msg" : get_api_message("get_company_user" , "get_company_user_success" , member_lang), 
							"data" : member_list
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
	function_name = "get_company_user"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_admin(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			package_admin = db.package_admin.find_one({"company_package_id": params['company_package_id']})
			
			package_admin_list = []

			if package_admin is None:
				company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)	

				data = { 
							"company_package_id": params['company_package_id'],
							"package_admin": [],
							"package_id": company_package_json['package_id'],
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}
				db.package_admin.insert_one(data)
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_admin_object = dumps(package_admin)
				package_admin_json = json.loads(package_admin_object)	

				for i in range(len(package_admin_json['package_admin'])):
					admin_info = get_member_info_by_id(package_admin_json['package_admin'][i])

					package_admin_list.append({
												"value" : package_admin_json['package_admin'][i],
												"label" : admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']
											})

			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			company_package_object = dumps(company_package)
			company_package_json = json.loads(company_package_object)

			if member_lang == "en":
				package_name = company_package_json['package_name_en']
			else:
				package_name = company_package_json['package_name_th']

			if company_package_json['package_model'] == "special":
				package_model = "Special"
			else:
				package_model = "Normal"

			if company_package_json['package_type'] == "hour":
				if member_lang == "en":
					package_type_text = "Per Hour"
				else:
					package_type_text = "รายชั่วโมง"
			else:
				if member_lang == "en":
					package_type_text = "Per Time"
				else:
					package_type_text = "รายครั้ง"
			package_type_amount = company_package_json['total_amount']

			end_date = datetime.strptime(company_package_json['end_date'], '%Y-%m-%d')
			today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
			delta = end_date - today
			remaining_date = delta.days

			check_date = int((int(company_package_json['total_usage_date']) * 10) / 100)

			if remaining_date >= check_date:
				remaining_date_10_percent = "1"
			else:
				remaining_date_10_percent = "0"

			data = {
						"company_package_id" : params['company_package_id'],
						"package_id": company_package_json['package_id'],
						"package_name": package_name,
						"package_model": package_model,
						"package_type": company_package_json['package_type'],
						"package_type_text": package_type_text,
						"package_type_amount": package_type_amount,
						"remaining_date": remaining_date,
						"remaining_date_10_percent": remaining_date_10_percent,
						"remaining_amount": company_package_json['remaining_amount'],
						"package_admin": package_admin_list
					}

			result = {
						"status" : True,
						"msg" : get_api_message("get_package_admin" , "get_package_admin_success" , member_lang), 
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
	function_name = "get_package_admin"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def assign_package_admin(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params
	isset_package_admin = "package_admin" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id and isset_package_admin:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			package_admin_list = []

			for i in range(len(params['package_admin'])):
				package_admin_list.append(params['package_admin'][i]['value'])

			# update data
			where_param = { "company_package_id": params['company_package_id'] }
			value_param = {
							"$set":
								{
									"package_admin": package_admin_list,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.package_admin.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("assign_package_admin" , "assign_package_admin_success" , member_lang),
							"package_admin_list" : package_admin_list 
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("assign_package_admin" , "data_update_failed" , member_lang) 
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
	function_name = "assign_package_admin"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			
			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})

			if company_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_package_user" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)	

				package_admin = ""

				#ดึงชื่อ package admin
				admin = db.package_admin.find_one({"company_package_id": params['company_package_id']})
			
				if admin is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					admin_object = dumps(admin)
					admin_json = json.loads(admin_object)

					for j in range(len(admin_json['package_admin'])):
						admin_info = get_member_info_by_id(admin_json['package_admin'][j])

						if j == 0:
							package_admin = admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']
						else:
							package_admin = package_admin+" , "+admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']

				package_info = get_package_info(company_package_json['package_id'])

				if member_lang == "en":
					package_name = package_info['package_name_en']
				else:
					package_name = package_info['package_name_th']

				if package_info['package_model'] == "special":
					package_model = "Special"
				else:
					package_model = "Normal"

				if package_info['package_type'] == "hour":
					if member_lang == "en":
						package_type_text = "Per Hour"
					else:
						package_type_text = "รายชั่วโมง"

					#*****
					total_amount = company_package_json['total_amount']
				else:
					if member_lang == "en":
						package_type_text = "Per Time"
					else:
						package_type_text = "รายครั้ง"

					#*****
					total_amount = company_package_json['total_amount']

				end_date = datetime.strptime(company_package_json['end_date'], '%Y-%m-%d')
				today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
				delta = end_date - today
				remaining_date = delta.days

				check_date = int((int(company_package_json['total_usage_date']) * 10) / 100)

				if remaining_date >= check_date:
					remaining_date_10_percent = "1"
				else:
					remaining_date_10_percent = "0"

				member_package = db.member_package.find({
															"$or": [
																{ "member_package_status": "1" },
																{ "usage_amount" : {"$gt" : 0} }
															],
															"company_package_id": params['company_package_id']
														})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_package_object = dumps(member_package)
				member_package_json = json.loads(member_package_object)	

				package_user_list = []
				usage_amount = 0
				remaining_amount = 0
				assign_amount = 0
				unassign_amount = 0
				package_usage_type = company_package_json['package_usage_type']

				for i in range(len(member_package_json)):
					user_info = get_member_info_by_id(member_package_json[i]['member_id'])
					# เซ็ตค่าว่าเป็น package แบบแบ่ง หรือ แบบร่วม
					package_usage_type = member_package_json[i]['package_usage_type']

					user_total_amount = member_package_json[i]['total_amount']
					user_usage_amount = member_package_json[i]['usage_amount']
					user_remaining_amount = member_package_json[i]['remaining_amount']

					if package_usage_type == "quota":
						assign_amount = assign_amount + member_package_json[i]['total_amount']
					else:
						assign_amount = None 

					package_user_list.append({
												"member_package_id": member_package_json[i]['_id']['$oid'],
												"member_id" : member_package_json[i]['member_id'],
												"member_fullname" : user_info['member_firstname_en']+" "+user_info['member_lastname_en'],
												"total_amount": user_total_amount,
												"usage_amount": user_usage_amount,
												"remaining_amount": user_remaining_amount
											})
					
					usage_amount = usage_amount + member_package_json[i]['usage_amount']
					
				if package_usage_type == "quota":
					unassign_amount = total_amount - assign_amount
				else:
					unassign_amount = None

				remaining_amount = company_package_json['remaining_amount']
				
				data = {
							"company_package_id" : company_package_json['_id']['$oid'],
							"package_id": company_package_json['package_id'],
							"package_name": package_name,
							"package_model": package_model,
							"package_type": package_info['package_type'],
							"package_type_text": package_type_text,
							"package_usage_type": package_usage_type,
							"total_amount": total_amount,
							"usage_amount": usage_amount,
							"remaining_amount": remaining_amount,
							"assign_amount": assign_amount,
							"unassign_amount": unassign_amount,
							"remaining_date": remaining_date,
							"remaining_date_10_percent": remaining_date_10_percent,
							"package_admin": package_admin,
							"package_user": package_user_list
						}

				result = {
							"status" : True,
							"msg" : get_api_message("get_package_user" , "get_package_user_success" , member_lang),
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
	function_name = "get_package_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

# def add_package_user(request):
# 	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_accept = "Accept" in request.headers
# 	isset_content_type = "Content-Type" in request.headers
# 	isset_token = "Authorization" in request.headers
# 	member_id = None

# 	params = json.loads(request.data)

# 	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
# 	isset_app_version = "app_version" in params
# 	isset_company_package_id = "company_package_id" in params
# 	isset_package_usage_type = "package_usage_type" in params
# 	isset_member_id = "member_id" in params

# 	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id and isset_package_usage_type and isset_member_id:
# 		#เช็ค token ว่า expire แล้วหรือยัง
# 		token = request.headers['Authorization']
# 		check_token = check_token_expire(token)

# 		if check_token:
# 			member_info = get_member_info(token)
# 			member_lang = member_info['member_lang']
# 			member_id = member_info['_id']['$oid']
# 			member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']

# 			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})

# 			if company_package is None:
# 				result = { 
# 							"status" : False,
# 							"msg" : get_api_message("add_package_user" , "data_not_found" , member_lang) 
# 						}
# 			else:
# 				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 				company_package_object = dumps(company_package)
# 				company_package_json = json.loads(company_package_object)
# 				order_id = company_package_json['order_id']
# 				order_no = company_package_json['order_no']
# 				package_amount = company_package_json['package_amount']

# 				#ดึงข้อมูลจาก tb member_package ที่มี company_package_id ตรงกับ company_package_id ที่ส่งเข้ามา
# 				member_package = db.member_package.find_one({
# 																"company_package_id": params['company_package_id'],
# 																"member_id": params['member_id']
# 															})

# 				if member_package is None:
# 					#เช็คว่า package_usage_type จาก tb member_package ตรงกับ package_usage_type ที่ส่งเข้ามาหรือไม่
# 					#ถ้าตรง ให้เช็คต่อ
# 					if company_package_json['package_usage_type'] == params['package_usage_type']:
# 						#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
# 						member_package_id = ObjectId()
# 						#แปลง ObjectId ให้เป็น string
# 						member_package_id_string = str(member_package_id)

# 						end_date_int = int(datetime.strptime(company_package_json['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
# 						member_package_info = get_member_info_by_id(params['member_id'])
						
# 						data = { 
# 									"_id": member_package_id,
# 									"order_id": order_id,
# 									"order_no": order_no,
# 									"order_date": company_package_json['order_date'],
# 									"company_package_id": params['company_package_id'],
# 									"company_id": member_info['company_id'],
# 									"member_id": params['member_id'],
# 									"member_name": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
# 									"package_id": company_package_json['package_id'],
									
# 									"package_code": company_package_json['package_code'],
# 									"package_type": company_package_json['package_type'],
# 									"package_type_amount": company_package_json['total_amount'],
# 									"package_name_en": company_package_json['package_name_en'],
# 									"package_name_th": company_package_json['package_name_th'],
# 									"package_detail_en": company_package_json['package_detail_en'],
# 									"package_detail_th": company_package_json['package_detail_th'],
# 									"package_condition_en": company_package_json['package_condition_en'],
# 									"package_condition_th": company_package_json['package_condition_th'],
# 									"package_model": company_package_json['package_model'],
# 									"total_usage_date": company_package_json['total_usage_date'],
# 									"special_company": company_package_json['special_company'],
# 									"service_time": company_package_json['service_time'],
# 									"driver_level": company_package_json['driver_level'],
# 									"communication": company_package_json['communication'],
# 									"communication_en": company_package_json['communication_en'],
# 									"communication_th": company_package_json['communication_th'],
# 									"normal_paid_rate": float(company_package_json['normal_paid_rate']),
# 									"normal_received_rate": float(company_package_json['normal_received_rate']),
# 									"overtime_paid_rate": float(company_package_json['overtime_paid_rate']),
# 									"overtime_received_rate": float(company_package_json['overtime_received_rate']),
# 									"package_image": company_package_json['package_image'],
# 									"package_price": float(company_package_json['package_price']),
# 									"package_price_not_vat": float(company_package_json['package_price_not_vat']),
# 									"package_price_vat": float(company_package_json['package_price_vat']),
# 									"vat_rate": float(company_package_json['vat_rate']),

# 									"package_usage_type": params['package_usage_type'],
# 									"package_amount": package_amount,
# 									"total_amount": 0,
# 									"usage_amount": 0,
# 									"remaining_amount": 0,
# 									"member_package_status": "1",
# 									"start_date": company_package_json['start_date'],
# 									"end_date": company_package_json['end_date'],
# 									"end_date_int": end_date_int,
# 									"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
# 									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 								}

# 						if db.member_package.insert_one(data):
# 							result = {
# 										"status" : True,
# 										"msg" : get_api_message("add_package_user" , "add_package_user_success" , member_lang), 
# 										"package_user": {
# 															"member_package_id": member_package_id_string,
# 															"member_id": params['member_id'],
# 															"member_fullname": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
# 															"usage_amount": 0,
# 															"remaining_amount": 0
# 														}
# 									}
# 						else:
# 							result = {
# 										"status" : False,
# 										"msg" : get_api_message("add_package_user" , "data_insert_failed" , member_lang) 
# 									}
# 					else:
# 						result = { 
# 							"status" : False,
# 							"msg" : get_api_message("add_package_user" , "can_not_insert_package_user_please_check_package_usage_type_value" , member_lang) 
# 						}
# 				else:
# 					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
# 					member_package_object = dumps(member_package)
# 					member_package_json = json.loads(member_package_object)

# 					#ถ้า member_package_status = 1 แสดงว่าเคย assign แล้ว ให้ฟ้อง error กลับไปว่ามีข้อมูลผู้ใช้นี้แล้ว
# 					if member_package_json['member_package_status'] == "1":
# 						result = { 
# 									"status" : False,
# 									"msg" : get_api_message("add_package_user" , "can_not_insert_package_user_because_it_already_has_a_user" , member_lang) 
# 								}	
# 					#ถ้า member_package_status = 0 แสดงว่าเคยถูกลบ ให้อัพเดต member_package_status กลับมาเป็น 1
# 					else:
# 						member_package_info = get_member_info_by_id(params['member_id'])

# 						# update data
# 						where_param = { "_id": ObjectId(member_package_json['_id']['$oid']) }
# 						value_param = {
# 										"$set":
# 											{
# 												"package_usage_type": params['package_usage_type'],
# 												"total_amount": 0,
# 												"usage_amount": 0,
# 												"remaining_amount": 0,
# 												"member_package_status": "1",
# 												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 											}
# 									}

# 						if db.member_package.update(where_param , value_param):
# 							result = {
# 										"status" : True,
# 										"msg" : get_api_message("add_package_user" , "add_package_user_success" , member_lang), 
# 										"package_user": {
# 															"member_package_id": member_package_json['_id']['$oid'],
# 															"member_id": params['member_id'],
# 															"member_fullname": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
# 															"usage_amount": 0,
# 															"remaining_amount": 0
# 														}
# 									}
# 						else:
# 							result = {
# 										"status" : False,
# 										"msg" : get_api_message("add_package_user" , "data_update_failed" , member_lang) 
# 									}			
# 		else:
# 			result = { 
# 						"status" : False,
# 						"error_code" : 401,
# 						"msg" : get_api_message("all" , "unauthorized")
# 					}
# 	else:
# 		result = { 
# 					"status" : False,
# 					"msg" : get_api_message("all" , "please_check_your_parameters")
# 				}

# 	#set log detail
# 	user_type = "customer"
# 	function_name = "add_package_user"
# 	request_headers = request.headers
# 	params_get = None
# 	params_post = params
# 	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

# 	return result

#last update 2021-02-02
def add_package_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params
	isset_package_usage_type = "package_usage_type" in params
	isset_member_id = "member_id" in params
	isset_remaining_amount = "remaining_amount" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id and isset_package_usage_type and isset_member_id and isset_remaining_amount:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']

			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})

			if company_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("add_package_user" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)
				order_id = company_package_json['order_id']
				order_no = company_package_json['order_no']
				package_amount = company_package_json['package_amount']

				#ดึงข้อมูลจาก tb member_package ที่มี company_package_id ตรงกับ company_package_id ที่ส่งเข้ามา
				member_package = db.member_package.find_one({
																"company_package_id": params['company_package_id'],
																"member_id": params['member_id']
															})

				if member_package is None:
					#เช็คว่า package_usage_type จาก tb member_package ตรงกับ package_usage_type ที่ส่งเข้ามาหรือไม่
					#ถ้าตรง ให้เช็คต่อ
					if company_package_json['package_usage_type'] == params['package_usage_type']:
						#ดึงข้อมูลจาก tb member_package ที่มี company_package_id เท่ากับ company_package_id ที่ส่งเข้ามา
						mp = db.member_package.find({"company_package_id": params['company_package_id']})
						
						if mp is None:
							result = { 
										"status" : False,
										"msg" : get_api_message("add_package_user" , "member_package_not_found" , member_lang) 
									}
						else:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							mp_object = dumps(mp)
							mp_json = json.loads(mp_object)

							total_amount = 0
							assign_amount = 0
							usage_amount = 0
							remaining_amount = 0
							unassign_amount = 0
							max_assign_amount = 0

							#วน loop sum ค่า usage_amount และ remaining_amount
							#จะรู้ค่า sum_total_amount , sum_usage_amount , sum_remaining_amount และ unassign_amount
							#ex. sum_total_amount = 25 , sum_usage_amount = 16 , sum_remaining_amount = 4 
							for i in range(len(mp_json)):
								assign_amount = assign_amount + mp_json[i]['total_amount']
								usage_amount = usage_amount + mp_json[i]['usage_amount']

							if params['package_usage_type'] == "quota":
								# unassign_amount = total_amount(ของ package) - assign_amount -> 30 - 25 = 5
								# max_assign_amount = remaining_amount(ล่าสุดของ user นั้น) + unassign_amount -> 4 + 5 = 9
								total_amount = company_package['total_amount']
								remaining_amount = total_amount - usage_amount
								unassign_amount = total_amount - assign_amount
								max_assign_amount = 0 + unassign_amount

								#ถ้า max_assign_amount >= remaining_amount ที่ส่งเข้ามา ถึงจะอัพเดตได้
								remaining_amount = int(params['remaining_amount'])

								if max_assign_amount >= remaining_amount:
									diff_amount = remaining_amount - 0
									user_total_amount = 0 + diff_amount
									user_remaining_amount = 0 + diff_amount

									last_assign_amount = assign_amount + diff_amount
									last_unassign_amount = unassign_amount - diff_amount

									if user_remaining_amount == 0:
										member_package_status = "0"
									else:
										member_package_status = "1"

									mp_total_amount = user_total_amount
									mp_usage_amount = 0
									mp_remaining_amount = user_remaining_amount

								# แต่ถ้า max_assign_amount < remaining_amount ที่ส่งเข้ามา จะฟ้องกลับไป
								else:
									mp_total_amount = None
									mp_usage_amount = None
									mp_remaining_amount = None
							else:
								total_amount = company_package['total_amount']
								remaining_amount = total_amount - usage_amount
								last_assign_amount = 0
								last_unassign_amount = 0

								mp_total_amount = 0
								mp_usage_amount = 0
								mp_remaining_amount = 0						

						if mp_total_amount is None and mp_usage_amount is None and mp_remaining_amount is None:
							result = {
										"status" : False,
										"msg" : get_api_message("add_package_user" , "please_check_remaining_amount" , member_lang)
									}
						else:
							#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
							member_package_id = ObjectId()
							#แปลง ObjectId ให้เป็น string
							member_package_id_string = str(member_package_id)

							end_date_int = int(datetime.strptime(company_package_json['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
							member_package_info = get_member_info_by_id(params['member_id'])
							
							data = { 
										"_id": member_package_id,
										"order_id": order_id,
										"order_no": order_no,
										"order_date": company_package_json['order_date'],
										"company_package_id": params['company_package_id'],
										"company_id": member_info['company_id'],
										"member_id": params['member_id'],
										"member_name": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
										"package_id": company_package_json['package_id'],
										
										"package_code": company_package_json['package_code'],
										"package_type": company_package_json['package_type'],
										"package_type_amount": company_package_json['total_amount'],
										"package_name_en": company_package_json['package_name_en'],
										"package_name_th": company_package_json['package_name_th'],
										"package_detail_en": company_package_json['package_detail_en'],
										"package_detail_th": company_package_json['package_detail_th'],
										"package_condition_en": company_package_json['package_condition_en'],
										"package_condition_th": company_package_json['package_condition_th'],
										"package_model": company_package_json['package_model'],
										"total_usage_date": company_package_json['total_usage_date'],
										"special_company": company_package_json['special_company'],
										"service_time": company_package_json['service_time'],
										"driver_level": company_package_json['driver_level'],
										"communication": company_package_json['communication'],
										"communication_en": company_package_json['communication_en'],
										"communication_th": company_package_json['communication_th'],
										"normal_paid_rate": float(company_package_json['normal_paid_rate']),
										"normal_received_rate": float(company_package_json['normal_received_rate']),
										"overtime_paid_rate": float(company_package_json['overtime_paid_rate']),
										"overtime_received_rate": float(company_package_json['overtime_received_rate']),
										"package_image": company_package_json['package_image'],
										"package_price": float(company_package_json['package_price']),
										"package_price_not_vat": float(company_package_json['package_price_not_vat']),
										"package_price_vat": float(company_package_json['package_price_vat']),
										"vat_rate": float(company_package_json['vat_rate']),

										"package_usage_type": params['package_usage_type'],
										"package_amount": package_amount,
										"total_amount": mp_total_amount,
										"usage_amount": mp_usage_amount,
										"remaining_amount": mp_remaining_amount,
										"member_package_status": "1",
										"start_date": company_package_json['start_date'],
										"end_date": company_package_json['end_date'],
										"end_date_int": end_date_int,
										"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}

							if db.member_package.insert_one(data):
								result = {
											"status" : True,
											"msg" : get_api_message("add_package_user" , "add_package_user_success" , member_lang), 
											"package_user": {
																"member_package_id": member_package_id_string,
																"member_id": params['member_id'],
																"member_fullname": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
																"total_amount": mp_total_amount,
																"usage_amount": mp_usage_amount,
																"remaining_amount": mp_remaining_amount
															},
											"total_amount" : total_amount, #package ทั้งหมด
											"usage_amount" : usage_amount, #package ที่ถูกใช้ไปแล้ว
											"remaining_amount" : remaining_amount,
											"assign_amount" : last_assign_amount, #package ที่ assign ไปแล้ว
											"unassign_amount" : last_unassign_amount, #package ยังไม่ได้ assign
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("add_package_user" , "data_insert_failed" , member_lang) 
										}
					else:
						result = { 
							"status" : False,
							"msg" : get_api_message("add_package_user" , "can_not_insert_package_user_please_check_package_usage_type_value" , member_lang) 
						}
				else:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)

					#ถ้า member_package_status = 1 แสดงว่าเคย assign แล้ว ให้ฟ้อง error กลับไปว่ามีข้อมูลผู้ใช้นี้แล้ว
					if member_package_json['member_package_status'] == "1":
						result = { 
									"status" : False,
									"msg" : get_api_message("add_package_user" , "can_not_insert_package_user_because_it_already_has_a_user" , member_lang)
								}	
					#ถ้า member_package_status = 0 แสดงว่าเคยถูกลบ ให้อัพเดต member_package_status กลับมาเป็น 1
					else:
						#ดึงข้อมูลจาก tb member_package ที่มี company_package_id เท่ากับ company_package_id ที่ส่งเข้ามา
						mp = db.member_package.find({"company_package_id": params['company_package_id']})
						
						if mp is None:
							result = { 
										"status" : False,
										"msg" : get_api_message("add_package_user" , "member_package_not_found" , member_lang) 
									}
						else:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							mp_object = dumps(mp)
							mp_json = json.loads(mp_object)

							total_amount = 0
							assign_amount = 0
							usage_amount = 0
							remaining_amount = 0
							unassign_amount = 0
							max_assign_amount = 0

							#วน loop sum ค่า usage_amount และ remaining_amount
							#จะรู้ค่า sum_total_amount , sum_usage_amount , sum_remaining_amount และ unassign_amount
							#ex. sum_total_amount = 25 , sum_usage_amount = 16 , sum_remaining_amount = 4 
							for i in range(len(mp_json)):
								assign_amount = assign_amount + mp_json[i]['total_amount']
								usage_amount = usage_amount + mp_json[i]['usage_amount']

							if params['package_usage_type'] == "quota":
								check_package = db.member_package.find_one({"_id": ObjectId(member_package_json['_id']['$oid'])})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								check_package_object = dumps(check_package)
								check_package_json = json.loads(check_package_object)

								# unassign_amount = total_amount(ของ package) - assign_amount -> 30 - 25 = 5
								# max_assign_amount = remaining_amount(ล่าสุดของ user นั้น) + unassign_amount -> 4 + 5 = 9
								total_amount = company_package['total_amount']
								remaining_amount = total_amount - usage_amount
								unassign_amount = total_amount - assign_amount
								max_assign_amount = check_package_json['remaining_amount'] + unassign_amount

								#ถ้า max_assign_amount >= remaining_amount ที่ส่งเข้ามา ถึงจะอัพเดตได้
								remaining_amount = int(params['remaining_amount'])

								if max_assign_amount >= remaining_amount:
									diff_amount = remaining_amount - check_package_json['remaining_amount']
									user_total_amount = check_package_json['total_amount'] + diff_amount
									user_remaining_amount = check_package_json['remaining_amount'] + diff_amount

									last_assign_amount = assign_amount + diff_amount
									last_unassign_amount = unassign_amount - diff_amount

									if user_remaining_amount == 0:
										member_package_status = "0"
									else:
										member_package_status = "1"

									mp_total_amount = user_total_amount
									mp_usage_amount = member_package_json['usage_amount']
									mp_remaining_amount = user_remaining_amount

								# แต่ถ้า max_assign_amount < remaining_amount ที่ส่งเข้ามา จะฟ้องกลับไป
								else:
									mp_total_amount = None
									mp_usage_amount = None
									mp_remaining_amount = None
							else:
								total_amount = company_package['total_amount']
								remaining_amount = total_amount - usage_amount
								last_assign_amount = 0
								last_unassign_amount = 0

								mp_total_amount = 0
								mp_usage_amount = member_package_json['usage_amount']
								mp_remaining_amount = 0

						if mp_total_amount is None and mp_usage_amount is None and mp_remaining_amount is None:
							result = {
										"status" : False,
										"msg" : get_api_message("add_package_user" , "please_check_remaining_amount" , member_lang)
									}
						else:
							member_package_info = get_member_info_by_id(params['member_id'])

							# update data
							where_param = { "_id": ObjectId(member_package_json['_id']['$oid']) }
							value_param = {
											"$set":
												{
													"package_usage_type": params['package_usage_type'],
													"total_amount": mp_total_amount,
													"usage_amount": mp_usage_amount,
													"remaining_amount": mp_remaining_amount,
													"member_package_status": "1",
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.member_package.update(where_param , value_param):
								result = {
											"status" : True,
											"msg" : get_api_message("add_package_user" , "add_package_user_success" , member_lang), 
											"package_user": {
																"member_package_id": member_package_json['_id']['$oid'],
																"member_id": params['member_id'],
																"member_fullname": member_package_info['member_firstname_en']+" "+member_package_info['member_lastname_en'],
																"total_amount": mp_total_amount,
																"usage_amount": mp_usage_amount,
																"remaining_amount": mp_remaining_amount
															},
											"total_amount" : total_amount, #package ทั้งหมด
											"usage_amount" : usage_amount, #package ที่ถูกใช้ไปแล้ว
											"remaining_amount" : remaining_amount,
											"assign_amount" : last_assign_amount, #package ที่ assign ไปแล้ว
											"unassign_amount" : last_unassign_amount, #package ยังไม่ได้ assign
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("add_package_user" , "data_update_failed" , member_lang) 
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
	function_name = "add_package_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_package_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params
	isset_member_package_id = "member_package_id" in params
	isset_remaining_amount = "remaining_amount" in params
	isset_member_id = "member_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_company_package_id and isset_member_package_id and isset_remaining_amount and isset_member_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})

			if company_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("edit_package_user" , "company_package_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				company_package_object = dumps(company_package)
				company_package_json = json.loads(company_package_object)

				#ถ้า package_usage_type จาก tb company_package เท่ากับ quota ถึงจะอัพเดตได้
				if company_package_json['package_usage_type'] == "quota":
					#ดึงข้อมูลจาก tb member_package ที่มี company_package_id เท่ากับ company_package_id ที่ส่งเข้ามา
					member_package = db.member_package.find({"company_package_id": params['company_package_id']})
					
					if member_package is None:
						result = { 
									"status" : False,
									"msg" : get_api_message("edit_package_user" , "member_package_not_found" , member_lang) 
								}
					else:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						member_package_object = dumps(member_package)
						member_package_json = json.loads(member_package_object)

						total_amount = 0
						assign_amount = 0
						usage_amount = 0
						remaining_amount = 0
						unassign_amount = 0
						max_assign_amount = 0

						#วน loop sum ค่า usage_amount และ remaining_amount
						#จะรู้ค่า sum_total_amount , sum_usage_amount , sum_remaining_amount และ unassign_amount
						#ex. sum_total_amount = 25 , sum_usage_amount = 16 , sum_remaining_amount = 4 
						for i in range(len(member_package_json)):
							assign_amount = assign_amount + member_package_json[i]['total_amount']
							usage_amount = usage_amount + member_package_json[i]['usage_amount']

						check_package = db.member_package.find_one({"_id": ObjectId(params['member_package_id'])})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						check_package_object = dumps(check_package)
						check_package_json = json.loads(check_package_object)

						# unassign_amount = total_amount(ของ package) - assign_amount -> 30 - 25 = 5
						# max_assign_amount = remaining_amount(ล่าสุดของ user นั้น) + unassign_amount -> 4 + 5 = 9
						total_amount = company_package['total_amount']
						remaining_amount = total_amount - usage_amount
						unassign_amount = total_amount - assign_amount
						max_assign_amount = check_package_json['remaining_amount'] + unassign_amount

						#ถ้า max_assign_amount >= remaining_amount ที่ส่งเข้ามา ถึงจะอัพเดตได้
						remaining_amount = int(params['remaining_amount'])

						if max_assign_amount >= remaining_amount:
							diff_amount = remaining_amount - check_package_json['remaining_amount']
							user_total_amount = check_package_json['total_amount'] + diff_amount
							user_remaining_amount = check_package_json['remaining_amount'] + diff_amount

							last_assign_amount = assign_amount + diff_amount
							last_unassign_amount = unassign_amount - diff_amount

							if user_remaining_amount == 0:
								member_package_status = "0"
							else:
								member_package_status = "1"

							# update data
							where_param = { "_id": ObjectId(params['member_package_id']) }
							value_param = {
											"$set":
												{
													"total_amount": user_total_amount,
													"remaining_amount": user_remaining_amount,
													"member_package_status": member_package_status, 
													"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
												}
										}

							if db.member_package.update(where_param , value_param):
								result = {
											"status" : True,
											"msg" : get_api_message("edit_package_user" , "edit_package_user_success" , member_lang), 
											"total_amount" : total_amount, #package ทั้งหมด
											"usage_amount" : usage_amount, #package ที่ถูกใช้ไปแล้ว
											"remaining_amount" : remaining_amount,
											"assign_amount" : last_assign_amount, #package ที่ assign ไปแล้ว
											"unassign_amount" : last_unassign_amount, #package ยังไม่ได้ assign
											# "diff_amount" : diff_amount
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("edit_package_user" , "data_update_failed" , member_lang) 
										}
						# แต่ถ้า max_assign_amount < remaining_amount ที่ส่งเข้ามา จะฟ้องกลับไป
						else:
							result = {
										"status" : False,
										"msg" : get_api_message("edit_package_user" , "please_check_remaining_amount" , member_lang) 
									}
				else:
					result = { 
								"status" : False,
								"msg" : get_api_message("edit_package_user" , "can_not_update_package_user_please_check_package_usage_type_value" , member_lang) 
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
	function_name = "edit_package_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def delete_package_user(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_package_id = "member_package_id" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_package_id:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			member_package = db.member_package.find_one({"_id": ObjectId(params['member_package_id'])})
			
			if member_package is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("delete_package_user" , "member_package_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_package_object = dumps(member_package)
				member_package_json = json.loads(member_package_object)	

				if member_package_json['usage_amount'] == 0:
					# update data
					where_param = { "_id": ObjectId(params['member_package_id']) }
					value_param = {
									"$set":
										{
											"total_amount": 0,
											"usage_amount": 0,
											"remaining_amount": 0,
											"member_package_status": "0",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.member_package.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : get_api_message("delete_package_user" , "delete_package_user_success" , member_lang) 
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("delete_package_user" , "data_update_failed" , member_lang) 
								}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("delete_package_user" , "can_not_delete_package_user_because_it_has_been_used" , member_lang) 
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
	function_name = "delete_package_user"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def package_manage_list(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_package_type = "package_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']
			company_user_type = member_info['company_user_type']

			today = datetime.now().strftime('%Y-%m-%d')

			#company user
			if company_user_type == "0":
				result = { 
							"status" : False,
							"msg" : get_api_message("package_manage_list" , "company_user_type_is_invalid" , member_lang) 
						}
			else:
				if params['package_type'] == "all":
					company_package = db.company_package.find({
																"company_id": company_id,
																"company_package_status": "1"
															}).sort([("created_at", -1)])
				else:
					company_package = db.company_package.find({
																"company_id": company_id,
																"package_type": params['package_type'],
																"company_package_status": "1"
															}).sort([("created_at", -1)])
			
				company_package_list = []
				
				if company_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_package_object = dumps(company_package)
					company_package_json = json.loads(company_package_object)

					for i in range(len(company_package_json)):
						if member_lang == "en":
							package_name = company_package_json[i]['package_name_en']
						else:
							package_name = company_package_json[i]['package_name_th']

						if company_package_json[i]['package_model'] == "special":
							package_model = "Special"
						else:
							package_model = "Normal"

						if company_package_json[i]['package_type'] == "hour":
							if member_lang == "en":
								package_type_text = "Per Hour"
							else:
								package_type_text = "รายชั่วโมง"
						else:
							if member_lang == "en":
								package_type_text = "Per Time"
							else:
								package_type_text = "รายครั้ง"
						package_type_amount = company_package_json[i]['total_amount']


						admin = db.package_admin.find_one({"company_package_id": company_package_json[i]['_id']['$oid']})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						admin_object = dumps(admin)
						admin_json = json.loads(admin_object)

						package_admin = ""
						show_customer_package = "0"

						if admin_json is not None:
							for j in range(len(admin_json['package_admin'])):
								admin_info = get_member_info_by_id(admin_json['package_admin'][j])

								if j == 0:
									package_admin = admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']
								else:
									package_admin = package_admin+" , "+admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']

								if member_info['_id']['$oid'] == admin_json['package_admin'][j]:
									show_customer_package = "1"


						member_package = db.member_package.find_one({"company_package_id": company_package_json[i]['_id']['$oid']})
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						member_package_object = dumps(member_package)
						member_package_json = json.loads(member_package_object)

						package_usage_type = None
						package_usage_type_show = None

						if member_package_json is not None:
							package_usage_type = member_package_json['package_usage_type']

							if package_usage_type == "quota":
								if member_lang == "en":
									package_usage_type_show = "Quota Package"
								else:
									package_usage_type_show = "Package แบ่ง"
							else:
								if member_lang == "en":
									package_usage_type_show = "Share Package"
								else:
									package_usage_type_show = "Package ร่วม"
						
						end_date = datetime.strptime(company_package_json[i]['end_date'], '%Y-%m-%d')
						today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
						delta = end_date - today
						remaining_date = delta.days

						start_date = datetime.strptime(company_package_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
						end_date = datetime.strptime(company_package_json[i]['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
						
						if remaining_date >= 0:
							#master admin
							if company_user_type == "2":
								company_package_list.append({
									"company_package_id" : company_package_json[i]['_id']['$oid'],
									"package_id" : company_package_json[i]['package_id'],
									"package_name": package_name,
									"package_model": package_model,
									"package_type": company_package_json[i]['package_type'],
									"package_type_text": package_type_text,
									"package_type_amount": package_type_amount,
									"package_image": company_package_json[i]['package_image'],
									"start_date": start_date,
									"end_date": end_date,
									"remaining_date": remaining_date,
									"total_amount": company_package_json[i]['total_amount'],
									"usage_amount": company_package_json[i]['usage_amount'],
									"remaining_amount": company_package_json[i]['remaining_amount'],
									"package_admin": package_admin,
									"package_usage_type": package_usage_type,
									"package_usage_type_show": package_usage_type_show
								})
							#admin company
							elif company_user_type == "1" and show_customer_package == "1":
								company_package_list.append({
									"company_package_id" : company_package_json[i]['_id']['$oid'],
									"package_id" : company_package_json[i]['package_id'],
									"package_name": package_name,
									"package_model": package_model,
									"package_type": company_package_json[i]['package_type'],
									"package_type_text": package_type_text,
									"package_type_amount": package_type_amount,
									"package_image": company_package_json[i]['package_image'],
									"start_date": start_date,
									"end_date": end_date,
									"remaining_date": remaining_date,
									"total_amount": company_package_json[i]['total_amount'],
									"usage_amount": company_package_json[i]['usage_amount'],
									"remaining_amount": company_package_json[i]['remaining_amount'],
									"package_admin": package_admin,
									"package_usage_type": package_usage_type,
									"package_usage_type_show": package_usage_type_show
								})
				
				result = {
							"status" : True,
							"msg" : get_api_message("package_manage_list" , "get_package_manage_list_success" , member_lang),
							"data" : company_package_list
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
	function_name = "package_manage_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def change_package_usage_type(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_company_package_id = "company_package_id" in params
	isset_package_usage_type = "package_usage_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_package_usage_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			company_package = db.company_package.find_one({"_id": ObjectId(params['company_package_id'])})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			company_package_object = dumps(company_package)
			company_package_json = json.loads(company_package_object)

			if len(company_package_json) == 0:
				result = { 
							"status" : False,
							"msg" : get_api_message("change_package_usage_type" , "company_package_not_found" , member_lang)
						}
			else:
				#ดึงข้อมูลจาก tb member_package ที่มี company_package_id ตรงกับ company_package_id ที่ส่งเข้ามา
				member_package = db.member_package.find({"company_package_id": params['company_package_id']})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_package_object = dumps(member_package)
				member_package_json = json.loads(member_package_object)

				current_date_int = int(datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))
				
				if len(member_package_json) == 0:
					if company_package_json['package_usage_type'] != params['package_usage_type']:
						# update data
						where_param = { "_id": ObjectId(params['company_package_id']) }
						value_param = {
										"$set":
											{
												"package_usage_type": params['package_usage_type'],
												"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
											}
									}

						db.company_package.update(where_param , value_param)

						result = {
									"status" : True,
									"msg" : get_api_message("change_package_usage_type" , "change_package_usage_type_success" , member_lang)
								}
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("change_package_usage_type" , "can_not_change_package_usage_type_because_package_usage_type_is_original_value" , member_lang) 
								}	
				else:
					if company_package_json['package_usage_type'] != params['package_usage_type']:
						#ถ้า package_usage_type == "quota" ให้วนลูปอัพเดตข้อมูลลง tb member_package
						#โดยให้ total_amount = usage_amount และ remaining_amount = 0
						if params['package_usage_type'] == "quota":
							for i in range(len(member_package_json)):
								user_total_amount = member_package_json[i]['usage_amount']
								user_remaining_amount = 0

								if current_date_int <= member_package_json[i]['end_date_int']:
									member_package_status = member_package_json[i]['member_package_status']
								else:
									member_package_status = "0"

								# update data
								where_param = { "_id": ObjectId(member_package_json[i]['_id']['$oid']) }
								value_param = {
												"$set":
													{
														"package_usage_type": params['package_usage_type'],
														"total_amount": user_total_amount,
														"remaining_amount": user_remaining_amount,
														"member_package_status": member_package_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.member_package.update(where_param , value_param):
									response = True
								else:
									response = False
									break

							if response:
								# update data
								where_param = { "_id": ObjectId(params['company_package_id']) }
								value_param = {
												"$set":
													{
														"package_usage_type": params['package_usage_type'],
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								db.company_package.update(where_param , value_param)
								
								result = {
											"status" : True,
											"msg" : get_api_message("change_package_usage_type" , "change_package_usage_type_success" , member_lang) 
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("change_package_usage_type" , "data_update_failed" , member_lang)
										}
						#แต่ถ้า package_usage_type == "share" ให้วนลูปอัพเดตข้อมูลลง tb member_package
						#โดยให้ total_amount = 0 และ remaining_amount = 0
						else:
							for i in range(len(member_package_json)):
								user_total_amount = 0
								user_remaining_amount = 0
			
								if current_date_int <= member_package_json[i]['end_date_int']:
									member_package_status = "1"
								else:
									member_package_status = "0"

								# update data
								where_param = { "_id": ObjectId(member_package_json[i]['_id']['$oid']) }
								value_param = {
												"$set":
													{
														"package_usage_type": params['package_usage_type'],
														"total_amount": user_total_amount,
														"remaining_amount": user_remaining_amount,
														"member_package_status": member_package_status,
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.member_package.update(where_param , value_param):
									response = True
								else:
									response = False
									break

							if response:
								# update data
								where_param = { "_id": ObjectId(params['company_package_id']) }
								value_param = {
												"$set":
													{
														"package_usage_type": params['package_usage_type'],
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								db.company_package.update(where_param , value_param)
								
								result = {
											"status" : True,
											"msg" : get_api_message("change_package_usage_type" , "change_package_usage_type_success" , member_lang) 
										}
							else:
								result = {
											"status" : False,
											"msg" : get_api_message("change_package_usage_type" , "data_update_failed" , member_lang) 
										}
					else:
						result = { 
									"status" : False,
									"msg" : get_api_message("change_package_usage_type" , "can_not_change_package_usage_type_because_package_usage_type_is_original_value" , member_lang) 
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
	function_name = "change_package_usage_type"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_car_list(request):
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
								"car_group": "company",
								"company_id": member_info['company_id'],
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
							car_group_text = "Company car"
						else:
							car_type_name = car_type_json['car_type_name_th']
							car_brand_name = car_brand_json['brand_name']
							car_gear_name = car_gear_json['car_gear_th']
							car_engine_name = car_engine_json['car_engine_th']
							car_group_text = "รถบริษัท"

						car_list.append({
							"car_id" : car_json[i]['_id']['$oid'],
							"company_id": car_json[i]['company_id'],
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
						"msg" : get_api_message("company_car_list" , "get_company_car_list_success" , member_lang),
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
	function_name = "company_car_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_company_car_detail(car_id,request):
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

			car = db.car.find_one({"_id": ObjectId(car_id)})
			if car is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_company_car_detail" , "data_not_found" , member_lang)
						}
			else:
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

				if member_lang == "en":
					car_type_name = car_type_json['car_type_name_en']
					car_brand_name = car_brand_json['brand_name']
					car_gear_name = car_gear_json['car_gear_en']
					car_engine_name = car_engine_json['car_engine_en']
					car_group_text = "Company car"

					if car_json['car_status'] == "1":
						car_status_text = "Active"
					else:
						car_status_text = "Inactive"
				else:
					car_type_name = car_type_json['car_type_name_th']
					car_brand_name = car_brand_json['brand_name']
					car_gear_name = car_gear_json['car_gear_th']
					car_engine_name = car_engine_json['car_engine_th']
					car_group_text = "รถบริษัท"

					if car_json['car_status'] == "1":
						car_status_text = "เปิดใช้งาน"
					else:
						car_status_text = "ปิดใช้งาน"

				data = {
							"car_id" : car_json['_id']['$oid'],
							"company_id": car_json['company_id'],
							"member_id": car_json['member_id'],
							"car_type_id": car_json['car_type_id'],
							"car_type_name": car_type_name,
							"car_brand_id": car_json['car_brand_id'],
							"car_brand_name": car_brand_name,
							"car_gear_id": car_json['car_gear_id'],
							"car_gear_name": car_gear_name,
							"car_engine_id": car_json['car_engine_id'],
							"car_engine_name": car_engine_name,
							"license_plate": car_json['license_plate'],
							"car_group": car_json['car_group'],
							"car_group_text": car_group_text,
							"car_status": car_json['car_status'],
							"car_status_text": car_status_text,
							"car_image": car_json['car_image']
						}

				result = {
							"status" : True,
							"msg" : get_api_message("get_company_car_detail" , "get_company_car_detail_success" , member_lang), 
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
	function_name = "get_company_car_detail"
	request_headers = request.headers
	params_get = {"car_id" : car_id}
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def company_car_manage_list(request):
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

			car = db.car.find({
								"car_group": "company",
								"company_id": member_info['company_id']
							})
			car_list = []

			if car is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				for i in range(len(car_json)):
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
						
						if car_json[i]['car_status'] == "1":
							car_status_text = "Active"
						else:
							car_status_text = "Inactive"
					else:
						car_type_name = car_type_json['car_type_name_th']
						car_brand_name = car_brand_json['brand_name']
						car_gear_name = car_gear_json['car_gear_th']
						car_engine_name = car_engine_json['car_engine_th']

						if car_json[i]['car_status'] == "1":
							car_status_text = "เปิดใช้งาน"
						else:
							car_status_text = "ปิดใช้งาน"

					car_list.append({
						"car_id" : car_json[i]['_id']['$oid'],
						"company_id": car_json[i]['company_id'],
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
						"car_status": car_json[i]['car_status'],
						"car_status_text": car_status_text,
						"car_image": car_json[i]['car_image']
					})

			result = {
						"status" : True,
						"msg" : get_api_message("company_car_manage_list" , "get_company_car_manage_list_success" , member_lang),
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
	function_name = "company_car_manage_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def car_usage_history_list(request):
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

			car = db.car.find_one({"_id": ObjectId(params['car_id'])})
			if car is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("car_usage_history_list" , "data_not_found" , member_lang) #"Data not found."
						}
			else:
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

				if member_lang == "en":
					car_type_name = car_type_json['car_type_name_en']
					car_brand_name = car_brand_json['brand_name']
					car_gear_name = car_gear_json['car_gear_en']
					car_engine_name = car_engine_json['car_engine_en']
					car_group_text = "Company car"

					if car_json['car_status'] == "1":
						car_status_text = "Active"
					else:
						car_status_text = "Inactive"
				else:
					car_type_name = car_type_json['car_type_name_th']
					car_brand_name = car_brand_json['brand_name']
					car_gear_name = car_gear_json['car_gear_th']
					car_engine_name = car_engine_json['car_engine_th']
					car_group_text = "รถบริษัท"

					if car_json['car_status'] == "1":
						car_status_text = "เปิดใช้งาน"
					else:
						car_status_text = "ปิดใช้งาน"

				request_driver = db.request_driver.find({
															"car_id": params['car_id'],
															"company_id": member_info['company_id'],
															"request_status": {"$nin" : ["2","3"]}
														}).sort([("start_date", -1)])

				request_driver_list = []

				if request_driver is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					car_usage_amount = 0

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

						check_status = request_driver_json[i]['check_status']
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
								car_inspection = db.car_inspection.find_one({"request_id": request_driver_json[i]['_id']['$oid']})
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


						request_driver_list.append({
							"request_id" : request_driver_json[i]['_id']['$oid'],
							"request_no": request_driver_json[i]['request_no'],
							"company_id": request_driver_json[i]['company_id'],
							"member_id": request_driver_json[i]['member_id'],
							"passenger_id": request_driver_json[i]['passenger_id'],
							"request_to": request_driver_json[i]['request_to'],
							"start_date": start_date,
							"start_time": start_time,
							"from_location_name": request_driver_json[i]['from_location_name'],
							"from_location_address": request_driver_json[i]['from_location_address'],
							"to_location_name": request_driver_json[i]['to_location_name'],
							"main_package_name": main_package_name,
							"request_status": request_driver_json[i]['request_status'],
							"request_status_text": request_status_text,
							"check_status": check_status,
							"check_status_text": check_status_text,
							"start_mileage": start_mileage,
							"end_mileage": end_mileage
						})

						car_usage_amount = car_usage_amount + 1
				

				result = {
							"status" : True,
							"msg" : get_api_message("car_usage_history_list" , "get_car_usage_history_success" , member_lang),
							"car_id" : car_json['_id']['$oid'],
							"company_id": car_json['company_id'],
							"car_group_text": car_group_text,
							"car_type_id": car_json['car_type_id'],
							"car_type_name": car_type_name,
							"car_brand_id": car_json['car_brand_id'],
							"car_brand_name": car_brand_name,
							"car_gear_id": car_json['car_gear_id'],
							"car_gear_name": car_gear_name,
							"car_engine_id": car_json['car_engine_id'],
							"car_engine_name": car_engine_name,
							"license_plate": car_json['license_plate'],
							"car_image": car_json['car_image'],
							"car_usage_amount": car_usage_amount,
							"request_driver" : request_driver_list
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
	function_name = "car_usage_history_list"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_company_car(request):
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
	isset_car_status = "car_status" in params
	isset_car_image = "car_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_type_id and isset_car_brand_id and isset_car_gear_id and isset_car_engine_id and isset_license_plate and isset_car_status and isset_car_image:
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
					validate.append({"error_param" : "license_plate","msg" : get_api_message("add_company_car" , "car_has_been_used" , member_lang)})

					result = {
								"status" : False,
								"msg" : get_api_message("add_company_car" , "car_has_been_used" , member_lang),
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
								"car_group": "company",
								"company_id": member_info['company_id'],
								"member_id": member_info['_id']['$oid'],
								"car_type_id": params['car_type_id'],
								"car_brand_id": params['car_brand_id'],
								"car_gear_id": params['car_gear_id'],
								"car_engine_id": params['car_engine_id'],
								"license_plate": params['license_plate'].strip(),
								"car_image": image_name,
								"car_status": params['car_status'],
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

					if db.car.insert_one(data):
						result = {
									"status" : True,
									"msg" : get_api_message("add_company_car" , "add_company_car_success" , member_lang) 
								}
					else:
						result = {
								"status" : False,
								"msg" : get_api_message("add_company_car" , "data_insert_failed" , member_lang) 
								}
			else:
				validate.append({"error_param" : "license_plate","msg" : get_api_message("add_company_car" , "invalid_license_plate_format" , member_lang)})

				result = {
							"status" : False,
							"msg" : get_api_message("add_company_car" , "invalid_license_plate_format" , member_lang),
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
	function_name = "add_company_car"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def edit_company_car(request):
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
	isset_car_status = "car_status" in params
	isset_car_image = "car_image" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_id and isset_car_type_id and isset_car_brand_id and isset_car_gear_id and isset_car_engine_id and isset_license_plate and isset_car_status and isset_car_image:
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
											"license_plate": params['license_plate'].strip()
										}).count()

				if check_car > 0:
					validate.append({"error_param" : "license_plate","msg" : get_api_message("edit_company_car" , "car_has_been_used" , member_lang)})

					result = {
								"status" : False,
								"msg" : get_api_message("edit_company_car" , "car_has_been_used" , member_lang),
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

					if params['car_status'] is None:
						car_status = car_json['car_status']
					elif params['car_status'] == "0":
						car_status = "0"
					else:
						car_status = "1"

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
											"car_status": car_status,
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					if db.car.update(where_param , value_param):
						result = {
									"status" : True,
									"msg" : get_api_message("edit_company_car" , "edit_company_car_success" , member_lang)
								}
					else:
						result = {
									"status" : False,
									"msg" : get_api_message("edit_company_car" , "data_update_failed" , member_lang)
								}
			else:
				validate.append({"error_param" : "license_plate","msg" : get_api_message("edit_company_car" , "invalid_license_plate_format" , member_lang)})

				result = {
							"status" : False,
							"msg" : get_api_message("edit_company_car" , "invalid_license_plate_format" , member_lang),
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
	function_name = "edit_company_car"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def add_contact(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_contact_topic_id = "contact_topic_id" in params
	isset_contact_firstname = "contact_firstname" in params
	isset_contact_lastname = "contact_lastname" in params
	isset_contact_email = "contact_email" in params
	isset_contact_tel = "contact_tel" in params
	isset_contact_message = "contact_message" in params

	if isset_accept and isset_content_type and isset_app_version and isset_contact_topic_id and isset_contact_firstname and isset_contact_lastname and isset_contact_email and isset_contact_tel and isset_contact_message:
		validate = []
		member_lang = "en"

		#check required
		if params['contact_topic_id']=="" or params['contact_topic_id'] is None:
			validate.append({"error_param" : "contact_topic_id","msg" : get_api_message("add_contact" , "contact_topic_is_required" , member_lang)}) 
		if params['contact_firstname']=="" or params['contact_firstname'] is None:
			validate.append({"error_param" : "contact_firstname","msg" : get_api_message("add_contact" , "firstname_is_required" , member_lang)}) 
		if params['contact_lastname']=="" or params['contact_lastname'] is None:
			validate.append({"error_param" : "contact_lastname","msg" : get_api_message("add_contact" , "lastname_is_required" , member_lang)}) 
		if params['contact_email']=="" or params['contact_email'] is None:
			validate.append({"error_param" : "contact_email","msg" : get_api_message("add_contact" , "email_is_required" , member_lang)}) 
		if params['contact_tel']=="" or params['contact_tel'] is None:
			validate.append({"error_param" : "contact_tel","msg" : get_api_message("add_contact" , "tel_is_required" , member_lang)}) 
		if params['contact_message']=="" or params['contact_message'] is None:
			validate.append({"error_param" : "contact_message","msg" : get_api_message("add_contact" , "message_is_required" , member_lang)}) 

		#check tel format
		if params['contact_tel']!="" and params['contact_tel'] is not None:
			tel = params['contact_tel'].replace("-", "")
			count_tel = len(tel)

			try:
				data_contact_tel = int(params['contact_tel'])
				check_data_contact_tel = True
			except ValueError:
				check_data_contact_tel = False

			if ((count_tel < 9) or (count_tel > 10) or (not check_data_contact_tel)):
				validate.append({"error_param" : "contact_tel","msg" : get_api_message("add_contact" , "invalid_tel_format" , member_lang)}) 

		#ถ้า validate ผ่าน
		if len(validate) == 0:
			contact_topic = db.contact_topic.find_one({"_id": ObjectId(params['contact_topic_id'])})

			if contact_topic is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("add_contact" , "data_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				contact_topic_object = dumps(contact_topic)
				contact_topic_json = json.loads(contact_topic_object)
				contact_topic_name = contact_topic_json['topic_th']

				created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				create_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'))

			data = { 
						"contact_topic_id": params['contact_topic_id'],
						"contact_topic_name": contact_topic_name,
						"contact_firstname": params['contact_firstname'].strip(),
						"contact_lastname": params['contact_lastname'].strip(),
						"contact_email": params['contact_email'].strip().lower(),
						"contact_tel": params['contact_tel'].strip(),
						"contact_message": params['contact_message'].strip(),
						"created_at": created_at,
						"create_date_int": create_date_int,
						"updated_at": created_at
					}

			if db.contact.insert_one(data):
				result = {
							"status" : True,
							"msg" : get_api_message("add_contact" , "add_contact_success" , member_lang) 
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("add_contact" , "data_insert_failed" , member_lang) 
						}
		else:
			result = {
						"status" : False,
						"msg" : get_api_message("add_contact" , "please_check_your_parameters_value" , member_lang), 
						"error_list" : validate
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "customer"
	function_name = "add_contact"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def request_list_frontend(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_request_status = "request_status" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_request_status:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			#ถ้า request_status = null ให้ดึงสถานะทั้งหมดมาแสดง
			if params['request_status'] == "all":
				request_driver = db.request_driver.find({
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															]
														}).sort([("created_at", -1)])
			#ถ้า request_status != null ให้ดึงเฉพาะสถานะที่เลือกมาแสดง
			else:
				request_driver = db.request_driver.find({
															"$or": [
																{ "member_id": member_id },
																{ "passenger_id": member_id }
															],
															"request_status": params['request_status']
														}).sort([("created_at", -1)])

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

				if member_lang == "en":
					code_all = "All Status"
					code_0 = "Waiting for reply"
					code_1 = "Accepted"
					code_2 = "Canceled by customer"
					code_3 = "Canceled by driver"
					code_4 = "Upcoming work"
					code_5 = "Traveling"
					code_6 = "Finish"
				else:
					code_all = "สถานะทั้งหมด"
					code_0 = "รอตอบรับ"
					code_1 = "ตอบรับแล้ว"
					code_2 = "ยกเลิกโดยลูกค้า"
					code_3 = "ยกเลิกโดยคนขับ"
					code_4 = "งานที่ใกล้จะถึง"
					code_5 = "กำลังเดินทาง"
					code_6 = "สำเร็จ"

				request_status_list = [
										{"code": "all","name": code_all},
										{"code": "0","name": code_0},
										{"code": "1","name": code_1},
										{"code": "2","name": code_2},
										{"code": "3","name": code_3},
										{"code": "4","name": code_4},
										{"code": "5","name": code_5},
										{"code": "6","name": code_6}
									]

			result = {
						"status" : True,
						"msg" : get_api_message("request_list_frontend" , "get_request_list_success" , member_lang), 
						"data" : request_driver_list,
						"request_status" : request_status_list
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
	function_name = "request_list_frontend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

#edit -- add special skill
def request_detail_frontend(request):
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
							"msg" : get_api_message("request_detail_frontend" , "request_not_found" , member_lang) 
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				request_driver_object = dumps(request_driver)
				request_driver_json = json.loads(request_driver_object)

				mem_info = get_member_info_by_id(request_driver_json['member_id'])
				member_fullname = mem_info['member_firstname_en']+" "+mem_info['member_lastname_en']

				passenger_info = get_member_info_by_id(request_driver_json['passenger_id'])
				passenger_fullname = passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en']
				passenger_tel = passenger_info['member_tel']
				passenger_email = passenger_info['member_email']

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

				if delay_minute > 30 and delay_minute < 60:
					cal_delay_hour = delay_hour + 1
				else:
					cal_delay_hour = delay_hour


				car_id = request_driver_json['car_id']

				car = db.car.find_one({"_id": ObjectId(car_id)})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				if car_json['car_group'] == "company":
					if member_lang == "en":
						car_group = "Company car"
					else:
						car_group = "รถบริษัท"
				else:
					if member_lang == "en":
						car_group = "Personal car"
					else:
						car_group = "รถส่วนตัว"

				car_image = car_json['car_image']
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

				license_plate = car_json['license_plate']

				if request_driver_json['special_request'] is not None:
					driver_age_range_list = []
					communication_list = []
					driver_gender_list = []
					special_skill_list = []
					driver_gender_text = ""
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
				overtime_paid_rate = float(package_info['overtime_paid_rate'])

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

			

				if check_status is not None and check_status != "0" and check_status != "1":
					car_inspection = db.car_inspection.find_one({"request_id": params['request_id']})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					car_inspection_object = dumps(car_inspection)
					car_inspection_json = json.loads(car_inspection_object)

					outside_inspection_json = car_inspection_json['outside_inspection']
					inspection_before_use_json = car_inspection_json['inspection_before_use']

					outside_inspection_list = []
					inspection_before_use_list = []
					inspection_before_use_comment = car_inspection_json['inspection_before_use_comment']
					inspection_before_use_image = car_inspection_json['inspection_before_use_image']

					for i in range(len(outside_inspection_json)):
						if member_lang == "en":
							point_name = outside_inspection_json[i]['point_name_en']
						else:
							point_name = outside_inspection_json[i]['point_name_th']

						part_list = []
						check_error = "0"

						for j in range(len(outside_inspection_json[i]['part'])):
							if member_lang == "en":
								part_name = outside_inspection_json[i]['part'][j]['part_name_en']
							else:
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
				else:
					outside_inspection_list = []
					inspection_before_use_list = []
					inspection_before_use_comment = None
					inspection_before_use_image = []


				select_new_driver = "0"
				check_request_info = check_request_status(params['request_id'])

				if check_request_info is not None:
					if check_request_info['all_driver'] == check_request_info['count_reject']:
						select_new_driver = "1"

				overtime_paid_price = cal_delay_hour * overtime_paid_rate

				deley_detail = {
								"delay_hour": delay_hour,
								"delay_minute": delay_minute,
								"delay_end_date": delay_end_date,
								"delay_end_time": delay_end_time,
								"overtime_paid_rate": overtime_paid_rate,
								"overtime_paid_price": overtime_paid_price
							}

				data = {
							"request_id" : request_driver_json['_id']['$oid'],
							"request_no": request_driver_json['request_no'],
							"company_id": request_driver_json['company_id'],
							"member_id": request_driver_json['member_id'],
							"passenger_id": request_driver_json['passenger_id'],
							"member_fullname": member_fullname,
							"passenger_fullname": passenger_fullname,
							"passenger_tel": passenger_tel,
							"passenger_email": passenger_email,
							"request_to": request_driver_json['request_to'],
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
							"car_image": car_image,
							"car_group": car_group,
							"car_type_code": car_type_code,
							"car_type_name": car_type_name,
							"car_brand_name": car_brand_name,
							"car_gear_name": car_gear_name,
							"car_engine_name": car_engine_name,
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
							"outside_inspection": outside_inspection_list,
							"inspection_before_use": inspection_before_use_list,
							"inspection_before_use_comment": inspection_before_use_comment,
							"inspection_before_use_image": inspection_before_use_image,
							"deley_detail": deley_detail,
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
							"msg" : get_api_message("request_detail_frontend" , "get_request_detail_success" , member_lang), 
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
	function_name = "request_detail_frontend"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def billing_statement_list(request):
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

			company = db.company.find_one({"_id": ObjectId(member_info['company_id'])})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			company_object = dumps(company)
			company_json = json.loads(company_object)
			billing_date = company_json['billing_date']

			billing_statement = db.billing_statement.find({ 
															"company_id" : member_info['company_id'] 
														}).sort([("updated_at" , -1)])
			total_data = db.billing_statement.find({ "company_id" : member_info['company_id'] }).count()

			if billing_statement is None:
				result = { 
						"status" : False,
						"msg" : get_api_message("billing_statement_list" , "data_not_found" , member_lang)
					}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				billing_statement_object = dumps(billing_statement)
				billing_statement_json = json.loads(billing_statement_object)

				billing_statement_list = []

				for i in range(len(billing_statement_json)):
					company = db.company.find_one({"_id": ObjectId(billing_statement_json[i]['company_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					company_object = dumps(company)
					company_json = json.loads(company_object)
					company_name = company_json['company_name']

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
						"company_name": company_name,
						"billing_statement_amount": float(billing_statement_json[i]['sum_paid']),
						"billing_statement_status": billing_statement_json[i]['billing_statement_status'],
						"billing_statement_status_show": billing_statement_status_show
					})

				result = {
							"status" : True,
							"msg" : get_api_message("billing_statement_list" , "get_billing_statement_success" , member_lang), 
							"billing_date" : billing_date,
							"billing_statement" : billing_statement_list

							# "where_param" : where_param
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
	function_name = "billing_statement_list"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_billing_statement_detail(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_billing_statement_id = "billing_statement_id" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_billing_statement_id and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			# if params['sort_name'] == "":
			# 	sort_name = "updated_at"
			# 	sort_type = -1
			# else:
			# 	#การ sort ข้อมูล
			# 	#billing_statement_code = billing_statement_code
			# 	#billing_statement_month = billing_statement_month
			# 	#billing_statement_date = created_at
			# 	#company_name = company_name
			# 	#billing_statement_amount = sum_paid
			# 	#billing_statement_status = billing_statement_status

			# 	if params['sort_name'] == "billing_statement_date":
			# 		sort_name = "created_at"
			# 	elif params['sort_name'] == "billing_statement_amount":
			# 		sort_name = "sum_paid"
			# 	else:
			# 		sort_name = params['sort_name']

			# 	if params['sort_type'] == "desc":
			# 		sort_type = -1
			# 	else:
			# 		sort_type = 1
				
			billing_statement = db.billing_statement.find_one({"_id": ObjectId(params['billing_statement_id'])})

			if billing_statement is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("get_billing_statement_detail" , "data_not_found" , member_lang) 
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

				billing_in = []		

				for i in range(len(billing_statement_json['billing'])):
					billing_in.append(ObjectId(billing_statement_json['billing'][i]))

				billing = db.billing.find({
											"_id" : {"$in" : billing_in}
										})

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
							"msg" : get_api_message("get_billing_statement_detail" , "get_billing_statement_detail_success" , member_lang),
							"billing_statement_id": billing_statement_json['_id']['$oid'],
							"billing_statement_code": billing_statement_json['billing_statement_code'],
							"billing_statement_month": billing_statement_month_text,
							"billing_statement_date": billing_statement_date,
							"billing_statement_amount": billing_statement_json['sum_paid'],
							"company_name": company_json['company_name'],
							"company_tax_id": company_json['company_tax_id'],
							"billing_date": company_json['billing_date'],
							"billing_statement_status": billing_statement_json['billing_statement_status'],
							"billing_list": billing_list

							# "where_param" : where_param
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
	function_name = "get_billing_statement_detail"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def car_inspection_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_check_status = "check_status" in params
	isset_car_type = "car_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_check_status and isset_car_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if company_id is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("car_inspection_report" , "you_are_not_a_company_member" , member_lang)
						}
			else:
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
							"msg" : get_api_message("car_inspection_report" , "data_start_is_not_a_number" , member_lang)
						}
				elif not check_data_length:
					result = { 
							"status" : False,
							"msg" : get_api_message("car_inspection_report" , "data_length_is_not_a_number" , member_lang)
						}
				else:
					if params['car_type'] == "sedan" or params['car_type'] == "suv" or params['car_type'] == "van":
						where_param = { 
											"company_id": company_id,
											"job_status": {"$in" : ["6","7","8","9","10","11"]}, 
											"car_type_code": params['car_type']
										}

						#request_no , driver_name , passenger_name , car_brand_name , license_plate
						if params['search_text'] != "":
							add_params = {
											"$or": [
														{ "request_no": {"$regex": params['search_text']} },
														{ "driver_name_en": {"$regex": params['search_text']} },
														{ "driver_name_th": {"$regex": params['search_text']} },
														{ "passenger_name": {"$regex": params['search_text']} },
														{ "car_brand_name": {"$regex": params['search_text']} },
														{ "license_plate": {"$regex": params['search_text']} }
														
													]
										}
							where_param.update(add_params)

						if params['check_status'] == "0" or params['check_status'] == "1" or params['check_status'] == "2" or params['check_status'] == "3" or params['check_status'] == "4" or params['check_status'] == "5":
							add_params = {"check_status" : params['check_status']}
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
							# check_status_text = check_status
							# car_type_code = car_type_code
							# car_brand_name = car_brand_name
							# license_plate = license_plate
							# passenger_name = passenger_name
							# driver_name = driver_name_en / driver_name_th

							if params['sort_name'] == "driver_name":
								if member_lang == "en":
									sort_name = "driver_name_en"
								else:
									sort_name = "driver_name_th"
							elif params['sort_name'] == "check_status_text":
								sort_name = "check_status"
							elif params['sort_name'] == "start_date":
								sort_name = "start_at"
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

							car_inspection_list = []

							for i in range(len(request_driver_json)):
								start_date = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
								start_time = datetime.strptime(request_driver_json[i]['start_time'], '%H:%M:%S').strftime('%H:%M')
								start_datetime = start_date+" "+start_time

								if member_lang == "en":
									driver_name = request_driver_json[i]['driver_name_en']
								else:
									driver_name = request_driver_json[i]['driver_name_th']

								if request_driver_json[i]['check_status'] == "5":
									if member_lang == "en":
										check_status_text = "The passenger did not confirm the car inspection"
									else:
										check_status_text = "ผู้โดยสารไม่ยืนยันการตรวจสภาพรถ"
								elif request_driver_json[i]['check_status'] == "4":
									if member_lang == "en":
										check_status_text = "Successfully inspected the car"
									else:
										check_status_text = "ตรวจสภาพรถเรียบร้อย"
								elif request_driver_json[i]['check_status'] == "3":
									if member_lang == "en":
										check_status_text = "Inspect the car does not pass"
									else:
										check_status_text = "ตรวจสภาพรถไม่ผ่าน"
								elif request_driver_json[i]['check_status'] == "2":
									if member_lang == "en":
										check_status_text = "Waiting for confirmation of car inspection from passengers"
									else:
										check_status_text = "รอยืนยันการตรวจสภาพรถจากผู้โดยสาร"
								elif request_driver_json[i]['check_status'] == "1":
									if member_lang == "en":
										check_status_text = "Skip the car inspection"
									else:
										check_status_text = "ข้ามการตรวจสภาพรถ"
								else:
									if member_lang == "en":
										check_status_text = "Have not checked the car inspection"
									else:
										check_status_text = "ยังไม่ได้ตรวจสภาพรถ"

								car_inspection = db.car_inspection.find_one({"request_id": request_driver_json[i]['_id']['$oid']})
								#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								car_inspection_object = dumps(car_inspection)
								car_inspection_json = json.loads(car_inspection_object)

								outside_inspection_json = car_inspection_json['outside_inspection']
								inspection_before_use_json = car_inspection_json['inspection_before_use']

								for j in range(len(outside_inspection_json)):
									for k in range(len(outside_inspection_json[j]['part'])):
										var_result_1 = "outside_check_result"
										var_result_2 = str(j+1)
										var_result_3 = str(k+1)
										var_result_name = var_result_1+"_"+var_result_2+"_"+var_result_3

										var_remark_1 = "outside_check_remark"
										var_remark_2 = str(j+1)
										var_remark_3 = str(k+1)
										var_remark_name = var_remark_1+"_"+var_remark_2+"_"+var_remark_3

										if outside_inspection_json[j]['part'][k]['check_result'] == "0":
											if member_lang == "en":
												outside_check_result = "Abnormal"
											else:
												outside_check_result = "ผิดปกติ"

											outside_check_remark = outside_inspection_json[j]['part'][k]['check_remark']
										else:
											if member_lang == "en":
												outside_check_result = "Normal"
											else:
												outside_check_result = "ปกติ"

											outside_check_remark = ""

										globals()[var_result_name] = outside_check_result
										globals()[var_remark_name] = outside_check_remark				

								for j in range(len(inspection_before_use_json)):
									var_result_1 = "before_use_check_result"
									var_result_2 = str(j+1)
									var_result_name = var_result_1+"_"+var_result_2

									var_remark_1 = "before_use_check_remark"
									var_remark_2 = str(j+1)
									var_remark_name = var_remark_1+"_"+var_remark_2

									if inspection_before_use_json[j]['check_result'] == "0":
										if member_lang == "en":
											before_use_check_result = "Abnormal"
										else:
											before_use_check_result = "ผิดปกติ"

										before_use_check_remark = inspection_before_use_json[j]['check_remark']
									else:
										if member_lang == "en":
											before_use_check_result = "Normal"
										else:
											before_use_check_result = "ปกติ"

										before_use_check_remark = ""

									globals()[var_result_name] = before_use_check_result
									globals()[var_remark_name] = before_use_check_remark

								if params['car_type'] == "sedan":
									if member_lang == "en":
										car_type_text = "Sedan"
									else:
										car_type_text = "รถเก๋ง"

									car_inspection_list.append({
										"id_index": data_start_at+(i+1),
										"request_no": request_driver_json[i]['request_no'],
										"start_date": start_datetime,
										"check_status": request_driver_json[i]['check_status'],
										"check_status_text": check_status_text,
										"car_type": car_type_text,
										"car_brand": request_driver_json[i]['car_brand_name'],
										"license_plate": request_driver_json[i]['license_plate'],
										"passenger_name": request_driver_json[i]['passenger_name'],
										"driver_name": driver_name,

										"outside_check_result_1_1": outside_check_result_1_1,
										"outside_check_remark_1_1": outside_check_remark_1_1,
										"outside_check_result_1_2": outside_check_result_1_2,
										"outside_check_remark_1_2": outside_check_remark_1_2,
										"outside_check_result_1_3": outside_check_result_1_3,
										"outside_check_remark_1_3": outside_check_remark_1_3,
										"outside_check_result_1_4": outside_check_result_1_4,
										"outside_check_remark_1_4": outside_check_remark_1_4,
										"outside_check_result_1_5": outside_check_result_1_5,
										"outside_check_remark_1_5": outside_check_remark_1_5,
										"outside_check_result_2_1": outside_check_result_2_1,
										"outside_check_remark_2_1": outside_check_remark_2_1,
										"outside_check_result_2_2": outside_check_result_2_2,
										"outside_check_remark_2_2": outside_check_remark_2_2,
										"outside_check_result_3_1": outside_check_result_3_1,
										"outside_check_remark_3_1": outside_check_remark_3_1,
										"outside_check_result_4_1": outside_check_result_4_1,
										"outside_check_remark_4_1": outside_check_remark_4_1,
										"outside_check_result_4_2": outside_check_result_4_2,
										"outside_check_remark_4_2": outside_check_remark_4_2,
										"outside_check_result_4_3": outside_check_result_4_3,
										"outside_check_remark_4_3": outside_check_remark_4_3,
										"outside_check_result_5_1": outside_check_result_5_1,
										"outside_check_remark_5_1": outside_check_remark_5_1,
										"outside_check_result_5_2": outside_check_result_5_2,
										"outside_check_remark_5_2": outside_check_remark_5_2,
										"outside_check_result_6_1": outside_check_result_6_1,
										"outside_check_remark_6_1": outside_check_remark_6_1,
										"outside_check_result_7_1": outside_check_result_7_1,
										"outside_check_remark_7_1": outside_check_remark_7_1,
										"outside_check_result_7_2": outside_check_result_7_2,
										"outside_check_remark_7_2": outside_check_remark_7_2,
										"outside_check_result_8_1": outside_check_result_8_1,
										"outside_check_remark_8_1": outside_check_remark_8_1,
										"outside_check_result_8_2": outside_check_result_8_2,
										"outside_check_remark_8_2": outside_check_remark_8_2,
										"outside_check_result_8_3": outside_check_result_8_3,
										"outside_check_remark_8_3": outside_check_remark_8_3,
										"outside_check_result_9_1": outside_check_result_9_1,
										"outside_check_remark_9_1": outside_check_remark_9_1,
										"outside_check_result_9_2": outside_check_result_9_2,
										"outside_check_remark_9_2": outside_check_remark_9_2,
										"outside_check_result_10_1": outside_check_result_10_1,
										"outside_check_remark_10_1": outside_check_remark_10_1,
										"outside_check_result_11_1": outside_check_result_11_1,
										"outside_check_remark_11_1": outside_check_remark_11_1,
										"outside_check_result_11_2": outside_check_result_11_2,
										"outside_check_remark_11_2": outside_check_remark_11_2,
										"outside_check_result_11_3": outside_check_result_11_3,
										"outside_check_remark_11_3": outside_check_remark_11_3,
										"outside_check_result_11_4": outside_check_result_11_4,
										"outside_check_remark_11_4": outside_check_remark_11_4,
										"outside_check_result_11_5": outside_check_result_11_5,
										"outside_check_remark_11_5": outside_check_remark_11_5,

										"before_use_check_result_1": before_use_check_result_1,
										"before_use_check_remark_1": before_use_check_remark_1,
										"before_use_check_result_2": before_use_check_result_2,
										"before_use_check_remark_2": before_use_check_remark_2,
										"before_use_check_result_3": before_use_check_result_3,
										"before_use_check_remark_3": before_use_check_remark_3,
										"before_use_check_result_4": before_use_check_result_4,
										"before_use_check_remark_4": before_use_check_remark_4,
										"before_use_check_result_5": before_use_check_result_5,
										"before_use_check_remark_5": before_use_check_remark_5,
										"before_use_check_result_6": before_use_check_result_6,
										"before_use_check_remark_6": before_use_check_remark_6,
										"before_use_check_result_7": before_use_check_result_7,
										"before_use_check_remark_7": before_use_check_remark_7,
										"before_use_check_result_8": before_use_check_result_8,
										"before_use_check_remark_8": before_use_check_remark_8,
										"before_use_check_result_9": before_use_check_result_9,
										"before_use_check_remark_9": before_use_check_remark_9,
										"before_use_check_result_10": before_use_check_result_10,
										"before_use_check_remark_10": before_use_check_remark_10
									})
								elif params['car_type'] == "suv":
									if member_lang == "en":
										car_type_text = "SUV"
									else:
										car_type_text = "รถ SUV"

									car_inspection_list.append({
										"id_index": data_start_at+(i+1),
										"request_no": request_driver_json[i]['request_no'],
										"start_date": start_datetime,
										"check_status": request_driver_json[i]['check_status'],
										"check_status_text": check_status_text,
										"car_type": car_type_text,
										"car_brand": request_driver_json[i]['car_brand_name'],
										"license_plate": request_driver_json[i]['license_plate'],
										"passenger_name": request_driver_json[i]['passenger_name'],
										"driver_name": driver_name,

										"outside_check_result_1_1": outside_check_result_1_1,
										"outside_check_remark_1_1": outside_check_remark_1_1,
										"outside_check_result_1_2": outside_check_result_1_2,
										"outside_check_remark_1_2": outside_check_remark_1_2,
										"outside_check_result_1_3": outside_check_result_1_3,
										"outside_check_remark_1_3": outside_check_remark_1_3,
										"outside_check_result_1_4": outside_check_result_1_4,
										"outside_check_remark_1_4": outside_check_remark_1_4,
										"outside_check_result_1_5": outside_check_result_1_5,
										"outside_check_remark_1_5": outside_check_remark_1_5,
										"outside_check_result_2_1": outside_check_result_2_1,
										"outside_check_remark_2_1": outside_check_remark_2_1,
										"outside_check_result_2_2": outside_check_result_2_2,
										"outside_check_remark_2_2": outside_check_remark_2_2,
										"outside_check_result_3_1": outside_check_result_3_1,
										"outside_check_remark_3_1": outside_check_remark_3_1,
										"outside_check_result_3_2": outside_check_result_3_2,
										"outside_check_remark_3_2": outside_check_remark_3_2,
										"outside_check_result_3_3": outside_check_result_3_3,
										"outside_check_remark_3_3": outside_check_remark_3_3,
										"outside_check_result_3_4": outside_check_result_3_4,
										"outside_check_remark_3_4": outside_check_remark_3_4,
										"outside_check_result_4_1": outside_check_result_4_1,
										"outside_check_remark_4_1": outside_check_remark_4_1,
										"outside_check_result_4_2": outside_check_result_4_2,
										"outside_check_remark_4_2": outside_check_remark_4_2,
										"outside_check_result_5_1": outside_check_result_5_1,
										"outside_check_remark_5_1": outside_check_remark_5_1,
										"outside_check_result_6_1": outside_check_result_6_1,
										"outside_check_remark_6_1": outside_check_remark_6_1,
										"outside_check_result_6_2": outside_check_result_6_2,
										"outside_check_remark_6_2": outside_check_remark_6_2,
										"outside_check_result_7_1": outside_check_result_7_1,
										"outside_check_remark_7_1": outside_check_remark_7_1,
										"outside_check_result_7_2": outside_check_result_7_2,
										"outside_check_remark_7_2": outside_check_remark_7_2,
										"outside_check_result_7_3": outside_check_result_7_3,
										"outside_check_remark_7_3": outside_check_remark_7_3,
										"outside_check_result_8_1": outside_check_result_8_1,
										"outside_check_remark_8_1": outside_check_remark_8_1,
										"outside_check_result_8_2": outside_check_result_8_2,
										"outside_check_remark_8_2": outside_check_remark_8_2,
										"outside_check_result_9_1": outside_check_result_9_1,
										"outside_check_remark_9_1": outside_check_remark_9_1,
										"outside_check_result_9_2": outside_check_result_9_2,
										"outside_check_remark_9_2": outside_check_remark_9_2,
										"outside_check_result_9_3": outside_check_result_9_3,
										"outside_check_remark_9_3": outside_check_remark_9_3,
										"outside_check_result_9_4": outside_check_result_9_4,
										"outside_check_remark_9_4": outside_check_remark_9_4,
										"outside_check_result_9_5": outside_check_result_9_5,
										"outside_check_remark_9_5": outside_check_remark_9_5,
										"outside_check_result_9_6": outside_check_result_9_6,
										"outside_check_remark_9_6": outside_check_remark_9_6,

										"before_use_check_result_1": before_use_check_result_1,
										"before_use_check_remark_1": before_use_check_remark_1,
										"before_use_check_result_2": before_use_check_result_2,
										"before_use_check_remark_2": before_use_check_remark_2,
										"before_use_check_result_3": before_use_check_result_3,
										"before_use_check_remark_3": before_use_check_remark_3,
										"before_use_check_result_4": before_use_check_result_4,
										"before_use_check_remark_4": before_use_check_remark_4,
										"before_use_check_result_5": before_use_check_result_5,
										"before_use_check_remark_5": before_use_check_remark_5,
										"before_use_check_result_6": before_use_check_result_6,
										"before_use_check_remark_6": before_use_check_remark_6,
										"before_use_check_result_7": before_use_check_result_7,
										"before_use_check_remark_7": before_use_check_remark_7,
										"before_use_check_result_8": before_use_check_result_8,
										"before_use_check_remark_8": before_use_check_remark_8,
										"before_use_check_result_9": before_use_check_result_9,
										"before_use_check_remark_9": before_use_check_remark_9,
										"before_use_check_result_10": before_use_check_result_10,
										"before_use_check_remark_10": before_use_check_remark_10
									})
								elif params['car_type'] == "van":
									if member_lang == "en":
										car_type_text = "Van"
									else:
										car_type_text = "รถตู้"

									car_inspection_list.append({
										"id_index": data_start_at+(i+1),
										"request_no": request_driver_json[i]['request_no'],
										"start_date": start_datetime,
										"check_status": request_driver_json[i]['check_status'],
										"check_status_text": check_status_text,
										"car_type": car_type_text,
										"car_brand": request_driver_json[i]['car_brand_name'],
										"license_plate": request_driver_json[i]['license_plate'],
										"passenger_name": request_driver_json[i]['passenger_name'],
										"driver_name": driver_name,

										"outside_check_result_1_1": outside_check_result_1_1,
										"outside_check_remark_1_1": outside_check_remark_1_1,
										"outside_check_result_1_2": outside_check_result_1_2,
										"outside_check_remark_1_2": outside_check_remark_1_2,
										"outside_check_result_1_3": outside_check_result_1_3,
										"outside_check_remark_1_3": outside_check_remark_1_3,
										"outside_check_result_1_4": outside_check_result_1_4,
										"outside_check_remark_1_4": outside_check_remark_1_4,
										"outside_check_result_1_5": outside_check_result_1_5,
										"outside_check_remark_1_5": outside_check_remark_1_5,
										"outside_check_result_2_1": outside_check_result_2_1,
										"outside_check_remark_2_1": outside_check_remark_2_1,
										"outside_check_result_2_2": outside_check_result_2_2,
										"outside_check_remark_2_2": outside_check_remark_2_2,
										"outside_check_result_3_1": outside_check_result_3_1,
										"outside_check_remark_3_1": outside_check_remark_3_1,
										"outside_check_result_4_1": outside_check_result_4_1,
										"outside_check_remark_4_1": outside_check_remark_4_1,
										"outside_check_result_4_2": outside_check_result_4_2,
										"outside_check_remark_4_2": outside_check_remark_4_2,
										"outside_check_result_4_3": outside_check_result_4_3,
										"outside_check_remark_4_3": outside_check_remark_4_3,
										"outside_check_result_5_1": outside_check_result_5_1,
										"outside_check_remark_5_1": outside_check_remark_5_1,
										"outside_check_result_5_2": outside_check_result_5_2,
										"outside_check_remark_5_2": outside_check_remark_5_2,
										"outside_check_result_6_1": outside_check_result_6_1,
										"outside_check_remark_6_1": outside_check_remark_6_1,
										"outside_check_result_7_1": outside_check_result_7_1,
										"outside_check_remark_7_1": outside_check_remark_7_1,
										"outside_check_result_7_2": outside_check_result_7_2,
										"outside_check_remark_7_2": outside_check_remark_7_2,
										"outside_check_result_8_1": outside_check_result_8_1,
										"outside_check_remark_8_1": outside_check_remark_8_1,
										"outside_check_result_8_2": outside_check_result_8_2,
										"outside_check_remark_8_2": outside_check_remark_8_2,
										"outside_check_result_8_3": outside_check_result_8_3,
										"outside_check_remark_8_3": outside_check_remark_8_3,
										"outside_check_result_9_1": outside_check_result_9_1,
										"outside_check_remark_9_1": outside_check_remark_9_1,
										"outside_check_result_9_2": outside_check_result_9_2,
										"outside_check_remark_9_2": outside_check_remark_9_2,
										"outside_check_result_10_1": outside_check_result_10_1,
										"outside_check_remark_10_1": outside_check_remark_10_1,
										"outside_check_result_11_1": outside_check_result_11_1,
										"outside_check_remark_11_1": outside_check_remark_11_1,
										"outside_check_result_11_2": outside_check_result_11_2,
										"outside_check_remark_11_2": outside_check_remark_11_2,
										"outside_check_result_11_3": outside_check_result_11_3,
										"outside_check_remark_11_3": outside_check_remark_11_3,
										"outside_check_result_11_4": outside_check_result_11_4,
										"outside_check_remark_11_4": outside_check_remark_11_4,
										"outside_check_result_11_5": outside_check_result_11_5,
										"outside_check_remark_11_5": outside_check_remark_11_5,

										"before_use_check_result_1": before_use_check_result_1,
										"before_use_check_remark_1": before_use_check_remark_1,
										"before_use_check_result_2": before_use_check_result_2,
										"before_use_check_remark_2": before_use_check_remark_2,
										"before_use_check_result_3": before_use_check_result_3,
										"before_use_check_remark_3": before_use_check_remark_3,
										"before_use_check_result_4": before_use_check_result_4,
										"before_use_check_remark_4": before_use_check_remark_4,
										"before_use_check_result_5": before_use_check_result_5,
										"before_use_check_remark_5": before_use_check_remark_5,
										"before_use_check_result_6": before_use_check_result_6,
										"before_use_check_remark_6": before_use_check_remark_6,
										"before_use_check_result_7": before_use_check_result_7,
										"before_use_check_remark_7": before_use_check_remark_7,
										"before_use_check_result_8": before_use_check_result_8,
										"before_use_check_remark_8": before_use_check_remark_8,
										"before_use_check_result_9": before_use_check_result_9,
										"before_use_check_remark_9": before_use_check_remark_9,
										"before_use_check_result_10": before_use_check_result_10,
										"before_use_check_remark_10": before_use_check_remark_10
									})

						result = {
									"status" : True,
									"msg" : get_api_message("car_inspection_report" , "get_car_inspection_report_success" , member_lang),
									"car_type" : params['car_type'],
									"car_inspection_data" : car_inspection_list,
									"total_data" : total_data
								}
					else:
						result = { 
							"status" : False,
							"msg" : get_api_message("car_inspection_report" , "please_check_your_car_type_value" , member_lang)
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
	function_name = "car_inspection_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_car_inspection_report_form(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_car_type = "car_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_car_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']

			if member_lang == "en":
				check_status_text_0 = "Have not checked the car inspection"
				check_status_text_1 = "Skip the car inspection"
				check_status_text_2 = "Waiting for confirmation of car inspection from passengers"
				check_status_text_3 = "Inspect the car does not pass"
				check_status_text_4 = "Successfully inspected the car"
				check_status_text_5 = "The passenger did not confirm the car inspection"
			else:
				check_status_text_0 = "ยังไม่ได้ตรวจสภาพรถ"
				check_status_text_1 = "ข้ามการตรวจสภาพรถ"
				check_status_text_2 = "รอยืนยันการตรวจสภาพรถจากผู้โดยสาร"
				check_status_text_3 = "ตรวจสภาพรถไม่ผ่าน"
				check_status_text_4 = "ตรวจสภาพรถเรียบร้อย"
				check_status_text_5 = "ผู้โดยสารไม่ยืนยันการตรวจสภาพรถ"

			check_status_list = [
									{"code": "0","name": check_status_text_0},
									{"code": "1","name": check_status_text_1},
									{"code": "2","name": check_status_text_2},
									{"code": "3","name": check_status_text_3},
									{"code": "4","name": check_status_text_4},
									{"code": "5","name": check_status_text_5}
								]

			car_type_list = []

			car_type = db.car_type.find()

			if car_type is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)

				for i in range(len(car_type_json)):
					if member_lang == "en":
						car_type_name = car_type_json[i]['car_type_name_en']
					else:
						car_type_name = car_type_json[i]['car_type_name_th']

					car_type_list.append({
						"code" : car_type_json[i]['car_type_code'],
						"name": car_type_name
					})

			car_inspection_column = []
			
			outside_inspection = db.outside_inspection.find({"car_type_code": params['car_type']})
			inspection_before_use = db.inspection_before_use.find({"check_status": "1"})

			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			outside_inspection_object = dumps(outside_inspection)
			outside_inspection_json = json.loads(outside_inspection_object)

			inspection_before_use_object = dumps(inspection_before_use)
			inspection_before_use_json = json.loads(inspection_before_use_object)

			outside_inspection_list = []
			inspection_before_use_list = []
			total_outside_inspection = []
			total_inspection_before_use = 0

			if member_lang == "en":
				request_no = "Request number"
				start_date = "Start date"
				check_status = "Check status"
				car_type = "Car type"
				car_brand = "Car brand"
				license_plate = "License plate"
				passenger_name = "Passenger name"
				driver_name = "Driver name"
			else:	
				request_no = "เลขที่งาน"
				start_date = "วันที่เดินทาง"
				check_status = "สถานะการตรวจ"
				car_type = "ประเภทรถ"
				car_brand = "ยี่ห้อรถ"
				license_plate = "ทะเบียนรถ"
				passenger_name = "ชื่อผู้โดยสาร"
				driver_name = "ชื่อคนขับ"

			car_inspection_column = [
				"#",
				request_no,
				start_date,
				check_status,
				car_type,
				car_brand,
				license_plate,
				passenger_name,
				driver_name
			]

			for j in range(len(outside_inspection_json)):
				if member_lang == "en":
					point_name = outside_inspection_json[j]['point_name_en']
				else:
					point_name = outside_inspection_json[j]['point_name_th']

				for k in range(len(outside_inspection_json[j]['part'])):
					if member_lang == "en":
						part_name = outside_inspection_json[j]['part'][k]['part_name_en']
						column_remark_name = "Remark"
					else:
						part_name = outside_inspection_json[j]['part'][k]['part_name_th']
						column_remark_name = "หมายเหตุ"

					column_result_name = point_name+" : "+part_name
					car_inspection_column.append(column_result_name)
					car_inspection_column.append(column_remark_name)

				total_outside_inspection.append(len(outside_inspection_json[j]['part']))

			for j in range(len(inspection_before_use_json)):
				if member_lang == "en":
					check_name = inspection_before_use_json[j]['check_name_en']
					column_remark_name = "Remark"
				else:
					check_name = inspection_before_use_json[j]['check_name_th']
					column_remark_name = "หมายเหตุ"

				car_inspection_column.append(check_name)
				car_inspection_column.append(column_remark_name)

			total_inspection_before_use = len(inspection_before_use_json)

			result = {
						"status" : True,
						"msg" : get_api_message("get_car_inspection_report_form" , "get_car_inspection_report_form_success" , member_lang),
						"car_type" : car_type_list,
						"check_status" : check_status_list,
						"car_inspection_column": car_inspection_column,
						"total_outside_inspection": total_outside_inspection,
						"total_inspection_before_use": total_inspection_before_use,
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
	function_name = "get_car_inspection_report_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def package_usage_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_package_usage_type = "package_usage_type" in params
	isset_package_type = "package_type" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_package_usage_type and isset_package_type and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if company_id is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("package_usage_report" , "you_are_not_a_company_member" , member_lang)
						}
			else:
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
							"msg" : get_api_message("package_usage_report" , "data_start_is_not_a_number" , member_lang)
						}
				elif not check_data_length:
					result = { 
							"status" : False,
							"msg" : get_api_message("package_usage_report" , "data_length_is_not_a_number" , member_lang)
						}
				else:
					where_param = { 
										"company_id": company_id
									}

					#package_code , package_name , member_name
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "package_code": {"$regex": params['search_text']} },
													{ "package_name_en": {"$regex": params['search_text']} },
													{ "package_name_th": {"$regex": params['search_text']} },
													{ "member_name": {"$regex": params['search_text']} }
													
												]
									}
						where_param.update(add_params)

					if params['package_usage_type'] == "quota" or params['package_usage_type'] == "share":
						add_params = {"package_usage_type" : params['package_usage_type']}
						where_param.update(add_params)

					if params['package_type'] == "hour" or params['package_type'] == "time":
						add_params = {"package_type" : params['package_type']}
						where_param.update(add_params)

					if params['sort_name'] == "":
						sort_name = "updated_at"
						sort_type = -1
					else:
						#การ sort ข้อมูล
						# package_code = package_code
						# package_name = package_name_en / package_name_th
						# remaining_date_amount = end_date_int
						# package_usage_type = package_usage_type
						# member_name = member_name
						# package_type = package_type
						# total_amount = total_amount
						# usage_amount = usage_amount
						# remaining_amount = remaining_amount

						if params['sort_name'] == "package_name":
							if member_lang == "en":
								sort_name = "package_name_en"
							else:
								sort_name = "package_name_th"
						elif params['sort_name'] == "remaining_date_amount":
							sort_name = "end_date_int"
						else:
							sort_name = params['sort_name']

						if params['sort_type'] == "desc":
							sort_type = -1
						else:
							sort_type = 1

						
					member_package = db.member_package.find(where_param).sort([(sort_name, sort_type)]).skip(data_start_at).limit(data_length)
					total_data = db.member_package.find(where_param).count()

					if member_package is not None:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						member_package_object = dumps(member_package)
						member_package_json = json.loads(member_package_object)

						package_usage_list = []
						package_admin = ""

						for i in range(len(member_package_json)):
							if member_lang == "en":
								package_name = member_package_json[i]['package_name_en']

								if member_package_json[i]['package_usage_type'] == "quota":
									package_usage_type = "ใช้ Package แบบแบ่ง"
								else:
									package_usage_type = "ใช้ Package แบบร่วม"

								if member_package_json[i]['package_type'] == "time":
									package_type = "รายครั้ง"
								else:
									package_type = "รายชั่วโมง"
							else:
								package_name = member_package_json[i]['package_name_th']

								if member_package_json[i]['package_usage_type'] == "quota":
									package_usage_type = "Quota Package"
								else:
									package_usage_type = "Share Package"

								if member_package_json[i]['package_type'] == "time":
									package_type = "Per Time"
								else:
									package_type = "Per Hour"


							if member_package_json[i]['package_usage_type'] == "quota":
								total_amount = str(member_package_json[i]['total_amount'])
								usage_amount = str(member_package_json[i]['usage_amount'])
								remaining_amount = str(member_package_json[i]['remaining_amount'])
							else:
								total_amount = "-"
								usage_amount = str(member_package_json[i]['usage_amount'])
								remaining_amount = "-"

							current_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
							end_date = datetime.strptime(member_package_json[i]['end_date'], '%Y-%m-%d')

							if end_date > current_date:
								timediff = end_date - current_date
								remaining_date_amount = str(timediff.days)
							else:
								remaining_date_amount = "0"

							admin = db.package_admin.find_one({"company_package_id": member_package_json[i]['company_package_id']})
							
							if admin is not None:	
								# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
								admin_object = dumps(admin)
								admin_json = json.loads(admin_object)

								if len(admin_json['package_admin']) > 0:
									for j in range(len(admin_json['package_admin'])):
										admin_info = get_member_info_by_id(admin_json['package_admin'][j])

										if j == 0:
											package_admin = admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']
										else:
											package_admin = package_admin+" , "+admin_info['member_firstname_en']+" "+admin_info['member_lastname_en']

							package_usage_list.append({
								"id_index": data_start_at+(i+1),
								"package_code": member_package_json[i]['package_code'],
								"package_name": package_name,
								"package_usage_type": package_usage_type,
								"member_name": member_package_json[i]['member_name'],
								"package_type": package_type,
								"package_admin": package_admin,
								"remaining_date_amount": remaining_date_amount,
								"total_amount": total_amount,
								"usage_amount": usage_amount,
								"remaining_amount": remaining_amount
							})		

					result = {
								"status" : True,
								"msg" : get_api_message("package_usage_report" , "get_package_usage_report_success" , member_lang),
								"package_usage" : package_usage_list,
								"total_data" : total_data,

								"len": len(member_package_json)
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
	function_name = "package_usage_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_package_usage_report_form(request):
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

			if member_lang == "en":		
				package_usage_type_quota = "Quota Package"
				package_usage_type_share = "Share Package"
				package_type_hour = "Per Hour"
				package_type_time = "Per Time"
			else:
				package_usage_type_quota = "ใช้ Package แบบแบ่ง"
				package_usage_type_share = "ใช้ Package แบบร่วม"
				package_type_hour = "รายชั่วโมง"
				package_type_time = "รายครั้ง"

			package_usage_type_list = [
									{"code": "quota","name": package_usage_type_quota},
									{"code": "share","name": package_usage_type_share}
								]

			package_type_list = [
									{"code": "hour","name": package_type_hour},
									{"code": "time","name": package_type_time}
								]
		
			result = {
						"status" : True,
						"msg" : get_api_message("get_package_usage_report_form" , "get_package_usage_report_form_success" , member_lang),
						"package_usage_type" : package_usage_type_list,
						"package_type" : package_type_list
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
	function_name = "get_package_usage_report_form"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def unpaid_expense_report(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_data_start_at = "data_start_at" in params
	isset_data_length = "data_length" in params
	isset_search_text = "search_text" in params
	isset_start_date = "start_date" in params
	isset_end_date = "end_date" in params
	isset_sort_name = "sort_name" in params
	isset_sort_type = "sort_type" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_data_start_at and isset_data_length and isset_search_text and isset_start_date and isset_end_date and isset_sort_name and isset_sort_type:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']

			if company_id is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("unpaid_expense_report" , "you_are_not_a_company_member" , member_lang)
						}
			else:
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
							"msg" : get_api_message("unpaid_expense_report" , "data_start_is_not_a_number" , member_lang)
						}
				elif not check_data_length:
					result = { 
							"status" : False,
							"msg" : get_api_message("unpaid_expense_report" , "data_length_is_not_a_number" , member_lang)
						}
				else:
					where_param = { 
										"company_id": company_id,
										"billing_statement_status": "0"
									}

					#billing_statement_code
					if params['search_text'] != "":
						add_params = {
										"$or": [
													{ "billing_statement_code": {"$regex": params['search_text']} }
												]
									}
						where_param.update(add_params)

					if params['start_date'] != "" and params['end_date'] != "":
						start_date_int = int(datetime.strptime(params['start_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
						end_date_int = int(datetime.strptime(params['end_date'], '%Y-%m-%d').strftime('%Y%m%d')) 
					
						add_params = {"billing_statement_date_int" : {"$gte" : start_date_int , "$lte" : end_date_int}}
						where_param.update(add_params)

					if params['sort_name'] == "":
						sort_name = "updated_at"
						sort_type = -1
					else:
						#การ sort ข้อมูล
						# billing_statement_code = billing_statement_code
						# billing_statement_date = created_at
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

						unpaid_expense_list = []

						for i in range(len(billing_statement_json)):
							if member_lang == "en":
								billing_statement_status = "Waiting"
							else:
								billing_statement_status = "รอดำเนินการ"

							billing_statement_date = datetime.strptime(billing_statement_json[i]['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
							sum_paid = '{:,.2f}'.format(round(float(billing_statement_json[i]['sum_paid']) , 2)) 

							unpaid_expense_list.append({
								"id_index": data_start_at+(i+1),
								"billing_statement_code": billing_statement_json[i]['billing_statement_code'],
								"billing_statement_date": billing_statement_date,
								"sum_paid": sum_paid,
								"billing_statement_status": billing_statement_status
							})		

					result = {
								"status" : True,
								"msg" : get_api_message("unpaid_expense_report" , "get_unpaid_expense_report_success" , member_lang),
								"unpaid_expense" : unpaid_expense_list,
								"total_data" : total_data
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
	function_name = "unpaid_expense_report"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result