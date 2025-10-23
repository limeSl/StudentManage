import streamlit as st
import requests

st.set_page_config(page_title="학생 메인/프로필", page_icon="🌷", layout="centered")

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

# ---------------- 공용 함수 ----------------
def call_api(action: str, payload: dict):
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
    st.title("🌷 내 프로필")

    # --- 스타일 커스터마이징 ---
    st.markdown("""
        <style>
        .profile-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 60px;
            margin-top: 40px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }
        .profile-img {
            width: 260px;
            height: 260px;
            border-radius: 50%;
            object-fit: cover;
            object-position: center;
            border: 5px solid #fff;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
        }
        .profile-info {
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: left;
        }
        .profile-name {
            font-size: 2rem;
            font-weight: 800;
            color: #111;
            margin-bottom: 18px;
            letter-spacing: 1px;
        }
        .profile-id {
            font-size: 1.4rem;
            font-weight: 600;
            color: #333;
            margin-top: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 프로필 표시 영역 ---
    st.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)

    # 프로필 이미지 (동그랗게 꽉 차게 표시)
    img_html = (
        f'<img src="{st.session_state.profile_image}" class="profile-img">'
        if st.session_state.profile_image
        else '<div style="width:260px;height:260px;border-radius:50%;background:#eee;display:flex;align-items:center;justify-content:center;font-size:90px;color:#bbb;">🙂</div>'
    )
    st.markdown(img_html, unsafe_allow_html=True)

    # 이름 + 학번
    st.markdown(
        f"""
        <div class="profile-info">
            <div class="profile-name">{st.session_state.student_name}</div>
            <div class="profile-id">{st.session_state.student_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 프로필 수정 섹션 ---
    st.subheader("프로필 이미지 변경")
    new_img = st.text_input("이미지 URL 입력", value=st.session_state.profile_image, placeholder="https://...")

    if st.button("이미지 저장"):
        resp = call_api("updateProfile", {"studentId": st.session_state.student_id, "imageUrl": new_img})
        if resp.get("ok"):
            st.session_state.profile_image = new_img  # 즉시 반영
            st.success("프로필 이미지가 업데이트되었습니다.")
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
