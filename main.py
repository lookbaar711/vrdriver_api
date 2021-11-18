from flask import Flask,request
from flask_mail import Mail
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from modules.login import *
from modules.send_email import *
from modules.push_notification import *
from modules.master_data import *
from modules.customer import *
from modules.driver import *
from modules.frontend import *
from modules.backend import *
from modules.cronjob import *

app = Flask(__name__, static_url_path='/static' , static_folder='static')
CORS(app)


scheduler = BackgroundScheduler()
#***** ถ้าต้องการให้ cronjob ทำงาน ให้เอา comment บรรทัดข้างล่างออก

#อัพเดต member_token และ noti_key ที่มี last_active เกิน 30 วันเป็น null
scheduler.add_job(func=check_logout, trigger="cron", hour='23', minute='59')
#เช็คงานที่มีการ request ไปแล้ว 45 นาทีว่ามี activity หรือไม่ ถ้าไม่มีให้ส่ง noti หาลูกค้าให้ทำการเลือกคนขับอีกครั้ง
scheduler.add_job(func=check_accept_job, trigger="interval", minutes=1)
#อัพเดต news_status ที่มี start_date ตรงกับวันที่ปัจจุบัน จาก 0 เป็น 1
scheduler.add_job(func=check_start_news, trigger="cron", hour='00', minute='01')
#อัพเดต news_status ที่มี end_date ตรงกับวันที่ปัจจุบัน จาก 1 เป็น 0
scheduler.add_job(func=check_end_news, trigger="cron", hour='23', minute='59')
#อัพเดต member_status ของคนขับที่มี member_status จาก 4 เป็น 1 และอัพเดต break_start_date , break_end_date เป็น null
scheduler.add_job(func=check_unlock_driver, trigger="cron", hour='23', minute='59')
#ส่ง noti หา user ที่เหลือวันที่ใช้งาน package (member_package) น้อยกว่า 10%
scheduler.add_job(func=check_nearby_end_date_member_package, trigger="cron", hour='00', minute='01')
#ส่ง noti หา user ที่เหลือวันที่ใช้งาน package (company_package) น้อยกว่า 10%
scheduler.add_job(func=check_nearby_end_date_company_package, trigger="cron", hour='00', minute='01')
#อัพเดต member_package_status ที่มี end_date ตรงกับวันที่ปัจจุบัน จาก 1 เป็น 0
scheduler.add_job(func=check_end_member_package, trigger="cron", hour='23', minute='59')
#อัพเดต company_package_status ที่มี end_date ตรงกับวันที่ปัจจุบัน จาก 1 เป็น 0
scheduler.add_job(func=check_end_company_package, trigger="cron", hour='23', minute='59')
#อัพเดต request_status จาก 1 เป็น 4 (เมื่อถึง 3 วันก่อนเริ่มงาน)
scheduler.add_job(func=check_coming_soon_job_3_days, trigger="interval", minutes=1)
#เช็คงานที่กำลังจะเริ่มในอีก 12 ชม. แล้วส่ง noti หาคนขับรถของงานนั้น
scheduler.add_job(func=check_confirm_job_12_hr, trigger="interval", minutes=1)
#เช็คงานที่กำลังจะเริ่มในอีก 1 ชม. แล้วส่ง noti หาคนขับรถของงานนั้น เพื่อยืนยันเวลาการถึงจุดหมาย
scheduler.add_job(func=check_confirm_job_1_hr, trigger="interval", minutes=1)
#เช็คงาน หากคนขับไม่ยืนยันเวลาการถึงจุดหมายภายใน 15 นาที
#ก่อนเวลาเริ่มงาน ระบบจะส่ง noti ไปหาลูกค้าและ admin backend ว่าไม่มี activity จากคนขับ
scheduler.add_job(func=check_not_responding_driver, trigger="interval", minutes=1)
#ส่ง noti แจ้งเตือนเมื่อถึง 15 นาทีก่อนจบงาน ไปหาคนขับ
scheduler.add_job(func=check_before_end_job, trigger="interval", minutes=1)
#เช็คงานที่เลยเวลาจบงานมาแล้ว 30 นาที
scheduler.add_job(func=check_end_job, trigger="interval", minutes=1)
#เช็คงานที่เลยเวลาจบงานมาแล้ว 35 นาที กรณีที่ยังไม่ได้ชำระค่าบริการส่วนเกิน
scheduler.add_job(func=check_pay_overtime, trigger="interval", minutes=1)
#อัพเดต check_status ที่เท่ากับ 2 เป็น 5 หลังจากเลยเวลาจบงานไปแล้ว 2 ชม.
scheduler.add_job(func=check_car_inspection, trigger="interval", minutes=1)
#ออกใบวางบิลตามวันที่ billing_date จาก tb company
scheduler.add_job(func=check_company_billing, trigger="cron", hour='00', minute='01')
#ส่ง noti และอัพเดต send_status ที่เท่ากับ 0 เป็น 1 
scheduler.add_job(func=check_queue_noti, trigger="interval", minutes=1)
#ส่ง email และอัพเดต send_status ที่เท่ากับ 0 เป็น 1 
scheduler.add_job(func=check_queue_email, trigger="interval", minutes=1)


scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

#กรณีมีการทำซ้ำ ให้เปิดรันตัวนี้ก่อน แล้วค่อย comment ออก
#scheduler.shutdown()



#mail configz
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'vrdriverfortest@gmail.com'
app.config['MAIL_PASSWORD'] = 'vrdriver1234'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/')
def index():
	return 'Hello World! ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/showpost',methods=['POST','PUT','DELETE'])
def showpost():
	return request.data

@app.route("/showget/<string:id_data>",methods=['GET'])
def showget(id_data):
	return id_data



#module login
@app.route('/login',methods=['POST'])
def call_login():
	return login(request)

@app.route('/login_social',methods=['POST'])
def call_login_social():
	return login_social(request)

@app.route('/logout',methods=['GET'])
def call_logout():
	return logout(request)

@app.route('/check_token',methods=['GET'])
def call_check_token():
	return check_token(request)

@app.route('/change_password',methods=['POST'])
def call_change_password():
	return change_password(request)

@app.route('/forgot_password',methods=['POST'])
def call_forgot_password():
	return forgot_password(request)

@app.route('/change_language',methods=['POST'])
def call_change_language():
	return change_language(request)

@app.route('/backend/login',methods=['POST'])
def call_backend_login():
	return backend_login(request)

@app.route('/backend/logout',methods=['GET'])
def call_backend_logout():
	return backend_logout(request)

@app.route('/backend/change_password',methods=['POST'])
def call_backend_change_password():
	return backend_change_password(request)

@app.route('/backend/forgot_password',methods=['POST'])
def call_backend_forgot_password():
	return backend_forgot_password(request)

@app.route('/get_specification_policy',methods=['POST'])
def call_get_specification_policy():
	return get_specification_policy(request)



#module customer
@app.route('/get_customer_profile/<string:id_data>',methods=['GET'])
def call_get_customer_profile(id_data):
	return get_customer_profile(id_data,request)

@app.route('/get_my_customer_profile',methods=['GET'])
def call_get_my_customer_profile():
	return get_my_customer_profile(request)

@app.route('/customer_news_list',methods=['POST'])
def call_customer_news_list():
	return customer_news_list(request)

@app.route('/get_news_detail/<string:id_data>',methods=['GET'])
def call_get_news_detail_frontend(id_data):
	return get_news_detail_frontend(id_data,request)

@app.route('/main_customer_guest',methods=['POST'])
def call_main_customer_guest():
	return main_customer_guest(request)

@app.route('/main_customer',methods=['POST'])
def call_main_customer():
	return main_customer(request)

@app.route('/send_customer_register',methods=['POST'])
def call_send_customer_register():
	return send_customer_register(request)

@app.route('/edit_my_customer_profile',methods=['POST'])
def call_edit_my_customer_profile():
	return edit_my_customer_profile(request)

@app.route('/package_list',methods=['POST'])
def call_package_list():
	return package_list(request)

@app.route('/get_package_detail',methods=['POST'])
def call_get_package_detail():
	return get_package_detail(request)

@app.route('/order_list',methods=['POST'])
def call_order_list():
	return order_list(request)

@app.route('/get_order_detail',methods=['POST'])
def call_get_order_detail():
	return get_order_detail(request)

@app.route('/add_order',methods=['POST'])
def call_add_order():
	return add_order(request)

@app.route('/cancel_order',methods=['POST'])
def call_cancel_order():
	return cancel_order(request)

@app.route('/confirm_order_payment',methods=['POST'])
def call_confirm_order_payment():
	return confirm_order_payment(request)

@app.route('/payment_channel_list',methods=['GET'])
def call_payment_channel_list():
	return payment_channel_list(request)

@app.route('/my_package_list_customer',methods=['POST'])
def call_my_package_list_customer():
	return my_package_list_customer(request)

@app.route('/personal_car_list',methods=['POST'])
def call_personal_car_list():
	return personal_car_list(request)

@app.route('/car_usage_history_list',methods=['POST'])
def call_car_usage_history_list():
	return car_usage_history_list(request)

@app.route('/get_car_form',methods=['GET'])
def call_get_car_form():
	return get_car_form(request)

@app.route('/get_car_brand',methods=['POST'])
def call_get_car_brand():
	return get_car_brand(request)

@app.route('/add_personal_car',methods=['POST'])
def call_add_personal_car():
	return add_personal_car(request)

@app.route('/edit_personal_car',methods=['POST'])
def call_edit_personal_car():
	return edit_personal_car(request)

@app.route('/delete_personal_car',methods=['POST'])
def call_delete_personal_car():
	return delete_personal_car(request)

@app.route('/location_list',methods=['GET'])
def call_location_list():
	return location_list(request)

@app.route('/add_location',methods=['POST'])
def call_add_location():
	return add_location(request)

@app.route('/edit_location',methods=['POST'])
def call_edit_location():
	return edit_location(request)

@app.route('/delete_location',methods=['POST'])
def call_delete_location():
	return delete_location(request)

@app.route('/request_list',methods=['POST'])
def call_request_list():
	return request_list(request)

@app.route('/request_detail',methods=['POST'])
def call_request_detail():
	return request_detail(request)

@app.route('/driver_request_list',methods=['POST'])
def call_driver_request_list():
	return driver_request_list(request)

@app.route('/edit_driver_request_list',methods=['POST'])
def call_edit_driver_request_list():
	return edit_driver_request_list(request)

@app.route('/check_main_package_request',methods=['POST'])
def call_check_main_package_request():
	return check_main_package_request(request)

@app.route('/check_second_package_request',methods=['POST'])
def call_check_second_package_request():
	return check_second_package_request(request)

@app.route('/get_special_request_form',methods=['POST'])
def call_get_special_request_form():
	return get_special_request_form(request)

@app.route('/check_completed_request',methods=['GET'])
def call_check_completed_request():
	return check_completed_request(request)

@app.route('/add_driver_request',methods=['POST'])
def call_add_driver_request():
	return add_driver_request(request)

@app.route('/edit_driver_request',methods=['POST'])
def call_edit_driver_request():
	return edit_driver_request(request)

@app.route('/cancel_request',methods=['POST'])
def call_cancel_request():
	return cancel_request(request)

@app.route('/accept_start_request',methods=['POST'])
def call_accept_start_request():
	return accept_start_request(request)

@app.route('/accept_car_inspection',methods=['POST'])
def call_accept_car_inspection():
	return accept_car_inspection(request)

@app.route('/reject_car_inspection',methods=['POST'])
def call_reject_car_inspection():
	return reject_car_inspection(request)

@app.route('/delay_job',methods=['POST'])
def call_delay_job():
	return delay_job(request)

@app.route('/not_delay_job',methods=['POST'])
def call_not_delay_job():
	return not_delay_job(request)

@app.route('/get_overtime_package',methods=['POST'])
def call_get_overtime_package():
	return get_overtime_package(request)

@app.route('/pay_overtime',methods=['POST'])
def call_pay_overtime():
	return pay_overtime(request)

@app.route('/customer_noti_list',methods=['POST'])
def call_customer_noti_list():
	return customer_noti_list(request)

@app.route('/set_read_noti',methods=['GET'])
def call_set_read_noti():
	return set_read_noti(request)

@app.route('/get_driver_rating_question',methods=['GET'])
def call_get_driver_rating_question():
	return get_driver_rating_question(request)

@app.route('/send_driver_rating',methods=['POST'])
def call_send_driver_rating():
	return send_driver_rating(request)

@app.route('/set_job_1_hour',methods=['POST'])
def call_set_job_1_hour():
	return set_job_1_hour(request)

@app.route('/set_job_time',methods=['POST'])
def call_set_job_time():
	return set_job_time(request)
	

# @app.route('/get_address_ggmap',methods=['POST'])
# def call_get_address_ggmap():
# 	return get_address_ggmap(request)

#update data
# @app.route('/update_order_package',methods=['GET'])
# def call_update_order_package():
# 	return update_order_package(request)

# @app.route('/update_member_package',methods=['GET'])
# def call_update_member_package():
# 	return update_member_package(request)

# @app.route('/update_company_package',methods=['GET'])
# def call_update_company_package():
# 	return update_company_package(request)

# @app.route('/check_pay_overtime',methods=['GET'])
# def call_check_pay_overtime():
# 	return check_pay_overtime(request)

# @app.route('/check_company_billing',methods=['GET'])
# def call_check_company_billing():
# 	return check_company_billing(request)



#module driver
@app.route('/get_driver_profile/<string:id_data>',methods=['GET'])
def call_get_driver_profile(id_data):
	return get_driver_profile(id_data,request)

@app.route('/get_my_driver_profile',methods=['GET'])
def call_get_my_driver_profile():
	return get_my_driver_profile(request)

@app.route('/driver_news_list',methods=['POST'])
def call_driver_news_list():
	return driver_news_list(request)

@app.route('/main_driver_guest',methods=['POST'])
def call_main_driver_guest():
	return main_driver_guest(request)

@app.route('/main_driver',methods=['POST'])
def call_main_driver():
	return main_driver(request)	

@app.route('/get_driver_register',methods=['POST'])
def call_get_driver_register():
	return get_driver_register(request)

@app.route('/send_driver_register',methods=['POST'])
def call_send_driver_register():
	return send_driver_register(request)

@app.route('/edit_my_driver_profile',methods=['POST'])
def call_edit_my_driver_profile():
	return edit_my_driver_profile(request)

@app.route('/job_list',methods=['POST'])
def call_job_list():
	return job_list(request)

@app.route('/job_detail',methods=['POST'])
def call_job_detail():
	return job_detail(request)

@app.route('/change_request_status',methods=['POST'])
def call_change_request_status():
	return change_request_status(request)

@app.route('/change_driver_request_status',methods=['POST'])
def call_change_driver_request_status():
	return change_driver_request_status(request)

@app.route('/accept_job',methods=['POST'])
def call_accept_job():
	return accept_job(request)

@app.route('/reject_job',methods=['POST'])
def call_reject_job():
	return reject_job(request)

@app.route('/cancel_job',methods=['POST'])
def call_cancel_job():
	return cancel_job(request)

@app.route('/coming_soon_job_form',methods=['GET'])
def call_coming_soon_job_form():
	return coming_soon_job_form(request)

@app.route('/coming_soon_job',methods=['POST'])
def call_coming_soon_job():
	return coming_soon_job(request)

@app.route('/confirm_start_job',methods=['POST'])
def call_confirm_start_job():
	return confirm_start_job(request)

@app.route('/get_car_inspection_form',methods=['POST'])
def call_get_car_inspection_form():
	return get_car_inspection_form(request)

@app.route('/confirm_car_inspection',methods=['POST'])
def call_confirm_car_inspection():
	return confirm_car_inspection(request)

@app.route('/add_start_mileage',methods=['POST'])
def call_add_start_mileage():
	return add_start_mileage(request)

@app.route('/get_car_inspection_detail',methods=['POST'])
def call_get_car_inspection_detail():
	return get_car_inspection_detail(request)

@app.route('/driver_noti_list',methods=['POST'])
def call_driver_noti_list():
	return driver_noti_list(request)

@app.route('/end_job',methods=['POST'])
def call_end_job():
	return end_job(request)

@app.route('/get_driver_rating_summary',methods=['GET'])
def call_get_driver_rating_summary():
	return get_driver_rating_summary(request)
	
@app.route('/update_driver_location',methods=['POST'])
def call_update_driver_location():
	return update_driver_location(request)

@app.route('/last_location_list',methods=['GET'])
def call_last_location_list():
	return last_location_list(request)

@app.route('/update_location',methods=['POST'])
def call_update_location():
	return update_location(request)

@app.route('/get_income_summary',methods=['POST'])
def call_get_income_summary():
	return get_income_summary(request)



#module frontend
@app.route('/company_dashboard',methods=['POST'])
def call_company_dashboard():
	return company_dashboard(request)

@app.route('/get_contact_us',methods=['POST'])
def call_get_contact_us():
	return get_contact_us(request)

@app.route('/edit_my_web_profile',methods=['POST'])
def call_edit_my_web_profile():
	return edit_my_web_profile(request)

@app.route('/activate_user/<string:id_data>',methods=['GET'])
def call_activate_user(id_data):
	return activate_user(id_data,request)

@app.route('/province_list',methods=['GET'])
def call_province_list():
	return province_list(request)

@app.route('/district_list',methods=['POST'])
def call_district_list():
	return district_list(request)

@app.route('/sub_district_list',methods=['POST'])
def call_sub_district_list():
	return sub_district_list(request)

@app.route('/get_address_info',methods=['POST'])
def call_get_address_info():
	return get_address_info(request)

@app.route('/get_company_info',methods=['GET'])
def call_get_company_info():
	return get_company_info(request)

@app.route('/edit_company',methods=['POST'])
def call_edit_company():
	return edit_company(request)

@app.route('/company_user_list',methods=['GET'])
def call_company_user_list():
	return company_user_list(request)

@app.route('/get_company_user_form',methods=['GET'])
def call_get_company_user_form():
	return get_company_user_form(request)

@app.route('/get_company_user_detail/<string:id_data>',methods=['GET'])
def call_get_company_user_detail(id_data):
	return get_company_user_detail(id_data,request)

@app.route('/add_company_user',methods=['POST'])
def call_add_company_user():
	return add_company_user(request)

@app.route('/edit_company_user',methods=['POST'])
def call_edit_company_user():
	return edit_company_user(request)

@app.route('/my_package_list_frontend',methods=['POST'])
def call_my_package_list_frontend():
	return my_package_list_frontend(request)

@app.route('/package_list_frontend',methods=['POST'])
def call_package_list_frontend():
	return package_list_frontend(request)

@app.route('/get_company_admin',methods=['GET'])
def call_get_company_admin():
	return get_company_admin(request)

@app.route('/get_company_user',methods=['GET'])
def call_get_company_user():
	return get_company_user(request)

@app.route('/get_package_admin',methods=['POST'])
def call_get_package_admin():
	return get_package_admin(request)

@app.route('/assign_package_admin',methods=['POST'])
def call_assign_package_admin():
	return assign_package_admin(request)

@app.route('/get_package_user',methods=['POST'])
def call_get_package_user():
	return get_package_user(request)

@app.route('/add_package_user',methods=['POST'])
def call_add_package_user():
	return add_package_user(request)

@app.route('/edit_package_user',methods=['POST'])
def call_edit_package_user():
	return edit_package_user(request)

@app.route('/delete_package_user',methods=['POST'])
def call_delete_package_user():
	return delete_package_user(request)

@app.route('/package_manage_list',methods=['POST'])
def call_package_manage_list():
	return package_manage_list(request)

@app.route('/change_package_usage_type',methods=['POST'])
def call_change_package_usage_type():
	return change_package_usage_type(request)

@app.route('/company_car_list',methods=['POST'])
def call_company_car_list():
	return company_car_list(request)

@app.route('/get_company_car_detail/<string:id_data>',methods=['GET'])
def call_get_company_car_detail(id_data):
	return get_company_car_detail(id_data,request)

@app.route('/company_car_manage_list',methods=['GET'])
def call_company_car_manage_list():
	return company_car_manage_list(request)

@app.route('/add_company_car',methods=['POST'])
def call_add_company_car():
	return add_company_car(request)

@app.route('/edit_company_car',methods=['POST'])
def call_edit_company_car():
	return edit_company_car(request)

@app.route('/add_contact',methods=['POST'])
def call_add_contact():
	return add_contact(request)

@app.route('/request_list_frontend',methods=['POST'])
def call_request_list_frontend():
	return request_list_frontend(request)

@app.route('/request_detail_frontend',methods=['POST'])
def call_request_detail_frontend():
	return request_detail_frontend(request)

@app.route('/billing_statement_list',methods=['GET'])
def call_billing_statement_list():
	return billing_statement_list(request)

@app.route('/get_billing_statement_detail',methods=['POST'])
def call_get_billing_statement_detail():
	return get_billing_statement_detail(request)
	
@app.route('/car_inspection_report',methods=['POST'])
def call_car_inspection_report():
	return car_inspection_report(request)

@app.route('/get_car_inspection_report_form',methods=['POST'])
def call_get_car_inspection_report_form():
	return get_car_inspection_report_form(request)

@app.route('/package_usage_report',methods=['POST'])
def call_package_usage_report():
	return package_usage_report(request)

@app.route('/get_package_usage_report_form',methods=['GET'])
def call_get_package_usage_report_form():
	return get_package_usage_report_form(request)

@app.route('/unpaid_expense_report',methods=['POST'])
def call_unpaid_expense_report():
	return unpaid_expense_report(request)





#module master_data
@app.route('/backend/car_type_list',methods=['GET'])
def call_car_type_list():
	return car_type_list(request)

@app.route('/backend/car_brand_list',methods=['POST'])
def call_car_brand_list():
	return car_brand_list(request)

@app.route('/backend/add_car_brand',methods=['POST'])
def call_add_car_brand():
	return add_car_brand(request)

@app.route('/backend/edit_car_brand',methods=['POST'])
def call_edit_car_brand():
	return edit_car_brand(request)

@app.route('/backend/delete_car_brand',methods=['POST'])
def call_delete_car_brand():
	return delete_car_brand(request)

@app.route('/backend/get_outside_inspection',methods=['POST'])
def call_get_outside_inspection():
	return get_outside_inspection(request)

@app.route('/backend/edit_outside_inspection',methods=['POST'])
def call_edit_outside_inspection():
	return edit_outside_inspection(request)

@app.route('/backend/get_inspection_before_use',methods=['GET'])
def call_get_inspection_before_use():
	return get_inspection_before_use(request)

@app.route('/backend/add_inspection_before_use',methods=['POST'])
def call_add_inspection_before_use():
	return add_inspection_before_use(request)

@app.route('/backend/edit_inspection_before_use',methods=['POST'])
def call_edit_inspection_before_use():
	return edit_inspection_before_use(request)

@app.route('/backend/delete_inspection_before_use',methods=['POST'])
def call_delete_inspection_before_use():
	return delete_inspection_before_use(request)

@app.route('/backend/driver_level_list',methods=['GET'])
def call_driver_level_list():
	return driver_level_list(request)

@app.route('/backend/add_driver_level',methods=['POST'])
def call_add_driver_level():
	return add_driver_level(request)

@app.route('/backend/edit_driver_level',methods=['POST'])
def call_edit_driver_level():
	return edit_driver_level(request)

@app.route('/backend/delete_driver_level',methods=['POST'])
def call_delete_driver_level():
	return delete_driver_level(request)

@app.route('/backend/payment_channel_list',methods=['GET'])
def call_payment_channel_list_backend():
	return payment_channel_list_backend(request)

@app.route('/backend/add_payment_channel',methods=['POST'])
def call_add_payment_channel():
	return add_payment_channel(request)

@app.route('/backend/edit_payment_channel',methods=['POST'])
def call_edit_payment_channel():
	return edit_payment_channel(request)

@app.route('/backend/delete_payment_channel',methods=['POST'])
def call_delete_payment_channel():
	return delete_payment_channel(request)

@app.route('/backend/get_emergency_call',methods=['GET'])
def call_get_emergency_call():
	return get_emergency_call(request)

@app.route('/backend/edit_emergency_call',methods=['POST'])
def call_edit_emergency_call():
	return edit_emergency_call(request)

@app.route('/backend/region_list',methods=['GET'])
def call_region_list():
	return region_list(request)

@app.route('/backend/province_list',methods=['GET'])
def call_province_list_backend():
	return province_list_backend(request)

@app.route('/backend/add_province',methods=['POST'])
def call_add_province():
	return add_province(request)

@app.route('/backend/edit_province',methods=['POST'])
def call_edit_province():
	return edit_province(request)

@app.route('/backend/delete_province',methods=['POST'])
def call_delete_province():
	return delete_province(request)

@app.route('/backend/district_list',methods=['POST'])
def call_district_list_backend():
	return district_list_backend(request)

@app.route('/backend/add_district',methods=['POST'])
def call_add_district():
	return add_district(request)

@app.route('/backend/edit_district',methods=['POST'])
def call_edit_district():
	return edit_district(request)

@app.route('/backend/delete_district',methods=['POST'])
def call_delete_district():
	return delete_district(request)

@app.route('/backend/sub_district_list',methods=['POST'])
def call_sub_district_list_backend():
	return sub_district_list_backend(request)

@app.route('/backend/add_sub_district',methods=['POST'])
def call_add_sub_district():
	return add_sub_district(request)

@app.route('/backend/edit_sub_district',methods=['POST'])
def call_edit_sub_district():
	return edit_sub_district(request)

@app.route('/backend/delete_sub_district',methods=['POST'])
def call_delete_sub_district():
	return delete_sub_district(request)

@app.route('/backend/get_address_info',methods=['POST'])
def call_get_address_info_backend():
	return get_address_info_backend(request)

@app.route('/backend/text_list',methods=['GET'])
def call_text_list():
	return text_list(request)

@app.route('/backend/add_text',methods=['POST'])
def call_add_text():
	return add_text(request)

@app.route('/backend/edit_text',methods=['POST'])
def call_edit_text():
	return edit_text(request)

@app.route('/backend/delete_text',methods=['POST'])
def call_delete_text():
	return delete_text(request)

@app.route('/backend/communication_list',methods=['GET'])
def call_communication_list():
	return communication_list(request)

@app.route('/backend/edit_communication',methods=['POST'])
def call_edit_communication():
	return edit_communication(request)

@app.route('/backend/get_contact_us',methods=['GET'])
def call_get_contact_us_backend():
	return get_contact_us_backend(request)

@app.route('/backend/edit_contact_us',methods=['POST'])
def call_edit_contact_us():
	return edit_contact_us(request)

@app.route('/backend/contact_topic_list',methods=['GET'])
def call_contact_topic_list():
	return contact_topic_list(request)

@app.route('/backend/add_contact_topic',methods=['POST'])
def call_add_contact_topic():
	return add_contact_topic(request)

@app.route('/backend/edit_contact_topic',methods=['POST'])
def call_edit_contact_topic():
	return edit_contact_topic(request)

@app.route('/backend/delete_contact_topic',methods=['POST'])
def call_delete_contact_topic():
	return delete_contact_topic(request)

@app.route('/backend/service_rating_question_list',methods=['GET'])
def call_service_rating_question_list():
	return service_rating_question_list(request)

@app.route('/backend/edit_service_rating_question',methods=['POST'])
def call_edit_service_rating_question():
	return edit_service_rating_question(request)

@app.route('/backend/service_area_list',methods=['GET'])
def call_service_area_list():
	return service_area_list(request)

@app.route('/backend/add_service_area',methods=['POST'])
def call_add_service_area():
	return add_service_area(request)

@app.route('/backend/edit_service_area',methods=['POST'])
def call_edit_service_area():
	return edit_service_area(request)

@app.route('/backend/get_specification_policy',methods=['POST'])
def call_get_specification_policy_backend():
	return get_specification_policy_backend(request)

@app.route('/backend/edit_specification_policy',methods=['POST'])
def call_edit_specification_policy():
	return edit_specification_policy(request)

@app.route('/backend/car_engine_list',methods=['GET'])
def call_car_engine_list():
	return car_engine_list(request)

@app.route('/backend/add_car_engine',methods=['POST'])
def call_add_car_engine():
	return add_car_engine(request)

@app.route('/backend/edit_car_engine',methods=['POST'])
def call_edit_car_engine():
	return edit_car_engine(request)

@app.route('/backend/get_vat_rate',methods=['GET'])
def call_get_vat_rate():
	return get_vat_rate_backend(request)

@app.route('/backend/edit_vat_rate',methods=['POST'])
def call_edit_vat_rate():
	return edit_vat_rate(request)

@app.route('/backend/request_driver_remark_list',methods=['GET'])
def call_request_driver_remark_list():
	return request_driver_remark_list(request)

@app.route('/backend/add_request_driver_remark',methods=['POST'])
def call_add_request_driver_remark():
	return add_request_driver_remark(request)

@app.route('/backend/edit_request_driver_remark',methods=['POST'])
def call_edit_request_driver_remark():
	return edit_request_driver_remark(request)

@app.route('/backend/special_skill_list',methods=['GET'])
def call_special_skill_list():
	return special_skill_list(request)

@app.route('/backend/add_special_skill',methods=['POST'])
def call_add_special_skill():
	return add_special_skill(request)

@app.route('/backend/edit_special_skill',methods=['POST'])
def call_edit_special_skill():
	return edit_special_skill(request)

@app.route('/backend/delete_special_skill',methods=['POST'])
def call_delete_special_skill():
	return delete_special_skill(request)



#module backend
@app.route('/backend/package_list',methods=['POST'])
def call_package_list_backend():
	return package_list_backend(request)

@app.route('/backend/get_package_detail/<string:id_data>',methods=['GET'])
def call_get_package_detail_backend(id_data):
	return get_package_detail_backend(id_data,request)

@app.route('/backend/get_package_form',methods=['GET'])
def call_get_package_form():
	return get_package_form(request)

@app.route('/backend/get_package_company',methods=['GET'])
def call_get_package_company():
	return get_package_company(request)

@app.route('/backend/add_package',methods=['POST'])
def call_add_package():
	return add_package(request)

@app.route('/backend/edit_package',methods=['POST'])
def call_edit_package():
	return edit_package(request)

@app.route('/backend/delete_package',methods=['POST'])
def call_delete_package():
	return delete_package(request)

@app.route('/backend/company_list',methods=['POST'])
def call_company_list():
	return company_list(request)

@app.route('/backend/get_company_form',methods=['GET'])
def call_get_company_form():
	return get_company_form(request)

@app.route('/backend/get_company_info/<string:id_data>',methods=['GET'])
def call_get_company_info_backend(id_data):
	return get_company_info_backend(id_data,request)

@app.route('/backend/edit_company',methods=['POST'])
def call_edit_company_backend():
	return edit_company_backend(request)

@app.route('/backend/driver_register_list',methods=['POST'])
def call_driver_register_list():
	return driver_register_list(request)

@app.route('/backend/get_driver_register_form',methods=['GET'])
def call_get_driver_register_form():
	return get_driver_register_form(request)

@app.route('/backend/get_driver_detail/<string:id_data>',methods=['GET'])
def call_get_driver_detail(id_data):
	return get_driver_detail(id_data,request)

@app.route('/backend/edit_driver_register',methods=['POST'])
def call_edit_driver_register():
	return edit_driver_register(request)

@app.route('/backend/driver_list',methods=['POST'])
def call_driver_list():
	return driver_list(request)

@app.route('/backend/get_driver_form',methods=['GET'])
def call_get_driver_form():
	return get_driver_form(request)

@app.route('/backend/add_driver',methods=['POST'])
def call_add_driver():
	return add_driver(request)

@app.route('/backend/edit_driver',methods=['POST'])
def call_edit_driver():
	return edit_driver(request)

@app.route('/backend/edit_driver_car_type',methods=['POST'])
def call_edit_driver_car_type():
	return edit_driver_car_type(request)

@app.route('/backend/edit_driver_car_gear',methods=['POST'])
def call_edit_driver_car_gear():
	return edit_driver_car_gear(request)

@app.route('/backend/edit_driver_communication',methods=['POST'])
def call_edit_driver_communication():
	return edit_driver_communication(request)

@app.route('/backend/edit_driver_service_area',methods=['POST'])
def call_edit_driver_service_area():
	return edit_driver_service_area(request)

@app.route('/backend/edit_driver_workday',methods=['POST'])
def call_edit_driver_workday():
	return edit_driver_workday(request)

@app.route('/backend/edit_driver_special_skill',methods=['POST'])
def call_edit_driver_special_skill():
	return edit_driver_special_skill(request)

@app.route('/backend/package_purchase_list',methods=['POST'])
def call_package_purchase_list():
	return package_purchase_list(request)

@app.route('/backend/get_package_purchase_form',methods=['GET'])
def call_get_package_purchase_form():
	return get_package_purchase_form(request)

@app.route('/backend/get_package_purchase_detail/<string:id_data>',methods=['GET'])
def call_get_package_purchase_detail(id_data):
	return get_package_purchase_detail(id_data,request)

@app.route('/backend/approve_package_purchase',methods=['POST'])
def call_approve_package_purchase():
	return approve_package_purchase(request)

@app.route('/backend/not_approve_package_purchase',methods=['POST'])
def call_not_approve_package_purchase():
	return not_approve_package_purchase(request)

@app.route('/backend/admin_list',methods=['GET'])
def call_admin_list():
	return admin_list(request)

@app.route('/backend/add_admin',methods=['POST'])
def call_add_admin():
	return add_admin(request)

@app.route('/backend/edit_admin',methods=['POST'])
def call_edit_admin():
	return edit_admin(request)

@app.route('/backend/request_list',methods=['POST'])
def call_request_list_backend():
	return request_list_backend(request)

# @app.route('/backend/request_list',methods=['POST'])
# def call_request_list_backend():
# 	return request_list_backend(request)

@app.route('/backend/get_request_detail/<string:id_data>',methods=['GET'])
def call_get_request_detail(id_data):
	return get_request_detail(id_data,request)

@app.route('/backend/get_request_form',methods=['GET'])
def call_get_request_form():
	return get_request_form(request)

@app.route('/backend/assign_driver_list',methods=['POST'])
def call_assign_driver_list():
	return assign_driver_list(request)

@app.route('/backend/assign_driver',methods=['POST'])
def call_assign_driver():
	return assign_driver(request)

@app.route('/backend/news_list',methods=['POST'])
def call_news_list_backend():
	return news_list_backend(request)

@app.route('/backend/get_news_form',methods=['GET'])
def call_get_news_form():
	return get_news_form(request)

@app.route('/backend/get_news_detail/<string:id_data>',methods=['GET'])
def call_get_news_detail(id_data):
	return get_news_detail(id_data,request)

@app.route('/backend/add_news',methods=['POST'])
def call_add_news():
	return add_news(request)

@app.route('/backend/edit_news',methods=['POST'])
def call_edit_news():
	return edit_news(request)

@app.route('/backend/contact_list',methods=['POST'])
def call_contact_list():
	return contact_list(request)

@app.route('/backend/get_contact_form',methods=['GET'])
def call_get_contact_form():
	return get_contact_form(request)

@app.route('/backend/payment_driver_list',methods=['POST'])
def call_payment_driver_list():
	return payment_driver_list(request)

@app.route('/backend/get_payment_driver_form',methods=['GET'])
def call_get_payment_driver_form():
	return get_payment_driver_form(request)

@app.route('/backend/get_payment_driver_detail/<string:id_data>',methods=['GET'])
def call_get_payment_driver_detail(id_data):
	return get_payment_driver_detail(id_data,request)

@app.route('/backend/edit_payment_driver',methods=['POST'])
def call_edit_payment_driver():
	return edit_payment_driver(request)

@app.route('/backend/set_payment_date',methods=['POST'])
def call_set_payment_date():
	return set_payment_date(request)

@app.route('/backend/billing_statement_list',methods=['POST'])
def call_billing_statement_list_backend():
	return billing_statement_list_backend(request)

@app.route('/backend/get_billing_form',methods=['GET'])
def call_get_billing_form():
	return get_billing_form(request)

@app.route('/backend/get_billing_statement_detail',methods=['POST'])
def call_get_billing_statement_detail_backend():
	return get_billing_statement_detail_backend(request)

@app.route('/backend/change_billing_statement_status',methods=['POST'])
def call_change_billing_statement_status():
	return change_billing_statement_status(request)

@app.route('/backend/billing_list',methods=['POST'])
def call_billing_list():
	return billing_list(request)

@app.route('/backend/add_billing_statement',methods=['POST'])
def call_add_billing_statement():
	return add_billing_statement(request)

@app.route('/backend/get_car_inspection_detail',methods=['POST'])
def call_get_car_inspection_detail_backend():
	return get_car_inspection_detail_backend(request)

@app.route('/backend/get_driver_location',methods=['POST'])
def call_get_driver_location():
	return get_driver_location(request)

@app.route('/backend/company_package_list',methods=['POST'])
def call_company_package_list():
	return company_package_list(request)

@app.route('/backend/get_company_package_detail/<string:id_data>',methods=['GET'])
def call_get_company_package_detail(id_data):
	return get_company_package_detail(id_data,request)

@app.route('/backend/get_company_package_form',methods=['GET'])
def call_get_company_package_form():
	return get_company_package_form(request)

@app.route('/backend/edit_company_package',methods=['POST'])
def call_edit_company_package():
	return edit_company_package(request)

@app.route('/backend/company_request_list',methods=['POST'])
def call_company_request_list():
	return company_request_list(request)

@app.route('/backend/company_billing_statement_list',methods=['POST'])
def call_company_billing_statement_list():
	return company_billing_statement_list(request)

@app.route('/backend/app_version_list',methods=['GET'])
def call_app_version_list():
	return app_version_list(request)

@app.route('/backend/get_app_version_form',methods=['GET'])
def call_get_app_version_form():
	return get_app_version_form(request)

@app.route('/backend/add_app_version',methods=['POST'])
def call_add_app_version():
	return add_app_version(request)

@app.route('/backend/edit_app_version',methods=['POST'])
def call_edit_app_version():
	return edit_app_version(request)

@app.route('/backend/admin_noti_list',methods=['POST'])
def call_admin_noti_list():
	return admin_noti_list(request)

@app.route('/backend/set_read_noti',methods=['GET'])
def call_set_read_noti_backend():
	return set_read_noti_backend(request)

@app.route('/backend/payment_driver_report',methods=['POST'])
def call_payment_driver_report():
	return payment_driver_report(request)

@app.route('/backend/summary_payment_driver_report',methods=['POST'])
def call_summary_payment_driver_report():
	return summary_payment_driver_report(request)

@app.route('/backend/billing_statement_report',methods=['POST'])
def call_billing_statement_report():
	return billing_statement_report(request)

@app.route('/backend/summary_service_report',methods=['POST'])
def call_summary_service_report():
	return summary_service_report(request)

@app.route('/backend/get_summary_service_report_form',methods=['GET'])
def call_get_summary_service_report_form():
	return get_summary_service_report_form(request)

@app.route('/backend/package_purchase_report',methods=['POST'])
def call_package_purchase_report():
	return package_purchase_report(request)

@app.route('/backend/get_package_purchase_report_form',methods=['GET'])
def call_get_package_purchase_report_form():
	return get_package_purchase_report_form(request)

@app.route('/backend/dashboard_1',methods=['GET'])
def call_dashboard_1():
	return dashboard_1(request)

@app.route('/backend/dashboard_2',methods=['POST'])
def call_dashboard_2():
	return dashboard_2(request)

@app.route('/backend/dashboard_3',methods=['POST'])
def call_dashboard_3():
	return dashboard_3(request)




@app.route('/push_notification',methods=['POST'])
def push_notification_():
	return push_notification(request)

@app.route('/test_upload_image_base64',methods=['POST'])
def test_upload_image_base64_():
	return test_upload_image_base64(request)

@app.route('/test_upload_image_formdata',methods=['POST'])
def test_upload_image_formdata_():
	return test_upload_image_formdata(request)


@app.errorhandler(404)
def page_not_found(e):
	result = {
				"status" : False,
				"error_code" : 404,
				"msg" : "Page not found."
			}
	return result

#***** ถ้าต้องการให้ cronjob ทำงาน ให้เซ็ต use_reloader = False
#บน server -> use_reloader = False
#ใน local -> use_reloader = True
app.run(debug=True,host='0.0.0.0',use_reloader=False)
