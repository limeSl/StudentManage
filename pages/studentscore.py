import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

# 구글 시트 접근 설정
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)

# 구글 시트 불러오기
SHEET_URL = st.secrets["private_gsheets_url"]

@st.cache_data
def load_data():
    client = gspread.authorize(CREDS)
    sheet = client.open_by_url(SHEET_URL).sheet1
    data = sheet.get_all_values()
    # 1행은 헤더, 2행부터 유효 데이터
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

st.title("📊 학생 성적 조회 시스템")

df = load_data()

name = st.text_input("학생 이름을 입력하세요:")

if name:
    # B열 기준으로 이름 검색
    matches = df[df.iloc[:, 1] == name]

    if not matches.empty:
        st.success(f"✅ '{name}' 학생의 데이터를 찾았습니다.")

        # 해당 학생 행 가져오기
        row = matches.iloc[0]

        # 시험종류(헤더)를 키로, 점수를 값으로 변환
        score_dict = {df.columns[i]: row[i] for i in range(2, len(df.columns))}

        # DataFrame으로 변환
        score_df = pd.DataFrame(list(score_dict.items()), columns=["시험종류", "점수"])
        score_df["점수"] = pd.to_numeric(score_df["점수"], errors="coerce")

        # 증감율(%) 계산
        score_df["변화(%)"] = score_df["점수"].pct_change() * 100
        score_df["변화(%)"] = score_df["변화(%)"].fillna(0).round(1)

        st.subheader("📘 세부 성적 변화표")
        st.dataframe(score_df, hide_index=True)

        # ======================
        # Plotly 시각화
        # ======================
        st.subheader("📈 점수 변화 그래프")

        fig = go.Figure()

        # 막대그래프 (점수)
        fig.add_trace(go.Bar(
            x=score_df["시험종류"],
            y=score_df["점수"],
            name="점수",
            marker_color="royalblue",
            text=score_df["점수"],
            textposition="outside"
        ))

        # 꺾은선그래프 (변화율)
        fig.add_trace(go.Scatter(
            x=score_df["시험종류"],
            y=score_df["변화(%)"],
            name="변화율(%)",
            mode="lines+markers+text",
            text=score_df["변화(%)"].astype(str) + "%",
            textposition="top center",
            line=dict(color="orange", width=3)
        ))

        fig.update_layout(
            title=f"📊 {name} 학생의 시험별 점수 및 변화율",
            xaxis_title="시험종류",
            yaxis_title="점수",
            yaxis=dict(showgrid=True),
            legend=dict(orientation="h", x=0.3, y=-0.2),
            height=500,
            margin=dict(l=40, r=40, t=80, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(f"'{name}' 학생의 데이터를 찾을 수 없습니다.")
else:
    st.info("이름을 입력하면 해당 학생의 성적을 불러옵니다.")
