import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 페이지 설정 ---
st.set_page_config(page_title="학생 성적 추이 📈", layout="wide")

# --- 로그인 세션 확인 ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🔒 먼저 로그인해주세요!")
    st.stop()

user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

# --- 구글 스프레드시트 CSV export 링크 ---
SHEET_ID = "1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM"
sheet_csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data(url):
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ 구글 스프레드시트 불러오기 실패: {e}")
        return None
    return df

df = load_data(sheet_csv_url)

# --- 타이틀 영역 ---
st.title(f"🎓 {user_name} 학생의 성적 추이 그래프 📊")

if df is None:
    st.stop()

st.markdown(
    """
    💬 **안내:**  
    이 페이지에서는 **본인의 학번으로 로그인한 학생**만  
    자신만의 성적 변화 그래프를 확인할 수 있습니다.  
    (📘 A열 = 학번, 📗 B열 = 이름, 📙 C~F열 = 시험 점수)
    """
)

# --- 기본 데이터 검사 ---
if df.shape[1] < 4:
    st.error("⚠️ 시트에 최소한 '학번, 이름, 시험점수(C~F)' 형태의 열이 필요합니다.")
    st.stop()

# --- 컬럼 정의 ---
id_col = df.columns[0]
name_col = df.columns[1]
score_cols = df.columns[2:6]  # 시험 4개

# NaN 제거
df = df.dropna(subset=[id_col])

# --- 로그인된 학번 필터링 ---
student_row = df[df[id_col].astype(str) == str(user_id)]

if student_row.empty:
    st.warning("😢 성적 정보가 등록되어 있지 않습니다.")
    st.stop()

# --- 점수 추출 ---
scores = student_row[score_cols].iloc[0].astype(float).replace({np.nan: None})
x_labels = score_cols
y = [None if pd.isna(v) else float(v) for v in scores.values]

# --- 그래프 색상 함수 ---
def segment_color(y0, y1):
    if y0 is None or y1 is None:
        return "rgba(160,160,160,0.4)"
    delta = y1 - y0
    magnitude = min(abs(delta) / 100.0, 1.0)
    alpha = 0.3 + 0.7 * magnitude
    return f"rgba(255,99,132,{alpha:.3f})" if delta >= 0 else f"rgba(54,162,235,{alpha:.3f})"

# --- Plotly 그래프 생성 ---
fig = go.Figure()

# 선 구간별 색상 반영
for i in range(len(x_labels) - 1):
    y0, y1 = y[i], y[i + 1]
    if y0 is None and y1 is None:
        continue
    fig.add_trace(
        go.Scatter(
            x=[x_labels[i], x_labels[i + 1]],
            y=[y0, y1],
            mode="lines",
            line=dict(color=segment_color(y0, y1), width=5),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# 마커 색상 설정
marker_colors = []
for i in range(len(y)):
    if i < len(y) - 1 and y[i] is not None and y[i + 1] is not None:
        marker_colors.append(segment_color(y[i], y[i + 1]))
    elif i > 0 and y[i] is not None and y[i - 1] is not None:
        marker_colors.append(segment_color(y[i - 1], y[i]))
    else:
        marker_colors.append("rgba(120,120,120,0.6)")

# 점수 라벨 + 마커 추가
fig.add_trace(
    go.Scatter(
        x=x_labels,
        y=y,
        mode="markers+text",
        marker=dict(size=12, color=marker_colors, line=dict(width=1, color="DarkSlateGrey")),
        text=[("" if v is None else f"{v:.1f}") for v in y],
        textposition="top center",
        hovertemplate="%{x}<br>점수: %{y}<extra></extra>",
        name=user_name,
    )
)

# --- 그래프 레이아웃 스타일 ---
fig.update_layout(
    title=f"📊 {user_name} 학생의 시험별 점수 변화 추이",
    xaxis_title="🧾 시험 종류",
    yaxis_title="📈 점수",
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=40, r=40, t=80, b=40),
    yaxis=dict(range=[0, 100]),
    title_font=dict(size=22, color="#2c3e50"),
)

# --- 그래프 출력 ---
st.plotly_chart(fig, use_container_width=True)

# --- 부가 정보 영역 ---
with st.expander("📂 원본 데이터 보기"):
    st.dataframe(student_row.reset_index(drop=True), use_container_width=True)

st.markdown(
    """
    ---
    🌱 **Tip:**  
    성적이 올라갈수록 그래프는 🔴 **빨간색**으로,  
    내려갈수록 🔵 **파란색**으로 표시돼요.  
    꾸준히 성장하는 여러분을 응원합니다! 💪✨
    """
)
