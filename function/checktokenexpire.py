from connections.connect_mongo import db
from bson.objectid import ObjectId
from bson.json_util import loads , dumps
from datetime import datetime , date , timedelta
import sys
import json

def check_token_expire(token):
	member = db.member.find_one({"member_token": token})

	if member is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_object = dumps(member)
		member_json = json.loads(member_object)

		# ดึงเวลาปัจจุบัน
		current_time = datetime.now()
		show_current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

		# เอา last_active มาบวกเพิ่ม 30 วัน 
		last_active_time = datetime.strptime(member_json['last_active'], "%Y-%m-%d %H:%M:%S")
		add_date_time = last_active_time + timedelta(days=180)
		show_add_date_time = add_date_time.strftime("%Y-%m-%d %H:%M:%S")
		
		# ถ้าเวลาที่บวกเพิ่ม 30 น้อยกว่า เวลาปัจจุบัน แสดงว่า token expire แล้ว แต่ถ้ามากกว่าแสดงว่า token ยังไม่ expire 
		if add_date_time < current_time:
			# return show_add_date_time+' < '+show_current_time
			return False
		else:
			# return show_add_date_time+' > '+show_current_time
			return True

def check_token_expire_backend(token):
	admin = db.admin.find_one({
								"admin_token": token,
								"admin_status": "1"
							})

	if admin is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		admin_object = dumps(admin)
		admin_json = json.loads(admin_object)

		# ดึงเวลาปัจจุบัน
		current_time = datetime.now()
		show_current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

		# เอา last_active มาบวกเพิ่ม 30 วัน 
		last_active_time = datetime.strptime(admin_json['last_active'], "%Y-%m-%d %H:%M:%S")
		add_date_time = last_active_time + timedelta(days=180)
		show_add_date_time = add_date_time.strftime("%Y-%m-%d %H:%M:%S")
		
		# ถ้าเวลาที่บวกเพิ่ม 30 น้อยกว่า เวลาปัจจุบัน แสดงว่า token expire แล้ว แต่ถ้ามากกว่าแสดงว่า token ยังไม่ expire 
		if add_date_time < current_time:
			# return show_add_date_time+' < '+show_current_time
			return False
		else:
			# return show_add_date_time+' > '+show_current_time
			return True
