# study_time_tracker_pomodoro.py
import streamlit as st
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt

st.set_page_config(page_title="공부시간 추적 + 뽀모도로", layout="centered")
st.title("📚 공부시간 트래커 + 🍅 뽀모도로 타이머")

# -----------------------------
# 초기화
# -----------------------------
if "study_data" not in st.session_state:
    st.session_state["study_data"] = pd.DataFrame(columns=["date", "goal_hours", "goal_minutes", "real_hours", "real_minutes"])

if "pomodoro_running" not in st.session_state:
    st.session_state["pomodoro_running"] = False
    st.session_state["mode"] = "focus"
    st.session_state["remaining_time"] = 0

# -----------------------------
# 날짜 선택
# -----------------------------
selected_date = st.date_input("날짜 선택", datetime.date.today())

# -----------------------------
# 목표 공부시간 입력
# -----------------------------
st.subheader("🎯 오늘의 목표 공부시간 설정")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    goal_h = st.number_input("목표 시간", min_value=0, step=1)
with col2:
    goal_m = st.number_input("목표 분", min_value=0, max_value=59, step=1)
with col3:
    if st.button("목표 저장"):
        existing = st.session_state["study_data"]["date"] == selected_date
        if existing.any():
            st.session_state["study_data"].loc[existing, ["goal_hours", "goal_minutes"]] = [goal_h, goal_m]
        else:
            new = pd.DataFrame([{
                "date": selected_date,
                "goal_hours": goal_h,
                "goal_minutes": goal_m,
                "real_hours": 0,
                "real_minutes": 0
            }])
            st.session_state["study_data"] = pd.concat([st.session_state["study_data"], new], ignore_index=True)
        st.success("✅ 목표 공부시간이 저장되었습니다!")

# -----------------------------
# 실제 공부시간 입력
# -----------------------------
st.subheader("⏱️ 실제 공부시간 기록")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    real_h = st.number_input("실제 시간", min_value=0, step=1)
with col2:
    real_m = st.number_input("실제 분", min_value=0, max_value=59, step=1)
with col3:
    if st.button("실제 공부시간 저장"):
        existing = st.session_state["study_data"]["date"] == selected_date
        if existing.any():
            st.session_state["study_data"].loc[existing, ["real_hours", "real_minutes"]] = [real_h, real_m]
            st.success("✅ 실제 공부시간이 저장되었습니다!")
        else:
            st.warning("⚠️ 먼저 목표 공부시간을 설정해주세요!")

# -----------------------------
# 목표 vs 실제 비교 멘트
# -----------------------------
st.subheader("📊 오늘의 공부 현황")

record = st.session_state["study_data"][st.session_state["study_data"]["date"] == selected_date]
if not record.empty:
    row = record.iloc[0]
    goal_total = row["goal_hours"] * 60 + row["goal_minutes"]
    real_total = row["real_hours"] * 60 + row["real_minutes"]
    diff = real_total - goal_total

    if goal_total > 0:
        diff_h, diff_m = divmod(abs(diff), 60)
        if diff > 0:
            st.success(f"🔥 오늘 실제 공부시간은 목표보다 {diff_h}시간 {diff_m}분 많아요! 대단해요 👏")
        elif diff < 0:
            st.info(f"💪 오늘은 목표보다 {diff_h}시간 {diff_m}분 적어요. 내일은 더 힘내봐요!")
        else:
            st.success("🎯 오늘은 목표를 정확히 달성했어요! 완벽해요 ✨")

# -----------------------------
# 뽀모도로 타이머
# -----------------------------
st.markdown("---")
st.subheader("🍅 뽀모도로 타이머")

focus_time = st.number_input("집중 시간(분)", min_value=1, value=25)
break_time = st.number_input("휴식 시간(분)", min_value=1, value=5)

if st.button("🍅 뽀모도로 시작"):
    st.session_state["pomodoro_running"] = True
    st.session_state["mode"] = "focus"
    st.session_state["remaining_time"] = focus_time * 60

if st.session_state["pomodoro_running"]:
    placeholder = st.empty()
    while st.session_state["pomodoro_running"]:
        mins, secs = divmod(st.session_state["remaining_time"], 60)
        timer_display = f"⏳ {st.session_state['mode'].upper()} MODE | 남은 시간: {int(mins):02}:{int(secs):02}"
        placeholder.markdown(f"<h3 style='text-align:center;'>{timer_display}</h3>", unsafe_allow_html=True)
        time.sleep(1)
        st.session_state["remaining_time"] -= 1

        if st.session_state["remaining_time"] <= 0:
            if st.session_state["mode"] == "focus":
                st.success("🎉 집중 시간 종료! 휴식 시작 🍵")
                st.session_state["mode"] = "break"
                st.session_state["remaining_time"] = break_time * 60
            else:
                st.success("✅ 휴식 시간 종료! 새로운 사이클을 시작하세요 💪")
                st.session_state["pomodoro_running"] = False
            st.experimental_rerun()

# -----------------------------
# 최근 7일 그래프
# -----------------------------
st.markdown("---")
st.subheader("📈 최근 7일 공부시간 추이")

if len(st.session_state["study_data"]) > 0:
    df = st.session_state["study_data"].sort_values("date", ascending=True)
    df["goal_total"] = df["goal_hours"] * 60 + df["goal_minutes"]
    df["real_total"] = df["real_hours"] * 60 + df["real_minutes"]
    recent = df.tail(7)

    plt.figure(figsize=(6, 3))
    plt.plot(recent["date"], recent["goal_total"], label="목표 공부시간", color="gray", linestyle="--", marker="o")
    plt.plot(recent["date"], recent["real_total"], label="실제 공부시간", color="salmon", marker="o")
    plt.ylabel("공부시간 (분)")
    plt.legend()
    st.pyplot(plt)
else:
    st.info("최근 7일 데이터가 없습니다.")
