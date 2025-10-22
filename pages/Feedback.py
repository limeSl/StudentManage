# main.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re

st.set_page_config(page_title="학생 피드백 조회", page_icon="🎓", layout="centered")

# ---------- CSS: 다크/라이트 모두 동작하게 최소한의 스타일 ----------
st.markdown("""
<style>
/* 카드 배경: Streamlit 테마에 따라 자동으로 잘 보이도록 반투명 사용 */
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

st.markdown('<div class="header-title">🎓 학생 피드백 조회 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">학번(D열)과 이름(E열)을 입력하면 과제요약·점수·피드백을 확인합니다.</div>', unsafe_allow_html=True)

# ---------- Google Sheet CSV (공개 시트) ----------
# 원본: https://docs.google.com/spreadsheets/d/<ID>/edit?usp=sharing
sheet_csv_url = "https://docs.google.com/spreadsheets/d/1EUt6naZuxN1eJ0CIbUAphijpZU9r5pFJ-nKj4bA_l2Q/export?format=csv"

@st.cache_data(ttl=300)
def load_sheet(url):
    df = pd.read_csv(url, dtype=str)  # 모든 칼럼을 우선 문자열로 읽음
    # strip 컬럼명
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df = load_sheet(sheet_csv_url)
except Exception as e:
    st.error("구글 시트 로드에 실패했습니다. 링크나 공개 설정을 확인하세요.")
    st.stop()

# 최소 열 개수 체크
if df.shape[1] < 5:
    st.error("시트에 최소 5개 열(A~E)이 필요합니다. 현재 열 개수: {}".format(df.shape[1]))
    st.write("불러온 컬럼명:", list(df.columns))
    st.stop()

# ---------- 안전한 열 참조 (위치 기준) ----------
# A: 0, B:1, C:2, D:3(학번), E:4(이름)
summary_col = df.columns[0]
score_col = df.columns[1]
feedback_col = df.columns[2]
id_col = df.columns[3]
name_col = df.columns[4]

# ---------- 입력 UI ----------
st.markdown("### 🧑‍🎓 학생 정보 입력")
c1, c2, c3 = st.columns([3,3,1])
with c1:
    student_id_raw = st.text_input("🔢 학번 (예: 10201)")
with c2:
    student_name_raw = st.text_input("🧑 이름 (예: 박영희)")
with c3:
    if st.button("🔎 조회"):
        query_pressed = True
    else:
        query_pressed = False

# ---------- 유틸: 정규화 ----------
def clean_id(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    s = re.sub(r'\D+', '', s)  # 숫자만 남김
    return s

def clean_name(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

# 전처리 컬럼 추가(캐시 영향 작지 않음)
df['_id_clean'] = df[id_col].apply(clean_id)
df['_name_clean'] = df[name_col].apply(clean_name)
df['_score_parsed'] = df[score_col].apply(lambda x: \
    (float(re.sub(r'[^\d\.]', '', str(x))) if re.search(r'\d', str(x)) else np.nan))

# 입력 정리
student_id = clean_id(student_id_raw)
student_name = clean_name(student_name_raw)

# ---------- 검색 함수 ----------
def find_student(df, sid, sname):
    # 1) id+name 완전일치
    if sid and sname:
        m = df[(df['_id_clean'] == sid) & (df['_name_clean'] == sname)]
        if not m.empty: return m
    # 2) id만
    if sid:
        m = df[df['_id_clean'] == sid]
        if not m.empty: return m
    # 3) name만
    if sname:
        m = df[df['_name_clean'] == sname]
        if not m.empty: return m
    # 4) 부분일치 후보
    if sid:
        cand = df[df['_id_clean'].str.contains(sid, na=False)]
        if not cand.empty: return cand
    if sname:
        cand = df[df['_name_clean'].str.contains(sname, na=False)]
        if not cand.empty: return cand
    return pd.DataFrame()

# ---------- 실행부 ----------
if query_pressed:
    if not (student_id or student_name):
        st.warning("학번 또는 이름을 입력해주세요.")
    else:
        matches = find_student(df, student_id, student_name)
        if matches.empty:
            st.warning("해당 학생을 찾을 수 없습니다. (부분일치 후보가 있는지 아래에서 확인하세요)")
            with st.expander("시트 상위 10행(디버그)"):
                st.dataframe(df.head(10))
            # 후보 제시
            suggestions = pd.DataFrame()
            if student_id:
                s1 = df[df['_id_clean'].str.contains(student_id, na=False)]
                if not s1.empty: suggestions = pd.concat([suggestions, s1])
            if student_name:
                s2 = df[df['_name_clean'].str.contains(student_name, na=False)]
                if not s2.empty: suggestions = pd.concat([suggestions, s2])
            if not suggestions.empty:
                st.markdown("**부분 일치 후보**")
                st.dataframe(suggestions[[id_col, name_col, score_col, feedback_col]].head(20))
        else:
            # 여러행일 경우 첫 행을 대표로 사용 + 전체 후보 표시
            row = matches.iloc[0]
            st.success(f"✅ 찾았습니다: {row[name_col]} (학번: {row[id_col]})")

            # 요약
            summary = row[summary_col] if pd.notna(row[summary_col]) else ""
            st.markdown("### 📝 과제 내용 요약")
            st.markdown(f"<div class='feedback-box'>{summary}</div>", unsafe_allow_html=True)

            # 점수 비교 데이터 준비
            all_scores = df['_score_parsed'].dropna().astype(float)
            student_score = row['_score_parsed'] if not pd.isna(row['_score_parsed']) else np.nan

            if all_scores.empty or np.isnan(student_score):
                st.warning("점수 데이터가 부족하여 비교 그래프를 표시할 수 없습니다.")
                st.markdown(f"<div class='small-info'>원점수: {row[score_col]}</div>", unsafe_allow_html=True)
            else:
                avg_score = float(all_scores.mean())
                median_score = float(np.median(all_scores))

                # 다크모드 감지 (Streamlit theme)
                try:
                    theme_base = st.get_option("theme.base")  # 'dark' or 'light'
                except Exception:
                    theme_base = "light"
                if theme_base == "dark":
                    bar_color = "#7FDBFF"   # 연한 청록(다크에서 잘 보임)
                    bg = "#0e1117"
                else:
                    bar_color = "#1f77b4"   # 기본 파랑
                    bg = "#ffffff"

                # 막대 그래프 데이터 (내, 평균, 중간)
                score_df = pd.DataFrame({
                    "항목": ["내 점수", "평균 점수", "중간 점수"],
                    "점수": [student_score, avg_score, median_score]
                })

                # Altair 바 차트 (크기 작게)
                bar = (
                    alt.Chart(score_df)
                    .mark_bar(cornerRadius=6)
                    .encode(
                        x=alt.X('항목:N', sort=None, title=None),
                        y=alt.Y('점수:Q', scale=alt.Scale(domain=[0, 100])),
                        tooltip=['항목', alt.Tooltip('점수', format=".1f")]
                    )
                    .properties(width=320, height=220)
                    .configure_mark(opacity=0.9)
                )

                # 색 지정 (단일 색)
                bar = bar.encode(color=alt.value(bar_color))

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

            # 동일 후보 모두 보여주기(있으면)
            if len(matches) > 1:
                st.info("동일 조건으로 여러 행이 존재합니다:")
                st.dataframe(matches[[summary_col, score_col, feedback_col, id_col, name_col]])

# 끝
