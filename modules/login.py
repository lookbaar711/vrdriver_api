from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from function.notification import send_push_message
from function.checktokenexpire import check_token_expire , check_token_expire_backend
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
from modules.upload_image import upload_profile_image
from modules.send_email import send_email

def testlogin():
	array = list(db.user.find())
	return json_encoder(array)

def login(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None
	member_type = None
	member_lang = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_os_type = "os_type" in params
	isset_username = "member_username" in params
	isset_password = "member_password" in params
	isset_noti_key = "noti_key" in params
	isset_user_type = "user_type" in params

	if isset_accept and isset_content_type and isset_app_version and isset_os_type and isset_username and isset_password and isset_noti_key and isset_user_type:
		if params['user_type'] == "customer" or params['user_type'] == "web":
			check_username = db.member.find_one({
													"member_username": params['member_username'].strip().lower(),
													"member_type": "customer",
													"activated_at": {"$ne": None}
												})
		else:
			check_username = db.member.find_one({
													"member_username": params['member_username'].strip().lower(),
													"member_type": "driver"
												})

		if check_username is None:
			result = { 
						"status" : False,
						"username_invalid" : False,
						"password_invalid" : False,
						"msg" : get_api_message("login" , "username_not_found" , member_lang)
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			member_object = dumps(check_username)
			member_json = json.loads(member_object)
			member_id = member_json['_id']['$oid']
			member_type = member_json['member_type']
			member_lang = member_json['member_lang']

			#เอา password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(params['member_password'].encode())
			hash_pass = hash_input_pass.hexdigest()

			#ถ้า password ตรงกัน
			if member_json['member_password'] == hash_pass:
				# update member_token, noti_key
				where_param = { "_id": ObjectId(member_json['_id']['$oid']) }

				#ถ้า member_token ใน tb เป็น null
				if member_json['member_token'] is None:
					#generate token
					token = get_random_token(40)
					#ถ้าค่า noti_key ใน tb เป็น null
					if member_json['noti_key'] is None:
						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']
					#ถ้าค่า noti_key ใน tb ไม่ใช่ null ให้อัพเดตเป็นค่า noti_key เป็นค่าเดิมใน tb
					else:
						#noti_key = params['noti_key']

						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						elif member_json['noti_key'] == params['noti_key']:
							noti_key = member_json['noti_key']
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']

				#ถ้า member_token ใน tb ไม่ใช่ null
				else:
					#ถ้าค่า noti_key ใน tb เป็น null
					if member_json['noti_key'] is None:
						#generate token
						token = get_random_token(40)

						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']
					#ถ้าค่า noti_key ใน tb ไม่ใช่ null
					else:
						#ถ้า noti_key เป็นค่าเดิม ไม่ต้องอัพเดต member_token
						if member_json['noti_key'] == params['noti_key']:
							token = member_json['member_token']
							noti_key = member_json['noti_key']
						#ถ้า noti_key เป็นค่าใหม่ ให้อัพเดต member_token และส่ง noti ไปหา noti_key ค่าเก่า
						else:
							#generate token
							token = get_random_token(40)

							#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็นค่า null
							if params['noti_key'] is None:
								noti_key = None
							#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
							else:
								noti_key = params['noti_key']

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

				value_param = {
								"$set":
									{
										"member_token": token,
										"noti_key": noti_key,
										"os_type": params['os_type'],
										"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					if params['noti_key'] is not None:
						#เช็คว่าถ้ามี user ที่ใช้ noti_key เดียวกันอยู่ ให้ logout user อื่นออกจากระบบ
						check_noti_key = db.member.find({
															"member_username": {"$ne": params['member_username'].strip().lower()},
															"noti_key": params['noti_key']
														})

						if check_noti_key is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							mem_object = dumps(check_noti_key)
							mem_json = json.loads(mem_object)

							for i in range(len(mem_json)):
								#update member_token เป็น null เพื่อเตะ user ที่ใช้งานอยู่ออกจากระบบ
								where_param_2 = { "_id": ObjectId(mem_json[i]['_id']['$oid']) }
								value_param_2 = {
													"$set":
														{
															"member_token": None,
															"noti_key": None,
															"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
														}
												}
								db.member.update(where_param_2 , value_param_2)

					result = {
								"status" : True,
								"msg" : get_api_message("login" , "login_success" , member_lang),
								"token" : token
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("login" , "data_update_failed" , member_lang)
							}
			else:
				result = {
							"status" : False,
							"username_invalid" : True,
							"password_invalid" : False,
							"msg" : get_api_message("login" , "password_invalid" , member_lang)
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = member_type
	function_name = "login"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def login_social(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None
	member_type = None
	member_lang = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_os_type = "os_type" in params
	isset_social_type = "social_type" in params
	isset_social_id = "social_id" in params
	isset_noti_key = "noti_key" in params

	if isset_accept and isset_content_type and isset_app_version and isset_os_type and isset_social_type and isset_social_id and isset_noti_key:
		if params['social_type'] == "line":
			check_social_id = db.member.find_one({
													"member_type": "customer",
													"social_type": "line",
													"social_id": params['social_id']
												})

			if check_social_id is None:
				result = { 
							"status" : False,
							"social_type_invalid" : True,
							"social_id_invalid" : False,
							"msg" : get_api_message("login_social" , "social_id_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(check_social_id)
				member_json = json.loads(member_object)
				member_id = member_json['_id']['$oid']
				member_type = member_json['member_type']
				member_lang = member_json['member_lang']

				
				# update member_token, noti_key
				where_param = { "_id": ObjectId(member_json['_id']['$oid']) }

				#ถ้า member_token ใน tb เป็น null
				if member_json['member_token'] is None:
					#generate token
					token = get_random_token(40)
					#ถ้าค่า noti_key ใน tb เป็น null
					if member_json['noti_key'] is None:
						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']
					#ถ้าค่า noti_key ใน tb ไม่ใช่ null ให้อัพเดตเป็นค่า noti_key เป็นค่าเดิมใน tb
					else:
						#noti_key = params['noti_key']

						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						elif member_json['noti_key'] == params['noti_key']:
							noti_key = member_json['noti_key']
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']

				#ถ้า member_token ใน tb ไม่ใช่ null
				else:
					#ถ้าค่า noti_key ใน tb เป็น null
					if member_json['noti_key'] is None:
						#generate token
						token = get_random_token(40)

						#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็น null
						if params['noti_key'] is None:
							noti_key = None
						#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
						else:
							noti_key = params['noti_key']
					#ถ้าค่า noti_key ใน tb ไม่ใช่ null
					else:
						#ถ้า noti_key เป็นค่าเดิม ไม่ต้องอัพเดต member_token
						if member_json['noti_key'] == params['noti_key']:
							token = member_json['member_token']
							noti_key = member_json['noti_key']
						#ถ้า noti_key เป็นค่าใหม่ ให้อัพเดต member_token และส่ง noti ไปหา noti_key ค่าเก่า
						else:
							#generate token
							token = get_random_token(40)

							#ถ้าค่า noti_key ที่ส่งเข้ามาเป็น null ให้อัพเดตเป็นค่า null
							if params['noti_key'] is None:
								noti_key = None
							#ถ้าค่า noti_key ที่ส่งเข้ามาไม่ใช่ null ให้อัพเดตเป็นค่า noti_key ที่ส่งเข้ามา
							else:
								noti_key = params['noti_key']

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

				value_param = {
								"$set":
									{
										"member_token": token,
										"noti_key": noti_key,
										"os_type": params['os_type'],
										"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : get_api_message("login_social" , "login_success" , member_lang),
								"token" : token
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("login_social" , "data_update_failed" , member_lang)
							}	
		else:
			result = {
						"status" : False,
						"social_type_invalid" : False,
						"social_id_invalid" : False,
						"msg" : get_api_message("login_social" , "social_type_is_invalid" , member_lang)
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = member_type
	function_name = "login_social"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def logout(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None
	member_type = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member = db.member.find_one({"member_token": token})
			
			if member is None:
				result = {"status" : False}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(member)
				member_json = json.loads(member_object)
				member_id = member_json['_id']['$oid']
				member_type = member_json['member_type']
				member_lang = member_json['member_lang']

				# update member_token, noti_key
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
				
				if db.member.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : get_api_message("logout" , "logout_success" , member_lang)
							}
				else:
					result = {
								"status" : False,
								"msg" : get_api_message("logout" , "data_update_failed" , member_lang)
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
	user_type = member_type
	function_name = "logout"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def check_token(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None
	member_type = None

	if isset_accept and isset_content_type and isset_token:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_id = member_info['_id']['$oid']
			member_type = member_info['member_type']

			member = db.member.find_one({"member_token": token})
			if member is None:
				result = {
							"status" : False,
							"msg" : "False"
						}
			else:
				result = {
							"status" : True,
							"msg" : "True"
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
	user_type = member_type
	function_name = "check_token"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def change_password(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None
	member_type = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_current_password = "current_password" in params
	isset_new_password = "new_password" in params
	isset_confirm_password = "confirm_password" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_current_password and isset_new_password and isset_confirm_password:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_id = member_info['_id']['$oid']
			member_type = member_info['member_type']
			member_lang = member_info['member_lang']
			

			check_member = db.member.find_one({"member_token": token})

			if check_member is None:
				result = { 
							"status" : False,
							"msg" : get_api_message("change_password" , "data_not_found" , member_lang)
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				member_object = dumps(check_member)
				member_json = json.loads(member_object)

				#เอา current password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(params['current_password'].encode())
				current_password = hash_input_pass.hexdigest()

				#เช็คว่ารหัสผ่านตรงกันหรือไม่
				if current_password != member_json['member_password']:
					result = { 
								"status" : False,
								"msg" : get_api_message("change_password" , "current_password_is_incorrect" , member_lang)
							}
				else:
					#check new password & confirm password
					if params['new_password']!=params['confirm_password']:
						result = { 
							"status" : False,
							"msg" : get_api_message("change_password" , "new_password_do_not_match" , member_lang)
						}
					else:
						count_password = len(params['new_password'])
						if count_password < 6:
							result = {
										"status" : False,
										"msg" : get_api_message("change_password" , "new_password_less_than_6_character" , member_lang)
									}
						else:
							if params['new_password'] == params['current_password']:
								result = {
											"status" : False,
											"msg" : get_api_message("change_password" , "new_password_can_not_be_the_same_as_your_current_password" , member_lang)
										}
							else:
								#เอา new_password ที่รับมาเข้ารหัส
								hash_input_pass = hashlib.md5(params['new_password'].encode())
								hash_pass = hash_input_pass.hexdigest()

								# update password
								where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
								value_param = {
												"$set":
													{
														"member_password": hash_pass,
														"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.member.update(where_param , value_param):
									result = {
												"status" : True,
												"msg" : get_api_message("change_password" , "change_password_success" , member_lang)
											}
								else:
									result = {
												"status" : False,
												"msg" : get_api_message("change_password" , "data_update_failed" , member_lang)
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
	user_type = member_type
	function_name = "change_password"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def forgot_password(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None
	member_type = None
	member_lang = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_email = "member_email" in params
	isset_user_type = "user_type" in params

	if isset_accept and isset_content_type and isset_app_version and isset_email and isset_user_type:
		check_email = db.member.find_one({
											"member_type": params['user_type'],
											"member_email": params['member_email'].strip().lower()
										})

		if check_email is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("forgot_password" , "data_not_found" , member_lang)
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			member_object = dumps(check_email)
			member_json = json.loads(member_object)
			member_id = member_json['_id']['$oid']
			member_type = member_json['member_type']
			member_lang = member_json['member_lang']

			#generate password
			generate_password = get_random_token(8)

			#เอา generate password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(generate_password.encode())
			hash_pass = hash_input_pass.hexdigest()

			# update password
			where_param = { "_id": ObjectId(member_json['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"member_password": hash_pass,
									"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.member.update(where_param , value_param):
				#send email
				email_type = "forgot_password"
				subject = "VR Driver : Forgot password"
				to_email = params['member_email'].lower()
				template_html = "forgot_password.html"
				data = { "password" : generate_password }

				check_send_email = send_email(email_type , subject , to_email , template_html , data)

				if check_send_email:
					result = {
								"status" : True,
								"msg" : get_api_message("forgot_password" , "forgot_password_success" , member_lang)
							}
				else:
					result = {
							"status" : False,
							"msg" : get_api_message("forgot_password" , "can_not_send_email" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("forgot_password" , "data_update_failed" , member_lang)
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = member_type
	function_name = "forgot_password"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def change_language(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	member_id = None
	member_type = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_member_lang = "member_lang" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_member_lang:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire(token)

		if check_token:
			member_info = get_member_info(token)
			member_id = member_info['_id']['$oid']
			member_type = member_info['member_type']
			member_lang = member_info['member_lang']

			if params['member_lang']=="en":
				member_lang = "en"
			else:
				member_lang = "th"

			# update member lang
			where_param = { "member_token": token }
			value_param = {
							"$set":
								{
									"member_lang": member_lang,
									"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.member.update(where_param , value_param):
				result = {
							"status" : True,
							"msg" : get_api_message("change_language" , "change_language_success" , member_lang)
						}
			else:
				result = {
							"status" : False,
							"msg" : get_api_message("change_language" , "data_update_failed" , member_lang)
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
	user_type = member_type
	function_name = "change_language"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result
	
def get_specification_policy(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	member_id = None
	member_type = None
	member_lang = "en"

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_user_type = "user_type" in params

	if isset_accept and isset_content_type and isset_app_version and isset_user_type:
		member_type = params['user_type']

		specification = db.specification.find_one({"user_type": params['user_type']})
		
		if specification is None:
			result = { 
						"status" : False,
						"msg" : get_api_message("get_specification_policy" , "data_not_found" , member_lang)
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			specification_object = dumps(specification)
			specification_json = json.loads(specification_object)

			result = {
						"status" : True,
						"msg" : get_api_message("get_specification_policy" , "get_specification_and_policy_success" , member_lang),
						"user_type" : specification_json['user_type'],
						"specification_en" : specification_json['specification_en'],
						"specification_th" : specification_json['specification_th'],
						"policy_en" : specification_json['policy_en'],
						"policy_th" : specification_json['policy_th']
					}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}


	#set log detail
	user_type = member_type
	function_name = "get_specification_policy"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , member_id , function_name , request_headers , params_get , params_post , result)

	return result

def backend_login(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_username = "admin_username" in params
	isset_password = "admin_password" in params

	if isset_accept and isset_content_type and isset_app_version and isset_username and isset_password:
		check_username = db.admin.find_one({
												"admin_username": params['admin_username'].strip().lower(),
												"admin_status": "1"
											})

		if check_username is None:
			result = { 
						"status" : False,
						"username_invalid" : False,
						"password_invalid" : False,
						"msg" : "Username not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			admin_object = dumps(check_username)
			admin_json = json.loads(admin_object)
			admin_id = admin_json['_id']['$oid']

			#เอา password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(params['admin_password'].encode())
			hash_pass = hash_input_pass.hexdigest()

			#ถ้า password ตรงกัน
			if admin_json['admin_password'] == hash_pass:
				#generate token
				token = get_random_token(40)

				# update admin_token
				where_param = { "_id": ObjectId(admin_json['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"admin_token": token,
										"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				if db.admin.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Login success.",
								"token" : token,
								"fullname" : admin_json['admin_firstname']+" "+admin_json['admin_lastname'],
								"system" : "backend"
							}
				else:
					result = {
								"status" : False,
								"msg" : "Data update failed."
							}
			else:
				result = {
							"status" : False,
							"username_invalid" : True,
							"password_invalid" : False,
							"msg" : "Password invalid."
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "admin"
	function_name = "backend_login"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def backend_logout(request):
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
			admin = db.admin.find_one({
											"admin_token": token,
											"admin_status": "1"
										})
			
			if admin is None:
				result = {"status" : False}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				admin_object = dumps(admin)
				admin_json = json.loads(admin_object)
				admin_id = admin_json['_id']['$oid']

				# update admin_token, noti_key
				where_param = { "_id": ObjectId(admin_json['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"admin_token": None,
										"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				if db.admin.update(where_param , value_param):
					result = {
								"status" : True,
								"msg" : "Logout success."
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
	user_type = "admin"
	function_name = "backend_logout"
	request_headers = request.headers
	params_get = None
	params_post = None
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def backend_change_password(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	isset_token = "Authorization" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_current_password = "current_password" in params
	isset_new_password = "new_password" in params
	isset_confirm_password = "confirm_password" in params

	if isset_accept and isset_content_type and isset_token and isset_app_version and isset_current_password and isset_new_password and isset_confirm_password:
		#เช็ค token ว่า expire แล้วหรือยัง
		token = request.headers['Authorization']
		check_token = check_token_expire_backend(token)

		if check_token:
			check_admin = db.admin.find_one({
												"admin_token": token,
												"admin_status": "1"
											})

			if check_admin is None:
				result = { 
							"status" : False,
							"msg" : "Admin not found."
						}
			else:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				admin_object = dumps(check_admin)
				admin_json = json.loads(admin_object)
				admin_id = admin_json['_id']['$oid']

				#เอา current password ที่รับมาเข้ารหัส
				hash_input_pass = hashlib.md5(params['current_password'].encode())
				current_password = hash_input_pass.hexdigest()

				#เช็คว่ารหัสผ่านตรงกันหรือไม่
				if current_password != admin_json['admin_password']:
					result = { 
								"status" : False,
								"msg" : "Current password is incorrect."
							}
				else:
					#check new password & confirm password
					if params['new_password']!=params['confirm_password']:
						result = { 
							"status" : False,
							"msg" : "New password do not match."
						}
					else:
						count_password = len(params['new_password'])
						if count_password < 6:
							result = {
										"status" : False,
										"msg" : "New password less than 6 character."
									}
						else:
							if params['new_password'] == params['current_password']:
								result = {
											"status" : False,
											"msg" : "New password can't be the same as your current password."
										}
							else:
								#เอา new_password ที่รับมาเข้ารหัส
								hash_input_pass = hashlib.md5(params['new_password'].encode())
								hash_pass = hash_input_pass.hexdigest()

								# update password
								where_param = { "_id": ObjectId(admin_id) }
								value_param = {
												"$set":
													{
														"admin_password": hash_pass,
														"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								if db.admin.update(where_param , value_param):
									result = {
												"status" : True,
												"msg" : "Change password success."
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
	user_type = "admin"
	function_name = "backend_change_password"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def backend_forgot_password(request):
	#เช็ค parameter ใน header ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_accept = "Accept" in request.headers
	isset_content_type = "Content-Type" in request.headers
	admin_id = None

	params = json.loads(request.data)

	#เช็ค parameter ว่าส่งมาไหม ถ้าส่งมาจะมีค่าเป็น true ไม่ส่งมาจะมีค่าเป็น false
	isset_app_version = "app_version" in params
	isset_email = "admin_email" in params

	if isset_accept and isset_content_type and isset_app_version and isset_email:
		check_email = db.admin.find_one({
											"admin_email": params['admin_email'].strip().lower(),
											"admin_status": "1"
										})

		if check_email is None:
			result = { 
						"status" : False,
						"msg" : "E-mail not found."
					}
		else:
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			admin_object = dumps(check_email)
			admin_json = json.loads(admin_object)
			admin_id = admin_json['_id']['$oid']

			#generate password
			generate_password = get_random_token(8)

			#เอา generate password ที่รับมาเข้ารหัส
			hash_input_pass = hashlib.md5(generate_password.encode())
			hash_pass = hash_input_pass.hexdigest()

			# update password
			where_param = { "_id": ObjectId(admin_json['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"admin_password": hash_pass,
									"last_active": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}

			if db.admin.update(where_param , value_param):
				#send email
				email_type = "forgot_password_backend"
				subject = "VR Driver : Forgot password"
				to_email = params['admin_email'].lower()
				template_html = "forgot_password_backend.html"
				data = { "password" : generate_password }

				check_send_email = send_email(email_type , subject , to_email , template_html , data)

				if check_send_email:
					result = {
								"status" : True,
								"msg" : "Forgot password success."
							}
				else:
					result = {
							"status" : False,
							"msg" : "Can't send email."
						}
			else:
				result = {
							"status" : False,
							"msg" : "Data update failed."
						}
	else:
		result = { 
					"status" : False,
					"msg" : get_api_message("all" , "please_check_your_parameters")
				}

	#set log detail
	user_type = "admin"
	function_name = "backend_forgot_password"
	request_headers = request.headers
	params_get = None
	params_post = params
	set_api_log(user_type , admin_id , function_name , request_headers , params_get , params_post , result)

	return result

def get_random_token(string_length=40):
	#ใช้ตัวอักษร A-Z,a-z,0-9 ในการ generate token
	all_character = string.ascii_letters + string.digits
	return ''.join((random.choice(all_character) for i in range(string_length)))