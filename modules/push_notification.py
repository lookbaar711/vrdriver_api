import sys
from connections.connect_mongo import db
import json
from function.jsonencoder import json_encoder
from function.notification import send_push_message

import base64
from datetime import datetime
from modules.login import get_random_token

def push_notification(request):
	data = json.loads(request.data)
	send_push_message(data['token'],data['title'],data['message'],data['data'],data['badge'])
	return data

def test_upload_image_base64(request):
	data = json.loads(request.data)
	imgdata = base64.b64decode(data['image_base64'])
	now = datetime.now()
	date_time = now.strftime("%Y%m%d%H%M%S")
	gtk = get_random_token(100);
	filename = date_time+'_'+gtk+'_.jpg'
	with open('static/images/profiles/'+filename, 'wb') as f:
		f.write(imgdata)
	return 'Uploaded.'

def test_upload_image_formdata(request):
	picture = request.files.get('file')
	picture.save('static/images/profiles')
	return 'Uploaded.'
