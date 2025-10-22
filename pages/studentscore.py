# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="📊 학생 성취도 조회", page_icon="📈", layout="centered")
st.title("📊 학생 성취도 조회 시스템")

# -------------------------
# 사용자가 제공한 공개 구글 시트 링크 (입력값 고정)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/edit?usp=sharing"
# -------------------------

def extract_sheet_id_and_gid(url: str):
    """
    URL에서 sheet_id와 gid 추출. gid가 없으면 0 반환.
    """
    # 시트 id 추출: /d/<id>/
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    sheet_id = m.group(1) if m else None

    # gid 추출 (쿼리나 해시)
    gid = "0"
    # 쿼리 파싱
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "gid" in qs:
        gid = qs["gid"][0]
    else:
        # 해시(#gid=...) 확인
        if parsed.fragment:
            m2 = re.search(r"gid=(\d+)", parsed.fragment)
            if m2:
                gid = m2.group(1)
        # 혹은 ?usp=... 형태이면 기본 gid=0
    return sheet_id, gid

def build_csv_url_from_sheet(url: str):
    sheet_id, gid = extract_sheet_id_and_gid(url)
    if not sheet_id:
        raise ValueError("구글 시트 ID를 URL에서 추출하지 못했습니다. 링크를 확인해주세요.")
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return csv_url

@st.cache_data(ttl=300)
def load_sheet_as_df(url: str):
    csv_url = build_csv_url_from_sheet(url)
    # pandas로 읽을 때 실패할 수 있으므로 예외 처리
    df = pd.read_csv(csv_url)
    return df

# 데이터 불러오기
try:
    df = load_sheet_as_df(SHEET_URL)
except Exception as e:
    st.error("❌ 구글 시트를 불러오는 중 오류가 발생했습니다.")
    st.write("오류 내용:", e)
    st.stop()

st.success("✅ 구글 시트 데이터를 불러왔습니다.")
st.caption("공개(링크 보기 가능) 상태의 구글 시트에서 데이터를 가져옵니다.")

# 데이터 기본 확인
st.info("시트 첫 5행을 확인하세요.")
st.dataframe(df.head())

# 필요한 컬럼 있는지 확인 (최소 '번호', '이름' 필요)
required_cols = ["번호", "이름"]
for c in required_cols:
    if c not in df.columns:
        st.error(f"시트에 필수열 '{c}'이(가) 없습니다. 시트 컬럼명을 확인해주세요.")
        st.stop()

# 사용자 이름 입력
search_name = st.text_input("🔍 이름을 입력하세요 (예: 김민수):").strip()

def to_numeric_safe(series):
    """성적 칼럼을 숫자로 변환. 변환 실패는 NaN으로."""
    return pd.to_numeric(series, errors="coerce")

# 기본적으로 성적 열은 '번호','이름' 다음의 열들로 가정 (세 번째 열부터)
# 그러나 사용자가 직접 성적 열을 선택할 수 있게 옵션 제공
all_cols = df.columns.tolist()
possible_score_cols = all_cols[2:] if len(all_cols) > 2 else []
st.markdown("**(선택)** 성적으로 사용할 열을 직접 선택할 수 있습니다. 기본값은 시트의 3~6번째 열입니다.")
selected_score_cols = st.multiselect("성적 열 선택 (왼쪽에서 오른쪽 순서대로)", options=possible_score_cols, default=possible_score_cols[:4])

if not selected_score_cols:
    st.warning("성적으로 사용할 열을 하나 이상 선택하세요.")
    st.stop()

# 이름 검색 및 처리
if search_name:
    matches = df[df["이름"] == search_name]

    if len(matches) == 0:
        st.warning("❌ 해당 이름의 학생을 찾을 수 없습니다.")
    elif len(matches) > 1:
        st.info(f"🔎 동명이인 {len(matches)}명 발견. 아래에서 번호로 확인하세요.")
        st.dataframe(matches[["번호", "이름"] + selected_score_cols])
        # 사용자가 본인 번호를 선택할 수 있게 선택박스 제공
        chosen_no = st.selectbox("본인의 번호를 선택하세요 (번호를 선택하면 그래프가 표시됩니다):", options=matches["번호"].astype(str).tolist())
        if chosen_no:
            student = matches[matches["번호"].astype(str) == chosen_no].iloc[0]
            confirm = st.radio("이 사람 맞습니까?", ("예", "아니오"))
            if confirm == "예":
                chosen_student = student
            else:
                chosen_student = None
        else:
            chosen_student = None
    else:
        # matches == 1
        student = matches.iloc[0]
        st.write(f"번호: **{student['번호']}**, 이름: **{student['이름']}**")
        confirm = st.radio("이 사람 맞습니까?", ("예", "아니오"))
        chosen_student = student if confirm == "예" else None

    # 선택된 학생이 있으면 그래프 그리기
    if 'chosen_student' in locals() and chosen_student is not None:
        # 점수 읽기 및 숫자 변환
        scores_series = to_numeric_safe(chosen_student[selected_score_cols])
        # 인덱스(레이블)
        labels = selected_score_cols
        values = scores_series.values.astype(float)  # NaN 포함될 수 있음

        # 결측치가 모두이면 알림
        if pd.isna(values).all():
            st.warning("선택한 성적 열에 숫자가 없습니다. 시트의 성적 칼럼을 확인하세요.")
        else:
            # 변화량 계산 (현재 - 이전)
            changes = [0.0]  # 첫 항은 기준(색 없음 또는 회색)
            for i in range(1, len(values)):
                a = values[i]
                b = values[i-1]
                if pd.isna(a) or pd.isna(b):
                    changes.append(0.0)
                else:
                    changes.append(a - b)
            abs_changes = [abs(x) for x in changes]
            max_change = max(abs_changes) if max(abs_changes) > 0 else 1.0

            # 색 그라데이션 생성: 변화 크기에 비례해 연한->진한 색 사용
            def color_for_change(delta, max_c):
                """
                delta > 0 : red scale (light -> deep)
                delta < 0 : blue scale (light -> deep)
                delta == 0: gray
                returns hex color
                """
                intensity = min(abs(delta) / max_c, 1.0)  # 0..1
                # 간단한 interpolation between two hex colors
                if delta > 0:
                    # 연한 빨강(#ffc9c9) -> 진한 빨강(#b30000)
                    start = (255,201,201)
                    end = (179,0,0)
                elif delta < 0:
                    # 연한 파랑(#cfe6ff) -> 진한 파랑(#003f8a)
                    start = (207,230,255)
                    end = (0,63,138)
                else:
                    return "#9aa0a6"  # gray
                r = int(start[0] + (end[0]-start[0]) * intensity)
                g = int(start[1] + (end[1]-start[1]) * intensity)
                b = int(start[2] + (end[2]-start[2]) * intensity)
                return f"rgb({r},{g},{b})"

            colors = [color_for_change(changes[i], max_change) for i in range(len(changes))]

            # Plotly 그리기
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=labels,
                y=values,
                mode="lines+markers",
                line=dict(width=3, color="lightgray"),
                marker=dict(size=12, color=colors, line=dict(width=1, color="black")),
                hovertemplate="%{x}: %{y}<extra></extra>"
            ))
            fig.update_layout(
                title=f"🎯 {chosen_student['이름']} (번호 {chosen_student['번호']}) 성취도 변화",
                xaxis_title="구분",
                yaxis_title="점수",
                template="plotly_white",
                height=480,
                margin=dict(l=40, r=20, t=70, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)

            # 변경량(숫자)도 표로 보여주기
            change_df = pd.DataFrame({
                "구분": labels,
                "점수": [None if pd.isna(v) else float(v) for v in values],
                "변화(이전과의 차이)": [None if i==0 else (None if pd.isna(values[i]) or pd.isna(values[i-1]) else float(values[i]-values[i-1])) for i in range(len(values))],
                "색": colors
            })
            st.markdown("**세부값**")
            st.dataframe(change_df)

    elif search_name and ('chosen_student' in locals() and chosen_student is None):
        st.info("확인을 '아니오'로 선택하셨습니다. 다른 학생을 검색하거나 동명이인 목록에서 선택하세요.")
