import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Bark 秘钥和车牌号
BARK_KEY = os.getenv("BARK_KEY", "")
PLATE_NUMBER = os.getenv("PLATE_NUMBER", "京A12345")

# 北京限行规则（周一至周五对应限行尾号，通过环境变量可动态覆盖）
# 格式：RESTRICTION_RULES="1,6;2,7;3,8;4,9;5,0"
_restriction_env = os.getenv("RESTRICTION_RULES", "1,6;2,7;3,8;4,9;5,0")
_parsed = []
for _item in _restriction_env.split(";"):
    _pair = _item.strip().split(",")
    if len(_pair) == 2:
        _parsed.append((int(_pair[0].strip()), int(_pair[1].strip())))
    else:
        _parsed.append(None)

RESTRICTION_RULES = {
    0: _parsed[0] if len(_parsed) > 0 else (1, 6),   # 周一
    1: _parsed[1] if len(_parsed) > 1 else (2, 7),   # 周二
    2: _parsed[2] if len(_parsed) > 2 else (3, 8),   # 周三
    3: _parsed[3] if len(_parsed) > 3 else (4, 9),   # 周四
    4: _parsed[4] if len(_parsed) > 4 else (5, 0),   # 周五
    5: None,     # 周六不限行
    6: None      # 周日不限行
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def get_today_restriction_info():
    """获取今日限行信息（北京时间）"""
    now = datetime.now(BEIJING_TZ)
    today = now.date()
    weekday = today.weekday()
    weekday_name = WEEKDAY_NAMES[weekday]

    info = {
        "date": today.isoformat(),
        "weekday": weekday_name,
        "restricted_digits": None,
        "plate_last_digit": None,
        "is_restricted": False,
        "message": ""
    }

    # 周末不限行
    if weekday >= 5:
        info["message"] = (
            f"今日 {today.isoformat()}（{weekday_name}）不限行。\n"
            f"🕐 检查时间：{now.strftime('%H:%M:%S')}"
        )
        return info

    # 获取限行尾号
    restricted_digits = RESTRICTION_RULES[weekday]

    # 提取车牌最后一位数字
    plate_last_char = PLATE_NUMBER[-1]
    if not plate_last_char.isdigit():
        for ch in PLATE_NUMBER[::-1]:
            if ch.isdigit():
                plate_last_char = ch
                break
    plate_last_digit = int(plate_last_char)

    # 判断是否限行
    is_restricted = plate_last_digit in restricted_digits

    info["restricted_digits"] = restricted_digits
    info["plate_last_digit"] = plate_last_digit
    info["is_restricted"] = is_restricted

    # 生成消息
    time_str = now.strftime("%H:%M:%S")
    base_msg = (
        f"今日 {today.isoformat()}（{weekday_name}）\n"
        f"限行尾号：{restricted_digits[0]} 和 {restricted_digits[1]}\n"
        f"🕐 检查时间：{time_str}"
    )
    if is_restricted:
        info["message"] = f"{base_msg}\n⚠️ 您的车牌（尾号 {plate_last_digit}）今日限行，请勿上路！"
    else:
        info["message"] = f"{base_msg}\n✅ 您的车牌（尾号 {plate_last_digit}）今日不限行。"

    return info


def send_bark_notification(message):
    """发送 Bark 通知"""
    if not BARK_KEY:
        print("⚠️ 未配置 BARK_KEY，跳过推送")
        return False

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
            return True
        else:
            print(f"❌ Bark 推送失败，状态码：{resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Bark 推送出错：{e}")
        return False


def main():
    print("=" * 40)
    info = get_today_restriction_info()

    print(f"📅 {info['date']}（{info['weekday']}）")
    if info["restricted_digits"]:
        print(f"🔢 今日限行尾号：{info['restricted_digits'][0]} 和 {info['restricted_digits'][1]}")
    print(f"🚗 车牌尾号：{info['plate_last_digit']}")
    print(f"📢 {info['message']}")
    print("=" * 40)

    print("\n📱 正在推送 Bark 通知...")
    send_bark_notification(info["message"])
    print("✅ 本次检查完成。")


if __name__ == "__main__":
    main()
