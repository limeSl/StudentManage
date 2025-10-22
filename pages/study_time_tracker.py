# pages/study_time_tracker.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# --- 구글 시트 연결 설정 ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPE)
gc = gspread.authorize(creds)

# --- 시트 불러오기 ---
FILE_NAME = "StudyTimeDB"
students_sheet = gc.open(FILE_NAME).worksheet("students")
all_sheet = gc.open(FILE_NAME).worksheet("study_time_all")

students_df = pd.DataFrame(students_sheet.get_all_records())
all_df = pd.DataFrame(all_sheet.get_all_records())

# --- 로그인된 사용자 정보 ---
if "user_id" not in st.session_state:
    st.warning("로그인 후 이용 가능합니다.")
    st.stop()

user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

st.title(f"📘 공부시간 관리 ({user_name}님)")

# --- 1. 날짜 및 목표시간 입력 ---
today = datetime.today().date()
selected_date = st.date_input("📅 날짜 선택", value=today)

goal_hours = st.number_input("🎯 오늘의 목표 공부시간 (시간)", min_value=0.0, max_value=24.0, step=0.5)
actual_hours = st.number_input("⏰ 오늘의 실제 공부시간 (시간)", min_value=0.0, max_value=24.0, step=0.5)

if st.button("저장하기"):
    # 데이터프레임에 추가
    new_row = {
        "date": str(selected_date),
        "id": user_id,
        "name": user_name,
        "goal_hours": goal_hours,
        "actual_hours": actual_hours
    }
    all_df = pd.concat([all_df, pd.DataFrame([new_row])], ignore_index=True)

    # Google Sheets 업데이트
    all_sheet.append_row(list(new_row.values()))

    # 개인 시트 확인 후 없으면 생성
    try:
        student_sheet = gc.open(FILE_NAME).worksheet(user_id)
    except gspread.exceptions.WorksheetNotFound:
        student_sheet = gc.open(FILE_NAME).add_worksheet(title=user_id, rows="1000", cols="10")
        student_sheet.append_row(list(new_row.keys()))
    student_sheet.append_row(list(new_row.values()))

    st.success("오늘의 공부시간이 저장되었습니다!")

# --- 2. 목표 대비 실제 비교 ---
if goal_hours > 0 and actual_hours > 0:
    diff = actual_hours - goal_hours
    h = int(abs(diff))
    m = int(abs(diff * 60) % 60)
    if diff >= 0:
        st.info(f"✅ 오늘의 공부 시간은 목표보다 **{h}시간 {m}분 많아요!**")
    else:
        st.warning(f"⚠️ 오늘의 공부 시간은 목표보다 **{h}시간 {m}분 적어요.**")

    # --- 막대그래프 시각화 ---
    fig, ax = plt.subplots()
    ax.bar(["목표시간", "실제시간"], [goal_hours, actual_hours])
    ax.set_ylabel("시간")
    ax.set_title(f"{selected_date} 공부시간 비교")
    st.pyplot(fig)

# --- 3. 이번 주 공부시간 그래프 ---
st.subheader("📆 이번 주 공부시간 추이")

today = datetime.today()
start_of_week = today - timedelta(days=today.weekday())  # 월요일
end_of_week = start_of_week + timedelta(days=6)

mask = (pd.to_datetime(all_df["date"]) >= start_of_week) & (pd.to_datetime(all_df["date"]) <= end_of_week)
week_df = all_df[mask]

if not week_df.empty:
    # 개인 데이터
    user_week_df = week_df[week_df["id"] == user_id]
    user_week_df = user_week_df.groupby("date", as_index=False)["actual_hours"].mean()

    # 반 평균 (같은 class 기준)
    user_class = students_df[students_df["id"] == user_id]["class"].values[0]
    class_df = week_df.merge(students_df, on="id")
    class_week_df = class_df[class_df["class"] == user_class]
    class_avg_df = class_week_df.groupby("date", as_index=False)["actual_hours"].mean()

    # --- 선그래프 시각화 ---
    fig2, ax2 = plt.subplots()
    ax2.plot(user_week_df["date"], user_week_df["actual_hours"], marker="o", label="내 공부시간")
    ax2.plot(class_avg_df["date"], class_avg_df["actual_hours"], marker="s", linestyle="--", label="우리반 평균")
    ax2.set_title("이번 주 공부시간 비교")
    ax2.set_xlabel("날짜")
    ax2.set_ylabel("시간")
    ax2.legend()
    st.pyplot(fig2)
else:
    st.info("이번 주 공부기록이 아직 없습니다.")
