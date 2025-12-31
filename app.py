import streamlit as st
import google.generativeai as genai
import re

# --- 1. 配置與初始化 ---
st.set_page_config(page_title="互動標註實驗室", page_icon="🖱️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化 Session State
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 2. 核心邏輯函數 ---
def run_detection():
    # 這是點擊按鈕後觸發的函數
    if st.session_state.user_input_box:
        model = get_model()
        prompt = f"你是台灣編輯，修正大陸用語或文法。改動處用 [台灣用語](原詞) 格式。不要解釋。文字：{st.session_state.user_input_box}"
        try:
            response = model.generate_content(prompt)
            # 存入 session_state
            st.session_state.suggestions = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
            st.session_state.current_text = st.session_state.user_input_box
        except Exception as e:
            st.error(f"AI 連線失敗: {e}")

def apply_replacement(old, new):
    # 執行單個替換
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已替換：{old} → {new}")

# --- 3. UI 佈局 ---
st.title("🖱️ 特定詞彙互動修改模擬")

col_input, col_mobile = st.columns([1, 1])

with col_input:
    st.subheader("📝 原始文字")
    # 使用 key 綁定輸入框
    st.text_area("模擬剪貼簿文字：", height=150, 
                 value="這視頻質量特好，有被驚訝到，你不要噁心我。", 
                 key="user_input_box")
    
    # 點擊按鈕時觸發 run_detection
    st.button("🚀 開始偵測", on_click=run_detection, use_container_width=True)

with col_mobile:
    st.subheader("🤳 互動手機預覽")
    
    # 手機外殼 CSS (保持不變)
    st.markdown("""
    <style>
    .mobile-screen {
        border: 12px solid #333; border-radius: 30px; width: 300px; height: 500px;
        margin: auto; padding: 20px; background: #fff; overflow-y: auto; box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .preview-text { background: #f9f9f9; padding: 10px; border-radius: 8px; margin-top: 15px; border: 1px dashed #ccc; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mobile-screen">', unsafe_allow_html=True)
    
    if st.session_state.suggestions:
        st.markdown('<div style="font-size:0.8em; color:#ff4b4b; font-weight:bold;">偵測到建議 (點擊套用)：</div>', unsafe_allow_html=True)
        
        # 顯示互動建議按鈕
        for i, (new, old) in enumerate(st.session_state.suggestions):
            # 檢查原文中是否還存在該詞
            if old in st.session_state.current_text:
                st.button(f"替換「{old}」→「{new}」", 
                          key=f"btn_{i}", 
                          on_click=apply_replacement, 
                          args=(old, new),
                          use_container_width=True)
        
        st.markdown('<div class="preview-text">', unsafe_allow_html=True)
        st.write("**目前預覽：**")
        st.write(st.session_state.current_text)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("📋 複製最終結果", key="copy_final"):
            st.success("已模擬複製到剪貼簿！")
    else:
        st.markdown('<div style="text-align:center; margin-top:150px; color:#ccc;">等待偵測內容...</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
