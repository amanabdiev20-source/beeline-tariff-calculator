import csv
import json
import math
import os
from datetime import datetime, timedelta
from itertools import combinations_with_replacement

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calc_night_and_day_gb(start_dt: datetime, total_mb: float):
    if total_mb <= 0:
        return 0.0
    duration_min = max(1, int(math.ceil(total_mb / 5.0)))
    end_dt = start_dt + timedelta(minutes=duration_min)

    day_minutes = 0
    cur = start_dt
    while cur < end_dt:
        if not (1 <= cur.hour < 7):
            day_minutes += 1
        cur += timedelta(minutes=1)

    day_ratio = day_minutes / duration_min
    day_mb = total_mb * day_ratio
    return day_mb / 1024.0


def parse_usage_by_month(usage_file: str):
    months = {}
    current_tariff_id = None

    with open(usage_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not current_tariff_id and row.get("current_tariff"):
                current_tariff_id = row["current_tariff"].strip()

            dt_str = row["date"].strip()
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.strptime(dt_str, "%Y-%m-%d")

            month_key = dt.strftime("%Y-%m")
            if month_key not in months:
                months[month_key] = {
                    "minutes": 0,
                    "gb": 0.0,
                    "sms": 0,
                    "roaming_minutes": 0,
                    "roaming_gb": 0.0,
                    "roaming_sms": 0,
                }

            rec_type = row["type"].strip().lower()
            amount = float(row["amount"])
            is_roaming = str(row.get("roaming", "0")).strip().lower() in ("1", "true", "yes")

            if rec_type == "call":
                mins = math.ceil(amount / 60.0) if amount > 0 else 0
                if is_roaming:
                    months[month_key]["roaming_minutes"] += mins
                else:
                    months[month_key]["minutes"] += mins

            elif rec_type == "sms":
                cnt = int(amount)
                if is_roaming:
                    months[month_key]["roaming_sms"] += cnt
                else:
                    months[month_key]["sms"] += cnt

            elif rec_type == "data":
                if is_roaming:
                    months[month_key]["roaming_gb"] += amount / 1024.0
                else:
                    months[month_key]["gb"] += calc_night_and_day_gb(dt, amount)

    if not months:
        months["2026-01"] = {
            "minutes": 0, "gb": 0.0, "sms": 0,
            "roaming_minutes": 0, "roaming_gb": 0.0, "roaming_sms": 0
        }

    return months, current_tariff_id


def calc_month_cost(month_usage: dict, tariff: dict, selected_addons: tuple) -> float:
    total_fee = tariff["monthly_fee"] + sum(a["price"] for a in selected_addons)
    limit_min = tariff["minutes"] + sum(a["minutes"] for a in selected_addons)
    limit_gb = tariff["gb"] + sum(a["gb"] for a in selected_addons)
    limit_sms = tariff["sms"] + sum(a["sms"] for a in selected_addons)

    over_min = max(0, month_usage["minutes"] - limit_min)
    over_gb = max(0.0, month_usage["gb"] - limit_gb)
    over_sms = max(0, month_usage["sms"] - limit_sms)

    over_cost = (
        over_min * tariff["over_minute_price"]
        + over_gb * tariff["over_gb_price"]
        + over_sms * tariff["over_sms_price"]
    )

    roaming_cost = (
        month_usage["roaming_minutes"] * tariff["roaming_minute_price"]
        + month_usage["roaming_gb"] * tariff["roaming_gb_price"]
        + month_usage["roaming_sms"] * tariff["roaming_sms_price"]
    )

    return total_fee + over_cost + roaming_cost


def recommend(usage_file: str, tariffs=None, addons=None) -> dict:
    if tariffs is None:
        tariffs = load_json("tariffs.json")
    if addons is None:
        addons = load_json("addons.json")

    months_data, current_tariff_id = parse_usage_by_month(usage_file)
    num_months = len(months_data)

    tariff_map = {t["id"]: t for t in tariffs}
    if current_tariff_id not in tariff_map:
        current_tariff_id = "eto_100gb" if "eto_100gb" in tariff_map else tariffs[0]["id"]

    current_tariff = tariff_map[current_tariff_id]
    current_total_3m = sum(calc_month_cost(m, current_tariff, ()) for m in months_data.values())
    current_avg_month = round(current_total_3m / num_months, 2)

    addon_combos = [()]
    for a in addons:
        addon_combos.append((a,))
    for combo in combinations_with_replacement(addons, 2):
        addon_combos.append(combo)

    best_total_3m = float("inf")
    best_tariff = current_tariff
    best_addons = ()

    for t in tariffs:
        for combo in addon_combos:
            cost_3m = sum(calc_month_cost(m, t, combo) for m in months_data.values())
            if cost_3m < best_total_3m:
                best_total_3m = cost_3m
                best_tariff = t
                best_addons = combo

    switch_fee = 50.0 if best_tariff["id"] != current_tariff["id"] else 0.0
    savings_3m = current_total_3m - (best_total_3m + switch_fee)

    if savings_3m <= 0:
        return {
            "current_tariff": current_tariff["name"],
            "current_monthly_cost": current_avg_month,
            "recommendation": "остаться",
            "recommended_tariff": current_tariff["name"],
            "recommended_addons": [],
            "new_monthly_cost": current_avg_month,
            "monthly_savings": 0.0,
        }

    new_avg_month = round(best_total_3m / num_months, 2)
    monthly_savings = round(current_avg_month - new_avg_month, 2)
    addon_names = [a["name"] for a in best_addons]

    rec_label = best_tariff["name"]
    if addon_names:
        rec_label += " + " + ", ".join(addon_names)

    return {
        "current_tariff": current_tariff["name"],
        "current_monthly_cost": current_avg_month,
        "recommendation": rec_label,
        "recommended_tariff": best_tariff["name"],
        "recommended_addons": addon_names,
        "new_monthly_cost": new_avg_month,
        "monthly_savings": monthly_savings,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = recommend(sys.argv[1])
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("Использование: python calculator.py data/usage_1.csv")