import streamlit as st
import pandas as pd
import altair as alt

# =========== ✅ CONFIG ===========
st.set_page_config(page_title="학생 피드백 조회", page_icon="📘", layout="centered")

# =========== 🎨 UI 스타일 ===========
TITLE_STYLE = "font-size: 36px; font-weight: 700; text-align: center; margin-bottom: 10px;"
SUBTITLE_STYLE = "font-size: 20px; font-weight: 600; margin-top: 20px;"

# =========== 📂 구글 시트 불러오기 ===========
sheet_url = "https://docs.google.com/spreadsheets/d/1EUt6naZuxN1eJ0CIbUAphijpZU9r5pFJ-nKj4bA_l2Q/export?format=csv"
df = pd.read_csv(sheet_url)

# 데이터 전처리
df.columns = df.columns.str.strip()
df["D"] = df["D"].astype(str).str.strip()  # 학번
df["E"] = df["E"].astype(str).str.strip()  # 이름

# =========== 🧑 학생 입력 ===========

st.markdown(f"<h1 style='{TITLE_STYLE}'>📘 학생 피드백 조회 서비스</h1>", unsafe_allow_html=True)
st.write("아래에 학번과 이름을 입력하면 피드백과 점수를 확인할 수 있습니다.")

student_id = st.text_input("🔢 학번을 입력하세요 (예: 10101)").strip()
student_name = st.text_input("🧑 이름을 입력하세요").strip()

if st.button("조회하기"):
    if student_id and student_name:
        # 학생 행 검색
        student_row = df[(df["D"] == student_id) & (df["E"] == student_name)]

        if len(student_row) == 1:
            st.success(f"✅ {student_name} 학생의 데이터를 성공적으로 찾았습니다!")

            summary = student_row.iloc[0]["A"]
            score = float(student_row.iloc[0]["B"])
            all_scores = df["B"].astype(float)
            avg_score = all_scores.mean()
            median_score = all_scores.median()

            # ===== 과제 요약 =====
            st.markdown(f"<div style='{SUBTITLE_STYLE}'>📝 과제 내용 요약</div>", unsafe_allow_html=True)
            st.info(summary)

            # ===== 점수 비교 그래프 =====
            st.markdown(f"<div style='{SUBTITLE_STYLE}'>📊 점수 비교</div>", unsafe_allow_html=True)
            score_data = pd.DataFrame({
                "평가 항목": ["내 점수", "평균 점수", "중간 점수"],
                "점수": [score, avg_score, median_score]
            })

            bar_chart = (
                alt.Chart(score_data)
                .mark_bar()
                .encode(
                    x=alt.X("평가 항목", sort=None),
                    y="점수",
                    tooltip=["평가 항목", "점수"]
                )
                .properties(width=300, height=280)  # ✅ 크기 줄임
            )
            st.altair_chart(bar_chart, use_container_width=True)

            # ===== 피드백 =====
            st.markdown(f"<div style='{SUBTITLE_STYLE}'>💬 피드백</div>", unsafe_allow_html=True)
            feedback = student_row.iloc[0]["C"]
            st.write(feedback)

        else:
            st.error("⚠️ 학생 정보를 찾을 수 없습니다. 학번과 이름을 정확히 다시 입력해주세요.")
    else:
        st.warning("학번과 이름을 모두 입력해주세요.")
