import os
import csv
import random
from datetime import datetime, timedelta

os.makedirs("data", exist_ok=True)

# 10 профилей под ваш calculator.py:
# type="data" (МБ днем/ночью), type="call" (секунды), type="sms" (шт)
PROFILES = [
    # 1. Качает ~180 ГБ днем, сидит на "eto_250gb" -> выгоден «Безлимит 500 Pro Max» (330 с)
    {"file": "usage_1.csv", "tariff": "eto_250gb", "day_mb": 6144, "night_mb": 1024, "sec_per_day": 200, "sms_prob": 0.1},
    # 2. Качает ~35 ГБ днем, мало звонит, сидит на "eto_100gb" -> выгоден «Сеники» (250 с)
    {"file": "usage_2.csv", "tariff": "eto_100gb", "day_mb": 1200, "night_mb": 300, "sec_per_day": 60, "sms_prob": 0.05},
    # 3. Сидит на "ukmush_ai" и тратит ~70 ГБ -> выгодно «остаться»
    {"file": "usage_3.csv", "tariff": "ukmush_ai", "day_mb": 2400, "night_mb": 400, "sec_per_day": 80, "sms_prob": 0.0},
    # 4. Почти не качает днем (10 ГБ), но качает ночью (80 ГБ) и говорит 40 мин -> выгоден «Сеники» (ночь бесплатно!)
    {"file": "usage_4.csv", "tariff": "eto_100gb", "day_mb": 350, "night_mb": 2700, "sec_per_day": 70, "sms_prob": 0.1},
    # 5. Сидит на "seniki" и тратит ~35 ГБ -> выгодно «остаться»
    {"file": "usage_5.csv", "tariff": "seniki", "day_mb": 1150, "night_mb": 200, "sec_per_day": 60, "sms_prob": 0.05},
    # 6. Качает ~350 ГБ и говорит ~140 мин, сидит на "eto_250gb" -> выгоден «Безлимит 500 Pro Max» (330 с)
    {"file": "usage_6.csv", "tariff": "eto_250gb", "day_mb": 12000, "night_mb": 3000, "sec_per_day": 260, "sms_prob": 0.1},
    # 7. Тратит ~72 ГБ и 50 мин, сидит на "eto_100gb" -> выгоден «Безлимит 500 Pro Max» или «Укмуш AI»
    {"file": "usage_7.csv", "tariff": "eto_100gb", "day_mb": 2450, "night_mb": 500, "sec_per_day": 90, "sms_prob": 0.05},
    # 8. Тратит ~40 ГБ и много звонит (~95 мин), сидит на "eto_250gb" -> выгоден «Сеники» + доп. пакет минут
    {"file": "usage_8.csv", "tariff": "eto_250gb", "day_mb": 1350, "night_mb": 200, "sec_per_day": 185, "sms_prob": 0.1},
    # 9. Сидит на "bezlimit_500" и тратит ~280 ГБ -> выгодно «остаться»
    {"file": "usage_9.csv", "tariff": "bezlimit_500", "day_mb": 9500, "night_mb": 2000, "sec_per_day": 240, "sms_prob": 0.0},
    # 10. Очень много звонит (~230 мин) и качает ~120 ГБ, сидит на "eto_100gb" -> выгоден «Безлимит 500 Pro Max» + пакеты или «Это 250 GB»
    {"file": "usage_10.csv", "tariff": "eto_100gb", "day_mb": 4100, "night_mb": 500, "sec_per_day": 450, "sms_prob": 0.3},
]

start_date = datetime(2026, 8, 1)

for prof in PROFILES:
    filepath = os.path.join("data", prof["file"])
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "type", "amount", "roaming", "current_tariff"])
        
        for day_offset in range(90):
            curr_day = start_date + timedelta(days=day_offset)
            # Дневной интернет (14:30) в МБ
            d_mb = round(max(10.0, random.gauss(prof["day_mb"], prof["day_mb"] * 0.15)), 1)
            writer.writerow([curr_day.strftime("%Y-%m-%d 14:30:00"), "data", d_mb, 0, prof["tariff"]])
            
            # Ночной интернет (03:15 - попадает в бесплатное окно 01:00-07:00!)
            if prof["night_mb"] > 0:
                n_mb = round(max(0.0, random.gauss(prof["night_mb"], prof["night_mb"] * 0.15)), 1)
                if n_mb > 0:
                    writer.writerow([curr_day.strftime("%Y-%m-%d 03:15:00"), "data", n_mb, 0, prof["tariff"]])
            
            # Звонки (18:15) в секундах
            secs = max(0, int(round(random.gauss(prof["sec_per_day"], 40))))
            if secs > 0:
                writer.writerow([curr_day.strftime("%Y-%m-%d 18:15:00"), "call", secs, 0, prof["tariff"]])
                
            # SMS (12:00)
            if random.random() < prof["sms_prob"]:
                writer.writerow([curr_day.strftime("%Y-%m-%d 12:00:00"), "sms", 1, 0, prof["tariff"]])

print("Готово! 10 разнообразных профилей успешно созданы в папке data/")
