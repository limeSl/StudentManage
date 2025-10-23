# studytime_page.py
import streamlit as st
import gspread
import pandas as pd
import re
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# --- Google Sheets 연결 ---
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPE)
gc = gspread.authorize(creds)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pa6sSB1dFiCge6MwnpgEG1AQnCHnVkVhdb1EGkUPuTU/edit?gid=1916264337").worksheet("Studytime")

data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("📚 오늘의 공부시간 플래너")

# --- 입력 영역 ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 오늘의 목표 공부시간")
    goal_hours = st.number_input("시간", min_value=0, max_value=24, step=1, key="goal_h")
    goal_minutes = st.number_input("분", min_value=0, max_value=59, step=5, key="goal_m")

with col2:
    st.subheader("⏰ 오늘 실제 공부시간")
    actual_hours = st.number_input("시간 ", min_value=0, max_value=24, step=1, key="real_h")
    actual_minutes = st.number_input("분 ", min_value=0, max_value=59, step=5, key="real_m")

if st.button("결과 확인"):
    goal_total_min = goal_hours * 60 + goal_minutes
    actual_total_min = actual_hours * 60 + actual_minutes

    diff = actual_total_min - goal_total_min
    diff_hours = abs(diff) // 60
    diff_minutes = abs(diff) % 60

    if diff > 0:
        st.success(f"💪 오늘 실제 공부 시간은 목표보다 {diff_hours}시간 {diff_minutes}분 많아요!")
        st.write("대단해요! 꾸준한 노력이 성과로 이어지고 있어요 👏")
    elif diff < 0:
        st.warning(f"📉 오늘 실제 공부 시간은 목표보다 {diff_hours}시간 {diff_minutes}분 적어요.")
        st.write("괜찮아요 😊 내일은 조금 더 집중해봐요. 꾸준함이 가장 중요하답니다 💪")
    else:
        st.info("⏱️ 오늘은 목표 공부시간을 정확히 달성했어요! 완벽해요 🌟")

    # --- 구글 시트 평균 공부시간 계산 ---
    def parse_time(t):
        match = re.match(r"(\d+)시간\s*(\d+)분", t)
        if match:
            h, m = map(int, match.groups())
            return h * 60 + m
        return 0

    df["총분"] = df["공부시간"].apply(parse_time)
    avg_min = df["총분"].mean()
    avg_hours = int(avg_min // 60)
    avg_minutes = int(avg_min % 60)

    st.subheader("📊 공부시간 비교")
    st.write(f"전체 평균 공부시간: **{avg_hours}시간 {avg_minutes}분**")

    # --- 그래프 시각화 ---
    labels = ["내 공부시간", "전체 평균"]
    values = [actual_total_min / 60, avg_min / 60]

    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylabel("공부시간 (시간)")
    ax.set_title("오늘의 공부시간 비교")
    st.pyplot(fig)
