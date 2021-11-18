from flask import Flask , request , render_template
from flask_mail import Mail , Message
from flask_cors import CORS
from datetime import datetime , date , timedelta
from connections.connect_mongo import db
from function.jsonencoder import json_encoder
from bson.objectid import ObjectId
from bson.json_util import loads , dumps

app = Flask(__name__ , template_folder='../templates')
CORS(app)

#mail configz
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'vrdriverfortest@gmail.com'
app.config['MAIL_PASSWORD'] = 'vrdriver1234'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


def send_email(email_type , subject , to_email , template_html , data):
	admin_email = "vrdriverfortest@gmail.com"

	with app.app_context():
		if email_type == "forgot_password":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, password=data['password'])
		elif email_type == "forgot_password_backend":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, password=data['password'])
		elif email_type == "register_success_normal":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, android_link=data['android_link'], ios_link=data['ios_link'])
		elif email_type == "register_success_company":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, web_link=data['web_link'])
		elif email_type == "approve_company":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, android_link=data['android_link'], ios_link=data['ios_link'])
		elif email_type == "not_approve_company":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, web_link=data['web_link'])	
		elif email_type == "register_success_driver":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			# msg.html = render_template(template_html)
			msg.html = render_template(template_html, username=data['username'], password=data['password'])
		elif email_type == "approve_driver":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, android_link=data['android_link'], ios_link=data['ios_link'])
		elif email_type == "not_approve_driver":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, android_link=data['android_link'], ios_link=data['ios_link'])	
		elif email_type == "add_driver":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, username=data['username'], password=data['password'], android_link=data['android_link'], ios_link=data['ios_link'])
		elif email_type == "add_admin":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, username=data['username'], password=data['password'])
		elif email_type == "add_billing_statement":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, company_name=data['company_name'], billing_statement_code=data['billing_statement_code'], billing_amount=data['billing_amount'])
		elif email_type == "add_billing":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, member_fullname=data['member_fullname'], request_no=data['request_no'], billing_amount=data['billing_amount'])
		elif email_type == "approve_package_purchase":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, order_no=data['order_no'], purchase_date_show=data['purchase_date_show'], order_price_not_vat=data['order_price_not_vat'], order_vat=data['order_vat'], order_price=data['order_price'], vat_rate=data['vat_rate'])
		elif email_type == "not_approve_package_purchase":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, order_no=data['order_no'], purchase_date_show=data['purchase_date_show'], order_price_not_vat=data['order_price_not_vat'], order_vat=data['order_vat'], order_price=data['order_price'], vat_rate=data['vat_rate'], order_remark=data['order_remark'])	
		elif email_type == "change_customer_name":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, old_member_fullname=data['old_member_fullname'], new_member_fullname=data['new_member_fullname'])		
		elif email_type == "activate_user":
			msg = Message(
							subject = subject, 
							sender = ("VR Driver", admin_email), 
							recipients = [to_email]
						)
			msg.html = render_template(template_html, username=data['username'], password=data['password'], activate_link=data['activate_link'])		
		else:
			msg = None

		try:
			if msg is None:
				response = False
			else:
				mail.send(msg)
				response = True
		except:
			response = False

	# bbb = { 
	# 			"email_type": email_type,
	# 			"response": response,
	# 			"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	# 		}

	# db.aaa.insert_one(bbb)
	
	return response
