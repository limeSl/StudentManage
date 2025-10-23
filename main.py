import streamlit as st
import requests

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

if st.button("🧩 Apps Script 연결 테스트"):
    try:
        res = requests.post(API_URL, json={
            "action": "login",
            "apiKey": API_KEY,
            "studentId": "테스트학번",
            "password": "테스트비번"
        }, timeout=10)
        st.write("응답:", res.json())
    except Exception as e:
        st.error(f"요청 실패: {e}")
