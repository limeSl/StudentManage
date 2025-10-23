# pages/studentscore.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# --- 구글 시트 연결 설정 ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPE)
gc = gspread.authorize(creds)

# ✅ 로그인 정보 확인
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("먼저 로그인해주세요.")
    st.stop()

# ✅ 로그인된 사용자 정보
user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

st.title(f"📊 {user_name} 학생의 성적 조회")

# --- 성적 시트 불러오기 ---
sheet = gc.open("StudentPlannerDB").worksheet("scores")
scores_df = pd.DataFrame(sheet.get_all_records())

# ✅ 학번으로 필터링
student_score = scores_df[scores_df["id"] == user_id]

if student_score.empty:
    st.warning("성적 정보가 없습니다.")
else:
    st.dataframe(student_score)

# 로그아웃 버튼
if st.button("로그아웃"):
    st.session_state.clear()
    st.success("로그아웃되었습니다.")
    st.switch_page("app_login.py")
