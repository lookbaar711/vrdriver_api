from connections.connect_mongo import db
from bson.objectid import ObjectId
from bson.json_util import loads , dumps
from datetime import datetime , date , timedelta
import sys
import json

def get_member_info(token):
	member = db.member.find_one({"member_token": token})

	if member is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_object = dumps(member)
		member_json = json.loads(member_object)

		return member_json

def get_member_info_by_id(member_id):
	member = db.member.find_one({"_id": ObjectId(member_id)})

	if member is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		member_object = dumps(member)
		member_json = json.loads(member_object)

		return member_json

def get_package_info(package_id):
	package = db.package.find_one({"_id": ObjectId(package_id)})

	if package is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		package_object = dumps(package)
		package_json = json.loads(package_object)

		return package_json

def get_member_age(birthday):
	year = datetime.strptime(birthday, '%Y-%m-%d').strftime('%Y')
	birthday_year = int(year)
	current_year = int(datetime.now().strftime('%Y'))
	member_age = current_year - birthday_year

	return member_age

def get_admin_info(token):
	admin = db.admin.find_one({"admin_token": token})

	if admin is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		admin_object = dumps(admin)
		admin_json = json.loads(admin_object)

		return admin_json

def get_admin_info_by_id(admin_id):
	admin = db.admin.find_one({"_id": ObjectId(admin_id)})

	if admin is None:
		return False
	else:
		# เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		admin_object = dumps(member)
		admin_json = json.loads(member_object)

		return admin_json

def get_vat_rate():
	vat = db.vat_rate.find_one()
	
	if vat is None:
		return False
	else:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		vat_object = dumps(vat)
		vat_json = json.loads(vat_object)
		vat_rate = vat_json['vat_rate']

		return vat_rate

def check_update_version(app_code , app_version , os_type):
	check_app_version = db.app_version.find_one({
													"app_code": app_code,
													"app_version": app_version,
													"os_type": os_type
												})

	if check_app_version is None:
		return False
	else:
		#เอาค่าที่ได้จาก query มาแปลงจาก object เป็น json
		check_app_version_object = dumps(check_app_version)
		check_app_version_json = json.loads(check_app_version_object)

		if check_app_version_json['version_status'] == "1":
			return True
		else:
			return False

def count_pin(news_id=None):
	if news_id is None:
		check_news_pin = db.news.find({"pin": "1"}).count()
	else:
		check_news_pin = db.news.find({"_id": {"$ne": ObjectId(news_id)} , "pin": "1"}).count()

	return check_news_pin