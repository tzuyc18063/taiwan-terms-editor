import streamlit as st
import google.generativeai as genai
import re

# --- 1. 配置與初始化 ---
st.set_page_config(page_title="秒開版語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化狀態
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state:
    st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []

# --- 2. 本地詞庫定義 (不需要 API 的部分) ---
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "走心/在意", "內存": "記憶體", "優化": "優化/調整"
}

# --- 3. 智慧模型偵測 ---
@st.cache_resource
def get_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-2.0-flash-exp', 'models/gemini-1.5-flash', 'gemini-1.5-flash']
        for target in priority:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except: return None

# --- 4. 混合偵測邏輯 ---
def run_hybrid_detection():
    text = st.session_state.user_input_box
    if not text: return

    # A. 本地詞庫偵測 (瞬間完成)
    local_found = []
    for old, new in LOCAL_DICT.items():
        if old in text:
            local_found.append((new, old))
    st.session_state.local_suggestions = local_found
    st.session_state.current_text = text

    # B. AI 偵測 (非同步/需等待)
    model = get_working_model()
    if model:
        prompt = f"你是台灣編輯，修正大陸用語或文法（如：噁心我、有被）。改動處用 [台灣用語](原詞) 格式。不要解釋。文字：{text}"
        try:
            response = model.generate_content(prompt)
            # 排除掉已經在本地詞庫處理過的，避免重複
            ai_matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
            st.session_state.
