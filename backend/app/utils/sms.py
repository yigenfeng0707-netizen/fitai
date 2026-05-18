import json
import hmac
import hashlib
import base64
from datetime import datetime
import requests
from app.settings import settings

def send_sms_aliyun(phone: str, template_code: str, params: dict) -> bool:
    access_key_id = settings.aliyun_access_key_id
    access_key_secret = settings.aliyun_access_key_secret
    sign_name = settings.aliyun_sms_sign_name
    
    if not access_key_id or not access_key_secret:
        return False
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    signature = generate_signature(access_key_id, access_key_secret, timestamp)
    
    url = "https://dysmsapi.aliyuncs.com/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "Action": "SendSms",
        "Version": "2017-05-25",
        "AccessKeyId": access_key_id,
        "Signature": signature,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(datetime.now().timestamp()),
        "Timestamp": timestamp,
        "PhoneNumbers": phone,
        "SignName": sign_name,
        "TemplateCode": template_code,
        "TemplateParam": json.dumps(params)
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        return result.get("Code") == "OK"
    except Exception:
        return False

def generate_signature(access_key_id: str, access_key_secret: str, timestamp: str) -> str:
    params = {
        "AccessKeyId": access_key_id,
        "Action": "SendSms",
        "Format": "JSON",
        "PhoneNumbers": "",
        "RegionId": "cn-hangzhou",
        "SignName": "",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(datetime.now().timestamp()),
        "SignatureVersion": "1.0",
        "TemplateCode": "",
        "TemplateParam": "",
        "Timestamp": timestamp,
        "Version": "2017-05-25"
    }
    
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    string_to_sign = f"POST&%2F&{requests.utils.quote(query_string, safe='')}"
    
    secret = f"{access_key_secret}&"
    signature = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha1).digest()
    return base64.b64encode(signature).decode()