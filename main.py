import os
import requests
from datetime import date

BARK_KEY = os.getenv("BARK_KEY")
PLATE_NUMBER = os.getenv("PLATE_NUMBER")

# 免费限行查询API（无需Key）
RESTRICTION_API_URL = "https://api.iyk0.com/weihao/"

def get_restriction_from_api():
    """从免费API获取今日限行信息"""
    params = {"city": "北京"}
    
    try:
        print(f"🌐 正在请求免费限行API...")
        response = requests.get(RESTRICTION_API_URL, params=params, timeout=10)
        data = response.json()
        
        print(f"📡 API返回数据：{data}")
        
        if data.get("code") == 200:
            restriction = data.get("restriction", "")
            # 解析 "3和8" 这种格式
            digits = restriction.replace("和", "").replace("与", "").replace("、", "")
            if len(digits) >= 2 and digits[0].isdigit() and digits[1].isdigit():
                plates = (int(digits), int(digits))
                print(f"✅ 获取到今日限行尾号：{plates[0]} 和 {plates[1]}")
                return plates
        
        print("⚠️ 未能解析限行数据")
        return None
    except Exception as e:
        print(f"⚠️ API查询失败：{e}")
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
    
    # 从API获取限行信息
    print("🔍 正在获取北京今日限行尾号...")
    restricted_digits = get_restriction_from_api()
    
    if restricted_digits is None:
        print("❌ API查询失败，无法获取限行信息")
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
