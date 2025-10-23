# ---------- 프로필 페이지 ----------
show_sidebar_pages()
st.title("🌷 내 프로필")

# --- CSS 커스터마이징 ---
st.markdown("""
    <style>
    .profile-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 50px;
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
        box-shadow: 0 0 15px rgba(0,0,0,0.3);
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
        margin-bottom: 15px;
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

# 프로필 이미지 (여백 없이 꽉 찬 원형)
img_html = (
    f'<img src="{st.session_state.profile_image}" class="profile-img">'
    if st.session_state.profile_image
    else '<div style="width:260px;height:260px;border-radius:50%;background:#eee;display:flex;align-items:center;justify-content:center;font-size:90px;color:#bbb;">🙂</div>'
)
st.markdown(img_html, unsafe_allow_html=True)

# 이름 + 학번 (옆에 선명하게 표시)
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
