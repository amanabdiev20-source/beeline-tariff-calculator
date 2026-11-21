import json
import os
import tempfile
import streamlit as st
from calculator import recommend, load_json, parse_usage_by_month, calc_month_cost

st.set_page_config(page_title="Beeline Калькулятор Тарифа", page_icon="🐝", layout="centered")

st.markdown("""
<style>
.beeline-banner {
    background: linear-gradient(135deg, #1A1A1A 0%, #2B2610 100%);
    border-left: 6px solid #FFCC00;
    padding: 20px 24px;
    border-radius: 12px;
    margin-bottom: 18px;
}
.beeline-banner h1 {
    color: #FFCC00;
    margin: 0 0 6px 0;
    font-size: 28px;
}
.beeline-banner p {
    color: #E0E0E0;
    margin: 0;
    font-size: 18px !important;
}
.badge-row {
    margin-top: 14px;
}
.badge {
    display: inline-block;
    background-color: #FFCC00;
    color: #121212;
    font-weight: 700;
    font-size: 15px !important;
    padding: 6px 14px;
    border-radius: 20px;
    margin-right: 8px;
}
[data-testid="stAppViewContainer"] [data-testid="stMetricLabel"] p,
[data-testid="stAppViewContainer"] [data-testid="stMetricLabel"] label {
    font-size: 20px !important;
    font-weight: 600 !important;
}
[data-testid="stAppViewContainer"] [data-testid="stMetricValue"],
[data-testid="stAppViewContainer"] [data-testid="stMetricValue"] * {
    font-size: 25px !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    word-break: break-word !important;
    line-height: 1.2 !important;
}
[data-testid="stAppViewContainer"] [data-testid="stMetricDelta"],
[data-testid="stAppViewContainer"] [data-testid="stMetricDelta"] * {
    font-size: 16px !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
</style>
<div class="beeline-banner">
    <h1>🐝 Beeline • Умный подбор тарифа</h1>
    <p>Персональный анализ детализации за 3 месяца • Осенний хакатон INAI.KG • Команда ИСИТО</p>
    <div class="badge-row">
        <span class="badge">5 реальных тарифов</span>
        <span class="badge">Ночь 01:00–07:00 бесплатно</span>
        <span class="badge">Учёт перехода 50 сом</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📂 База абонентов (10 профилей)", "📤 Загрузить свой CSV"])

usage_path = None

with tab1:
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    files = sorted([f for f in os.listdir(data_dir) if f.endswith(".csv")], key=lambda x: int(x.split("_")[1].split(".")[0])) if os.path.exists(data_dir) else []
    if files:
        selected_file = st.selectbox("Выберите файл детализации абонента:", files)
        usage_path = os.path.join(data_dir, selected_file)
    else:
        st.warning("Сначала запустите generate_data.py для создания тестовых абонентов.")

with tab2:
    uploaded = st.file_uploader("Загрузите CSV-файл детализации", type=["csv"])
    if uploaded is not None:
        fd, tmp_path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getvalue())
        usage_path = tmp_path

if usage_path:
    res = recommend(usage_path)
    tariffs = load_json("tariffs.json")
    months_data, _ = parse_usage_by_month(usage_path)
    num_m = max(1, len(months_data))

    st.subheader("💰 Финансовый результат и рекомендация")
    col1, col2, col3 = st.columns([1.15, 1.35, 1.0])
    col1.metric("Текущий тариф", f'«{res["current_tariff"]}»', f"{res['current_monthly_cost']} сом/мес")
    addons_list = res.get("recommended_addons", [])
    short_rec = f'«{res["recommended_tariff"]}» + пакет' if addons_list else (f'«{res["recommendation"]}»' if res["recommendation"] != "остаться" else "остаться")
    col2.metric("Рекомендуемый тариф", short_rec, f"{res['new_monthly_cost']} сом/мес")
    col3.metric("Чистая экономия", f"{res['monthly_savings']} сом", "в месяц (с учётом 50 с)" if res["monthly_savings"] > 0 else "остаться выгоднее")

    rec_t = next((t for t in tariffs if t["name"] == res["recommended_tariff"]), None)
    perks = ""
    if rec_t:
        gb = rec_t.get("data_gb", rec_t.get("internet_gb", 0))
        mins = rec_t.get("minutes_other", rec_t.get("minutes", 0))
        sms = rec_t.get("sms", 0)
        gb_str = "безлимит ГБ" if gb in (-1, None) or gb >= 999 else f"{gb} ГБ"
        perks = f" (включает: {gb_str}, {mins} мин, {sms} SMS)"

    if res["recommendation"] == "остаться":
        st.info(f"💡 Ваш текущий тариф уже оптимален{perks} — переход не окупится за 3 месяца с учётом комиссии 50 сом.")
    else:
        if addons_list:
            from collections import Counter
            counts = Counter(addons_list)
            addons_text = " + ".join([f"{cnt} × {name}" if cnt > 1 else name for name, cnt in counts.items()])
            rec_phrase = f"тариф «{res['recommended_tariff']}»{perks} и подключить {addons_text}"
        else:
            rec_phrase = f"тариф «{res['recommended_tariff']}»{perks}"
        st.success(f"✅ Рекомендуем перейти на {rec_phrase} — чистая экономия составит {round(res['monthly_savings'] * 3, 2)} сом за 3 месяца!")
    
    st.subheader("📊 Сравнение средней стоимости по линейке Beeline")
    chart_data = {}
    for t in tariffs:
        avg_cost = round(sum(calc_month_cost(m, t, ()) for m in months_data.values()) / num_m, 2)
        chart_data[t["name"]] = avg_cost

    st.bar_chart(chart_data, color="#FFCC00")

    col_json, col_dl = st.columns([3, 1])
    with col_json:
        with st.expander("Посмотреть технический JSON-ответ"):
            st.json(res)
    with col_dl:
        st.download_button(
            label="⬇️ Скачать JSON",
            data=json.dumps(res, ensure_ascii=False, indent=2),
            file_name="recommendation.json",
            mime="application/json"
        )
