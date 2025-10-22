import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="📊 학생 성취도 조회", page_icon="📈", layout="centered")

st.title("📊 학생 성취도 조회 시스템")

# --- 구글 시트 CSV로 불러오기 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/edit?usp=sharing"

def load_sheet(url):
    if "https://docs.google.com/spreadsheets" in url:
        csv_url = url.replace("/edit?usp=sharing", "").replace("/edit#gid=", "/export?format=csv&gid=")
        csv_url = csv_url.replace("/edit", "/export?format=csv")
        df = pd.read_csv(csv_url)
        return df
    return None

try:
    df = load_sheet(SHEET_URL)
    if df is None:
        st.error("⚠️ 구글 시트를 불러오지 못했습니다.")
    else:
        st.success("✅ 구글 시트 데이터를 성공적으로 불러왔습니다.")
        st.caption("이름을 입력해 자신의 성취도를 조회하세요.")

        # --- 이름 검색 ---
        search_name = st.text_input("🔍 이름을 입력하세요:")

        if search_name:
            matches = df[df['이름'] == search_name]

            if len(matches) == 0:
                st.warning("❌ 해당 이름의 학생을 찾을 수 없습니다.")
            elif len(matches) == 1:
                student = matches.iloc[0]
                st.write(f"번호: {student['번호']}, 이름: {student['이름']}이(가) 맞습니까?")
                col1, col2 = st.columns(2)

                if col1.button("예"):
                    # --- C~F열 성적 가져오기 ---
                    score_cols = df.columns[2:6]  # 1학기~4학기 또는 과목별 성적
                    scores = student[score_cols]
                    score_labels = score_cols.tolist()
                    score_values = scores.values.tolist()

                    # --- 상승/하강 색상 설정 ---
                    colors = []
                    for i in range(len(score_values)):
                        if i == 0:
                            colors.append('gray')
                        else:
                            if score_values[i] > score_values[i - 1]:
                                colors.append('red')   # 상승
                            elif score_values[i] < score_values[i - 1]:
                                colors.append('blue')  # 하강
                            else:
                                colors.append('gray')  # 동일

                    # --- Plotly 그래프 ---
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=score_labels,
                        y=score_values,
                        mode='lines+markers',
                        line=dict(width=3, color='gray'),
                        marker=dict(size=10, color=colors),
                    ))
                    fig.update_layout(
                        title=f"🎯 {student['이름']} 학생의 성취도 변화",
                        xaxis_title="학기",
                        yaxis_title="점수",
                        template="plotly_white",
                        width=700,
                        height=450
                    )
                    st.plotly_chart(fig, use_container_width=True)

                if col2.button("아니오"):
                    st.info("🔍 동명이인을 검색 중...")
                    duplicates = df[df['이름'] == search_name]
                    if len(duplicates) > 1:
                        st.write("동명이인 목록:")
                        st.dataframe(duplicates[['번호', '이름']])
                    else:
                        st.warning("동명이인이 없습니다.")
            else:
                st.info("🔍 동명이인이 여러 명 있습니다. 아래 목록을 확인하세요.")
                st.dataframe(matches[['번호', '이름']])
except Exception as e:
    st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
