import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感實驗室 - 旗艦版", page_icon="⚡", layout="wide")

# 安全取得 API KEY
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化所有 Session State，確保操作不閃退
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state:
    st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []
if 'is_analyzed' not in st.session_state:
    st.session_state.is_analyzed = False

# --- 2. 本地快速詞庫 ---
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "在意", "內存": "記憶體", "優化": "調整",
    "挺好": "挺好/很好", "早上好": "早安", "晚上好": "晚安"
}

# --- 3. 智慧模型偵測器 ---
@st.cache_resource
def get_working_model():
    try:
        # 自動尋找可用模型，避開 404 錯誤
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-2.0-flash-
