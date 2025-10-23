import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re
import matplotlib.pyplot as plt

# --- Google Sheets 연결 ---
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Secrets에서 서비스 계정 정보 불러오기
SERVICE_ACCOUNT = st.secrets["google_service_account"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT, scopes=SCOPE)
gc = gspread.authorize(creds)

sheet = gc.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Pa6sSB1dFiCge6MwnpgEG1AQnCHnVkVhdb1EGkUPuTU/edit?gid=1916264337"
).worksheet("Studytime")

# --- 이하 기존 코드 동일 ---
data = sheet.get_all_records()
df = pd.DataFrame(data)
