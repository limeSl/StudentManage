# study_time_tracker_local.py
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="공부시간 트래커", layout="centered")

st.title("📚 공부시간 트래커 (로컬 버전)")

# --- 데이터 초기화 ---
if "study_data" not in st.session_state:
    st.session_state["study_data"] = pd.DataFrame(columns=["date", "goal_min", "actual_min"])

# --- 날짜 선택 ---
today = datetime.date.today()
selected_date = st.date_input("날짜를 선택하세요", today)

# --- 목표/실제 공부시간 입력 ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 목표 공부시간")
    goal_h = st.number_input("시간", 0, 24, 2, key="goal_h")
    goal_m = st.number_input("분", 0, 59, 0, key="goal_m")

with col2:
    st.subheader("⏰ 실제 공부시간")
    actual_h = st.number_input("시간 ", 0, 24, 1, key="actual_h")
    actual_m = st.number_input("분 ", 0, 59, 0, key="actual_m")

# --- 입력 처리 ---
if st.button("결과 저장"):
    goal_total = goal_h * 60 + goal_m
    actual_total = actual_h * 60 + actual_m

    # 날짜가 이미 있으면 갱신
    df = st.session_state["study_data"]
    df = df[df["date"] != str(selected_date)]
    df.loc[len(df)] = [str(selected_date), goal_total, actual_total]
    st.session_state["study_data"] = df

    # --- 비교 결과 ---
    diff = actual_total - goal_total
    diff_h, diff_m = divmod(abs(diff), 60)

    if diff > 0:
        st.success(f"💪 오늘 실제 공부 시간은 목표보다 {diff_h}시간 {diff_m}분 많아요!")
        st.write("대단해요! 꾸준한 노력이 성과로 이어지고 있어요 👏")
    elif diff < 0:
        st.warning(f"📉 오늘 실제 공부 시간은 목표보다 {diff_h}시간 {diff_m}분 적어요.")
        st.write("괜찮아요 😊 내일은 조금 더 집중해봐요. 꾸준함이 가장 중요하답니다 💪")
    else:
        st.info("⏱️ 오늘은 목표 공부시간을 정확히 달성했어요! 완벽해요 🌟")

# --- 최근 7일 그래프 ---
if len(st.session_state["study_data"]) > 0:
    st.subheader("📈 최근 7일 공부시간 추세")
    df = st.session_state["study_data"].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(7)

    df["goal_hr"] = df["goal_min"] / 60
    df["actual_hr"] = df["actual_min"] / 60

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["date"], df["goal_hr"], label="목표 공부시간", color="gray", linewidth=2, marker="o")
    ax.plot(df["date"], df["actual_hr"], label="실제 공부시간", color="#FF9999", linewidth=2, marker="o")

    ax.set_xlabel("날짜")
    ax.set_ylabel("공부시간 (시간)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# --- 데이터 표시 (디버그용) ---
with st.expander("📋 입력된 데이터 보기"):
    st.dataframe(st.session_state["study_data"])
