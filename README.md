schoollife.streamlit.app

로그인 페이지를 추가했습니다. (main.py 그대로 이용하면 됨)

https://docs.google.com/spreadsheets/d/1Pa6sSB1dFiCge6MwnpgEG1AQnCHnVkVhdb1EGkUPuTU/edit?gid=0#gid=0

이 구글 시트에서 사용자 데이터를 관리합니다.

참고해주세요 ^^

또한 각자 페이지에서는 

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 로그인 후 이용할 수 있습니다.")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.student_name

이 코드를 활용하여 학생 확인을 생략하고 바로 검색해서 이용할 수 있습니다. (학번과 이름 사용)
 = student_id
 = student_name
