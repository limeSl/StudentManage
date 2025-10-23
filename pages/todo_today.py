# todo_page.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="투두리스트", layout="centered")
st.title("📝 오늘의 투두리스트")

# -----------------------------
# 초기화
# -----------------------------
if "todos" not in st.session_state:
    st.session_state["todos"] = pd.DataFrame(columns=[
        "subject", "goal_type", "goal_value", "actual_value", "progress"
    ])

# -----------------------------
# 목표 입력 영역
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    subject = st.selectbox("과목 선택", ["국어", "수학", "영어", "과학", "사회", "정보"])

with col2:
    # 영어 과목일 때만 '단어 외우기' 추가
    goal_options = ["교과서 공부하기", "문제집 풀기", "직접 입력"]
    if subject == "영어":
        goal_options.insert(2, "단어 외우기")
    goal_type = st.selectbox("목표 선택", goal_options)

with col3:
    if goal_type == "직접 입력":
        goal_value = st.text_input("직접 목표 입력", placeholder="예: 수행평가 준비하기")
    else:
        unit = "페이지" if goal_type == "교과서 공부하기" else "문제"
        if goal_type == "단어 외우기":
            unit = "단어"
        goal_num = st.number_input(f"목표 {unit} 수", min_value=1, step=1, value=10)
        goal_value = f"{goal_num} {unit}"

if st.button("목표 추가"):
    new_row = pd.DataFrame([{
        "subject": subject,
        "goal_type": goal_type,
        "goal_value": goal_value,
        "actual_value": "",
        "progress": 0
    }])
    st.session_state["todos"] = pd.concat([st.session_state["todos"], new_row], ignore_index=True)
    st.success(f"✅ {subject} - {goal_type} 목표가 추가되었습니다!")

# -----------------------------
# 투두리스트 표시
# -----------------------------
st.subheader("📚 오늘의 목표 목록")

if len(st.session_state["todos"]) == 0:
    st.info("아직 추가된 목표가 없습니다. 위에서 새로운 목표를 등록해 보세요!")
else:
    df = st.session_state["todos"]
    for i, row in df.iterrows():
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([2, 1])

            goal_display = f"**{row['subject']} | {row['goal_type']}**<br>목표: {row['goal_value']}"
            if row["progress"] == 100:
                st.markdown(f"~~{goal_display}~~ ✅", unsafe_allow_html=True)
            else:
                st.markdown(goal_display, unsafe_allow_html=True)

            # 실제 공부량 입력
            if row["goal_type"] != "직접 입력":
                unit = "페이지" if "페이지" in row["goal_value"] else "문제"
                if "단어" in row["goal_value"]:
                    unit = "단어"
                actual_num = st.number_input(
                    f"실제 {unit} 수 ({row['subject']})", min_value=0, step=1, key=f"actual_{i}"
                )
                goal_num = int(''.join([c for c in row["goal_value"] if c.isdigit()]))
                progress = min(100, int((actual_num / goal_num) * 100)) if goal_num > 0 else 0
            else:
                progress = st.slider(f"직접 입력 - 달성률 (%) ({row['subject']})", 0, 100, 0, key=f"custom_{i}")
                actual_num = f"{progress}% 달성"

            # 진행도 반영
            st.session_state["todos"].at[i, "actual_value"] = actual_num
            st.session_state["todos"].at[i, "progress"] = progress

            # 메시지 / 버튼 / 효과
            if progress == 100:
                st.balloons()
                st.success("🎉 목표를 모두 달성했어요! 멋져요 👏")
            else:
                st.info(f"{progress}% 달성했어요.")
                if st.button("다 했어요!", key=f"done_{i}"):
                    st.session_state["todos"].at[i, "progress"] = 100
                    st.experimental_rerun()

# -----------------------------
# 전체 달성률 계산
# -----------------------------
df = st.session_state["todos"]
if len(df) > 0:
    avg_progress = df["progress"].mean()
    st.markdown("---")
    st.subheader(f"🌟 오늘의 전체 목표 달성률은 **{avg_progress:.1f}%**예요!")
