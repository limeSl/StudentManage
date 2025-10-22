# main.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="학생 피드백 조회", page_icon="🎓", layout="centered")

# --- 스타일 ---
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 56px;
            color: #0B4C86;
            font-weight: 900;
            margin-bottom: -6px;
        }
        .sub {
            text-align: center;
            color: #566573;
            font-size: 18px;
            margin-bottom: 24px;
        }
        .feedback-box {
            background-color: #FBFCFC;
            padding: 18px;
            border-radius: 12px;
            border-left: 6px solid #2E86C1;
            margin-top: 12px;
        }
        .score-box {
            background-color: #EBF5FB;
            padding: 12px 18px;
            border-radius: 10px;
            font-size: 16px;
            margin-top: 12px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">🎓 학생 피드백 조회 시스템</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">학번(D열)과 이름(E열)을 입력하면 해당 학생의 과제 요약·점수·피드백을 보여줍니다.</p>', unsafe_allow_html=True)

# 입력
st.markdown("### 🧑‍🎓 학생 정보 입력")
col1, col2 = st.columns([1,1])
with col1:
    student_name_raw = st.text_input("이름을 입력하세요 (예: 박영희)")
with col2:
    student_id_raw = st.text_input("학번을 입력하세요 (예: 10201)")

# 구글 시트(공개) 불러오기
sheet_url = "https://docs.google.com/spreadsheets/d/1EUt6naZuxN1eJ0CIbUAphijpZU9r5pFJ-nKj4bA_l2Q/edit?usp=sharing"
csv_url = sheet_url.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv")

@st.cache_data
def load_data(url):
    df = pd.read_csv(url, dtype=str)  # 우선 전부 문자열로 불러오기
    return df

try:
    df = load_data(csv_url)
except Exception as e:
    st.error("❌ 구글 시트 데이터를 불러오는 데 실패했습니다. (인터넷 접근 또는 링크 확인 필요)")
    st.stop()

# 안전하게 컬럼 인덱스 지정 (A~E expected)
if len(df.columns) < 5:
    st.error("시트의 열 수가 예상과 다릅니다. A~E(과제요약, 점수, 피드백, 학번, 이름) 순서인지 확인해주세요.")
    st.write("현재 불러온 컬럼들:", list(df.columns))
    st.stop()

summary_col = df.columns[0]   # A열
score_col = df.columns[1]     # B열
feedback_col = df.columns[2]  # C열
id_col = df.columns[3]        # D열 (학번)
name_col = df.columns[4]      # E열 (이름)

# 데이터 정리: 공백 정리 등
def clean_id(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    # 숫자만 남기기 (예: " 10201 " -> "10201")
    s = re.sub(r'\D+', '', s)
    return s

def clean_name(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    # 연속 공백 하나로, 앞뒤 공백 제거
    s = re.sub(r'\s+', ' ', s)
    return s

# 추가 컬럼으로 저장
df['_id_clean'] = df[id_col].apply(clean_id)
df['_name_clean'] = df[name_col].apply(clean_name)

# 입력값 정리
student_id = clean_id(student_id_raw)
student_name = clean_name(student_name_raw)

# 검색/매칭 함수
def find_student(df, sid, sname):
    # 1) 완전일치 (id AND name)
    if sid and sname:
        m = df[(df['_id_clean'] == sid) & (df['_name_clean'] == sname)]
        if not m.empty:
            return m

    # 2) 학번만으로 찾기 (정확히 일치)
    if sid:
        m = df[df['_id_clean'] == sid]
        if not m.empty:
            return m

    # 3) 이름만으로 찾기 (정확히 일치)
    if sname:
        m = df[df['_name_clean'] == sname]
        if not m.empty:
            return m

    # 4) 부분매칭 후보: 학번 포함 또는 이름 포함 (case-insensitive)
    candidates = pd.DataFrame()
    if sid:
        candidates = df[df['_id_clean'].str.contains(sid, na=False)]
    if sname and candidates.empty:
        candidates = df[df['_name_clean'].str.contains(sname, na=False)]
    return candidates

# 동작 UI
if not student_id_raw and not student_name_raw:
    st.info("👆 이름과/또는 학번을 입력해주세요. (둘 다 넣으면 더 정확합니다.)")
else:
    matches = find_student(df, student_id, student_name)

    if matches is None or matches.empty:
        st.warning("⚠️ 학생을 찾을 수 없습니다. 아래의 '시트 미리보기'를 확인해 보세요.")
        with st.expander("시트 상위 10행 미리보기 (디버그용)"):
            st.dataframe(df.head(10))
        # 후보 제시: 이름 유사(contains) 또는 학번 유사
        suggest_by_name = df[df['_name_clean'].str.contains(student_name, na=False)] if student_name else pd.DataFrame()
        suggest_by_id = df[df['_id_clean'].str.contains(student_id, na=False)] if student_id else pd.DataFrame()
        if not suggest_by_id.empty:
            st.markdown("**학번 부분일치 후보**")
            st.dataframe(suggest_by_id[[id_col, name_col, score_col, feedback_col]].head(10))
        if not suggest_by_name.empty:
            st.markdown("**이름 부분일치 후보**")
            st.dataframe(suggest_by_name[[id_col, name_col, score_col, feedback_col]].head(10))

    else:
        # 만약 여러행 매칭되면 첫 행 사용(동일 학생이 중복일 수 있음)
        row = matches.iloc[0]
        st.success(f"✅ {row[name_col]} 학생 데이터를 찾았습니다. (학번: {row[id_col]})")

        # 안전하게 값 추출
        summary = row[summary_col] if pd.notna(row[summary_col]) else ""
        feedback = row[feedback_col] if pd.notna(row[feedback_col]) else ""
        # 점수 파싱
        student_score = None
        try:
            student_score = float(re.sub(r'[^\d\.]', '', str(row[score_col])))
        except Exception:
            student_score = np.nan

        # 1) 과제 요약
        st.markdown("### 📘 과제 내용 요약")
        st.markdown(f"<div class='feedback-box'>{summary}</div>", unsafe_allow_html=True)

        # 2) 점수 시각화
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
        # 3) 피드백
        st.markdown("### 💬 피드백")
        st.markdown(f"<div class='feedback-box'>{feedback}</div>", unsafe_allow_html=True)

        # 추가: 동일 학번/이름으로 여러 건 있으면 표로 보여주기
        if len(matches) > 1:
            st.info("동일 학번/이름으로 여러 행이 있습니다. 모든 후보를 아래에서 확인하세요.")
            st.dataframe(matches[[summary_col, score_col, feedback_col, id_col, name_col]])

# 끝
