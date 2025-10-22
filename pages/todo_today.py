# pages/todo_today.py
import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta

# --- 구글 시트 연결 ---
from google.oauth2.service_account import Credentials
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPE)
gc = gspread.authorize(creds)

# --- 시트 설정 ---
FILE_NAME = "StudyTimeDB"
spreadsheet = gc.open(FILE_NAME)
todo_sheet = spreadsheet.worksheet("todo_list")
todo_df = pd.DataFrame(todo_sheet.get_all_records())

# --- 로그인 확인 ---
if "user_id" not in st.session_state:
    st.warning("로그인 후 이용 가능합니다.")
    st.stop()

user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

st.title(f"📋 오늘의 To-do 리스트 ({user_name}님)")

today = datetime.today().date()

# --- 1. 과목 선택 ---
subject = st.selectbox("과목을 선택하세요", ["국어", "수학", "영어", "사회", "과학"])

# --- 2. 목표 선택 ---
if subject == "영어":
    base_goals = ["교과서 공부하기", "문제집 풀기", "단어 외우기", "직접 입력"]
else:
    base_goals = ["교과서 공부하기", "문제집 풀기", "직접 입력"]

goal = st.selectbox("목표를 선택하세요", base_goals)

# --- 3. 세부사항 입력 ---
if goal == "교과서 공부하기":
    pages = st.number_input("몇 페이지 공부할까요?", min_value=1, max_value=1000, step=1)
    detail = f"{pages}페이지 공부하기"
elif goal == "문제집 풀기":
    q_num = st.number_input("몇 문제 풀까요?", min_value=1, max_value=500, step=1)
    detail = f"{q_num}문제 풀기"
elif goal == "단어 외우기":
    words = st.number_input("몇 개 외울까요?", min_value=1, max_value=500, step=1)
    detail = f"{words}개 외우기"
else:
    detail = st.text_input("목표를 직접 입력하세요")

if st.button("➕ 목표 추가하기"):
    new_row = {
        "date": str(today),
        "id": user_id,
        "name": user_name,
        "subject": subject,
        "task": goal,
        "detail": detail,
        "status": "",       # 아직 미완료
        "progress": 0
    }
    todo_sheet.append_row(list(new_row.values()))
    st.success("오늘의 목표가 추가되었습니다!")

# --- 오늘의 할 일 불러오기 ---
today_tasks = todo_df[(todo_df["date"] == str(today)) & (todo_df["id"] == user_id)]

st.subheader("✅ 오늘의 할 일 목록")

if today_tasks.empty:
    st.info("아직 오늘의 할 일이 없습니다. 위에서 추가해보세요!")
else:
    for idx, row in today_tasks.iterrows():
        col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
        with col1:
            st.write(f"📘 **{row['subject']}**")
        with col2:
            st.write(f"{row['task']} - {row['detail']}")
        with col3:
            status = st.radio(
                "상태 선택", ["", "O", "X", "→", "△"],
                index=["", "O", "X", "→", "△"].index(row["status"]),
                key=f"status_{idx}"
            )
        with col4:
            if status == "△":
                progress = st.slider("달성률(%)", 0, 100, int(row["progress"]), key=f"prog_{idx}")
            else:
                progress = 100 if status == "O" else 0

        # 상태 변경 시 처리
        if status != row["status"] or progress != row["progress"]:
            todo_sheet.update_cell(idx + 2, 7, status)   # G열: status
            todo_sheet.update_cell(idx + 2, 8, progress) # H열: progress

            # → 내일로 미루기 기능
            if status == "→":
                tomorrow = today + timedelta(days=1)
                new_row = row.copy()
                new_row["date"] = str(tomorrow)
                new_row["status"] = ""
                new_row["progress"] = 0
                todo_sheet.append_row(list(new_row.values()))
                st.info(f"'{row['task']}'을(를) 내일로 미뤘습니다!")

    # --- 달성률 계산 ---
    done = today_tasks["progress"].sum()
    total = 100 * len(today_tasks)
    overall = round((done / total) * 100, 1) if total > 0 else 0
    st.markdown(f"### 🌟 오늘의 목표 달성률은 **{overall}%** 예요!")
