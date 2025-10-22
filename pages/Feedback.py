import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="학생 피드백 조회", page_icon="🎓", layout="centered")

# 🎨 기본 스타일 설정
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 48px;      /* 제목 크기 키움 */
            color: #1A5276;
            font-weight: 800;
            margin-bottom: -10px;
        }
        .sub {
            text-align: center;
            color: #5D6D7E;
            font-size: 18px;
            margin-bottom: 40px;
        }
        .feedback-box {
            background-color: #F4F6F7;
            padding: 20px;
            border-radius: 10px;
            border-left: 6px solid #3498DB;
            margin-top: 20px;
        }
        .score-box {
            background-color: #EBF5FB;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 18px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# 1️⃣ 제목
# ----------------------------
st.markdown('<p class="title">🎓 학생 피드백 조회 시스템</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">이름과 학번을 입력하면, 구글 시트에서 피드백과 점수를 확인할 수 있습니다.</p>', unsafe_allow_html=True)

# ----------------------------
# 2️⃣ 학생 입력 구역
# ----------------------------
with st.container():
    st.markdown("### 🧑‍🎓 학생 정보 입력")
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("이름을 입력하세요", "")
    with col2:
        student_id = st.text_input("학번을 입력하세요", "")

# ----------------------------
# 3️⃣ 구글 시트 불러오기
# ----------------------------
sheet_url = "https://docs.google.com/spreadsheets/d/1EUt6naZuxN1eJ0CIbUAphijpZU9r5pFJ-nKj4bA_l2Q/edit?usp=sharing"
csv_url = sheet_url.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv")

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

try:
    df = load_data(csv_url)
except Exception as e:
    st.error("❌ 구글 시트 데이터를 불러오는 데 실패했습니다.")
    st.stop()

# ----------------------------
# 4️⃣ 학생 검색 및 피드백 표시
# ----------------------------
if student_name and student_id:
    # D열(학번), E열(이름) 기준 탐색
    id_col = df.columns[3]   # D열
    name_col = df.columns[4] # E열

    match = df[(df[id_col].astype(str) == student_id) & (df[name_col] == student_name)]

    if not match.empty:
        st.success(f"✅ {student_name} 학생의 데이터를 찾았습니다.")
        row = match.iloc[0]

        # A, B, C열 추출
        summary_col = df.columns[0]  # A열
        score_col = df.columns[1]    # B열
        feedback_col = df.columns[2] # C열

        summary = row[summary_col]
        score = float(row[score_col])
        feedback = row[feedback_col]

        # ----------------------------
        # 5️⃣ 과제 내용 요약 표시
        # ----------------------------
        st.markdown("### 📘 과제 내용 요약")
        st.markdown(f"<div class='feedback-box'>{summary}</div>", unsafe_allow_html=True)

        # ----------------------------
        # 6️⃣ 점수 시각화
        # ----------------------------
        st.markdown("### 📊 점수 비교")

        scores = df[score_col].dropna().astype(float)
        avg_score = np.mean(scores)
        median_score = np.median(scores)
        student_score = score

        fig = go.Figure()

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=student_score,
            title={'text': "내 점수"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2E86C1"},
                'steps': [
                    {'range': [0, median_score], 'color': "#E5E8E8"},
                    {'range': [median_score, avg_score], 'color': "#AED6F1"},
                    {'range': [avg_score, 100], 'color': "#D6EAF8"},
                ],
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div class='score-box'>
        📈 <b>평균 점수:</b> {avg_score:.1f}점  
        📊 <b>중간 점수:</b> {median_score:.1f}점  
        🧍 <b>내 점수:</b> {student_score:.1f}점
        </div>
        """, unsafe_allow_html=True)

        # ----------------------------
        # 7️⃣ 피드백 표시
        # ----------------------------
        st.markdown("### 💬 피드백")
        st.markdown(f"<div class='feedback-box'>{feedback}</div>", unsafe_allow_html=True)

    else:
        st.warning("⚠️ 입력한 이름과 학번이 일치하는 학생을 찾을 수 없습니다.")
else:
    st.info("👆 위에 이름과 학번을 입력해주세요.")
