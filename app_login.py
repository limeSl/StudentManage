# app_login.py
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

# --- 시트에서 사용자 정보 불러오기 ---
sheet = gc.open("StudentPlannerDB").worksheet("users")
users_df = pd.DataFrame(sheet.get_all_records())

# --- Streamlit UI ---
st.set_page_config(page_title="학생 플래너 로그인", page_icon="🎓", layout="centered")

st.title("🎓 학생 플래너 로그인")

user_id = st.text_input("아이디를 입력하세요")
password = st.text_input("비밀번호를 입력하세요", type="password")

login_button = st.button("로그인")

if login_button:
    # 해당 아이디가 시트에 있는지 확인
    match = users_df[(users_df['id'] == user_id) & (users_df['password'] == password)]

    if len(match) == 1:
        user_info = match.iloc[0]
        st.session_state["user_id"] = user_info["id"]
        st.session_state["user_name"] = user_info["name"]
        st.session_state["role"] = user_info["role"]

        st.success(f"{user_info['name']}님 환영합니다! ({'교사' if user_info['role']=='teacher' else '학생'})")

        # 페이지 이동 (Streamlit 1.36 이상)
        if user_info["role"] == "teacher":
            st.switch_page("pages/teacher_dashboard.py")
        else:
            st.switch_page("pages/student_dashboard.py")
    else:
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
