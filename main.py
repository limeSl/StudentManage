import streamlit as st
import requests

API_URL = st.secrets["apps_script"]["url"]
API_KEY = st.secrets["apps_script"]["api_key"]

if st.button("연결 테스트"):
    res = requests.post(st.secrets["apps_script"]["url"], json={
        "action": "login",
        "apiKey": st.secrets["apps_script"]["api_key"],
        "studentId": "10101",
        "password": "1234"
    })
    st.write("상태:", res.status_code)
    st.write("응답:", res.text)
