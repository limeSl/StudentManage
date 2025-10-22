import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="학생 성적 조회", page_icon="🎓", layout="centered")

st.title("🎓 학생 성적 조회 시스템")

# ✅ 구글 시트를 CSV 형태로 불러오기
sheet_url = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/export?format=csv"
try:
    df = pd.read_csv(sheet_url, skiprows=1)  # 1행(제목행) 건너뛰고 2행부터 읽기
except Exception as e:
    st.error(f"❌ 구글 시트를 불러오는 중 오류 발생: {e}")
    st.stop()

# ✅ 컬럼명 자동 정리 (예: ['번호', '이름', '1학기', '2학기', '기말', '총점'] 등)
df.columns = df.columns.str.strip()

# ✅ 사용자 이름 입력
name = st.text_input("학생 이름을 입력하세요:")

if name:
    matches = df[df['이름'].str.contains(name, na=False)]

    if len(matches) == 0:
        st.warning("⚠️ 해당 이름의 학생을 찾을 수 없습니다.")
    elif len(matches) == 1:
        student = matches.iloc[0]
        st.write(f"번호: **{student['번호']}**, 이름: **{student['이름']}** 이(가) 맞습니까?")
        if st.button("예"):
            try:
                scores = student.iloc[2:6].astype(float)
                subjects = df.columns[2:6]
                trend_color = 'red' if scores.iloc[-1] > scores.iloc[0] else 'blue'

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=subjects,
                    y=scores,
                    mode='lines+markers',
                    line=dict(color=trend_color, width=4),
                    marker=dict(size=10)
                ))

                fig.update_layout(
                    title=f"📊 {student['이름']} 학생의 성적 추이",
                    xaxis_title="과목 또는 학기",
                    yaxis_title="점수",
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"그래프를 표시하는 중 오류가 발생했습니다: {e}")
        elif st.button("아니오"):
            others = df[(df['이름'].str.contains(name, na=False)) & (df['번호'] != student['번호'])]
            if len(others) > 0:
                st.info("동명이인이 있습니다. 아래 목록을 확인하세요:")
                st.dataframe(others[['번호', '이름']])
            else:
                st.warning("해당 이름의 다른 학생은 없습니다.")
    else:
        st.info("동명이인이 있습니다. 아래에서 선택하세요:")
        st.dataframe(matches[['번호', '이름']])
