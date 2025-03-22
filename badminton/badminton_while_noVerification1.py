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
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = session.get(loginUrl)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 检查所有必需的字段
            required_fields = ["captcha", "currentMenu", "failN", "mfaState", "execution", "_eventId", "geolocation", "submit"]
            field_values = {}
            
            for field in required_fields:
                element = soup.find("input", {"name": field})
                if not element or not element.get("value"):
                    print(f"警告：找不到字段 {field} 或其值为空")
                    if attempt < max_retries - 1:
                        print("等待1秒后重试登录...")
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(f"无法获取登录所需的 {field} 字段")
                field_values[field] = element.get("value")
            
            data = {
                "username": username,
                "password": password,
                "rememberMe": False,
                **field_values
            }
            
            response = session.post(loginUrl, data=data)
            parsed_url = urlparse(response.request.path_url)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            
            if token:
                log("DEBUG", token)
                return token
            else:
                print("警告：未能获取到token")
                if attempt < max_retries - 1:
                    print("等待1秒后重试登录...")
                    time.sleep(1)
                    continue
                else:
                    raise Exception("登录失败：无法获取token")
                    
        except Exception as e:
            print(f"登录过程出错: {str(e)}")
            if attempt < max_retries - 1:
                print("等待1秒后重试登录...")
                time.sleep(1)
            else:
                raise Exception("登录失败，已达到最大重试次数")
    
    return None

def checkAvailability(token, date, startTime, areaName):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url_check = "https://ndyy.ncu.edu.cn/api/badminton/getReservationInformationByDateAndTime"
            params = {
                "date": date,
                "startTime": startTime
            }
            headers_check = {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
                "Referer": "https://ndyy.ncu.edu.cn/booking",
                "Token": token
            }
            session.headers.update(headers_check)
            response = session.get(url_check, params=params)
            
            if response.status_code == 200:
                result = response.json()
                print(f"场地查询响应: {result}")
                return result
            else:
                print(f"场地查询失败，状态码: {response.status_code}")
                if attempt < max_retries - 1:
                    print("等待1秒后重试查询...")
                    time.sleep(1)
                    continue
                
        except Exception as e:
            print(f"查询场地可用性时出错: {str(e)}")
            if attempt < max_retries - 1:
                print("等待1秒后重试查询...")
                time.sleep(1)
            else:
                print("查询场地可用性失败，已达到最大重试次数")
                return None
    
    return None

def preloadBookingPage(token):
    url_booking = "https://ndyy.ncu.edu.cn/booking"
    headers_booking = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Token": token
    }
    session.headers.update(headers_booking)
    return session.get(url_booking)

def makeReservation(token, date, startTime, areaName, areaNickname):
    try:
        # 先预加载预约页面
        preload_response = preloadBookingPage(token)
        if preload_response.status_code != 200:
            print(f"预加载预约页面失败，状态码: {preload_response.status_code}")
            return None

        # 检查场地可用性
        availability = checkAvailability(token, date, startTime, areaName)
        if not availability:
            print("获取场地可用性信息失败")
            return None
        
        print("场地可用性信息：", availability)
        
        url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
        
        params = {
            "role": "ROLE_STUDENT",
            "date": date,
            "startTime": startTime,
            "areaName": areaName,
            "areaNickname": areaNickname
        }
        
        # 打印预约参数
        print(f"正在尝试预约以下场地:")
        print(f"日期: {date}")
        print(f"时间: {startTime}")
        print(f"场地: {areaName}")
        
        headers_reservation = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
            "Referer": "https://ndyy.ncu.edu.cn/booking",
            "Token": token,
        }
        session.headers.update(headers_reservation)
        response_reservation = session.get(url_reservation, params=params)
        return response_reservation
        
    except Exception as e:
        print(f"预约过程出错: {str(e)}")
        return None

if __name__ == "__main__":
    print("欢迎使用羽毛球场地预约系统！")
    print("\n请输入预约信息：")
    
    # 获取用户输入的日期
    while True:
        date = input("请输入预约日期 (格式：YYYY-MM-DD，例如2024-02-26): ")
        try:
            datetime.strptime(date, "%Y-%m-%d")
            break
        except ValueError:
            print("日期格式错误，请重新输入！")
    
    # 获取用户输入的时间段
    print("\n可选时间段：")
    time_slots = [
        "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
        "14:00-15:00", "15:00-16:00", "16:00-17:00", "17:00-18:00",
        "18:00-19:00", "19:00-20:00", "20:00-21:00", "21:00-22:00"
    ]
    for i, slot in enumerate(time_slots, 1):
        print(f"{i}. {slot}")
    
    while True:
        try:
            choice = int(input("\n请选择时间段编号 (1-12): "))
            if 1 <= choice <= len(time_slots):
                startTime = time_slots[choice-1]
                break
            else:
                print("无效的选择，请重新输入！")
        except ValueError:
            print("请输入有效的数字！")
    
    # 获取用户输入的场地
    print("\n可选场地：")
    courts = [
        ("羽毛球1号场地", "hall1"),
        ("羽毛球2号场地", "hall2"),
        ("羽毛球3号场地", "hall3"),
        ("羽毛球4号场地", "hall4"),
        ("羽毛球5号场地", "hall5"),
        ("羽毛球6号场地", "hall6"),
        ("羽毛球7号场地", "hall7"),
        ("羽毛球8号场地", "hall8"),
        ("羽毛球9号场地", "hall9"),
        ("羽毛球10号场地", "hall10"),
        ("羽毛球11号场地", "hall11"),
        ("羽毛球12号场地", "hall12"),
    ]
    for i, (court_name, _) in enumerate(courts, 1):
        print(f"{i}. {court_name}")
    
    while True:
        try:
            choice = int(input("\n请选择场地编号 (1-12): "))
            if 1 <= choice <= len(courts):
                areaName, areaNickname = courts[choice-1]
                break
            else:
                print("无效的选择，请重新输入！")
        except ValueError:
            print("请输入有效的数字！")
    
    # 获取用户输入的目标时间
    while True:
        try:
            target_hour = int(input("\n请输入开始预约的目标时间（小时，24小时制，例如12）: "))
            if 0 <= target_hour <= 23:
                target_minute = int(input("请输入开始预约的目标时间（分钟，例如00）: "))
                if 0 <= target_minute <= 59:
                    break
                else:
                    print("请输入0-59之间的数字！")
            else:
                print("请输入0-23之间的数字！")
        except ValueError:
            print("请输入有效的数字！")
    
    print(f"\n系统将在每天 {target_hour}:{target_minute} 开始预约")
    print(f"预约信息确认：")
    print(f"日期：{date}")
    print(f"时间段：{startTime}")
    print(f"场地：{areaName}")
    print("\n等待预约时间...")
    
    # 无限循环，直到当前时间为指定时间点
    while True:
        current_time = datetime.now()
        if current_time.hour == target_hour and current_time.minute == target_minute:
            print(f"当前时间: {current_time}")
            break  # 到达指定时间点，退出循环并开始执行预订任务
        else:
            time.sleep(1)  # 每秒检查一次时间

    # 开始执行预订任务
    log("INFO", "BEGIN")
    token = getXToken(username, password)
    print(f"获取到的Token: {token}")
    
    # 尝试预约3次
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\n第 {attempt + 1} 次尝试预约")
        # 每次尝试都重新获取token
        if attempt > 0:
            token = getXToken(username, password)
            print(f"刷新Token: {token}")
            
        response_reservation = makeReservation(token, date, startTime, areaName, areaNickname)
        if response_reservation and response_reservation.status_code == 200:
            print("预订请求成功发送")
            result = response_reservation.json()
            print(f"预订结果: {result}")
            if result.get('code') == '200':  # 假设200是成功码
                print("预订成功！")
                break
            else:
                print(f"预订失败: {result.get('msg')}")
        else:
            if response_reservation:
                print(f"请求失败，状态码：{response_reservation.status_code}")
                print(response_reservation.text)
            else:
                print("预约请求未能完成")
        
        if attempt < max_retries - 1:
            print("等待1秒后重试...")
            time.sleep(1)
    
    log("INFO", "END")