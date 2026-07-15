import os
import requests
import re
from datetime import date
from bs4 import BeautifulSoup

BARK_KEY = os.getenv("BARK_KEY")
PLATE_NUMBER = os.getenv("PLATE_NUMBER")

def get_restriction_from_web():
    """从北京交警官网抓取今日限行信息"""
    
    # 尝试多个数据源
    urls = [
        "https://www.bjjtgl.gov.cn",
        "https://jtgl.beijing.gov.cn",
        "https://www.beijing.gov.cn"
    ]
    
    today = date.today()
    
    for url in urls:
        try:
            print(f"🌐 正在从 {url} 获取限行信息...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            text = response.text
            
            # 方法1：用正则匹配"限行尾号 X 和 X"
            patterns = [
                rf"{today.month}月{today.day}日.*?限行尾号[：:]\s*(\d)\s*[和与至\-]\s*(\d)",
                rf"限行尾号[：:]\s*(\d)\s*[和与至\-]\s*(\d)",
                rf"尾号[：:]\s*(\d)\s*[和与至\-]\s*(\d)",
                rf"限行[：:]\s*(\d)\s*[和与至\-]\s*(\d)",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    digits = (int(match.group(1)), int(match.group(2)))
                    print(f"✅ 从网页抓取到今日限行尾号：{digits[0]} 和 {digits[1]}")
                    return digits
            
            # 方法2：用BeautifulSoup解析页面
            soup = BeautifulSoup(text, 'html.parser')
            # 查找包含"限行"关键字的文本
            for tag in soup.find_all(['p', 'span', 'div', 'li']):
                if tag.text and '限行' in tag.text:
                    text = tag.text.strip()
                    match = re.search(r'(\d)\s*[和与至\-]\s*(\d)', text)
                    if match:
                        digits = (int(match.group(1)), int(match.group(2)))
                        print(f"✅ 从页面解析到限行尾号：{digits[0]} 和 {digits[1]}")
                        return digits
            
            print(f"⚠️ {url} 未找到限行信息")
            
        except Exception as e:
            print(f"⚠️ 访问 {url} 失败：{e}")
    
    print("❌ 所有数据源都无法获取限行信息")
    return None

def get_plate_last_digit(plate_number):
    """提取车牌最后一位数字"""
    for ch in reversed(plate_number):
        if ch.isdigit():
            return int(ch)
    return 0

def send_bark_notification(message):
    """发送Bark通知"""
    if not BARK_KEY:
        print("⚠️ 未配置 BARK_KEY，跳过推送")
        return
    
    url = f"https://api.day.app/{BARK_KEY}"
    payload = {
        "title": "🚗 北京限行提醒",
        "body": message,
        "group": "限行提醒",
        "sound": "alarm.caf"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Bark 推送成功")
        else:
            print(f"❌ Bark 推送失败，状态码：{resp.status_code}")
    except Exception as e:
        print(f"❌ Bark 推送出错：{e}")

def main():
    print("=" * 50)
    today = date.today()
    weekday = today.weekday()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    
    print(f"📅 {today.isoformat()} 星期{weekdays[weekday]}")
    
    # 周末直接结束
    if weekday >= 5:
        print("🎉 今天是周末，不限行！")
        send_bark_notification(f"今日{today.isoformat()}（周六/日）不限行，祝您周末愉快！")
        return
    
    # 从网页抓取限行信息
    print("🔍 正在从北京交警官网抓取限行数据...")
    restricted_digits = get_restriction_from_web()
    
    if restricted_digits is None:
        print("❌ 网页抓取失败，无法获取限行信息")
        send_bark_notification("⚠️ 今日限行信息获取失败，请手动查询！")
        return
    
    # 获取车牌尾号
    plate_last_digit = get_plate_last_digit(PLATE_NUMBER)
    
    # 判断是否限行
    is_restricted = plate_last_digit in restricted_digits
    
    # 构建消息
    restriction_msg = f"今日限行尾号：{restricted_digits[0]} 和 {restricted_digits[1]}"
    plate_msg = f"您的车牌尾号：{plate_last_digit}"
    
    if is_restricted:
        status_msg = "⚠️ 今日限行，请勿开车上路！"
    else:
        status_msg = "✅ 今日不限行，可正常出行"
    
    full_message = f"{today.isoformat()} 星期{weekdays[weekday]}\n{restriction_msg}\n{plate_msg}\n{status_msg}"
    
    print(f"📌 {restriction_msg}")
    print(f"🚗 {plate_msg}")
    print(f"📢 {status_msg}")
    print("=" * 50)
    
    # 发送通知
    print("\n📱 正在推送Bark通知...")
    send_bark_notification(full_message)
    print("✅ 本次检查完成。")

if __name__ == "__main__":
    main()
