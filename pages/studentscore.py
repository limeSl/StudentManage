import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Google Sheets CSV URL 변환
sheet_url = "https://docs.google.com/spreadsheets/d/1Nap48AW6zmfwVqeTyVJ8oGcegt2j8VgD5ovBxxNKMgM/export?format=csv"

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(sheet_url)
    return df

st.title("📊 학생 성적 추이 시각화")
st.write("이름을 선택하면 해당 학생의 성적 변화가 표시됩니다.")

df = load_data()

# 학생 이름 선택
students = df['이름'].unique()
selected_student = st.selectbox("학생 선택", students)

# 선택한 학생 데이터 필터링
student_data = df[df['이름'] == selected_student].sort_values(by='시험종류')

# 그래프 그리기
if not student_data.empty:
    scores = student_data['성적'].values
    exams = student_data['시험종류'].values

    # 상승/하강 색상 처리
    colors = ['red' if j - i >= 0 else 'blue' for i, j in zip(scores[:-1], scores[1:])]
    colors.insert(0, colors[0])  # 첫 데이터 색상 맞추기

    fig = go.Figure(
        data=go.Scatter(
            x=exams,
            y=scores,
            mode='lines+markers',
            line=dict(color='rgba(255,0,0,0.3)', width=3),
            marker=dict(size=12, color=colors, line=dict(width=2, color='DarkSlateGrey'))
        )
    )

    fig.update_layout(
        title=f"{selected_student} 학생의 성적 변화",
        xaxis_title="시험 종류",
        yaxis_title="성적",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("선택한 학생의 데이터가 없습니다.")
