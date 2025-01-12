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
from datetime import datetime, timedelta
import time

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

debug = getEnv("DEBUG", False)
# 将 username 和 password 替换为自己的学号和密码
username = "419100240107"
password = "31415926535@Zj"
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

def makeReservation(token):
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
    # 请根据实际情况修改以下参数
    # data = "2024-11-13"
    # startTime = "18:00-19:00"
    # areaName = "羽毛球2号场地"
    # areaNickname = "hall2"
    date = "2025-1-14"
    startTime = "18:00-19:00"
    areaName = "羽毛球1号场地"
    areaNickname = "hall1"
    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname
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
    # 无限循环，直到当前时间为中午 12 点
    while True:
        current_time = datetime.now()
        if current_time.hour == 12 and current_time.minute == 0:
            print(current_time.hour)
            break  # 到达中午 12 点，退出循环并开始执行预订任务
        else:
            # print(current_time.minute)
            time.sleep(1)  # 每分钟检查一次时间

    # 12 点开始执行预订任务
    log("INFO", "BEGIN")
    token = getXToken(username, password)
    print(token)
    response_reservation = makeReservation(token)
    if response_reservation.status_code == 200:
        print("预订成功")
        print(response_reservation.json())
    else:
        print(f"预订失败，状态码：{response_reservation.status_code}")
        print(response_reservation.text)
    log("INFO", "END")