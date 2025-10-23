import streamlit as st
import requests

st.set_page_config(page_title="학생 메인/프로필", page_icon="👤", layout="centered")

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

# 사이드바 페이지 목록 숨기기 (로그인 전)
def hide_sidebar_pages():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] ul[data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 페이지 링크 보여주기 (로그인 후)
def show_sidebar_pages():
    st.sidebar.markdown("### 페이지")
    # 여기에 실제 pages 파일명에 맞춰 링크 표기 (Streamlit 1.31+)
    try:
        st.sidebar.page_link("pages/Feedback.py", label="피드백 페이지")
        # st.sidebar.page_link("pages/Another.py", label="다른 페이지")
    except Exception:
        st.sidebar.write("피드백 페이지로 이동은 상단 메뉴를 이용하세요.")

def call_api(action, payload):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    data = {"action": action}
    data.update(payload)
    r = requests.post(API_URL, json=data, headers=headers, timeout=15)
    return r.json()

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_id" not in st.session_state:
    st.session_state.student_id = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "profile_image" not in st.session_state:
    st.session_state.profile_image = ""

if not st.session_state.logged_in:
    hide_sidebar_pages()
    st.title("🔐 학생 로그인")
    student_id = st.text_input("학번")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if not student_id or not password:
            st.warning("학번과 비밀번호를 입력하세요.")
        else:
            try:
                resp = call_api("login", {"studentId": student_id, "password": password})
                if resp.get("ok"):
                    st.session_state.logged_in = True
                    st.session_state.student_id = resp["data"]["id"]
                    st.session_state.student_name = resp["data"]["name"]
                    st.session_state.profile_image = resp["data"].get("imageUrl") or ""
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("로그인 실패: " + str(resp.get("error")))
            except Exception as e:
                st.error(f"서버 통신 오류: {e}")
else:
    # 로그인 후: 프로필 페이지
    show_sidebar_pages()
    st.title("👤 내 프로필")
    col1, col2 = st.columns([1,2])
    with col1:
        if st.session_state.profile_image:
            st.image(st.session_state.profile_image, caption="프로필 이미지", use_column_width=True)
        else:
            st.info("프로필 이미지가 없습니다.")
    with col2:
        st.write(f"**학번:** {st.session_state.student_id}")
        st.write(f"**이름:** {st.session_state.student_name}")

    st.divider()
    st.subheader("프로필 이미지 URL 설정")
    new_img = st.text_input("이미지 URL 입력", value=st.session_state.profile_image, placeholder="https://...")
    if st.button("이미지 저장"):
        try:
            resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "imageUrl": new_img})
            if resp.get("ok"):
                st.session_state.profile_image = resp["data"].get("imageUrl") or ""
                st.success("이미지 URL이 저장되었습니다.")
            else:
                st.error("저장 실패: " + str(resp.get("error")))
        except Exception as e:
            st.error(f"서버 통신 오류: {e}")

    st.subheader("비밀번호 변경")
    new_pw = st.text_input("새 비밀번호", type="password")
    if st.button("비밀번호 변경"):
        if not new_pw:
            st.warning("새 비밀번호를 입력하세요.")
        else:
            try:
                resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "newPassword": new_pw})
                if resp.get("ok"):
                    st.success("비밀번호가 변경되었습니다.")
                else:
                    st.error("변경 실패: " + str(resp.get("error")))
            except Exception as e:
                st.error(f"서버 통신 오류: {e}")

    st.divider()
    if st.button("로그아웃"):
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.rerun()
