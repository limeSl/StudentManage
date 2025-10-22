import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="학생 성적 조회", page_icon="🎓", layout="centered")

st.title("🎓 학생 성적 조회 시스템")

# ✅ 구글 시트 CSV 링크 (2행부터 유효 데이터)
sheet_url = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/export?format=csv"

# ✅ 데이터 불러오기
try:
    df = pd.read_csv(sheet_url, skiprows=1)  # 1행 제목 건너뜀
except Exception as e:
    st.error(f"❌ 구글 시트를 불러오는 중 오류 발생: {e}")
    st.stop()

# ✅ 열 이름 정리
df.columns = df.columns.str.strip()

# ✅ '이름' 열이 정확히 있는지 확인
possible_name_cols = [col for col in df.columns if '이름' in col]
if len(possible_name_cols) == 0:
    st.error(f"❌ '이름' 열을 찾을 수 없습니다. 현재 시트의 열: {list(df.columns)}")
    st.stop()
else:
    name_col = possible_name_cols[0]  # 예: '학생이름', '이름 ' 등 변형 가능

# ✅ 사용자 입력
name = st.text_input("학생 이름을 입력하세요:")

if name:
    # 이름이 포함된 행 찾기
    matches = df[df[name_col].astype(str).str.contains(name, na=False)]

    if len(matches) == 0:
        st.warning("⚠️ 해당 이름의 학생을 찾을 수 없습니다.")
    elif len(matches) == 1:
        student = matches.iloc[0]

        # 번호 컬럼 유추
        possible_num_cols = [col for col in df.columns if '번' in col or '번호' in col]
        num_col = possible_num_cols[0] if possible_num_cols else df.columns[0]

        st.write(f"번호: **{student[num_col]}**, 이름: **{student[name_col]}** 이(가) 맞습니까?")
        yes = st.button("예", key="yes_button")
        no = st.button("아니오", key="no_button")

        if yes:
            try:
                # C~F열 (3~6번째 컬럼) 선택
                score_cols = df.columns[2:6]
                scores = student[score_cols].astype(float)

                # 상승 / 하강 판단
                trend_color = 'red' if scores.iloc[-1] > scores.iloc[0] else 'blue'

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=score_cols,
                    y=scores,
                    mode='lines+markers',
                    line=dict(color=trend_color, width=4),
                    marker=dict(size=10)
                ))

                fig.update_layout(
                    title=f"📊 {student[name_col]} 학생의 성적 추이",
                    xaxis_title="과목 또는 학기",
                    yaxis_title="점수",
                    template="plotly_white"
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"그래프를 표시하는 중 오류가 발생했습니다: {e}")

        elif no:
            others = df[(df[name_col].astype(str).str.contains(name, na=False)) &
                        (df[num_col] != student[num_col])]
            if len(others) > 0:
                st.info("동명이인이 있습니다. 아래 목록을 확인하세요:")
                st.dataframe(others[[num_col, name_col]])
            else:
                st.warning("해당 이름의 다른 학생은 없습니다.")
    else:
        st.info("동명이인이 있습니다. 아래에서 선택하세요:")
        st.dataframe(matches)
