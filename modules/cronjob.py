from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from function.notification import send_push_message
from function.checktokenexpire import check_token_expire
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
from flask_mail import Mail , Message
from modules.login import get_random_token
from modules.send_email import send_email

def check_logout():
	#set log detail
	user_type = "cronjob"
	function_name = "check_logout"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	# ดึงเวลาปัจจุบัน
	current_time = datetime.now()

	member = db.member.find()

	if member is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_object = dumps(member)
		member_json = json.loads(member_object)

		for i in range(len(member_json)):
			# เอา last_active มาบวกเพิ่ม 30 วัน 
			last_active_time = datetime.strptime(member_json[i]['last_active'], "%Y-%m-%d %H:%M:%S")
			add_date_time = last_active_time + timedelta(days=180)

			# ถ้าเวลาที่บวกเพิ่ม 30 น้อยกว่า เวลาปัจจุบัน แสดงว่า token expire แล้ว 
			if add_date_time < current_time:
				# update member
				where_param = { "_id": ObjectId(member_json[i]['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"member_token": None,
										"noti_key": None,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				db.member.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_logout"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_accept_job():
	#set log detail
	user_type = "cronjob"
	function_name = "check_accept_job"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')

	request_driver = db.request_driver.find({
												"driver_id": None,
												"request_status": "0",
												"end_accept_at": {"$regex": current_datetime}
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			#ถ้าไม่มีคนรับงานเลย
			if request_driver_json[i]['driver_id'] is None and request_driver_json[i]['request_status'] == "0":
				# update request_driver
				where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"driver_list_id": None,
										"request_status": "0",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				db.request_driver.update(where_param , value_param)

				driver_list_id = request_driver_json[i]['driver_list_id']
				driver_list = []

				if driver_list_id is not None:
					dl = db.driver_list.find_one({"_id": ObjectId(driver_list_id)})

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					dl_object = dumps(dl)
					dl_json = json.loads(dl_object)

					for j in range(len(dl_json['driver_list'])):
						driver_list.append({
							"driver_id" : dl_json['driver_list'][j]['driver_id'],
							"driver_request_status": "4" #ปฏิเสธงาน
						})

				# update driver_list
				where_param = { "_id": ObjectId(driver_list_id) }
				value_param = {
								"$set":
									{
										"driver_list_status": "0",
										"driver_list": driver_list,
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				db.driver_list.update(where_param , value_param)

	
				noti_type = "not_responding_request"
				request_id = request_driver_json[i]['_id']['$oid']
				request_no = request_driver_json[i]['request_no']

				noti_title_en = "The driver unresponsive to job : "+request_no
				noti_title_th = "คนขับไม่ตอบสนองงาน "+request_no
				noti_message_en = "please select driver again."
				noti_message_th = "กรุณาเลือกคนขับอีกครั้ง"

				#-----------------------------------------------------------------#

				#sent noti to member
				customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])
				
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
				if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
					passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])
					
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_accept_job"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_start_news():
	#set log detail
	user_type = "cronjob"
	function_name = "check_start_news"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_date = datetime.now().strftime('%Y-%m-%d')

	news = db.news.find({
							"news_status": "0",
							"start_date": current_date
						})

	if news is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		news_object = dumps(news)
		news_json = json.loads(news_object)

		for i in range(len(news_json)):
			# update request_driver
			where_param = { "_id": ObjectId(news_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"news_status": "1",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			if db.news.update(where_param , value_param):
				if news_json[i]['display'] == "customer":
					member = db.member.find({
												"member_type": "customer"
											})
				elif news_json[i]['display'] == "driver":
					member = db.member.find({
												"member_type": "driver"
											})
				elif news_json[i]['display'] == "private":
					company_in = []
					for j in range(len(news_json[i]['private'])):
						company_in.append(news_json[i]['private'][j]['company_id'])

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
					for k in range(len(member_json)):
						member_info = get_member_info_by_id(member_json[k]['_id']['$oid'])

						noti_title_en = "News & Promotion"
						noti_title_th = "ข่าวสารโปรโมชั่น"
						noti_message_en = news_json[i]['news_title_en']
						noti_message_th = news_json[i]['news_title_th']

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
						send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "news_id": news_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
						send_noti_badge = 1

						#insert member_notification
						noti_detail = {
											"news_id": news_json[i]['_id']['$oid']
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_start_news"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_end_news():
	#set log detail
	user_type = "cronjob"
	function_name = "check_end_news"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_date = datetime.now().strftime('%Y-%m-%d')

	news = db.news.find({
							"news_status": "1",
							"end_date": current_date
						})

	if news is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		news_object = dumps(news)
		news_json = json.loads(news_object)

		for i in range(len(news_json)):
			# update request_driver
			where_param = { "_id": ObjectId(news_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"pin": "0",
									"news_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.news.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_end_news"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_unlock_driver():
	#set log detail
	user_type = "cronjob"
	function_name = "check_unlock_driver"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_date = datetime.now().strftime('%Y-%m-%d')

	driver = db.member.find({
								"member_type": "driver",
								"member_status": "4",
								"break_end_date": current_date
							})

	if driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		driver_object = dumps(driver)
		driver_json = json.loads(driver_object)

		for i in range(len(driver_json)):
			# update member
			where_param = { "_id": ObjectId(driver_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"member_status": "1",
									"break_start_date": None,
									"break_end_date": None,
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.member.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_unlock_driver"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_nearby_end_date_member_package():
	#set log detail
	user_type = "cronjob"
	function_name = "check_nearby_end_date_member_package"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	percent_check_package = 10

	member_package = db.member_package.find({
												"company_id": None,
												"member_package_status": "1"
											})

	if member_package is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_package_object = dumps(member_package)
		member_package_json = json.loads(member_package_object)

		for i in range(len(member_package_json)):
			#หา 10% ของ total_usage_date 
			check_nearby_amount = int((member_package_json[i]['total_usage_date'] / 100) * percent_check_package)

			current_date = datetime.now().strftime('%Y-%m-%d')
			current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')

			#วันที่แจ้งเตือน = วันที่หมดอายุ - 10% ของ total_usage_date
			end_date_obj = datetime.strptime(member_package_json[i]['end_date'], '%Y-%m-%d')
			check_nearby_date_obj = end_date_obj - timedelta(days=check_nearby_amount)

			#ถ้าวันที่แจ้งเตือน ตรงกับ วันที่ปัจจุบัน ให้แจ้งเตือน
			if check_nearby_date_obj == current_date_obj:
				member_info = get_member_info_by_id(member_package_json[i]['member_id'])
				noti_type = "nearby_end_date_member_package"
				member_fullname = member_info['member_firstname_en']+" "+member_info['member_lastname_en']

				noti_title_en = member_fullname+"'s "+member_package_json[i]['package_name_en']+" package"
				noti_title_th = "แพ็คเกจ "+member_package_json[i]['package_name_th']+" ของ "+member_fullname
				noti_message_en = "has less than 10%"+" "+"usage date"
				noti_message_th = "เหลือวันที่ใช้งานน้อยกว่า 10%"

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
				send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "member_package_id": member_package_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
				send_noti_badge = 1

				#insert member_notification
				noti_detail = {
									"member_package_id": member_package_json[i]['_id']['$oid']
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_nearby_end_date_member_package"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_nearby_end_date_company_package():
	#set log detail
	user_type = "cronjob"
	function_name = "check_nearby_end_date_company_package"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	percent_check_package = 10

	company_package = db.company_package.find({
												"company_package_status": "1"
											})

	if company_package is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		company_package_object = dumps(company_package)
		company_package_json = json.loads(company_package_object)

		for i in range(len(company_package_json)):
			company_id = company_package_json[i]['company_id']

			#หา 10% ของ total_usage_date 
			check_nearby_amount = int((company_package_json[i]['total_usage_date'] / 100) * percent_check_package)

			current_date = datetime.now().strftime('%Y-%m-%d')
			current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')

			#วันที่แจ้งเตือน = วันที่หมดอายุ - 10% ของ total_usage_date
			end_date_obj = datetime.strptime(company_package_json[i]['end_date'], '%Y-%m-%d')
			check_nearby_date_obj = end_date_obj - timedelta(days=check_nearby_amount)

			#ถ้าวันที่แจ้งเตือน ตรงกับ วันที่ปัจจุบัน ให้แจ้งเตือน
			if check_nearby_date_obj == current_date_obj:

				#ส่ง noti หา master admin ของ company นั้นๆ
				master_admin = db.member.find({
												"company_id": company_id,
												"company_user_type": "2"
											})

				if master_admin is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					master_admin_object = dumps(master_admin)
					master_admin_json = json.loads(master_admin_object)
					
					noti_type = "nearby_end_date_company_package"

					member_in = []

					for j in range(len(master_admin_json)):
						member_in.append(master_admin_json[j]['_id']['$oid'])

						#sent noti to member
						customer_info = get_member_info_by_id(master_admin_json[j]['_id']['$oid'])
						member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']
						company_name = company_package_json[i]['company_name']

						noti_title_en = company_name+"'s "+company_package_json[i]['package_name_en']+" package"
						noti_title_th = "แพ็คเกจ "+company_package_json[i]['package_name_th']+" ของบริษัท "+company_name
						noti_message_en = "has less than 10%"+" "+"usage date"
						noti_message_th = "เหลือวันที่ใช้งานน้อยกว่า 10%"

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
						send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "company_package_id": company_package_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
						send_noti_badge = 1

						#insert member_notification
						noti_detail = {
											"company_id": company_id,
											"company_package_id": company_package_json[i]['_id']['$oid']
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

				#ส่ง noti หา member package ของ company นั้นๆ และต้องไม่ซ้ำกับคนที่เป็น master admin
				member_package = db.member_package.find({
															"company_package_id": company_package_json[i]['_id']['$oid'],
															"member_id": {"$nin" : member_in}
														})

				if member_package is not None:
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					
					noti_type = "nearby_end_date_company_package"

					send_email_list = []

					for j in range(len(member_package_json)):
						#sent noti to member
						customer_info = get_member_info_by_id(member_package_json[j]['member_id'])
						member_fullname = customer_info['member_firstname_en']+" "+customer_info['member_lastname_en']
						company_name = company_package_json[i]['company_name']

						noti_title_en = company_name+"'s "+company_package_json[i]['package_name_en']+" package"
						noti_title_th = "แพ็คเกจ "+company_package_json[i]['package_name_th']+" ของบริษัท "+company_name
						noti_message_en = "has less than 10%"+" "+"usage date"
						noti_message_th = "เหลือวันที่ใช้งานน้อยกว่า 10%"

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
						send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "company_package_id": company_package_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
						send_noti_badge = 1

						#insert member_notification
						noti_detail = {
											"company_id": company_id,
											"company_package_id": company_package_json[i]['_id']['$oid']
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_nearby_end_date_company_package"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_end_member_package():
	#set log detail
	user_type = "cronjob"
	function_name = "check_end_member_package"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_date = datetime.now().strftime('%Y-%m-%d')

	member_package = db.member_package.find({
												"member_package_status": "1",
												"end_date": current_date
											})

	if member_package is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_package_object = dumps(member_package)
		member_package_json = json.loads(member_package_object)

		for i in range(len(member_package_json)):
			# update request_driver
			where_param = { "_id": ObjectId(member_package_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"member_package_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.member_package.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_end_member_package"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_end_company_package():
	#set log detail
	user_type = "cronjob"
	function_name = "check_end_company_package"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_date = datetime.now().strftime('%Y-%m-%d')

	company_package = db.company_package.find({
												"company_package_status": "1",
												"end_date": current_date
											})

	if company_package is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		company_package_object = dumps(company_package)
		company_package_json = json.loads(company_package_object)

		for i in range(len(company_package_json)):
			# update request_driver
			where_param = { "_id": ObjectId(company_package_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"company_package_status": "0",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.company_package.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_end_company_package"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_coming_soon_job_3_days():
	#set log detail
	user_type = "cronjob"
	function_name = "check_coming_soon_job_3_days"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	coming_soon_datetime_obj = current_datetime_obj + timedelta(days=3)
	# coming_soon_datetime = coming_soon_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
	coming_soon_date = coming_soon_datetime_obj.strftime('%Y-%m-%d')
	coming_soon_time = coming_soon_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "1",
												"start_date": coming_soon_date,
												"start_time": coming_soon_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			# update request_driver
			where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"request_status": "4",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.request_driver.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_coming_soon_job_3_days"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_confirm_job_12_hr():
	#set log detail
	user_type = "cronjob"
	function_name = "check_confirm_job_12_hr"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj + timedelta(hours=12)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "4",
												"start_date": check_date,
												"start_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			#ถ้ามีคนรับงานแล้ว
			if request_driver_json[i]['driver_id'] is not None:
				# update request_driver
				where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"job_status": "1",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				db.request_driver.update(where_param , value_param)

				driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				noti_type = "confirm_job_12_hr"
				request_id = request_driver_json[i]['_id']['$oid']
				request_no = request_driver_json[i]['request_no']

				noti_title_en = "12 Hours left before start job : "+request_no
				noti_title_th = "อีก 12 ชั่วโมงจะถึงเวลาเริ่มงาน "+request_no
				noti_message_en = ""
				noti_message_th = ""

				if driver_info['member_lang'] == "en":
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
				send_noti_key = driver_info['noti_key']
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
							"member_id": driver_info['_id']['$oid'],
							"member_fullname": driver_info['member_firstname_en']+" "+driver_info['member_lastname_en'],
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_confirm_job_12_hr"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_confirm_job_1_hr():
	#set log detail
	user_type = "cronjob"
	function_name = "check_confirm_job_1_hr"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj + timedelta(hours=1)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "4",
												"job_status": "1",
												"start_date": check_date,
												"start_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			#ถ้ามีคนรับงานแล้ว
			if request_driver_json[i]['driver_id'] is not None:
				# update request_driver
				where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"job_status": "2",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				
				db.request_driver.update(where_param , value_param)

				driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				noti_type = "confirm_job_1_hr"
				request_id = request_driver_json[i]['_id']['$oid']
				request_no = request_driver_json[i]['request_no']

				noti_title_en = "1 Hour left before start job : "+request_no
				noti_title_th = "อีก 1 ชั่วโมงจะถึงเวลาเริ่มงาน "+request_no
				noti_message_en = ""
				noti_message_th = ""

				if driver_info['member_lang'] == "en":
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
				send_noti_key = driver_info['noti_key']
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
							"member_id": driver_info['_id']['$oid'],
							"member_fullname": driver_info['member_firstname_en']+" "+driver_info['member_lastname_en'],
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
	
	#set log detail
	user_type = "cronjob"
	function_name = "check_confirm_job_1_hr"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)		

def check_not_responding_driver():
	#set log detail
	user_type = "cronjob"
	function_name = "check_not_responding_driver"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj + timedelta(minutes=15)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "4",
												"job_status": "2",
												"start_date": check_date,
												"start_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			# update request_driver
			where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"job_status": "4",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.request_driver.update(where_param , value_param)

			#-----------------------------------------------------------------#

			driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
			noti_type = "not_responding_driver"
			request_id = request_driver_json[i]['_id']['$oid']
			request_no = request_driver_json[i]['request_no']

			# noti_title_en = "Driver : "+driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
			# noti_title_th = "คนขับ "+driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
			# noti_message_en = "unresponsive to job : "+request_no
			# noti_message_th = "ไม่ตอบสนองงาน "+request_no

			noti_title_en = "Driver unresponsive to job"
			noti_title_th = "คนขับไม่ตอบสนองงาน"
			noti_message_en = "Driver : "+driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']+" unresponsive to job "+request_no
			noti_message_th = "คนขับ "+driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']+" ไม่ตอบสนองงาน "+request_no
			
			#sent noti to member
			customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])

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
			if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
				passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])

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

			#-----------------------------------------------------------------#

			#insert admin_notification
			noti_type_admin = "not_responding_driver"
			noti_detail_admin = {
									"request_id": request_id,
									"request_no": request_no
								}

			data_admin = { 
							"noti_type": noti_type_admin,
							"noti_title_en": noti_title_en,
							"noti_title_th": noti_title_th,
							"noti_message_en": noti_message_en,
							"noti_message_th": noti_message_th,
							"noti_detail": noti_detail_admin,
							"noti_status": "0",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}
			db.admin_notification.insert_one(data_admin)

	#set log detail
	user_type = "cronjob"
	function_name = "check_not_responding_driver"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)
			
def check_before_end_job():
	#set log detail
	user_type = "cronjob"
	function_name = "check_before_end_job"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj + timedelta(minutes=15)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "5",
												"job_status": "6",
												"delay_end_date": check_date,
												"delay_end_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			# update request_driver
			where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"job_status": "7",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.request_driver.update(where_param , value_param)

			#-----------------------------------------------------------------#

			driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
			noti_type_customer = "before_end_job_customer"
			noti_type_passenger = "before_end_job_customer"
			noti_type_driver = "before_end_job_driver"
			request_id = request_driver_json[i]['_id']['$oid']
			request_no = request_driver_json[i]['request_no']

			noti_title_en = "15 minute to arrival time : "+request_no
			noti_title_th = "อีก 15 นาทีจะถึงเวลาจบงาน "+request_no
			noti_message_en = ""
			noti_message_th = ""

			#sent noti to member & driver
			customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])

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
			send_noti_key_customer = customer_info['noti_key']
			send_noti_key_driver = driver_info['noti_key']
			send_noti_title = noti_title
			send_noti_message = noti_message
			send_noti_data_customer = { "action" : noti_type_customer , "noti_message" : show_noti , "request_id": request_id , "created_datetime" : created_datetime }
			send_noti_data_driver = { "action" : noti_type_driver , "noti_message" : show_noti , "request_id": request_id , "created_datetime" : created_datetime }
			send_noti_badge = 1

			#insert member_notification
			noti_detail = {
								"request_id": request_id,
								"request_no": request_no
							}

			data_customer = { 
								"member_id": customer_info['_id']['$oid'],
								"member_fullname": customer_info['member_firstname_en']+" "+customer_info['member_lastname_en'],
								"noti_type": noti_type_customer,
								"noti_message_en": noti_title_en+" "+noti_message_en,
								"noti_message_th": noti_title_th+" "+noti_message_th,
								"noti_detail": noti_detail,

								"send_noti_key": send_noti_key_customer,
								"send_noti_title": send_noti_title,
								"send_noti_message": send_noti_message,
								"send_noti_data": send_noti_data_customer,
								"send_noti_badge": send_noti_badge,

								"send_status": "0",
								"created_at": created_at,
								"updated_at": created_at
							}
			db.queue_notification.insert_one(data_customer)

			data_driver = { 
							"member_id": driver_info['_id']['$oid'],
							"member_fullname": driver_info['member_firstname_en']+" "+driver_info['member_lastname_en'],
							"noti_type": noti_type_driver,
							"noti_message_en": noti_title_en+" "+noti_message_en,
							"noti_message_th": noti_title_th+" "+noti_message_th,
							"noti_detail": noti_detail,

							"send_noti_key": send_noti_key_driver,
							"send_noti_title": send_noti_title,
							"send_noti_message": send_noti_message,
							"send_noti_data": send_noti_data_driver,
							"send_noti_badge": send_noti_badge,

							"send_status": "0",
							"created_at": created_at,
							"updated_at": created_at
						}
			db.queue_notification.insert_one(data_driver)

			#-----------------------------------------------------------------#

			#sent noti to passenger
			if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
				passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])

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
				send_noti_key_passenger = passenger_info['noti_key']
				send_noti_title = noti_title
				send_noti_message = noti_message
				send_noti_data_passenger = { "action" : noti_type_passenger , "noti_message" : show_noti , "request_id": request_id , "created_datetime" : created_datetime }
				send_noti_badge = 1

				#insert member_notification
				noti_detail = {
									"request_id": request_id,
									"request_no": request_no
								}

				data_passenger = { 
									"member_id": passenger_info['_id']['$oid'],
									"member_fullname": passenger_info['member_firstname_en']+" "+passenger_info['member_lastname_en'],
									"noti_type": noti_type_passenger,
									"noti_message_en": noti_title_en+" "+noti_message_en,
									"noti_message_th": noti_title_th+" "+noti_message_th,
									"noti_detail": noti_detail,

									"send_noti_key": send_noti_key_passenger,
									"send_noti_title": send_noti_title,
									"send_noti_message": send_noti_message,
									"send_noti_data": send_noti_data_passenger,
									"send_noti_badge": send_noti_badge,

									"send_status": "0",
									"created_at": created_at,
									"updated_at": created_at
								}
				db.queue_notification.insert_one(data_passenger)

	#set log detail
	user_type = "cronjob"
	function_name = "check_before_end_job"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_end_job():
	#set log detail
	user_type = "cronjob"
	function_name = "check_end_job"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj - timedelta(minutes=30)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "5",
												"job_status": "7",
												"delay_end_date": check_date,
												"delay_end_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			#อัพเดต requset_status เป็น 6
			delay_end_time_obj = datetime.strptime(request_driver_json[i]['delay_end_date']+" "+request_driver_json[i]['delay_end_time'], '%Y-%m-%d %H:%M:%S')
			end_time_obj = datetime.strptime(request_driver_json[i]['end_date']+" "+request_driver_json[i]['end_time'], '%Y-%m-%d %H:%M:%S')
			end_time_30_obj = end_time_obj + timedelta(minutes=30)
			main_package_info = request_driver_json[i]['main_package'][0]

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

			for j in range(len(request_driver_json[i]['main_package'])):
				main_package_normal_received = main_package_normal_received + (request_driver_json[i]['main_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
				main_package_overtime_received = main_package_overtime_received + (request_driver_json[i]['main_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

				total_normal_usage = total_normal_usage + request_driver_json[i]['main_package'][j]['normal_usage']
				total_overtime_usage = total_overtime_usage + request_driver_json[i]['main_package'][j]['overtime_usage']

			main_package_received = main_package_normal_received + main_package_overtime_received

			if len(request_driver_json[i]['second_package']) > 0:
				for j in range(len(request_driver_json[i]['second_package'])):
					second_package_normal_received = second_package_normal_received + (request_driver_json[i]['second_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
					second_package_overtime_received = second_package_overtime_received + (request_driver_json[i]['second_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

					total_normal_usage = total_normal_usage + request_driver_json[i]['second_package'][j]['normal_usage']
					total_overtime_usage = total_overtime_usage + request_driver_json[i]['second_package'][j]['overtime_usage']

				second_package_received = second_package_normal_received + second_package_overtime_received

			if len(request_driver_json[i]['overtime_package']) > 0:
				for j in range(len(request_driver_json[i]['overtime_package'])):
					overtime_package_normal_received = overtime_package_normal_received + (request_driver_json[i]['overtime_package'][j]['normal_usage'] * main_package_info['normal_received_rate'])
					overtime_package_overtime_received = overtime_package_overtime_received + (request_driver_json[i]['overtime_package'][j]['overtime_usage'] * main_package_info['overtime_received_rate'])

					total_normal_usage = total_normal_usage + request_driver_json[i]['overtime_package'][j]['normal_usage']
					total_overtime_usage = total_overtime_usage + request_driver_json[i]['overtime_package'][j]['overtime_usage']

				overtime_package_received = overtime_package_normal_received + overtime_package_overtime_received

			if len(request_driver_json[i]['billing_id']) > 0:
				for j in range(len(request_driver_json[i]['billing_id'])):
					billing = db.billing.find_one({"_id": ObjectId(request_driver_json[i]['billing_id'][j])})
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
			where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
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
				car = db.car.find_one({"_id": ObjectId(request_driver_json[i]['car_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_object = dumps(car)
				car_json = json.loads(car_object)

				car_type = db.car_type.find_one({"_id": ObjectId(car_json['car_type_id'])})
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				car_type_object = dumps(car_type)
				car_type_json = json.loads(car_type_object)
				car_type_code = car_type_json['car_type_code']

				driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])
				
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

				#อัพเดตข้อมูล จำนวนประเภทรถที่รับงานสำเร็จ
				where_param = { "_id": ObjectId(request_driver_json[i]['driver_id']) }
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

				#-----------------------------------------------------------------#

				#อัพเดตข้อมูล end_mileage เป็น 0
				where_param = { "request_id": request_driver_json[i]['_id']['$oid'] }
				value_param = {
								"$set":
									{
										"end_mileage": None,
										"end_mileage_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}

				db.car_inspection.update(where_param , value_param)

				#-----------------------------------------------------------------#

				#เพิ่มข้อมูลคะแนนการใช้บริการ
				data = { 
							"request_id": request_driver_json[i]['_id']['$oid'],
							"driver_id": request_driver_json[i]['driver_id'],
							"passenger_id": request_driver_json[i]['passenger_id'],
							"rating": [],
							"average_rating": "0",
							"recommend": None,
							"rating_status": "0",
							"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
							"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						}
				db.service_rating.insert_one(data)

				#-----------------------------------------------------------------#

				#sent noti to member
				customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])
				driver_info = get_member_info_by_id(request_driver_json[i]['driver_id'])

				#จบงานเกินเวลาจอง
				if delay_end_time_obj > end_time_30_obj:
					#ถ้าเวลาจบงานล่าสุด มากกว่า เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 9
					noti_type = "end_job_overtime"
					request_no = request_driver_json[i]['request_no']

					noti_title_en = "Driver : "+driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
					noti_title_th = "คนขับ "+driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
					noti_message_en = "end overbooking job : "+request_no+" please choose paymemt method for excess charges."
					noti_message_th = "จบงาน "+request_no+" เกินเวลา กรุณาเลือกช่องทางชำระค่าใช้จ่ายส่วนเกิน"
				#จบงานตามเวลาจอง
				else:
					#ถ้าเวลาจบงานล่าสุด น้อยกว่าหรือเท่ากับ เวลาจบงานที่จอง + 30 นาที ให้อัพเดต job_status เป็น 8
					noti_type = "end_job_normal"
					request_no = request_driver_json[i]['request_no']

					noti_title_en = "Driver : "+driver_info['member_firstname_en']+" "+driver_info['member_lastname_en']
					noti_title_th = "คนขับ "+driver_info['member_firstname_th']+" "+driver_info['member_lastname_th']
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
				send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": request_driver_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
				send_noti_badge = 1

				#insert member_notification
				noti_detail = {
									"request_id": request_driver_json[i]['_id']['$oid'],
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
				if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
					#จบงานตามเวลาจอง ให้ส่ง noti หาผู้โดยสารด้วย
					if noti_type == "end_job_normal":
						passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])

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
						send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "request_id": request_driver_json[i]['_id']['$oid'] , "created_datetime" : created_datetime }
						send_noti_badge = 1

						#insert member_notification
						noti_detail = {
											"request_id": request_driver_json[i]['_id']['$oid'],
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

	#set log detail
	user_type = "cronjob"
	function_name = "check_end_job"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_pay_overtime():
	#set log detail
	user_type = "cronjob"
	function_name = "check_pay_overtime"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj - timedelta(minutes=35)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "6",
												"job_status": "9",
												"delay_end_date": check_date,
												"delay_end_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		request_driver_list = []

		for i in range(len(request_driver_json)):
			#เช็ค
			member_info = get_member_info_by_id(request_driver_json[i]['member_id'])
			member_lang = member_info['member_lang']
			member_id = member_info['_id']['$oid']
			company_id = member_info['company_id']
			request_id = request_driver_json[i]['_id']['$oid']
			request_no = request_driver_json[i]['request_no']

			company = db.company.find_one({"_id": ObjectId(company_id)})
			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			company_object = dumps(company)
			company_json = json.loads(company_object)
			billing_receiver_email = company_json['billing_receiver_email']

			main_package_id = request_driver_json[i]['main_package_id']
			main_package_info = request_driver_json[i]['main_package'][0]
			end_date = request_driver_json[i]['end_date']
			end_time = request_driver_json[i]['end_time']
			delay_end_date = request_driver_json[i]['delay_end_date']
			delay_end_time = request_driver_json[i]['delay_end_time']

			if int(request_driver_json[i]['delay_minute']) <= 30:
				delay_hour = 0
				delay_minute = int(request_driver_json[i]['delay_minute'])
			else:
				delay_hour = int(request_driver_json[i]['delay_minute']) // 60 
				delay_minute = int(request_driver_json[i]['delay_minute']) % 60 

			overtime_amount = delay_hour

			start_date_obj = datetime.strptime(request_driver_json[i]['start_date'], '%Y-%m-%d')
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

			member_package_in = []
			
			if package is not None:
				#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
				package_object = dumps(package)
				package_json = json.loads(package_object)

				all_remainning_amount = 0

				for j in range(len(package_json)):
					member_package = db.member_package.find({
															"member_id": member_info['_id']['$oid'],
															"package_id": package_json[j]['_id'],
															"member_package_status": "1"
														}).sort([("end_date", 1)])

					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					member_package_object = dumps(member_package)
					member_package_json = json.loads(member_package_object)
					
					remaining_package_list = []

					for k in range(len(member_package_json)):
						if member_package_json[k]['package_usage_type'] == "share" and member_package_json[k]['company_package_id'] is not None:
							company_package = db.company_package.find_one({"_id": ObjectId(member_package_json[k]['company_package_id'])})
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							company_package_object = dumps(company_package)
							company_package_json = json.loads(company_package_object)

							overtime_package_remaining_amount = company_package_json['remaining_amount']
						else:
							overtime_package_remaining_amount = member_package_json[k]['remaining_amount']

						end_date = datetime.strptime(member_package_json[k]['end_date'], '%Y-%m-%d')
						today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
						
						delta = end_date - today
						remaining_date = delta.days

						if overtime_package_remaining_amount > 0 and remaining_date >= 0:
							mp_id = member_package_json[k]['_id']['$oid']
							member_package_in.append(ObjectId(mp_id))

							all_remainning_amount = all_remainning_amount + overtime_package_remaining_amount

			#ถ้ามี package มากพอให้หัก
			if all_remainning_amount >= overtime_amount:
				request_driver_list.append({
												"request_id" : request_id,
												"request_no": request_no,
												"pay_channel": "package"
											})

				#วน loop overtime_package_list
				if len(member_package_in) > 0:
					op_list = []
					use_amount = 0
					old_use_amount = 0
					start_overtime = '20:00'
					end_overtime = '05:00'
					start_overtime_int = 20
					end_overtime_int = 5
					sum_ot = 0

					# ดึง member_package อีกรอบเพื่อเอาข้อมูลที่เหลือวันใช้งานน้อยมาใช้ก่อน
					member_package = db.member_package.find({
																"_id": {"$in" : member_package_in} 
															}).sort([("end_date", 1)])

					if member_package is None:
						result = { 
									"status" : False,
									"msg" : "Data not found."
								}
					else:
						#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
						member_package_object = dumps(member_package)
						member_package_json = json.loads(member_package_object)

						member_package_list = []
						overtime_package_list = []

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

							if int(request_driver_json[i]['delay_minute']) <= 30:
								delay_hour = 0
								delay_minute = int(request_driver_json[i]['delay_minute'])
							else:
								delay_hour = int(request_driver_json[i]['delay_minute']) // 60 
								delay_minute = int(request_driver_json[i]['delay_minute']) % 60

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
									start_time = datetime.strptime(request_driver_json[i]['end_time'], '%H:%M:%S').strftime('%H:%M')

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

								normal_paid = normal_usage * float(main_package_info['normal_paid_rate'])
								overtime_paid = overtime_usage * float(main_package_info['overtime_paid_rate'])
								sum_paid = normal_paid + overtime_paid

								normal_received = normal_usage * float(main_package_info['normal_received_rate'])
								overtime_received = overtime_usage * float(main_package_info['overtime_received_rate'])
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
									start_time = datetime.strptime(request_driver_json[i]['end_time'], '%H:%M:%S').strftime('%H:%M')

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

								normal_paid = normal_usage * main_package_info['normal_paid_rate']
								overtime_paid = overtime_usage * main_package_info['overtime_paid_rate']
								sum_paid = normal_paid + overtime_paid

								normal_received = normal_usage * main_package_info['normal_received_rate']
								overtime_received = overtime_usage * main_package_info['overtime_received_rate']
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
									"package_type": member_package_json[j]['package_type'],
									"usage_amount": usage_amount_value,
									"usage_hour_amount": usage_hour_amount_value,

									"normal_usage": normal_usage,
									"overtime_usage": overtime_usage,
									"normal_paid_rate": float(overtime_package_info['normal_paid_rate']),
									"normal_received_rate": float(overtime_package_info['normal_received_rate']),
									"overtime_paid_rate": float(overtime_package_info['overtime_paid_rate']),
									"overtime_received_rate": float(overtime_package_info['overtime_received_rate'])										
								})

							last_end_time_obj = end_time_obj

						if use_amount >= overtime_amount:
							payment_amount = float(request_driver_json[i]['payment_amount']) + float(sum_received)
							total_normal_usage = request_driver_json[i]['total_normal_usage'] + normal_usage
							total_overtime_usage = request_driver_json[i]['total_overtime_usage'] + overtime_usage
							normal_payment_amount = request_driver_json[i]['normal_payment_amount'] + normal_received
							overtime_payment_amount = request_driver_json[i]['overtime_payment_amount'] + overtime_received

							# update tb request_driver.billing_id
							where_param = { "_id": ObjectId(request_id) }
							value_param = {
											"$set":
												{
													"overtime_package_id": op_list,
													"overtime_package": overtime_package_list,
													"normal_payment_amount": normal_payment_amount,
													"overtime_payment_amount": overtime_payment_amount,
													"payment_amount": payment_amount,
													"payment_date": datetime.now().strftime('%Y-%m-%d'),
													"payment_status": "1",
													"total_normal_usage": total_normal_usage,
													"total_overtime_usage": total_overtime_usage,
													"job_status": "10",
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


										noti_type = "pay_overtime_success"
										request_id = request_driver_json[i]['_id']['$oid']
										request_no = request_driver_json[i]['request_no']

										noti_title_en = "Job : "+request_no
										noti_title_th = "งาน "+request_no
										noti_message_en = "excess expenses have been paid."
										noti_message_th = "ชำระค่าใช้จ่ายส่วนเกินเรียบร้อยแล้ว"

										#-----------------------------------------------------------------#

										#sent noti to member
										customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])
										
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
										if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
											passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])
											
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


								# result = {
								# 			"status" : True,
								# 			"msg" : "Pay overtime success."
								# 		}
							# else:
							# 	result = {
							# 				"status" : False,
							# 				"msg" : "Request update failed."
							# 			}
						

			#ถ้ามี package ไม่พอให้หัก
			else:
				# ถ้าเป็น company user 
				if member_info['company_id'] is not None:
					request_driver_list.append({
													"request_id" : request_id,
													"request_no": request_no,
													"pay_channel": "billing"
												})

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

					# 16 = 12 + 4
					if int(end_time_obj.strftime('%H')) == 0:
						end_time = 24
					else:
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

						# 1 = 22 - 21
						sum_overtime_usage = end_time - start_time
						# 0 = 1 - 1
						sum_normal_usage = missing_amount - sum_overtime_usage

					normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
					overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
					sum_paid = normal_paid + overtime_paid

					normal_received = sum_normal_usage * main_package_info['normal_received_rate']
					overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
					sum_received = normal_received + overtime_received

					billing_array = request_driver_json[i]['billing_id']
					
					#แปลง format วันที่
					created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					billing_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 

					#เช็ตให้ ObjectId เก็บค่าเป็น Object กรณีที่ต้องการรู้ id ก่อน insert
					billing_id = ObjectId()
					#แปลง ObjectId ให้เป็น string
					billing_id_string = str(billing_id)

					billing_data = { 
										"_id": billing_id,
										"request_id": request_id,
										"request_no": request_driver_json[i]['request_no'],
										"company_id": member_info['company_id'],
										"package_id": main_package_id,
										"package_type": main_package_info['package_type'],
										"usage_hour_amount": overtime_amount,
										"normal_usage": sum_normal_usage,
										"overtime_usage": sum_overtime_usage,
										"normal_paid_rate": float(main_package_info['normal_paid_rate']),
										"normal_received_rate": float(main_package_info['normal_received_rate']),
										"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
										"overtime_received_rate": float(main_package_info['overtime_received_rate']),
										"sum_paid": sum_paid,
										"sum_received": sum_received,
										"service_period": "overtime",
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
							billing_amount = '{:,.2f}'.format(round(float(sum_paid) , 2))

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

								#ส่ง noti
								send_noti_key = customer_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "request_id": request_id , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"company_id": company_id,
													"request_id": request_id,
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

								#send email
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
												"created_at": created_at,
												"updated_at": created_at
											}
								db.queue_email.insert_one(data_email)


						#เซ็ตค่า billing
						billing_array.append(billing_id_string)

					payment_amount = float(request_driver_json[i]['payment_amount']) + float(sum_received)
					total_normal_usage = request_driver_json[i]['total_normal_usage'] + sum_normal_usage
					total_overtime_usage = request_driver_json[i]['total_overtime_usage'] + sum_overtime_usage
					normal_payment_amount = request_driver_json[i]['normal_payment_amount'] + normal_received
					overtime_payment_amount = request_driver_json[i]['overtime_payment_amount'] + overtime_received

					#update tb request_driver.billing_id
					where_param = { "_id": ObjectId(request_id) }
					value_param = {
									"$set":
										{
											"overtime_package_id": [],
											"overtime_package": [],
											"normal_payment_amount": normal_payment_amount,
											"overtime_payment_amount": overtime_payment_amount,
											"payment_amount": payment_amount,
											"payment_date": datetime.now().strftime('%Y-%m-%d'),
											"payment_status": "1",
											"total_normal_usage": total_normal_usage,
											"total_overtime_usage": total_overtime_usage,
											"billing_id": billing_array,
											"job_status": "10",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}	

					db.request_driver.update(where_param , value_param)

					noti_type = "pay_overtime_success"
					request_id = request_driver_json[i]['_id']['$oid']
					request_no = request_driver_json[i]['request_no']

					noti_title_en = "Job : "+request_no
					noti_title_th = "งาน "+request_no
					noti_message_en = "excess expenses have been paid."
					noti_message_th = "ชำระค่าใช้จ่ายส่วนเกินเรียบร้อยแล้ว"

					#-----------------------------------------------------------------#

					#sent noti to member
					customer_info = get_member_info_by_id(request_driver_json[i]['member_id'])
					
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
					if request_driver_json[i]['member_id'] != request_driver_json[i]['passenger_id']:
						passenger_info = get_member_info_by_id(request_driver_json[i]['passenger_id'])
						
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

				#ถ้าเป็น normal user
				else:
					request_driver_list.append({
													"request_id" : request_id,
													"request_no": request_no,
													"pay_channel": "overdue"
												})

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

					# 16 = 12 + 4
					if int(end_time_obj.strftime('%H')) == 0:
						end_time = 24
					else:
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

						# 1 = 22 - 21
						sum_overtime_usage = end_time - start_time
						# 0 = 1 - 1
						sum_normal_usage = missing_amount - sum_overtime_usage

					normal_paid = sum_normal_usage * main_package_info['normal_paid_rate']
					overtime_paid = sum_overtime_usage * main_package_info['overtime_paid_rate']
					sum_paid = normal_paid + overtime_paid

					normal_received = sum_normal_usage * main_package_info['normal_received_rate']
					overtime_received = sum_overtime_usage * main_package_info['overtime_received_rate']
					sum_received = normal_received + overtime_received

					if main_package_info['package_type'] == "time":
						usage_amount = int("1")
					else:
						usage_amount = int(overtime_amount)

					overtime_package_list = []
					op_list = []

					overtime_package_list.append({
						"member_package_id" : main_package_info['member_package_id'],
						"package_id": main_package_info['package_id'],
						"package_type": main_package_info['package_type'],
						"usage_amount": usage_amount,
						"usage_hour_amount": int(overtime_amount),

						"normal_usage": sum_normal_usage,
						"overtime_usage": sum_overtime_usage,
						"normal_paid_rate": float(main_package_info['normal_paid_rate']),
						"normal_received_rate": float(main_package_info['normal_received_rate']),
						"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
						"overtime_received_rate": float(main_package_info['overtime_received_rate'])										
					})

					op_list.append(main_package_info['package_id'])

					payment_amount = float(request_driver_json[i]['payment_amount']) + float(sum_received)

					# update data to tb request_driver
					where_param = { "_id": ObjectId(request_id) }
					value_param = {
									"$set":
										{
											"overtime_package_id": [],
											"overtime_package": [],
											"payment_amount": payment_amount,
											"job_status": "11",
											"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
										}
								}

					db.request_driver.update(where_param , value_param)

					# insert data to tb pay_overtime_list
					data = { 
								"request_id": request_id,
								"member_package_id" : main_package_info['member_package_id'],
								"package_id": main_package_info['package_id'],
								"package_type": main_package_info['package_type'],
								"usage_amount": usage_amount,
								"usage_hour_amount": int(overtime_amount),
								"normal_usage": sum_normal_usage,
								"overtime_usage": sum_overtime_usage,
								"normal_paid_rate": float(main_package_info['normal_paid_rate']),
								"normal_received_rate": float(main_package_info['normal_received_rate']),
								"overtime_paid_rate": float(main_package_info['overtime_paid_rate']),
								"overtime_received_rate": float(main_package_info['overtime_received_rate']),
								"pay_overtime_status": "0",
								"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
								"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
							}

					db.pay_overtime_list.insert_one(data)

	#set log detail
	user_type = "cronjob"
	function_name = "check_pay_overtime"
	result = {
				"status" : True,
				"msg" : "End cronjob.",
				"request_driver" : request_driver_list
			}
	set_cronjob_log(user_type , function_name , result)
						
def check_car_inspection():
	#set log detail
	user_type = "cronjob"
	function_name = "check_car_inspection"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	check_datetime_obj = current_datetime_obj - timedelta(minutes=120)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	request_driver = db.request_driver.find({
												"request_status": "6",
												"delay_end_date": check_date,
												"delay_end_time": check_time
											})

	if request_driver is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		request_driver_object = dumps(request_driver)
		request_driver_json = json.loads(request_driver_object)

		for i in range(len(request_driver_json)):
			#ถ้ายังตรวจสภาพไม่ผ่าน ให้อัพเดต check_status = 5
			if request_driver_json[i]['check_status'] == "2":
				# update request_driver
				where_param = { "_id": ObjectId(request_driver_json[i]['_id']['$oid']) }
				value_param = {
								"$set":
									{
										"check_status": "5",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				db.request_driver.update(where_param , value_param)

				# update car_inspection
				where_param = { "request_id": request_driver_json[i]['_id']['$oid'] }
				value_param = {
								"$set":
									{
										"check_status": "5",
										"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
									}
							}
				db.car_inspection.update(where_param , value_param)

	#set log detail
	user_type = "cronjob"
	function_name = "check_car_inspection"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)
				
def check_company_billing():
	#set log detail
	user_type = "cronjob"
	function_name = "check_company_billing"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	# current_datetime = "2020-09-10 00:00:00"
	current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')+":00"
	current_datetime_obj = datetime.strptime(current_datetime, '%Y-%m-%d %H:%M:%S')
	current_date = current_datetime_obj.strftime('%Y-%m-%d')

	company_billing_date = str(int(current_datetime_obj.strftime('%d')))
	company_billing_month = str(int(current_datetime_obj.strftime('%m')))

	if company_billing_month == "2":
		number_of_month = 29
	elif company_billing_month == "4" or company_billing_month == "6" or company_billing_month == "9" or company_billing_month == "11":
		number_of_month = 30
	else:
		number_of_month = 31

	check_datetime_obj = current_datetime_obj - timedelta(days=number_of_month)
	check_date = check_datetime_obj.strftime('%Y-%m-%d')
	check_time = check_datetime_obj.strftime('%H:%M:%S')

	company = db.company.find({
								"billing_date": company_billing_date,
								"company_status": "1"
							})

	if company is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		company_object = dumps(company)
		company_json = json.loads(company_object)

		billing_list = []

		for i in range(len(company_json)):
			company_id = company_json[i]['_id']['$oid']
			company_name = company_json[i]['company_name']
			billing_receiver_fullname = company_json[i]['billing_receiver_firstname']+" "+company_json[i]['billing_receiver_lastname']
			billing_receiver_tel = company_json[i]['billing_receiver_tel']
			billing_receiver_email = company_json[i]['billing_receiver_email']
					
			billing = db.billing.find({
										"company_id": company_id,
										"billing_status": "0"
									})

			#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
			billing_object = dumps(billing)
			billing_json = json.loads(billing_object)

			#แปลง format วันที่
			created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

			billing_statement_date_int = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')) 
			billing_statement_month = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%m'))

			if len(billing_json) > 0:
				billing_normal_paid = 0
				billing_overtime_paid = 0
				billing_paid = 0

				for j in range(len(billing_json)):
					request_driver = db.request_driver.find_one({"_id": ObjectId(billing_json[j]['request_id'])})
					#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
					request_driver_object = dumps(request_driver)
					request_driver_json = json.loads(request_driver_object)

					if request_driver is not None:
						#ต้องเป็นงานที่จบแล้ว และชำระเงินเรียบร้อยแล้วเท่านั้น
						if request_driver_json['request_status'] == "6" and (request_driver_json['job_status'] == "8" or request_driver_json['job_status'] == "10"):
							billing_datetime_obj = datetime.strptime(billing_json[j]['created_at'], '%Y-%m-%d %H:%M:%S')
							billing_date = current_datetime_obj.strftime('%Y-%m-%d')

							#เลือกงานที่มีวันที่น้อยกว่าหรือเท่ากับวันที่ x ของเดือนนี้
							if billing_datetime_obj <= current_datetime_obj:
								billing_list.append(billing_json[j]['_id']['$oid'])

								billing_normal_paid = billing_normal_paid + (billing_json[j]['normal_usage'] * billing_json[j]['normal_paid_rate'])
								billing_overtime_paid = billing_overtime_paid + (billing_json[j]['overtime_usage'] * billing_json[j]['overtime_paid_rate'])

								#update data to tb billing
								where_param = { "_id": ObjectId(billing_json[j]['_id']['$oid']) }
								value_param = {
												"$set":
													{
														"billing_status": "1",
														"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
													}
											}

								db.billing.update(where_param , value_param)

				if len(billing_list) > 0:
					billing_paid = billing_normal_paid + billing_overtime_paid

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

					#insert data to tb billing_statement
					data = { 
								"_id": billing_statement_id,
								"billing_statement_code": billing_statement_code,
								"company_id": company_id,
								"company_name": company_name,
								"billing_receiver_fullname": billing_receiver_fullname,
								"billing_receiver_email": billing_receiver_email,
								"billing_receiver_tel": billing_receiver_tel,
								"billing": billing_list,
								"sum_paid": billing_paid,
								"billing_statement_status": "0",
								"billing_statement_date_int": billing_statement_date_int,
								"billing_statement_month": billing_statement_month,
								"created_at": created_at,
								"updated_at": created_at
							}

					if db.billing_statement.insert_one(data):
						#ส่ง noti หา master admin ของ company นั้นๆ
						master_admin = db.member.find({
														"company_id": company_id,
														"company_user_type": "2"
													})

						if master_admin is not None:
							#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
							master_admin_object = dumps(master_admin)
							master_admin_json = json.loads(master_admin_object)
							
							noti_type = "add_billing_statement"
							billing_amount = '{:,.2f}'.format(round(float(billing_paid) , 2))

							send_email_list = []

							for k in range(len(master_admin_json)):
								#sent noti to member
								customer_info = get_member_info_by_id(master_admin_json[k]['_id']['$oid'])
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

								#-----------------------------------------------------------------#

								#ส่ง noti
								send_noti_key = customer_info['noti_key']
								send_noti_title = noti_title
								send_noti_message = noti_message
								send_noti_data = { "action" : noti_type , "noti_message" : show_noti , "company_id": company_id , "created_datetime" : created_datetime }
								send_noti_badge = 1

								#insert member_notification
								noti_detail = {
													"company_id": company_id,
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
								to_email = master_admin_json[k]['member_email'].lower()
								template_html = "add_billing_statement.html"
								data_detail = { "company_name" : company_name, "billing_statement_code" : billing_statement_code, "billing_amount" : billing_amount }

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

	#set log detail
	user_type = "cronjob"
	function_name = "check_company_billing"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_queue_noti():
	#set log detail
	user_type = "cronjob"
	function_name = "check_queue_noti"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	queue_noti = db.queue_notification.find({"send_status": "0"}).skip(0).limit(40)

	if queue_noti is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		queue_noti_object = dumps(queue_noti)
		queue_noti_json = json.loads(queue_noti_object)

		for i in range(len(queue_noti_json)):
			# update queue_notification
			where_param = { "_id": ObjectId(queue_noti_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"send_status": "1",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.queue_notification.update(where_param , value_param)

			#-----------------------------------------------------------------#

			noti_type = queue_noti_json[i]['noti_type']
			send_noti_key = queue_noti_json[i]['send_noti_key']
			send_noti_title = queue_noti_json[i]['send_noti_title']
			send_noti_message = queue_noti_json[i]['send_noti_message']
			send_noti_data = queue_noti_json[i]['send_noti_data']
			send_noti_badge = queue_noti_json[i]['send_noti_badge']
			
			data = { 
						"member_id": queue_noti_json[i]['member_id'],
						"member_fullname": queue_noti_json[i]['member_fullname'],
						"noti_type": queue_noti_json[i]['noti_type'],
						"noti_message_en": queue_noti_json[i]['noti_message_en'],
						"noti_message_th": queue_noti_json[i]['noti_message_th'],
						"noti_detail": queue_noti_json[i]['noti_detail'],
						"noti_status": "0",
						"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
						"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					}
			db.member_notification.insert_one(data)

			if queue_noti_json[i]['send_noti_key'] is not None:
				try:
					send_push_message(send_noti_key , send_noti_title , send_noti_message , send_noti_data , send_noti_badge)
					send_status = True
				except:
					send_status = False	

	#set log detail
	user_type = "cronjob"
	function_name = "check_queue_noti"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

def check_queue_email():
	#set log detail
	user_type = "cronjob"
	function_name = "check_queue_email"
	result = {
				"status" : True,
				"msg" : "Start cronjob."
			}
	set_cronjob_log(user_type , function_name , result)

	queue_email = db.queue_email.find({"send_status": "0"}).skip(0).limit(30)

	if queue_email is not None:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		queue_email_object = dumps(queue_email)
		queue_email_json = json.loads(queue_email_object)

		for i in range(len(queue_email_json)):
			# update queue_email
			where_param = { "_id": ObjectId(queue_email_json[i]['_id']['$oid']) }
			value_param = {
							"$set":
								{
									"send_status": "1",
									"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
								}
						}
			
			db.queue_email.update(where_param , value_param)

			#-----------------------------------------------------------------#

			#send email
			email_type = queue_email_json[i]['email_type']
			subject = queue_email_json[i]['subject']
			to_email = queue_email_json[i]['to_email']
			template_html = queue_email_json[i]['template_html']
			data = queue_email_json[i]['data']

			check_send_email = send_email(email_type , subject , to_email , template_html , data)

	#set log detail
	user_type = "cronjob"
	function_name = "check_queue_email"
	result = {
				"status" : True,
				"msg" : "End cronjob."
			}
	set_cronjob_log(user_type , function_name , result)
			


			