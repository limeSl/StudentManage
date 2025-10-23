import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 세션 로그인 상태 확인 ---

if "logged_in" not in st.session_state or not st.session_state.logged_in: st.warning("⚠️ 로그인 후 이용할 수 있습니다. 메인 페이지로 이동해주세요.") st.stop()

student_id = str(st.session_state.get("student_id", "")).strip() student_name = str(st.session_state.get("student_name", "")).strip()
user_id = st.session_state["user_id"]
user_name = st.session_state.get("user_name", "")
user_role = st.session_state.get("role", "student")

st.set_page_config(page_title="학생 성적 추이", layout="wide")

# --- 구글 시트 CSV 가져오기 ---
SHEET_ID = "1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM"
sheet_csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(sheet_csv_url)

df = load_data()

# --- 데이터 구조 ---
id_col = df.columns[0]   # 학번
name_col = df.columns[1] # 이름
score_cols = df.columns[2:6]  # C~F 시험점수
st.title("📈 학생 성적 조회")

# --- 학생 전용 화면 ---
if user_role == "student":
    st.write(f"👋 {user_name} 학생({user_id})의 성적입니다.")

    # 로그인한 학번과 일치하는 행만 필터링
    student_data = df[df[id_col].astype(str) == str(user_id)]

    if student_data.empty:
        st.warning("해당 학번의 성적 데이터가 없습니다.")
        st.stop()

    scores = student_data[score_cols].iloc[0].astype(float)
    x_labels = score_cols
    y = [None if pd.isna(v) else v for v in scores.values]

    def segment_color(y0, y1):
        if y0 is None or y1 is None:
            return "rgba(150,150,150,0.3)"
        diff = y1 - y0
        intensity = min(abs(diff) / 100, 1)
        alpha = 0.3 + 0.7 * intensity
        return f"rgba(255,0,0,{alpha})" if diff >= 0 else f"rgba(0,0,255,{alpha})"

    fig = go.Figure()

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

    # 마커 표시
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
        title=f"{user_name} 학생의 성적 추이",
        xaxis_title="시험",
        yaxis_title="점수",
        template="plotly_white",
        hovermode="x unified",
        yaxis=dict(range=[0, 100])
    )

    st.plotly_chart(fig, use_container_width=True)

# --- 교사 전용 화면 ---
elif user_role == "teacher":
    st.write("👩‍🏫 교사용 전체 성적 조회 페이지입니다.")
    selected_name = st.selectbox("학생 선택", df[name_col].unique())

    student_data = df[df[name_col] == selected_name]
    if student_data.empty:
        st.warning("데이터가 없습니다.")
        st.stop()

    scores = student_data[score_cols].iloc[0].astype(float)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=score_cols, y=scores, marker_color="lightskyblue"))
    fig.update_layout(title=f"{selected_name} 학생 성적", yaxis_title="점수")
    st.plotly_chart(fig, use_container_width=True)
