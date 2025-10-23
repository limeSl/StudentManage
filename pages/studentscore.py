import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(page_title="학생 성적 추이", layout="wide")

# 구글 시트 CSV 링크
SHEET_ID = "1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM"
sheet_csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 캐시 무효화 기능 추가
def load_data(force_reload=False):
    if force_reload or "data" not in st.session_state:
        df = pd.read_csv(sheet_csv_url)
        st.session_state["data"] = df
    return st.session_state["data"]

st.title("📈 학생 성적 추이")
st.caption("A열=학번, B열=이름, C~F열=시험 점수")

# 🔄 새로고침 버튼
if st.button("🔄 최신 데이터 불러오기"):
    load_data(force_reload=True)
    st.success("데이터를 새로 불러왔습니다.")
    time.sleep(1)
    st.rerun()

df = load_data()

# --- 데이터 구조 확인 ---
if df.shape[1] < 4:
    st.error("시트에 최소한 '학번, 이름, 시험점수(C~F)' 형태의 열이 필요합니다.")
    st.stop()

# 열 인덱스 기반으로 정의
id_col = df.columns[0]   # 학번
name_col = df.columns[1] # 이름
score_cols = df.columns[2:6]  # C~F

st.write("사용 중인 시험 컬럼:", list(score_cols))

# 이름 선택
students = df[name_col].dropna().unique()
selected_student = st.selectbox("학생 선택", students)

student_row = df[df[name_col] == selected_student]

if student_row.empty:
    st.warning("선택한 학생 데이터가 없습니다.")
    st.stop()

# 점수 데이터
scores = student_row[score_cols].iloc[0].astype(float)
x_labels = list(score_cols)
y = [None if pd.isna(v) else v for v in scores.values]

# 색상 계산 함수
def segment_color(y0, y1):
    if y0 is None or y1 is None:
        return "rgba(150,150,150,0.3)"
    diff = y1 - y0
    intensity = min(abs(diff) / 100, 1)
    alpha = 0.3 + 0.7 * intensity
    return f"rgba(255,0,0,{alpha})" if diff >= 0 else f"rgba(0,0,255,{alpha})"

fig = go.Figure()

# 선 구간별 색상 적용
for i in range(len(x_labels) - 1):
    x_seg = [x_labels[i], x_labels[i + 1]]
    y_seg = [y[i], y[i + 1]]
    if all(v is None for v in y_seg):
        continue
    fig.add_trace(go.Scatter(
        x=x_seg, y=y_seg, mode="lines",
        line=dict(color=segment_color(y_seg[0], y_seg[1]), width=4),
        showlegend=False
    ))

# 점 추가
marker_colors = [
    segment_color(y[i-1], y[i]) if i > 0 else "rgba(120,120,120,0.7)"
    for i in range(len(y))
]
fig.add_trace(go.Scatter(
    x=x_labels, y=y,
    mode="markers+text",
    marker=dict(size=10, color=marker_colors, line=dict(width=1, color="black")),
    text=[("" if v is None else f"{v:.1f}") for v in y],
    textposition="top center",
    hovertemplate="%{x}<br>점수: %{y}<extra></extra>"
))

fig.update_layout(
    title=f"{selected_student} 학생의 성적 추이",
    xaxis_title="시험",
    yaxis_title="점수",
    template="plotly_white",
    hovermode="x unified",
    yaxis=dict(range=[0, 100])
)

st.plotly_chart(fig, use_container_width=True)
