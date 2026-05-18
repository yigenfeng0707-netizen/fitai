import requests
import json
from app.settings import settings

def get_wechat_access_token() -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={settings.wechat_app_id}&secret={settings.wechat_api_key}"
    try:
        response = requests.get(url)
        result = response.json()
        return result.get("access_token", "")
    except Exception:
        return ""

def send_wechat_message(openid: str, template_id: str, data: dict) -> bool:
    access_token = get_wechat_access_token()
    if not access_token:
        return False
    
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        return result.get("errcode") == 0
    except Exception:
        return False