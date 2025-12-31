import streamlit as st
import google.generativeai as genai
import re

# --- 1. 配置 ---
st.set_page_config(page_title="語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化狀態
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state: st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state: st.session_state.ai_suggestions = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# --- 2. 詞庫 ---
LOCAL_DICT = {"視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害", "立馬": "立刻", "特好": "很好"}

# --- 3. 偵測邏輯 ---
def run_detection():
    text = st.session_state.user_input_box
    if not text: return
    st.session_state.local_suggestions = [(v, k) for k, v in LOCAL_DICT.items() if k in text]
    st.session_state.current_text = text
    st.session_state.is_analyzed = True
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"你是台灣編輯，修正大陸用語。改動處用 [新](舊) 格式。不要解釋。文字：{text}"
        response = model.generate_content(prompt)
        matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
        st.session_state.ai_suggestions = [m for m in matches if m[1] not in LOCAL_DICT]
    except:
        st.session_state.ai_suggestions = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)

# --- 4. 介面 ---
st.title("⚡ 語感實驗室 (App 實境模擬)")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 輸入區")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，有被驚訝到。", key="user_input_box")
    st.button("🚀 執行偵測", on_click=run_detection, use_container_width=True)
    if st.session_state.is_analyzed:
        st.info(f"**即時預覽：**\n\n{st.session_state.current_text}")

with col2:
    st.subheader("🤳 手機預覽")
    
    # 這裡是用 CSS 畫出的手機邊框，這次不使用 div 封閉，而是直接用 container
    st.markdown("""
        <style>
        .phone-ui {
            border: 8px solid #333;
            border-radius: 20px;
            padding: 20px;
            background-color: #ffffff;
            min-height: 400px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True): # 使用內建邊框確保穩定
        st.write("📱 **建議清單**")
        if st.session_state.is_analyzed:
            for i, (new, old) in enumerate(st.session_state.local_suggestions):
                if old in st.session_state.current_text:
                    st.button(f"📘 替換「{old}」→「{new}」", key=f"l_{i}", on_click=apply_change, args=(old, new), use_container_width=True)
            
            for i, (new, old) in enumerate(st.session_state.ai_suggestions):
                if old in st.session_state.current_text:
                    st.button(f"🤖 AI：{old}→{new}", key=f"a_{i}", on_click=apply_change, args=(old, new), use_container_width=True)
            
            if not st.session_state.local_suggestions and not st.session_state.ai_suggestions:
                st.write("✅ 目前文字很道地！")
        else:
            st.write("等待偵測內容...")

    if st.session_state.is_analyzed:
        st.button("📋 複製最終結果", use_container_width=True)
