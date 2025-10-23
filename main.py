import streamlit as st
import requests

st.set_page_config(page_title="학생 메인/프로필", page_icon="👤", layout="centered")

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

# --------- 공용 함수 ----------
def call_api(action: str, payload: dict):
    """Apps Script Web API 호출 (POST, 서버-투-서버)"""
    data = {"action": action, "apiKey": API_KEY}
    data.update(payload or {})
    r = requests.post(API_URL, json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def hide_sidebar_pages():
    # 로그인 전 pages 숨김 (사이드바 목록 감추기)
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] ul[data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

def show_sidebar_pages():
    # 로그인 후에만 페이지 링크 노출(선택)
    st.sidebar.markdown("### 페이지")
    try:
        st.sidebar.page_link("pages/Feedback.py", label="피드백 페이지")
    except Exception:
        pass

# --------- 세션 상태 ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_id" not in st.session_state:
    st.session_state.student_id = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "profile_image" not in st.session_state:
    st.session_state.profile_image = ""

# --------- UI ----------
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
                    data = resp["data"]
                    st.session_state.logged_in = True
                    st.session_state.student_id = data["id"]
                    st.session_state.student_name = data["name"]
                    st.session_state.profile_image = data.get("imageUrl") or ""
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("로그인 실패: " + str(resp.get("error")))
            except requests.RequestException as e:
                st.error(f"서버 통신 오류: {e}")
else:
    #  로그인 후: 프로필 페이지
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
    st.subheader("프로필 이미지 URL 설정 (D열 저장)")
    new_img = st.text_input("이미지 URL", value=st.session_state.profile_image, placeholder="https://...")
    if st.button("이미지 저장"):
        try:
            resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "imageUrl": new_img})
            if resp.get("ok"):
                st.session_state.profile_image = resp["data"].get("imageUrl") or ""
                st.success("이미지 URL이 저장되었습니다.")
            else:
                st.error("저장 실패: " + str(resp.get("error")))
        except requests.RequestException as e:
            st.error(f"서버 통신 오류: {e}")

    st.subheader("비밀번호 변경 (C열 저장)")
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
            except requests.RequestException as e:
                st.error(f"서버 통신 오류: {e}")

    st.divider()
    if st.button("로그아웃"):
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.rerun()
