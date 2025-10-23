import streamlit as st
import requests

st.set_page_config(page_title="학생 메인/프로필", page_icon="🌸", layout="centered")

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

# ---------------- 공용 함수 ----------------
def call_api(action: str, payload: dict):
    """Apps Script Web API 호출 (POST, 예외처리 포함)"""
    data = {"action": action, "apiKey": API_KEY}
    data.update(payload or {})
    try:
        res = requests.post(API_URL, json=data, timeout=15)
    except requests.RequestException as e:
        return {"ok": False, "error": f"요청 실패: {e}"}

    if not res.text.strip():
        return {"ok": False, "error": "서버에서 빈 응답을 받았습니다."}
    try:
        return res.json()
    except ValueError:
        return {"ok": False, "error": f"JSON 파싱 실패: {res.text[:200]}"}

def hide_sidebar_pages():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] ul[data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

def show_sidebar_pages():
    st.sidebar.markdown("### 페이지")
    try:
        st.sidebar.page_link("pages/Feedback.py", label="📝 피드백 페이지")
    except Exception:
        pass

# ---------------- 세션 상태 ----------------
for key in ["logged_in","student_id","student_name","profile_image"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "logged_in" else False

# ---------------- UI ----------------
if not st.session_state.logged_in:
    hide_sidebar_pages()
    st.title("🔐 학생 로그인")

    student_id = st.text_input("학번")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if not student_id or not password:
            st.warning("학번과 비밀번호를 입력하세요.")
        else:
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
                st.error(f"로그인 실패: {resp.get('error')}")
else:
    # ---------- 프로필 페이지 ----------
    show_sidebar_pages()
    st.title("🌼 내 프로필")

    # --- CSS 커스터마이징 ---
    st.markdown("""
        <style>
        .profile-container {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
        }
        .profile-img {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            object-fit: cover;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        .profile-text {
            font-size: 1.3rem;
            font-weight: 600;
            text-align: center;
            color: var(--text-color, #222);
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 프로필 표시 ---
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    if st.session_state.profile_image:
        st.markdown(
            f'<img src="{st.session_state.profile_image}" class="profile-img">',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="width:180px;height:180px;border-radius:50%;background:#eee;display:flex;align-items:center;justify-content:center;font-size:60px;color:#aaa;">🙂</div>',
            unsafe_allow_html=True
        )
    st.markdown(
        f'<div class="profile-text">{st.session_state.student_name}<br>{st.session_state.student_id}</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 프로필 수정 섹션 ---
    st.subheader("프로필 이미지 변경")
    new_img = st.text_input("이미지 URL 입력", value=st.session_state.profile_image, placeholder="https://...")

    if st.button("이미지 저장"):
        resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "imageUrl": new_img})
        if resp.get("ok"):
            st.session_state.profile_image = new_img  # 바로 반영
            st.success("이미지 URL이 저장되었습니다.")
            st.rerun()
        else:
            st.error(f"저장 실패: {resp.get('error')}")

    st.subheader("비밀번호 변경")
    new_pw = st.text_input("새 비밀번호", type="password")
    if st.button("비밀번호 변경"):
        if not new_pw:
            st.warning("새 비밀번호를 입력하세요.")
        else:
            resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "newPassword": new_pw})
            if resp.get("ok"):
                st.success("비밀번호가 변경되었습니다.")
            else:
                st.error(f"변경 실패: {resp.get('error')}")

    st.divider()
    if st.button("로그아웃"):
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.rerun()
