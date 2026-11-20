import csv
import os
import tempfile
from calculator import recommend, calc_night_and_day_gb
from datetime import datetime


def make_temp_csv(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "type", "amount", "roaming", "current_tariff"])
        writer.writerows(rows)
    return path


def test_1_zero_usage():
    path = make_temp_csv([["2026-08-01 12:00:00", "call", 0, 0, "eto_250gb"]])
    res = recommend(path)
    os.remove(path)
    assert res["recommended_tariff"] == "Сеники"
    assert res["monthly_savings"] == 1250.0


def test_2_exact_limit():
    rows = [
        ["2026-08-01 12:00:00", "call", 3000, 0, "seniki"],
        ["2026-08-02 12:00:00", "data", 51200, 0, "seniki"],
    ]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["recommendation"] == "остаться"
    assert res["current_monthly_cost"] == 250.0


def test_3_zero_second_call():
    rows = [
        ["2026-08-01 12:00:00", "call", 3000, 0, "seniki"],
        ["2026-08-02 12:00:00", "call", 0, 0, "seniki"],
    ]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["current_monthly_cost"] == 250.0


def test_4_call_round_up():
    rows = [["2026-08-01 12:00:00", "call", 3001, 0, "seniki"]]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["current_monthly_cost"] == 252.0


def test_5_night_unlimited():
    rows = [["2026-08-01 03:00:00", "data", 10240, 0, "seniki"]]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["current_monthly_cost"] == 250.0


def test_6_night_boundary_crossing():
    day_gb = calc_night_and_day_gb(datetime(2026, 8, 1, 0, 55, 0), 50.0)
    assert 0 < day_gb < (50.0 / 1024.0)


def test_7_roaming_charged_separately():
    rows = [["2026-08-01 12:00:00", "call", 30, 1, "seniki"]]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["current_monthly_cost"] == 275.0


def test_8_switch_fee_50_not_worth_it():
    rows = [
        ["2026-08-01 12:00:00", "data", 76 * 1024, 0, "ukmush_ai"],
        ["2026-09-01 12:00:00", "data", 76 * 1024, 0, "ukmush_ai"],
        ["2026-10-01 12:00:00", "data", 76 * 1024, 0, "ukmush_ai"],
    ]
    path = make_temp_csv(rows)
    res = recommend(path)
    os.remove(path)
    assert res["recommendation"] == "остаться"