from app.celery import celery

@celery.task
def send_sms(phone: str, template: str, params: dict):
    pass

@celery.task
def send_wechat_message(openid: str, template_id: str, data: dict):
    pass

@celery.task
def generate_daily_report(date: str):
    pass

@celery.task
def generate_monthly_report(month: str):
    pass

@celery.task
def sync_attendance_data():
    pass

@celery.task
def cleanup_expired_bookings():
    pass

@celery.task
def generate_marketing_content(prompt: str):
    pass