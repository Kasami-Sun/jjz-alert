"""
北京限行提醒脚本
功能：
1. 手动触发：运行后立即查询今天限行并推送
2. 自动触发：每天凌晨自动运行一次
"""
import requests
from datetime import datetime, date
import json
import os

# ========== 配置区 ==========
# 建议通过环境变量设置，避免硬编码
BARK_KEY = os.getenv("BARK_DEVICE_KEY", "这里换成您的Bark Key")
PLATE_NUMBER = os.getenv("PLATE_NUMBER", "京A12345")
# ==========================

def get_today_restriction():
    """
    查询北京今日限行尾号
    返回：dict，包含限行信息
    """
    today = date.today()
    weekday = today.weekday()  # 0=周一, 6=周日
    
    # 周末不限行
    if weekday >= 5:  # 周六(5)或周日(6)
        return {
            "date": today.isoformat(),
            "weekday": ["周一","周二","周三","周四","周五","周六","周日"][weekday],
            "is_restricted": False,
            "message": "今天是周末，不限行！"
        }
    
    # 北京限行规则（2025年最新）
    # 周一至周五，每天限行两个尾号
    restriction_rules = {
        0: (3, 8),    # 周一限行 3 和 8
        1: (4, 9),    # 周二限行 4 和 9
        2: (5, 0),    # 周三限行 5 和 0
        3: (1, 6),    # 周四限行 1 和 6
        4: (2, 7),    # 周五限行 2 和 7
    }
    
    # 获取今天限行尾号
    today_restricted = restriction_rules[weekday]
    
    # 获取车牌尾号（取最后一位数字）
    plate_last_char = PLATE_NUMBER[-1]
    # 如果是非数字，尝试再往前一位
    if not plate_last_char.isdigit():
        for char in reversed(PLATE_NUMBER):
            if char.isdigit():
                plate_last_char = char
                break
    
    plate_last_digit = int(plate_last_char)
    
    # 判断是否限行
    is_restricted = plate_last_digit in today_restricted
    
    weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]
    
    result = {
        "date": today.isoformat(),
        "weekday": weekday_names[weekday],
        "restricted_digits": today_restricted,
        "plate_last_digit": plate_last_digit,
        "is_restricted": is_restricted,
        "message": f"今天({today.isoformat()}) 限行尾号：{today_restricted[0]} 和 {today_restricted[1]}"
    }
    
    if is_restricted:
        result["message"] += f"\n⚠️ 您的车牌(尾号{plate_last_digit})今日限行！请勿开车上路！"
    else:
        result["message"] += f"\n✅ 您的车牌(尾号{plate_last_digit})今日不限行，可以正常出行。"
    
    return result


def send_bark_notification(content):
    """
    通过Bark推送通知
    """
    if not BARK_KEY or BARK_KEY == "这里换成您的Bark Key":
        print("⚠️ Bark Key未配置，跳过推送")
        return False
    
    try:
        # Bark API地址
        url = f"https://api.day.app/{BARK_KEY}"
        
        # 构建推送内容
        payload = {
            "title": "🚗 北京限行提醒",
            "body": content,
            "group": "限行提醒",
            "sound": "alarm.caf",
            "icon": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f697.png"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Bark推送成功")
            return True
        else:
            print(f"❌ Bark推送失败，状态码：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bark推送异常：{str(e)}")
        return False


def main():
    """
    主函数：查询限行并推送
    """
    print(f"🕐 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 车牌号：{PLATE_NUMBER}")
    print("=" * 40)
    
    # 获取限行信息
    result = get_today_restriction()
    
    # 打印结果
    print(f"📅 日期：{result['date']} ({result['weekday']})")
    print(result['message'])
    print("=" * 40)
    
    # 推送通知
    print("\n📱 准备推送通知...")
    send_bark_notification(result['message'])
    
    print("\n✅ 本次检查完成！")
    
    # 返回结果用于GitHub Actions日志
    return result


if __name__ == "__main__":
    main()
