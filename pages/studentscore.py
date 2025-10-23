import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 페이지 설정 ---
st.set_page_config(page_title="학생 성적 추이 📈", layout="wide")

# --- 안전한 세션 읽기: KeyError 방지 ---
logged_in = st.session_state.get("logged_in", False)
user_id = st.session_state.get("user_id", None)
user_name = st.session_state.get("user_name", "학생")

# 만약 로그인 정보가 없다면 친절히 안내하고 로그인 페이지로 이동할 수 있게 함
if not logged_in or user_id is None:
    st.error("🔒 먼저 로그인해주세요.")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("로그인 페이지로 이동 🔁"):
            # 페이지 이름은 앱에서 사용하는 이름으로 바꿔주세요 (예: "app_login" 혹은 "app_login.py" 대신 "app_login")
            # streamlit >=1.10 의 switch_page 사용 시 페이지 이름(파일명 또는 제목)을 넣습니다.
            try:
                st.experimental_set_query_params()  # to avoid some Streamlit caching weirdness
                st.switch_page("app_login")
            except Exception:
                # 어떤 환경에서는 switch_page가 동작하지 않을 수 있으므로 안내만 함
                st.info("앱 환경에서 페이지 이동이 지원되지 않습니다. 직접 로그인 페이지로 이동해주세요.")
    with col2:
        if st.button("앱 새로고침 🔄"):
            st.experimental_rerun()
    st.stop()

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

st.title(f"🎓 {user_name}님 — 개인 성적 조회 📊")

if df is None:
    st.stop()

# --- 기본 검사 ---
if df.shape[1] < 3:
    st.error("⚠️ 시트에 최소한 '학번, 이름, 시험점수...' 형태의 열이 필요합니다.")
    st.stop()

# 컬럼 위치: A=학번, B=이름, C~ = 시험들
id_col = df.columns[0]
name_col = df.columns[1]
score_cols = df.columns[2:6] if df.shape[1] >= 6 else df.columns[2:]

# 학번 컬럼에 NaN 있는 행 제거
df = df.dropna(subset=[id_col])

# 로그인한 학번으로 필터링 (문자/숫자 혼용 대비 str 비교)
student_row = df[df[id_col].astype(str) == str(user_id)]

if student_row.empty:
    st.warning("😢 해당 학번의 성적이 등록되어 있지 않거나, 학번 형식이 시트와 다릅니다.")
    st.info(f"현재 로그인 학번: {user_id} / 시트의 학번 열 이름: '{id_col}'")
    # 디버그용으로 시트 상위 몇 행 보기(선택)
    if st.checkbox("시트 상위 5행 보기 (디버그)"):
        st.dataframe(df.head(5))
    st.stop()

# 점수 추출 (결측 처리)
scores = student_row[score_cols].iloc[0].astype(float).replace({np.nan: None})
x_labels = list(score_cols)
y = [None if pd.isna(v) else float(v) for v in scores.values]

# 색상 함수 (증가=붉은계열, 감소=푸른계열)
def segment_color(y0, y1):
    if y0 is None or y1 is None:
        return "rgba(160,160,160,0.4)"
    delta = y1 - y0
    magnitude = min(abs(delta) / 100.0, 1.0)
    alpha = 0.3 + 0.7 * magnitude
    return f"rgba(255,99,132,{alpha:.3f})" if delta >= 0 else f"rgba(54,162,235,{alpha:.3f})"

# Plotly 그림 생성
fig = go.Figure()

# 선 구간 추가
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

# 마커 및 라벨
marker_colors = []
for i in range(len(y)):
    if i < len(y) - 1 and y[i] is not None and y[i + 1] is not None:
        marker_colors.append(segment_color(y[i], y[i + 1]))
    elif i > 0 and y[i] is not None and y[i - 1] is not None:
        marker_colors.append(segment_color(y[i - 1], y[i]))
    else:
        marker_colors.append("rgba(120,120,120,0.6)")

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

fig.update_layout(
    title=f"📊 {user_name} 학생의 시험별 점수 변화",
    xaxis_title="🧾 시험",
    yaxis_title="📈 점수",
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=40, r=40, t=80, b=40),
    yaxis=dict(range=[0, 100]),
)

st.plotly_chart(fig, use_container_width=True)

# 원본 데이터 보기
with st.expander("📂 원본 데이터 (선택 학생)"):
    st.dataframe(student_row.reset_index(drop=True), use_container_width=True)

# 로그아웃 버튼 — 누르면 세션 정보 지우고 로그인 페이지로 이동 시도
if st.button("🔓 로그아웃"):
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)
    st.success("로그아웃되었습니다.")
    try:
        st.switch_page("app_login")
    except Exception:
        st.experimental_rerun()
