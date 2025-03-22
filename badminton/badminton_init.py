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
from typing import Dict, Any, Optional, Union, Tuple
import time

def getEnv(env: str, default: Any = "", required: bool = False) -> str:
    """
    从配置文件或环境变量获取配置参数
    
    Parameters
    ----------
    env : str
        环境变量名称
    default : Any
        默认值
    required : bool
        是否必须
        
    Returns
    -------
    str
        配置值
    """
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

# 从环境变量获取调试模式设置
debug = getEnv("DEBUG", True)

# 系统域名配置
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

def log(level: str, msg: str) -> None:
    """
    日志输出函数
    
    Parameters
    ----------
    level : str
        日志级别
    msg : str
        日志消息
    """
    if debug and level == "DEBUG":
        print(f"[{datetime.now()}] [DEBUG]: {msg}")
    else:
        print(f"[{datetime.now()}] [{level}]: {msg}")
        

def getXToken(username: str, password: str) -> Optional[str]:
    """
    获取系统登录Token
    
    Parameters
    ----------
    username : str
        用户名
    password : str
        密码
        
    Returns
    -------
    Optional[str]
        登录Token
    """
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


def getCaptcha(token: str) -> requests.Response:
    """
    获取验证码
    
    Parameters
    ----------
    token : str
        登录Token
        
    Returns
    -------
    requests.Response
        验证码响应对象
    """
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

def pad(data: bytes) -> bytes:
    """
    使用PKCS#7填充数据
    
    Parameters
    ----------
    data : bytes
        需要填充的数据
        
    Returns
    -------
    bytes
        填充后的数据
    """
    # 使用PKCS#7填充
    padding_length = AES.block_size - (len(data) % AES.block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def unpad(data: bytes) -> bytes:
    """
    移除PKCS#7填充
    
    Parameters
    ----------
    data : bytes
        带填充的数据
        
    Returns
    -------
    bytes
        移除填充后的数据
    """
    # 移除PKCS#7填充
    if not data:
        return data
    padding_length = data[-1]
    if padding_length > AES.block_size:
        return data  # 不是有效的填充，返回原始数据
    if len(data) < padding_length:
        return data  # 数据长度不足，不能移除填充
    # 验证所有填充字节是否相同
    if data[-padding_length:] != bytes([padding_length]) * padding_length:
        return data  # 填充无效，返回原始数据
    return data[:-padding_length]

def Encrypt(word: str, keyStr: Optional[str] = None, ivStr: Optional[str] = None) -> str:
    """
    AES加密函数
    
    Parameters
    ----------
    word : str
        需要加密的文本
    keyStr : Optional[str]
        加密密钥
    ivStr : Optional[str]
        初始化向量
        
    Returns
    -------
    str
        加密后的Base64编码字符串
    """
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    data = pad(word.encode('utf-8'))
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(data)
    encrypted_base64 = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_base64

def Decrypt(word: str, keyStr: Optional[str] = None, ivStr: Optional[str] = None) -> bytes:
    """
    AES解密函数
    
    Parameters
    ----------
    word : str
        需要解密的Base64编码字符串
    keyStr : Optional[str]
        解密密钥
    ivStr : Optional[str]
        初始化向量
        
    Returns
    -------
    bytes
        解密后的二进制数据
    """
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    encrypted_data = base64.b64decode(word)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)
    decrypted = unpad(decrypted)
    return decrypted

def decodeCaptcha(captcha_data: Dict[str, Any]) -> Optional[str]:
    """
    解码验证码
    
    Parameters
    ----------
    captcha_data : Dict[str, Any]
        验证码数据
        
    Returns
    -------
    Optional[str]
        识别后的验证码文本
    """
    captcha_base64 = captcha_data.get("captchaImg")
    if not captcha_base64:
        log("ERROR", "获取的验证码数据中缺少 'captchaImg' 键")
        print(captcha_data)
        return None
    
    log("DEBUG", f"验证码数据类型: {type(captcha_base64)}")
    log("DEBUG", f"验证码数据长度: {len(captcha_base64)}")
    log("DEBUG", f"验证码数据前30字符: {captcha_base64[:30]}")
    
    # 首先尝试直接作为Base64编码的图像数据处理
    if ',' in captcha_base64:
        # 如果包含逗号分隔符，可能是标准的Base64编码图像
        header, encoded = captcha_base64.split(',', 1)
        log("DEBUG", f"检测到Base64头部: {header}")
        try:
            image_data = base64.b64decode(encoded)
            log("DEBUG", "直接Base64解码成功")
        except Exception as e:
            log("ERROR", f"Base64解码失败: {str(e)}")
            return None
    else:
        # 如果没有逗号分隔符，尝试解密
        try:
            decrypted_data = Decrypt(captcha_base64)
            log("DEBUG", f"解密后数据类型: {type(decrypted_data)}")
            log("DEBUG", f"解密后数据长度: {len(decrypted_data)}")
            
            # 检查解密后的数据是否为图像
            if decrypted_data.startswith(b'\xff\xd8\xff'):  # JPEG文件头
                log("DEBUG", "检测到JPEG图像头部")
                image_data = decrypted_data
            else:
                # 尝试从解密后的数据中提取Base64编码
                try:
                    # 查找可能的Base64编码头部
                    if b',' in decrypted_data:
                        header, encoded = decrypted_data.split(b',', 1)
                        log("DEBUG", f"从解密数据中找到Base64头部: {header}")
                        image_data = base64.b64decode(encoded)
                    else:
                        # 尝试直接解码
                        log("DEBUG", "尝试直接解码解密后的数据")
                        try:
                            image_data = base64.b64decode(decrypted_data)
                        except:
                            # 如果解码失败，可能就是原始二进制数据
                            image_data = decrypted_data
                except Exception as e:
                    log("ERROR", f"处理解密数据时出错: {str(e)}")
                    # 最后尝试直接使用解密后的数据
                    image_data = decrypted_data
        except Exception as e:
            log("ERROR", f"解密失败: {str(e)}")
            # 解密失败时尝试直接解码Base64
            try:
                image_data = base64.b64decode(captcha_base64)
                log("DEBUG", "直接Base64解码成功")
            except Exception as e2:
                log("ERROR", f"Base64解码也失败: {str(e2)}")
                return None
    
    # 保存图像数据到文件
    captcha_file = 'captcha1.jpg'
    with open(captcha_file, 'wb') as f:
        f.write(image_data)
    log("DEBUG", "保存图片文件成功")
    
    # 使用OCR识别验证码
    try:
        ocr = ddddocr.DdddOcr()
        image = open(captcha_file, "rb").read()
        result = ocr.classification(image)
        log("DEBUG", f"OCR识别结果: {result}")
        return result
    except Exception as e:
        log("ERROR", f"OCR识别失败: {str(e)}")
        return None

def cleanup_temp_files() -> None:
    """
    清理程序生成的临时文件
    """
    temp_files = ['captcha1.jpg']
    for file in temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                log("DEBUG", f"临时文件 {file} 已删除")
        except Exception as e:
            log("ERROR", f"删除临时文件 {file} 失败: {str(e)}")

def makeReservation(token: str, captcha_result: str, date: str, startTime: str, areaName: str, areaNickname: str) -> requests.Response:
    """
    提交场地预约请求
    
    Parameters
    ----------
    token : str
        登录Token
    captcha_result : str
        验证码结果
    date : str
        预约日期，格式为YYYY-MM-DD
    startTime : str
        预约时间段，格式为HH:MM-HH:MM
    areaName : str
        场地名称
    areaNickname : str
        场地代码
        
    Returns
    -------
    requests.Response
        预约请求响应对象
    """
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
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

def get_user_input() -> Tuple[str, str, str, str, str, str]:
    """
    获取用户输入的预约信息
    
    Returns
    -------
    Tuple[str, str, str, str, str, str]
        用户名、密码、预约日期、时间段、场地名称、场地代码
    """
    # 默认账号密码
    DEFAULT_USERNAME = "419100240107"
    DEFAULT_PASSWORD = "31415926535@Zj"
    
    # 可选时间段列表
    TIME_SLOTS = [
        "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", 
        "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00", 
        "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00", 
        "20:00-21:00", "21:00-22:00"
    ]
    
    # 尝试从环境变量获取用户名密码（安全做法）
    username = getEnv("BADMINTON_USERNAME")
    password = getEnv("BADMINTON_PASSWORD")
    
    # 如果环境变量中没有，则请求用户输入
    if not username:
        username_input = input("请输入学号(直接回车使用默认账号): ")
        username = username_input if username_input.strip() else DEFAULT_USERNAME
    
    if not password:
        import getpass
        password_input = getpass.getpass("请输入密码(直接回车使用默认密码): ")
        password = password_input if password_input.strip() else DEFAULT_PASSWORD
    
    # 获取预约日期，默认为后天
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    date_input = input(f"请输入预约日期(格式:YYYY-MM-DD，直接回车预约{day_after_tomorrow}): ")
    date = date_input if date_input.strip() else day_after_tomorrow
    
    # 时间段选择
    print("\n可选时间段:")
    for i, time_slot in enumerate(TIME_SLOTS, 1):
        print(f"{i}. {time_slot}")
    
    time_choice = input("\n请选择时间段编号(1-14): ")
    try:
        time_idx = int(time_choice) - 1
        if 0 <= time_idx < len(TIME_SLOTS):
            startTime = TIME_SLOTS[time_idx]
        else:
            print("无效选择，默认选择12:00-13:00")
            startTime = "12:00-13:00"
    except ValueError:
        print("输入格式错误，默认选择12:00-13:00")
        startTime = "12:00-13:00"
    
    # 场地选择
    print("\n可选场地:")
    print("1. 羽毛球1号场地 (hall1)")
    print("2. 羽毛球2号场地 (hall2)")
    print("3. 羽毛球3号场地 (hall3)")
    print("4. 羽毛球4号场地 (hall4)")
    print("5. 羽毛球5号场地 (hall5)")
    print("6. 羽毛球6号场地 (hall6)")
    print("7. 羽毛球7号场地 (hall7)")
    print("8. 羽毛球8号场地 (hall8)")
    print("9. 羽毛球9号场地 (hall9)")
    print("10. 羽毛球10号场地 (hall10)")
    print("11. 羽毛球11号场地 (hall11)")
    print("12. 羽毛球12号场地 (hall12)")
    
    choice = input("\n请选择场地编号(1-12): ")
    try:
        hall_num = int(choice)
        if 1 <= hall_num <= 12:
            areaName = f"羽毛球{hall_num}号场地"
            areaNickname = f"hall{hall_num}"
        else:
            print("无效选择，默认选择7号场地")
            areaName = "羽毛球7号场地"
            areaNickname = "hall7"
    except ValueError:
        print("输入格式错误，默认选择7号场地")
        areaName = "羽毛球7号场地"
        areaNickname = "hall7"
    
    print(f"\n预约信息确认:")
    print(f"日期: {date}")
    print(f"时间段: {startTime}")
    print(f"场地: {areaName}")
    
    return username, password, date, startTime, areaName, areaNickname

if __name__ == "__main__":
    log("INFO", "BEGIN")
    
    try:
        # 获取用户输入
        username, password, date, startTime, areaName, areaNickname = get_user_input()
        
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
        
        print(f"\n系统将在每天 {target_hour:02d}:{target_minute:02d} 开始预约")
        print(f"预约信息确认：")
        print(f"日期：{date}")
        print(f"时间段：{startTime}")
        print(f"场地：{areaName}")
        print("\n等待预约时间...")
        
        # 无限循环，直到当前时间为指定时间点
        while True:
            current_time = datetime.now()
            if current_time.hour == target_hour and current_time.minute == target_minute:
                log("INFO", f"当前时间: {current_time}，开始执行预约")
                break  # 到达指定时间点，退出循环并开始执行预订任务
            else:
                time.sleep(1)  # 每秒检查一次时间
        
        # 获取登录token
        token = getXToken(username, password)
        log("INFO", f"获取到Token: {token}")
        
        # 循环尝试预约，直到成功
        success = False
        attempt_count = 0
        max_attempts = 50  # 最大尝试次数
        
        log("INFO", "开始循环尝试预约...")
        while not success and attempt_count < max_attempts:
            attempt_count += 1
            log("INFO", f"第 {attempt_count} 次尝试预约")
            
            try:
                # 每5次尝试刷新一次token
                if attempt_count > 1 and attempt_count % 5 == 0:
                    token = getXToken(username, password)
                    log("INFO", f"刷新Token: {token}")
                
                # 获取验证码
                response_captcha = getCaptcha(token)
                if response_captcha.status_code == 200:
                    captcha_data = response_captcha.json()
                    captcha_result = decodeCaptcha(captcha_data)
                    
                    # 提交预约
                    response_reservation = makeReservation(token, captcha_result, date, startTime, areaName, areaNickname)
                    if response_reservation.status_code == 200:
                        reservation_result = response_reservation.json()
                        if reservation_result.get('code') == '200':
                            success = True
                            log("INFO", "预订成功")
                            print(reservation_result)
                        else:
                            log("WARNING", f"预订未成功: {reservation_result}")
                            time.sleep(1)  # 等待1秒后重试
                    else:
                        log("WARNING", f"预订请求失败，状态码：{response_reservation.status_code}")
                        print(response_reservation.text)
                        time.sleep(2)  # 等待2秒后重试
                else:
                    log("WARNING", f"获取验证码失败，状态码：{response_captcha.status_code}")
                    print(response_captcha.text)
                    time.sleep(2)  # 等待2秒后重试
            except Exception as e:
                log("ERROR", f"本次尝试发生异常: {str(e)}")
                time.sleep(3)  # 发生异常后等待3秒
        
        if not success:
            log("ERROR", f"达到最大尝试次数 {max_attempts}，预约失败")
    except Exception as e:
        log("ERROR", f"程序运行异常: {str(e)}")
    finally:
        # 清理临时文件
        cleanup_temp_files()
        log("INFO", "END")
