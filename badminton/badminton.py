# pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
import ddddocr
import requests
import os
import time
from configparser import ConfigParser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import base64
from Crypto.Cipher import AES  
from Crypto.Util.Padding import pad, unpad 
import uuid

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

debug = getEnv("DEBUG", True)
# 将 username 和 password 替换为自己的学号和密码
username = getEnv("USERNAME", "419100240107")
password = getEnv("PASSWORD", "31415926535@Zj")
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
    try:
        log("DEBUG", f"开始获取Token，用户名: {username}")
        response = session.get(loginUrl)
        
        if response.status_code != 200:
            log("ERROR", f"获取登录页面失败，状态码: {response.status_code}")
            return None
            
        log("DEBUG", f"成功获取登录页面，状态码: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 检查登录页面元素是否存在
        captcha_input = soup.find("input", {"name": "captcha"})
        if not captcha_input:
            log("ERROR", "登录页面格式异常，未找到验证码输入框")
            log("DEBUG", "页面内容片段：" + response.text[:200] + "...")
            return None
            
        # 构建登录表单数据
        try:
            data = {
                "username": username,
                "password": password,
                "rememberMe": False,
                "captcha": captcha_input.get("value"),
                "currentMenu": soup.find("input", {"name": "currentMenu"}).get("value"),
                "failN": soup.find("input", {"name": "failN"}).get("value"),
                "mfaState": soup.find("input", {"name": "mfaState"}).get("value"),
                "execution": soup.find("input", {"name": "execution"}).get("value"),
                "_eventId": soup.find("input", {"name": "_eventId"}).get("value"),
                "geolocation": soup.find("input", {"name": "geolocation"}).get("value"),
                "submit": soup.find("input", {"name": "submit"}).get("value"),
            }
            log("DEBUG", "成功构建登录表单数据")
        except Exception as e:
            log("ERROR", f"构建登录表单数据失败: {str(e)}")
            return None
        
        # 发送POST请求进行登录
        log("DEBUG", "开始发送登录请求")
        response = session.post(loginUrl, data=data)
        
        # 检查响应状态
        if response.status_code != 200:
            log("ERROR", f"登录请求失败，状态码：{response.status_code}")
            return None
            
        log("DEBUG", f"登录请求成功，状态码: {response.status_code}")
        
        # 检查是否有重定向的请求路径
        if not hasattr(response, 'request') or not hasattr(response.request, 'path_url'):
            log("ERROR", "登录响应异常，无法获取请求路径")
            log("DEBUG", f"响应URL: {response.url}")
            return None
            
        parsed_url = urlparse(response.request.path_url)
        query_params = parse_qs(parsed_url.query)
        token = query_params.get('token', [None])[0]
        
        if not token:
            log("ERROR", "未能从响应中获取token")
            if 'login' in response.url.lower():
                log("DEBUG", "仍在登录页面，可能登录失败")
            return None
            
        log("DEBUG", f"成功获取Token: {token[:20]}...")
        return token
    except Exception as e:
        log("ERROR", f"获取Token过程中出现异常: {str(e)}")
        import traceback
        log("DEBUG", f"详细错误: {traceback.format_exc()}")
        return None


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
    # 使用PKCS#7填充
    padding_length = AES.block_size - (len(data) % AES.block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def unpad(data):
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
    decrypted = unpad(decrypted)
    return decrypted

def decodeCaptcha(captcha_data):
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
    
    # 生成一个确保唯一的文件名，以避免并发问题
    captcha_filename = f'captcha_{uuid.uuid4()}.jpg'
    
    # 保存图像数据到文件
    with open(captcha_filename, 'wb') as f:
        f.write(image_data)
    log("DEBUG", f"保存图片文件成功: {captcha_filename}")
    
    # 使用OCR识别验证码 - 确保使用文件读取方式
    try:
        ocr = ddddocr.DdddOcr(show_ad=False)  # 禁用广告显示
        with open(captcha_filename, 'rb') as f:
            image = f.read()
        result = ocr.classification(image)
        log("DEBUG", f"OCR识别结果: {result}")
        
        # 清理临时文件
        try:
            os.remove(captcha_filename)
            log("DEBUG", "临时文件已清理")
        except:
            pass
            
        return result
    except Exception as e:
        log("ERROR", f"OCR识别失败: {str(e)}")
        return None


def get_user_inputs():
    """
    获取用户输入的预约参数
    
    Returns
    -------
    dict
        包含用户输入的预约参数
    """
    print("\n===== 羽毛球场地预约系统 =====")
    
    # 定义可用的场地列表
    court_options = [
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
    
    # 定义可用的时间段
    time_slots = [
        "08:00-09:00", 
        "09:00-10:00", 
        "10:00-11:00", 
        "11:00-12:00",
        "14:00-15:00", 
        "15:00-16:00", 
        "16:00-17:00", 
        "17:00-18:00",
        "18:00-19:00", 
        "19:00-20:00", 
        "20:00-21:00", 
        "21:00-22:00"
    ]
    
    # 获取预约日期
    default_date = getEnv("BOOKING_DATE", "2025-03-24")
    date_input = input(f"请输入预约日期 (格式 YYYY-MM-DD, 默认 {default_date}): ")
    date = date_input.strip() if date_input.strip() else default_date
    
    # 显示时间段选项
    print("\n可选的时间段:")
    for i, time_slot in enumerate(time_slots, 1):
        print(f"{i}. {time_slot}")
    
    # 获取预约时间段
    time_choice = 0
    while time_choice < 1 or time_choice > len(time_slots):
        try:
            time_choice = int(input(f"\n请输入时间段序号 (1-{len(time_slots)}): "))
            if time_choice < 1 or time_choice > len(time_slots):
                print(f"输入错误，请输入1到{len(time_slots)}之间的数字")
        except ValueError:
            print("请输入有效的数字")
    
    start_time = time_slots[time_choice - 1]
    print(f"已选择时间段: {start_time}")
    
    # 显示场地选项
    print("\n可选的场地:")
    for i, (court_name, _) in enumerate(court_options, 1):
        print(f"{i}. {court_name}")
    
    # 获取场地信息
    court_choice = 0
    while court_choice < 1 or court_choice > len(court_options):
        try:
            court_choice = int(input(f"\n请输入场地序号 (1-{len(court_options)}): "))
            if court_choice < 1 or court_choice > len(court_options):
                print(f"输入错误，请输入1到{len(court_options)}之间的数字")
        except ValueError:
            print("请输入有效的数字")
    
    area_name, area_nickname = court_options[court_choice - 1]
    print(f"已选择场地: {area_name}")
    
    # 获取最大重试次数
    default_retries = getEnv("MAX_RETRIES", "10")
    retries_input = input(f"\n请输入最大重试次数 (默认 {default_retries}): ")
    max_retries = retries_input.strip() if retries_input.strip() else default_retries
    
    # 获取重试间隔
    default_interval = getEnv("RETRY_INTERVAL", "5")
    interval_input = input(f"请输入重试间隔(秒) (默认 {default_interval}): ")
    retry_interval = interval_input.strip() if interval_input.strip() else default_interval
    
    return {
        "date": date,
        "start_time": start_time,
        "area_name": area_name,
        "area_nickname": area_nickname,
        "max_retries": int(max_retries),
        "retry_interval": int(retry_interval)
    }

def makeReservation(token, captcha_result, booking_params=None):
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
    # 如果传入了预约参数，则使用传入的参数，否则从配置中获取
    if booking_params:
        date = booking_params["date"]
        startTime = booking_params["start_time"]
        areaName = booking_params["area_name"]
        areaNickname = booking_params["area_nickname"]
    else:
        # 从配置中获取预约参数
        date = getEnv("BOOKING_DATE", "2025-03-24")
        startTime = getEnv("BOOKING_TIME", "12:00-13:00")
        areaName = getEnv("BOOKING_AREA", "羽毛球7号场地")
        areaNickname = getEnv("BOOKING_AREA_NICKNAME", "hall7")
    
    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname,
        "captcha": captcha_result  
    }
    
    log("INFO", f"预约参数: 日期={date}, 时间={startTime}, 场地={areaName}")
    
    headers_reservation = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_reservation)  # 更新 session 的 headers
    response_reservation = session.get(url_reservation, params=params)
    return response_reservation

def wait_until_start_time():
    # 分步输入开始执行时间
    print("\n===== 设置开始执行时间 =====")
    print("直接回车表示立即开始执行")
    
    # 获取小时
    hour_input = input("请输入开始执行的小时 (0-23): ").strip()
    if not hour_input:
        log("INFO", "未设置开始执行时间，立即开始执行")
        return
        
    # 获取分钟
    minute_input = input("请输入开始执行的分钟 (0-59): ").strip()
    if not minute_input:
        log("INFO", "未设置开始执行时间，立即开始执行")
        return
    
    try:
        # 解析时间
        hour = int(hour_input)
        minute = int(minute_input)
        
        # 验证时间范围
        if hour < 0 or hour > 23:
            log("ERROR", f"小时值超出范围: 应为0-23")
            return
            
        if minute < 0 or minute > 59:
            log("ERROR", f"分钟值超出范围: 应为0-59")
            return
            
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果目标时间已经过去，不等待
        if target_time <= now:
            log("INFO", f"目标时间 {hour:02d}:{minute:02d} 已过去，立即开始执行")
            return
            
        time_diff = (target_time - now).total_seconds()
        log("INFO", f"将在 {hour:02d}:{minute:02d} 开始执行，等待 {time_diff:.0f} 秒")
        
        # 每30秒输出一次日志
        while now < target_time:
            time.sleep(min(30, (target_time - now).total_seconds()))
            now = datetime.now()
            time_diff = (target_time - now).total_seconds()
            if time_diff > 0:
                log("INFO", f"还有 {time_diff:.0f} 秒开始执行")
        
        log("INFO", "达到指定时间，开始执行")
    except Exception as e:
        log("ERROR", f"解析开始时间出错: {str(e)}，立即开始执行")

def try_reservation(booking_params=None):
    # 每次尝试时创建新的会话
    global session
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 1. 获取Token
        log("DEBUG", "开始尝试预约流程")
        token = getXToken(username, password)
        if not token:
            log("ERROR", "获取Token失败")
            return False
            
        log("INFO", "获取Token成功")
        
        # 2. 获取验证码
        max_captcha_retries = 3  # 验证码识别尝试次数
        captcha_result = None
        
        for captcha_attempt in range(1, max_captcha_retries + 1):
            log("DEBUG", f"尝试获取验证码 ({captcha_attempt}/{max_captcha_retries})")
            response_captcha = getCaptcha(token)
            
            if response_captcha.status_code != 200:
                log("ERROR", f"获取验证码失败，状态码：{response_captcha.status_code}")
                log("DEBUG", response_captcha.text)
                continue  # 尝试下一次获取验证码
                
            captcha_data = response_captcha.json()
            captcha_result = decodeCaptcha(captcha_data)
            
            if captcha_result:
                log("INFO", f"验证码识别成功: {captcha_result}")
                break  # 成功识别，跳出循环
            else:
                log("WARNING", f"验证码识别失败 ({captcha_attempt}/{max_captcha_retries})")
                if captcha_attempt < max_captcha_retries:
                    time.sleep(1)  # 等待1秒后重试
        
        if not captcha_result:
            log("ERROR", "所有验证码识别尝试都失败")
            return False
        
        # 3. 预约场地
        log("DEBUG", "开始发送预约请求")
        response_reservation = makeReservation(token, captcha_result, booking_params)
        
        if response_reservation.status_code != 200:
            log("ERROR", f"预订请求失败，状态码：{response_reservation.status_code}")
            log("DEBUG", response_reservation.text)
            return False
            
        # 4. 处理预约结果
        try:
            response_json = response_reservation.json()
            log("DEBUG", f"预约响应: {str(response_json)}")
            
            if response_json.get("success"):
                log("SUCCESS", "预订成功")
                log("INFO", str(response_json))
                return True
            else:
                error_msg = response_json.get('message', '未知错误')
                log("ERROR", f"预订失败: {error_msg}")
                # 如果是验证码错误，可以尝试重新获取验证码
                if "验证码" in error_msg or "captcha" in error_msg.lower():
                    log("INFO", "验证码错误，可以在下一次循环中重试")
                return False
        except Exception as e:
            log("ERROR", f"解析预约结果时出错: {str(e)}")
            return False
            
    except Exception as e:
        log("ERROR", f"预约过程出现异常: {str(e)}")
        import traceback
        log("DEBUG", f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    try:
        log("INFO", "BEGIN")
        
        # 获取用户输入的预约参数
        booking_params = get_user_inputs()
        
        # 等待直到指定的开始时间
        wait_until_start_time()
        
        max_retries = booking_params["max_retries"]
        retry_interval = booking_params["retry_interval"]
        success = False
        
        log("INFO", f"开始预约: 日期={booking_params['date']}, 时间={booking_params['start_time']}, 场地={booking_params['area_name']}")
        log("INFO", f"最大尝试次数: {max_retries}, 重试间隔: {retry_interval}秒")
        
        # 重试循环
        for attempt in range(1, max_retries + 1):
            log("INFO", f"尝试预约 ({attempt}/{max_retries})")
            
            try:
                if try_reservation(booking_params):
                    success = True
                    break
            except Exception as e:
                log("ERROR", f"第{attempt}次尝试中发生异常: {str(e)}")
                import traceback
                log("DEBUG", f"详细错误: {traceback.format_exc()}")
                
            if attempt < max_retries:
                log("INFO", f"将在 {retry_interval} 秒后重试")
                time.sleep(retry_interval)
        
        if success:
            log("SUCCESS", "预约成功完成!")
        else:
            log("ERROR", f"在 {max_retries} 次尝试后预约失败")
        
    except KeyboardInterrupt:
        log("INFO", "用户中断了程序执行")
    except Exception as e:
        log("ERROR", f"程序执行过程中发生异常: {str(e)}")
        import traceback
        log("ERROR", f"详细错误: {traceback.format_exc()}")
    finally:
        log("INFO", "END")
