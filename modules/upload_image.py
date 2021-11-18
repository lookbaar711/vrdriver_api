from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from datetime import datetime
import sys
import json
import base64

def upload_profile_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/profiles/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_driver_level_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/driver_level/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_flag_image(image_base64,image_name):
	imgdata = base64.b64decode(image_base64)
	filename = image_name+'.png'
	
	try:
		with open('static/images/flag/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_bank_logo(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/bank/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_vat_registration(doc_base64,token,file_type):
	docdata = base64.b64decode(doc_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	
	if file_type == "pdf":
		filename = date_time+'_'+token+'.pdf'
	else:
		filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/company/vat_registration/'+filename, 'wb') as f:
			f.write(docdata)
		response = filename
	except:
		response = None

	return response

def upload_company_certificate(doc_base64,token,file_type):
	docdata = base64.b64decode(doc_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")

	if file_type == "pdf":
		filename = date_time+'_'+token+'.pdf'
	else:
		filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/company/company_certificate/'+filename, 'wb') as f:
			f.write(docdata)
		response = filename
	except:
		response = None

	return response

def upload_company_logo(doc_base64,token):
	docdata = base64.b64decode(doc_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/company/logo/'+filename, 'wb') as f:
			f.write(docdata)
		response = filename
	except:
		response = None

	return response

def upload_package_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/package/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_transfer_slip(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/transfer_slip/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_car_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/car/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_inspection_before_use_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/inspection_before_use/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_outside_inspection_image(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/outside_inspection/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response

def upload_news_cover(image_base64,token):
	imgdata = base64.b64decode(image_base64)
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	filename = date_time+'_'+token+'.jpg'
	
	try:
		with open('static/images/news/'+filename, 'wb') as f:
			f.write(imgdata)
		response = filename
	except:
		response = None

	return response