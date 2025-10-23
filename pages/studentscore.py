# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="학생 성적 조회 (B열 2행~)", page_icon="🎓", layout="centered")
st.title("🎓 학생 성적 조회 (B열 2행부터 검색)")

# --- 고정된 구글 시트 export CSV URL (공개링크 필요) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/export?format=csv"

@st.cache_data(ttl=300)
def load_sheet_no_header(csv_url: str) -> pd.DataFrame:
    """
    헤더 없이(또는 헤더가 불완전할 때) 안정적으로 CSV를 읽음.
    반환 DF의 컬럼 인덱스는 정수(0,1,2,...).
    """
    # header=None 으로 읽으면 모든 행이 데이터로 들어오고 컬럼은 정수 인덱스가 됨.
    df = pd.read_csv(csv_url, header=None, dtype=str)  # 문자열로 읽어 안전하게 처리
    # 빈 행(모두 NaN or 모든 공백) 제거
    df = df.dropna(how="all").reset_index(drop=True)
    # strip whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

# 데이터 로드
try:
    df_raw = load_sheet_no_header(SHEET_CSV_URL)
except Exception as e:
    st.error("❌ 구글 시트를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()

st.info("구글 시트를 불러왔습니다. (헤더 무시, B열의 2행부터 검색합니다.)")
st.caption(f"읽은 행 수: {len(df_raw)}  — (컬럼 인덱스: 0=A열, 1=B열(이름), 2=C열, ... )")

# 최소 행 수 체크
if df_raw.shape[0] < 2:
    st.error("시트에 유효한 데이터(2행 이후)가 없습니다.")
    st.stop()

# B열(인덱스 1)에서 2행부터(인덱스 1부터 검색)
names_series = df_raw.iloc[1:, 1].astype(str)  # index: 1..n
numbers_series = df_raw.iloc[1:, 0].astype(str)  # A열(번호)도 함께 사용

# 검색 UI
search_name = st.text_input("🔍 이름을 입력하세요 (예: 김민수):").strip()

def color_for_change(delta, max_c):
    """변화량 기반 간단한 RGB 그라데이션 색 반환"""
    intensity = min(abs(delta) / max_c, 1.0) if max_c > 0 else 0
    if delta > 0:
        # 연한 빨강 -> 진한 빨강
        start = (255, 200, 200)
        end = (160, 0, 0)
    elif delta < 0:
        # 연한 파랑 -> 진한 파랑
        start = (200, 220, 255)
        end = (0, 40, 140)
    else:
        return "rgb(150,150,150)"
    r = int(start[0] + (end[0] - start[0]) * intensity)
    g = int(start[1] + (end[1] - start[1]) * intensity)
    b = int(start[2] + (end[2] - start[2]) * intensity)
    return f"rgb({r},{g},{b})"

if search_name:
    # 대소문자/공백 문제를 피하기 위해 비교 시 모두 strip & lower
    matches_mask = names_series.fillna("").str.strip().str.lower() == search_name.strip().lower()
    matched_indices = list(names_series.index[matches_mask])  # 실제 df_raw 인덱스 (starts at 1)
    
    if len(matched_indices) == 0:
        st.warning("⚠️ 해당 이름을 B열 2행부터 찾을 수 없습니다.")
    elif len(matched_indices) == 1:
        row_idx = matched_indices[0]  # 예: 1,2,...
        number = df_raw.iat[row_idx, 0]
        name_found = df_raw.iat[row_idx, 1]
        st.write(f"번호: **{number}**, 이름: **{name_found}** — 위치(원시 행 인덱스): {row_idx+1}")
        confirm = st.radio("이 사람 맞습니까?", ("예", "아니오"))
        if confirm == "예":
            # C~F열(인덱스 2~5)에서 성적 읽기 (존재하지 않으면 가능한 범위로 조정)
            max_col = df_raw.shape[1]
            score_col_start = 2
            score_col_end = min(5, max_col-1)  # inclusive index
            if score_col_start > score_col_end:
                st.error("성적을 가져올 열(C~F)이 시트에 존재하지 않습니다.")
            else:
                raw_scores = []
                labels = []
                for c in range(score_col_start, score_col_end+1):
                    labels.append(f"col_{c+1}")  # 기본 라벨: col_3, col_4 ...
                    val = df_raw.iat[row_idx, c]
                    try:
                        raw_scores.append(float(val) if val is not None and val != "" else float("nan"))
                    except:
                        raw_scores.append(float("nan"))
                # numeric array
                import numpy as np
                values = np.array(raw_scores, dtype=float)
                if np.all(np.isnan(values)):
                    st.warning("선택한 열에서 유효한 숫자형 성적을 찾을 수 없습니다.")
                else:
                    # 변화량 계산
                    changes = [0.0]
                    for i in range(1, len(values)):
                        a, b = values[i], values[i-1]
                        if np.isnan(a) or np.isnan(b):
                            changes.append(0.0)
                        else:
                            changes.append(a - b)
                    max_change = max([abs(x) for x in changes]) if any(abs(x) > 0 for x in changes) else 1.0
                    colors = [color_for_change(changes[i], max_change) for i in range(len(changes))]
                    
                    # Plotly
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=labels,
                        y=values,
                        mode="lines+markers",
                        line=dict(color="lightgray", width=3),
                        marker=dict(size=12, color=colors, line=dict(width=1, color="black")),
                        hovertemplate="%{x}: %{y}<extra></extra>"
                    ))
                    fig.update_layout(
                        title=f"{name_found} (번호 {number}) 성적 추이",
                        xaxis_title="구분 (C~F열)",
                        yaxis_title="점수",
                        template="plotly_white",
                        height=480
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 세부값 표시
                    detail = pd.DataFrame({
                        "열(인덱스)": [f"{c+1}" for c in range(score_col_start, score_col_end+1)],
                        "라벨": labels,
                        "점수": [None if np.isnan(v) else v for v in values],
                        "변화(이전과의 차이)": [None if i==0 else (None if np.isnan(values[i]) or np.isnan(values[i-1]) else values[i]-values[i-1]) for i in range(len(values))],
                        "색(표시용)": colors
                    })
                    st.markdown("**세부값**")
                    st.dataframe(detail)
        else:
            st.info("확인에서 '아니오'를 선택하셨습니다. 동명이인 검색 또는 이름 재입력 해주세요.")

    else:
        st.info(f"🔎 동명이인 {len(matched_indices)}명 발견. 번호로 본인 선택하세요.")
        # 목록 구성: show 번호(A열) and row index
        choices = []
        for idx in matched_indices:
            num = df_raw.iat[idx, 0]
            nm = df_raw.iat[idx, 1]
            display = f"{num} — {nm} (행 {idx+1})"
            choices.append((display, idx))
        # selectbox 사용자가 하나 선택
        display_texts = [c[0] for c in choices]
        selection = st.selectbox("목록에서 본인 번호 선택:", display_texts)
        if selection:
            # find chosen idx
            chosen_idx = dict(choices)[selection] if False else None
            # Above dict approach doesn't work because keys duplicate; do linear search:
            chosen_idx = None
            for disp, idx in choices:
                if disp == selection:
                    chosen_idx = idx
                    break
            if chosen_idx is not None:
                number = df_raw.iat[chosen_idx, 0]
                name_found = df_raw.iat[chosen_idx, 1]
                st.write(f"선택: 번호 **{number}**, 이름 **{name_found}** (행 {chosen_idx+1})")
                confirm2 = st.radio("이 사람 맞습니까?", ("예","아니오"), key="confirm2")
                if confirm2 == "예":
                    # 동일하게 성적(C~F열)을 표시
                    max_col = df_raw.shape[1]
                    score_col_start = 2
                    score_col_end = min(5, max_col-1)
                    if score_col_start > score_col_end:
                        st.error("성적을 가져올 열(C~F)이 시트에 존재하지 않습니다.")
                    else:
                        raw_scores = []
                        labels = []
                        for c in range(score_col_start, score_col_end+1):
                            labels.append(f"col_{c+1}")
                            val = df_raw.iat[chosen_idx, c]
                            try:
                                raw_scores.append(float(val) if val is not None and val != "" else float("nan"))
                            except:
                                raw_scores.append(float("nan"))
                        import numpy as np
                        values = np.array(raw_scores, dtype=float)
                        if np.all(np.isnan(values)):
                            st.warning("선택한 열에서 유효한 숫자형 성적을 찾을 수 없습니다.")
                        else:
                            changes = [0.0]
                            for i in range(1, len(values)):
                                a, b = values[i], values[i-1]
                                if np.isnan(a) or np.isnan(b):
                                    changes.append(0.0)
                                else:
                                    changes.append(a - b)
                            max_change = max([abs(x) for x in changes]) if any(abs(x) > 0 for x in changes) else 1.0
                            colors = [color_for_change(changes[i], max_change) for i in range(len(changes))]
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=labels,
                                y=values,
                                mode="lines+markers",
                                line=dict(color="lightgray", width=3),
                                marker=dict(size=12, color=colors, line=dict(width=1, color="black")),
                                hovertemplate="%{x}: %{y}<extra></extra>"
                            ))
                            fig.update_layout(title=f"{name_found} (번호 {number}) 성적 추이", xaxis_title="구분 (C~F열)", yaxis_title="점수", template="plotly_white", height=480)
                            st.plotly_chart(fig, use_container_width=True)

                            detail = pd.DataFrame({
                                "열(인덱스)": [f"{c+1}" for c in range(score_col_start, score_col_end+1)],
                                "라벨": labels,
                                "점수": [None if np.isnan(v) else v for v in values],
                                "변화(이전과의 차이)": [None if i==0 else (None if np.isnan(values[i]) or np.isnan(values[i-1]) else values[i]-values[i-1]) for i in range(len(values))],
                                "색(표시용)": colors
                            })
                            st.markdown("**세부값**")
                            st.dataframe(detail)
                else:
                    st.info("다른 학생을 선택하거나 이름을 다시 입력하세요.")
