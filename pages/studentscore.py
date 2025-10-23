import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="학생 성적 추이", layout="wide")

# --- 구글 스프레드시트 CSV export 링크 (시트 ID만 교체하면 됩니다) ---
SHEET_ID = "1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM"
sheet_csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=300)
def load_data(url):
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"구글 스프레드시트 불러오기 실패: {e}")
        return None
    return df

df = load_data(sheet_csv_url)
st.title("📈 학생 성적 추이 ")

if df is None:
    st.stop()

# 데이터 구조 안내
#st.caption("시트 구조: 1행 = 레이블(헤더), 2행부터 데이터. A=번호, B=이름, C~F=시험점수 (자동으로 C열부터 F열 사용)")

# 최소 컬럼 수 체크
if df.shape[1] < 4:
    st.error("시트에 최소한 '번호, 이름, 시험점수(C~F)' 형태의 열이 있어야 합니다. 현재 열 수가 부족합니다.")
    st.stop()

# 명확히 사용할 컬럼: index 0=A(번호), 1=B(이름), 2~5 = C~F (시험들)
# 사용자가 말한대로 C~F까지 4개의 시험 점수를 사용합니다.
num_cols = df.shape[1]
score_start_idx = 2
score_end_idx = min(6, num_cols)  # 2,3,4,5 -> up to index 5 inclusive -> slice [2:6)
score_cols = list(df.columns[score_start_idx:score_end_idx])

st.write("사용할 점수 컬럼:", score_cols)

# 이름 컬럼 (인덱스 1)
name_col = df.columns[1]

# Drop rows where name is NaN
df = df.dropna(subset=[name_col])

students = df[name_col].astype(str).unique()
selected_student = st.selectbox("학생 선택", students)

# 학생 필터링
student_row = df[df[name_col].astype(str) == str(selected_student)]

if student_row.empty:
    st.warning("선택한 학생의 데이터가 없습니다.")
    st.stop()

# Extract scores in the order of score_cols and coerce to numeric
scores = student_row[score_cols].iloc[0].astype(float).replace({np.nan: None})
# Prepare x labels from column names (시험명)
x_labels = score_cols

# If all scores are NaN -> warning
if scores.isnull().all():
    st.warning("선택한 학생의 점수가 모두 비어 있습니다.")
    st.stop()

# Convert to numeric list with possible None (we will skip None segments)
y = [None if pd.isna(v) else float(v) for v in scores.values]

# Build Plotly figure with segment-by-segment coloring
fig = go.Figure()

# Helper: compute RGBA color for segment
def segment_color(y0, y1):
    # if either is None -> neutral gray
    if y0 is None or y1 is None:
        return "rgba(128,128,128,0.6)"
    delta = y1 - y0
    magnitude = min(abs(delta) / 100.0, 1.0)  # scale change; adjust divisor to tune intensity
    alpha = 0.3 + 0.7 * magnitude  # range 0.3 ~ 1.0

    if delta >= 0:
        # red with alpha proportional to increase
        return f"rgba(255,0,0,{alpha:.3f})"
    else:
        # blue with alpha proportional to decrease
        return f"rgba(0,0,255,{alpha:.3f})"

# Add line segments between consecutive points
for i in range(len(x_labels) - 1):
    x_seg = [x_labels[i], x_labels[i + 1]]
    y_seg = [y[i], y[i + 1]]
    # If both are None, skip
    if y_seg[0] is None and y_seg[1] is None:
        continue
    color = segment_color(y_seg[0], y_seg[1])
    fig.add_trace(
        go.Scatter(
            x=x_seg,
            y=y_seg,
            mode="lines",
            line=dict(color=color, width=4),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Add markers for each point, color them according to next segment (or previous if last)
marker_colors = []
for i in range(len(y)):
    # determine reference pair for color: prefer next segment, else previous, else neutral
    if i < len(y) - 1 and y[i] is not None and y[i+1] is not None:
        marker_colors.append(segment_color(y[i], y[i+1]))
    elif i > 0 and y[i] is not None and y[i-1] is not None:
        marker_colors.append(segment_color(y[i-1], y[i]))
    else:
        marker_colors.append("rgba(100,100,100,0.7)")

# Add marker trace (shows markers and hover text)
fig.add_trace(
    go.Scatter(
        x=x_labels,
        y=y,
        mode="markers+text",
        marker=dict(size=10, color=marker_colors, line=dict(width=1, color="DarkSlateGrey")),
        text=[("" if v is None else f"{v:.1f}") for v in y],
        textposition="top center",
        hovertemplate="%{x}<br>점수: %{y}<extra></extra>",
        name=str(selected_student),
    )
)

fig.update_layout(
    title=f"{selected_student} 학생의 성적 추이",
    xaxis_title="시험",
    yaxis_title="점수",
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=40, r=40, t=80, b=40),
    yaxis=dict(range=[0, 100])  # 필요 시 변경
)

st.plotly_chart(fig, use_container_width=True)

# Optionally show raw row
with st.expander("원본 데이터(선택 학생)"):
    st.write(student_row.reset_index(drop=True))
