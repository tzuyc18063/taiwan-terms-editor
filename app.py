import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="秒開版語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化所有狀態，防止網頁重整後變數消失
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state:
    st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []

# --- 2. 本地快速詞庫 ---
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "在意", "內存": "記憶體", "優化": "調整"
}

# --- 3. 智慧模型獲取 ---
@st.cache_resource
def get_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-2.0-flash-exp', 'models/gemini-1.5-flash', 'gemini-1.5-flash']
        for target in priority:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

# --- 4. 核心偵測函數 ---
def run_hybrid_detection():
    # 確保輸入框有文字
    text = st.session_state.user_input_box
    if not text:
        return

    # A. 本地詞庫偵測 (0秒反應)
    local_found = []
    for old, new in LOCAL_DICT.items():
        if old in text:
            local
