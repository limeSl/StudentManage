import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re

st.set_page_config(page_title="학생 피드백 조회", page_icon="🎓", layout="centered")

# ---------- 로그인 확인 ----------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 로그인 후 이용할 수 있습니다. 메인 페이지로 이동해주세요.")
    st.stop()

# 로그인 정보 가져오기
student_id = str(st.session_state.get("student_id", "")).strip()
student_name = str(st.session_state.get("student_name", "")).strip()

# ---------- CSS ----------
st.markdown("""
<style>
.feedback-box {
  padding:14px;
  border-radius:10px;
  background-color: rgba(255,255,255,0.04);
  border-left:6px solid rgba(0,0,0,0.06);
  margin-bottom:10px;
  white-space:pre-wrap;
}
.header-title {
  font-size:48px;
  font-weight:800;
  text-align:center;
  margin-bottom:4px;
  color:var(--primary-color);
}
.header-sub {
  text-align:center;
  color:var(--text-color);
  margin-bottom:18px;
}
.small-info {
  background-color: rgba(255,255,255,0.02);
  padding:8px;
  border-radius:8px;
  font-size:14px;
}
</style>
""", unsafe_allow_html=True)

# ---------- 제목 ----------
st.markdown('<div class="header-title">🎓 학생 피드백 조회</div>', unsafe_allow_html=True)
st.markdown(f"<div class='header-sub'>{student_name} 학생의 과제 요약, 점수, 피드백입니다.</div>", unsafe_allow_html=True)

# ---------- 구글 시트 불러오기 ----------
sheet_csv_url = "https://docs.google.com/spreadsheets/d/1EUt6naZuxN1eJ0CIbUAphijpZU9r5pFJ-nKj4bA_l2Q/export?format=csv"

@st.cache_data(ttl=300)
def load_sheet(url):
    df = pd.read_csv(url, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df = load_sheet(sheet_csv_url)
except Exception as e:
    st.error("구글 시트를 불러오지 못했습니다. 공개 설정 또는 URL을 확인하세요.")
    st.stop()

# 열 확인
if df.shape[1] < 5:
    st.error("시트에 최소 5개 열(A~E)이 필요합니다.")
    st.write("불러온 컬럼명:", list(df.columns))
    st.stop()

# 열 매핑
summary_col = df.columns[0]
score_col = df.columns[1]
feedback_col = df.columns[2]
id_col = df.columns[3]
name_col = df.columns[4]

# ---------- 데이터 전처리 ----------
def clean_id(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    return re.sub(r'\D+', '', s)

def clean_name(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    return re.sub(r'\s+', ' ', s)

df['_id_clean'] = df[id_col].apply(clean_id)
df['_name_clean'] = df[name_col].apply(clean_name)
df['_score_parsed'] = df[score_col].apply(lambda x: float(re.sub(r'[^\d\.]', '', str(x))) if re.search(r'\d', str(x)) else np.nan)

# ---------- 학생 찾기 ----------
m = df[(df['_id_clean'] == clean_id(student_id)) & (df['_name_clean'] == clean_name(student_name))]
if m.empty:
    st.warning("⚠️ 로그인한 학번과 이름에 해당하는 데이터를 찾을 수 없습니다.")
    st.stop()

row = m.iloc[0]

# ---------- 표시 ----------
st.success(f"✅ {row[name_col]} 학생의 피드백을 불러왔습니다. (학번: {row[id_col]})")

# 과제 요약
summary = row[summary_col] if pd.notna(row[summary_col]) else ""
st.markdown("### 📝 과제 내용 요약")
st.markdown(f"<div class='feedback-box'>{summary}</div>", unsafe_allow_html=True)

# 점수 비교
all_scores = df['_score_parsed'].dropna().astype(float)
student_score = row['_score_parsed'] if not pd.isna(row['_score_parsed']) else np.nan

if all_scores.empty or np.isnan(student_score):
    st.warning("점수 데이터가 부족하여 비교 그래프를 표시할 수 없습니다.")
    st.markdown(f"<div class='small-info'>원점수: {row[score_col]}</div>", unsafe_allow_html=True)
else:
    avg_score = float(all_scores.mean())
    median_score = float(np.median(all_scores))

    try:
        theme_base = st.get_option("theme.base")
    except Exception:
        theme_base = "light"
    bar_color = "#7FDBFF" if theme_base == "dark" else "#1f77b4"

    score_df = pd.DataFrame({
        "항목": ["내 점수", "평균 점수", "중간 점수"],
        "점수": [student_score, avg_score, median_score]
    })

    bar = (
        alt.Chart(score_df)
        .mark_bar(size=35, cornerRadius=6)
        .encode(
            x=alt.X('항목:N', sort=None, title=None),
            y=alt.Y('점수:Q', scale=alt.Scale(domain=[0, 100])),
            color=alt.value(bar_color),
            tooltip=['항목', alt.Tooltip('점수', format=".1f")]
        )
        .properties(width=620, height=320)
    )

    st.markdown("### 📊 점수 비교")
    st.altair_chart(bar, use_container_width=False)

    st.markdown(f"""
    <div class='small-info'>
    📈 <b>평균:</b> {avg_score:.1f}점 &nbsp;&nbsp; 📊 <b>중간:</b> {median_score:.1f}점 &nbsp;&nbsp; 🧍 <b>내 점수:</b> {student_score:.1f}점
    </div>
    """, unsafe_allow_html=True)

# 피드백
fb = row[feedback_col] if pd.notna(row[feedback_col]) else ""
st.markdown("### 💬 피드백")
st.markdown(f"<div class='feedback-box'>{fb}</div>", unsafe_allow_html=True)

# 여러 행일 경우
if len(m) > 1:
    st.info("동일 조건으로 여러 행이 존재합니다:")
    st.dataframe(m[[summary_col, score_col, feedback_col, id_col, name_col]])
