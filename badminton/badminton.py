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

debug = getEnv("DEBUG", True)
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
    
    # 保存原始加密数据以便调试
    with open('captcha_raw.txt', 'w') as f:
        f.write(captcha_base64)
    log("DEBUG", "保存原始验证码数据成功")
    
    # 尝试直接解密
    try:
        # 使用更简单的PKCS7填充方式
        from Crypto.Util.Padding import unpad as crypto_unpad
        
        key = KEY
        iv = IV
        encrypted_data = base64.b64decode(captcha_base64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted_data)
        
        # 尝试移除填充，但可能不需要
        try:
            decrypted = crypto_unpad(decrypted, AES.block_size)
        except:
            log("DEBUG", "标准去填充失败，保持原始解密数据")
        
        # 查找Base64图像数据特征
        # 常见的Base64图像前缀: data:image/jpeg;base64, 或 data:image/png;base64,
        data_pos = decrypted.find(b'data:image')
        if data_pos >= 0:
            # 找到了图像数据标记
            img_data_start = decrypted.find(b',', data_pos)
            if img_data_start > 0:
                log("DEBUG", f"找到Base64图像数据，位置: {data_pos}, {img_data_start}")
                encoded = decrypted[img_data_start + 1:]
                try:
                    image_data = base64.b64decode(encoded)
                    log("DEBUG", "成功解码图像数据")
                except Exception as e:
                    log("ERROR", f"解码Base64图像数据失败: {str(e)}")
                    # 保存解密后的数据以便调试
                    with open('decrypted.bin', 'wb') as f:
                        f.write(decrypted)
                    return None
            else:
                log("DEBUG", "找到图像数据标记，但格式不符合预期")
                image_data = decrypted
        else:
            # 检查是否为直接的JPEG数据
            if decrypted.startswith(b'\xff\xd8\xff'):
                log("DEBUG", "解密数据是直接的JPEG格式")
                image_data = decrypted
            else:
                log("DEBUG", "尝试保存解密后的原始数据作为图像")
                image_data = decrypted
    except Exception as e:
        log("ERROR", f"解密验证码失败: {str(e)}")
        return None
    
    # 保存解密后的数据为图像文件
    with open('captcha_debug.bin', 'wb') as f:
        f.write(decrypted)
    
    # 将数据另存为一个基本的JPEG文件尝试
    with open('captcha.jpg', 'wb') as f:
        # 如果数据不是以JPEG文件头开始，添加一个标准JPEG文件头
        if not image_data.startswith(b'\xff\xd8\xff'):
            log("DEBUG", "添加JPEG文件头")
            # 最简单的JPEG文件头
            jpeg_header = b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00'
            f.write(jpeg_header)
        f.write(image_data)
    
    # 直接使用保存的文件，而不是字节数据
    try:
        ocr = ddddocr.DdddOcr()
        with open('captcha.jpg', 'rb') as f:
            image = f.read()
        result = ocr.classification(image)
        log("DEBUG", f"OCR识别结果: {result}")
        return result
    except Exception as e:
        log("ERROR", f"OCR识别失败: {str(e)}")
        
        # 尝试使用原始编码数据，跳过解密步骤
        try:
            log("DEBUG", "尝试直接使用原始Base64数据")
            # 尝试直接解码原始Base64
            raw_data = base64.b64decode(captcha_base64)
            with open('captcha_raw.jpg', 'wb') as f:
                f.write(raw_data)
                
            ocr = ddddocr.DdddOcr()
            with open('captcha_raw.jpg', 'rb') as f:
                image = f.read()
            result = ocr.classification(image)
            log("DEBUG", f"使用原始数据OCR识别结果: {result}")
            return result
        except Exception as e2:
            log("ERROR", f"使用原始数据OCR识别也失败: {str(e2)}")
            return None

def isCaptchaRequired(captcha_data):
    """
    检查是否需要验证码
    
    Parameters
    ----------
    captcha_data : dict
        验证码接口返回的数据
        
    Returns
    -------
    bool
        True表示需要验证码，False表示不需要
    """
    # 检查返回数据中是否包含验证码图片
    if not captcha_data.get("captchaImg"):
        log("DEBUG", "接口未返回验证码图片，可能不需要验证码")
        return False
        
    # 检查状态码或其他可能表明不需要验证码的字段
    if captcha_data.get("code") == "CAPTCHA_NOT_REQUIRED" or captcha_data.get("captchaRequired") is False:
        log("DEBUG", "服务器明确表示不需要验证码")
        return False
        
    # 检查接口返回的消息内容
    message = captcha_data.get("message", "").lower()
    if "not required" in message or "无需验证" in message:
        log("DEBUG", f"根据消息判断不需要验证码: {message}")
        return False
        
    # 默认情况下认为需要验证码
    log("DEBUG", "判断为需要验证码")
    return True

def makeReservationWithoutCaptcha(token, date, startTime, areaName, areaNickname):
    """
    不使用验证码直接进行预约
    """
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
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
    session.headers.update(headers_reservation)
    log("DEBUG", f"不使用验证码进行预约: {params}")
    response_reservation = session.get(url_reservation, params=params)
    return response_reservation

def makeReservation(token, captcha_result, date, startTime, areaName, areaNickname):
    """
    使用验证码进行预约
    
    Parameters
    ----------
    token : str
        认证token
    captcha_result : str
        验证码识别结果
    date : str
        预约日期
    startTime : str
        开始时间段
    areaName : str
        场地名称
    areaNickname : str
        场地昵称
        
    Returns
    -------
    Response
        预约请求的响应
    """
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname,
        "captcha": captcha_result  # 加入验证码
    }
    headers_reservation = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_reservation)
    log("DEBUG", f"使用验证码进行预约: {params}")
    response_reservation = session.get(url_reservation, params=params)
    return response_reservation

if __name__ == "__main__":
    log("INFO", "BEGIN")
    
    # 配置预约参数
    date = "2025-03-24"
    startTime = "12:00-13:00"
    areaName = "羽毛球8号场地"
    areaNickname = "hall8"
    
    # 获取token
    token = getXToken(username, password)
    if not token:
        log("ERROR", "获取token失败，无法继续")
        exit(1)
    log("INFO", f"成功获取token: {token}")
    
    # 获取验证码
    response_captcha = getCaptcha(token)
    if response_captcha.status_code != 200:
        log("ERROR", f"获取验证码失败，状态码：{response_captcha.status_code}")
        log("ERROR", response_captcha.text)
        exit(1)
    
    # 解析验证码响应
    try:
        captcha_data = response_captcha.json()
        log("DEBUG", f"验证码接口返回: {captcha_data}")
    except Exception as e:
        log("ERROR", f"解析验证码响应失败: {str(e)}")
        log("ERROR", response_captcha.text)
        exit(1)
    
    # 检查是否需要验证码
    if isCaptchaRequired(captcha_data):
        log("INFO", "需要验证码，进行验证码识别")
        
        # 尝试识别验证码，最多重试3次
        captcha_result = None
        max_retries = 3
        retry_count = 0
        
        while captcha_result is None and retry_count < max_retries:
            if retry_count > 0:
                log("INFO", f"第{retry_count}次重试验证码识别")
                # 重新获取验证码
                response_captcha = getCaptcha(token)
                if response_captcha.status_code == 200:
                    try:
                        captcha_data = response_captcha.json()
                    except:
                        log("ERROR", "重新获取验证码解析失败")
                        retry_count += 1
                        continue
                else:
                    log("ERROR", f"重新获取验证码失败: {response_captcha.status_code}")
                    retry_count += 1
                    continue
            
            captcha_result = decodeCaptcha(captcha_data)
            retry_count += 1
        
        if captcha_result is None:
            log("ERROR", f"验证码识别失败，尝试了{max_retries}次，尝试无验证码预约")
            # 当验证码识别失败时，尝试不使用验证码进行预约
            response_reservation = makeReservationWithoutCaptcha(token, date, startTime, areaName, areaNickname)
        else:
            log("INFO", f"验证码识别结果: {captcha_result}")
            # 使用验证码进行预约
            response_reservation = makeReservation(token, captcha_result, date, startTime, areaName, areaNickname)
    else:
        log("INFO", "不需要验证码，直接进行预约")
        # 不使用验证码直接预约
        response_reservation = makeReservationWithoutCaptcha(token, date, startTime, areaName, areaNickname)
    
    # 处理预约结果
    if response_reservation.status_code == 200:
        try:
            result = response_reservation.json()
            log("INFO", "预约响应成功")
            log("INFO", f"预约结果: {result}")
            
            # 检查预约是否真正成功
            if result.get("success") or result.get("code") == 200 or "success" in str(result).lower():
                log("INFO", "🎉 预约成功 🎉")
            else:
                log("WARN", f"预约可能失败: {result}")
        except Exception as e:
            log("ERROR", f"解析预约结果失败: {str(e)}")
            log("ERROR", response_reservation.text)
    else:
        log("ERROR", f"预约失败，状态码：{response_reservation.status_code}")
        log("ERROR", response_reservation.text)
    
    log("INFO", "END")
