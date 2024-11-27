import requests
import os
from configparser import ConfigParser
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


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
username = "419100230079"
password = "Zxcv1234."
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

    if token:
        log("INFO", f"登录成功，token: {token}")
    else:
        log("ERROR", "登录失败，未获取到 token")

    return token


def refreshPage():
    """模拟刷新页面，获取最新的预订页面信息"""
    refresh_url = "https://ndyy.ncu.edu.cn/booking"  # 预订页面的 URL
    response = session.get(refresh_url)
    if response.status_code == 200:
        log("INFO", "页面刷新成功")
    else:
        log("ERROR", f"页面刷新失败，状态码：{response.status_code}")
    return response


def makeReservation(token):
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"

    # 请根据实际情况修改以下参数
    date = "2024-11-27"
    startTime = "18:00-19:00"
    areaName = "羽毛球7号场地"
    areaNickname = "hall7"

    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname,
    }

    headers_reservation = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",  # 确保这个值和实际请求的一致
        "Token": token,
    }
    session.headers.update(headers_reservation)  # 更新 session 的 headers

    # 尝试刷新页面获取最新的状态信息
    refreshPage()

    # 进行预订请求
    response_reservation = session.get(url_reservation, params=params)

    # 打印响应内容，检查返回的错误详情
    log("INFO", f"预订请求返回状态码：{response_reservation.status_code}")
    log("INFO", f"返回内容：{response_reservation.text}")

    return response_reservation


if __name__ == "__main__":
    log("INFO", "BEGIN")
    token = getXToken(username, password)

    # 检查登录是否成功
    if not token:
        log("ERROR", "登录失败，无法继续执行预定")
        exit(1)  # 登录失败时退出脚本

    # 直接跳过验证码部分，直接进行预约
    response_reservation = makeReservation(token)
    if response_reservation.status_code == 200:
        print("预订成功")
        print(response_reservation.json())
    else:
        print(f"预订失败，状态码：{response_reservation.status_code}")
        print(response_reservation.text)

    log("INFO", "END")
