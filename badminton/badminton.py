# pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
import ddddocr
import requests
import os
from configparser import ConfigParser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import base64
from Crypto.Cipher import AES  
from Crypto.Util.Padding import pad, unpad 

def getEnv(env, default="", required=False):
    if os.path.exists("config.ini"):
        config = ConfigParser()
        config.read("config.ini", encoding="utf-8")
        if config.has_option("CONFIG", env):
            return config["CONFIG"][env]
    if os.environ.get(env):
        return os.getenv(env)
    if required:
        raise Exception(f"Env {env} is required")
    return default

debug = getEnv("DEBUG", False)\
# 将 username 和 password 替换为自己的学号和密码
username = "XXXXXXXXXX"
password = "XXXXXXXXXX"
ndyy = "ndyy.ncu.edu.cn"
cas = "cas.ncu.edu.cn"
loginUrl = (
    f"https://{cas}:8443/cas/login?service=http%3A%2F%2F{ndyy}%3A8089%2Fcas%2Flogin"
)
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/120.0 Mobile/15E148 Safari/605.1.15",
    "connection": "close",
}
session.headers.update(headers)

def log(level, msg):
    if debug and level == "DEBUG":
        print(f"[{datetime.now()}] [DEBUG]: {msg}")
    else:
        print(f"[{datetime.now()}] [{level}]: {msg}")
        

def getXToken(username, password):
    response = session.get(loginUrl)
    soup = BeautifulSoup(response.text, "html.parser")
    data = {
        "username": username,
        "password": password,
        "rememberMe": False,
        "captcha": soup.find("input", {"name": "captcha"}).get("value"),
        "currentMenu": soup.find("input", {"name": "currentMenu"}).get("value"),
        "failN": soup.find("input", {"name": "failN"}).get("value"),
        "mfaState": soup.find("input", {"name": "mfaState"}).get("value"),
        "execution": soup.find("input", {"name": "execution"}).get("value"),
        "_eventId": soup.find("input", {"name": "_eventId"}).get("value"),
        "geolocation": soup.find("input", {"name": "geolocation"}).get("value"),
        "submit": soup.find("input", {"name": "submit"}).get("value"),
    }
    response = session.post(loginUrl, data=data)
    parsed_url = urlparse(response.request.path_url)
    query_params = parse_qs(parsed_url.query)
    token = query_params.get('token', [None])[0]
    log("DEBUG", token)
    return token


def getCaptcha(token):
    url_captcha = "https://ndyy.ncu.edu.cn/api/generateCaptcha"
    headers_captcha = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_captcha) 
    response_captcha = session.get(url_captcha)
    return response_captcha

KEY = b'ndyyM1m2c3$0j9m8'
IV = b'ncuHe110F*4g5htt'

def pad(data):
    pad_length = AES.block_size - len(data) % AES.block_size
    return data + b'\0' * pad_length

def unpad(data):

    return data.rstrip(b'\0')

def Encrypt(word, keyStr=None, ivStr=None):
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    data = pad(word.encode('utf-8'))
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(data)
    encrypted_base64 = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_base64

def Decrypt(word, keyStr=None, ivStr=None):
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    encrypted_data = base64.b64decode(word)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)
    decrypted = unpad(decrypted).decode('utf-8')
    return decrypted

def decodeCaptcha(captcha_data):
    captcha_base64 = captcha_data.get("captchaImg")
    if not captcha_base64:
        log("ERROR", "获取的验证码数据中缺少 'captchaImg' 键")
        print(captcha_data)
        return None
    captcha_new = Decrypt(captcha_base64)
    header, encoded = captcha_new.split(',', 1)
    
    image_data = base64.b64decode(encoded)
    
    with open('captcha1.jpg', 'wb') as f:
        f.write(image_data)
    ocr = ddddocr.DdddOcr()
    image = open("captcha1.jpg", "rb").read()
    result = ocr.classification(image)
    return result

def makeReservation(token, captcha_result):
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
    # 请根据实际情况修改以下参数
    # data = "2024-11-07"
    # startTime = "18:00-19:00"
    # areaName = "羽毛球5号场地"
    # areaNickname = "hall5"
    date = "202X-XX-XX"
    startTime = "XX:00-XX:00"
    areaName = "羽毛球X号场地"
    areaNickname = "hallX"
    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname,
        "captcha": captcha_result  
    }
    headers_reservation = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_reservation)  # 更新 session 的 headers
    response_reservation = session.get(url_reservation, params=params)
    return response_reservation

if __name__ == "__main__":
    log("INFO", "BEGIN")
    token = getXToken(username, password)
    print(token)
    response_captcha = getCaptcha(token)
    if response_captcha.status_code == 200:
        captcha_data = response_captcha.json()
        captcha_result = decodeCaptcha(captcha_data)
        response_reservation = makeReservation(token, captcha_result)
        if response_reservation.status_code == 200:
            print("预订成功")
            print(response_reservation.json())
        else:
            print(f"预订失败，状态码：{response_reservation.status_code}")
            print(response_reservation.text)
    else:
        print(f"获取验证码失败，状态码：{response_captcha.status_code}")
        print(response_captcha.text)
    log("INFO", "END")