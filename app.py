import streamlit as st
import google.generativeai as genai
import re

# --- 1. 初始化與配置 ---
st.set_page_config(page_title="語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state: st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state: st.session_state.ai_suggestions = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# 本地詞庫
LOCAL_DICT = {"視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體", "牛逼": "厲害", "立馬": "立刻", "特好": "很好"}

# --- 2. 核心偵測邏輯 ---
def run_detection():
    text = st.session_state.u_input
    if not text: return
    # 執行偵測
    st.session_state.local_suggestions = [(v, k) for k, v in LOCAL_DICT.items() if k in text]
    st.session_state.current_text = text
    st.session_state.is_analyzed = True
    
    # AI 偵測 (選用，額度滿時會跳過)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"你是台灣編輯，修正大陸用語。改動處用 [新](舊) 格式。文字：{text}"
        response = model.generate_content(prompt)
        matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
        st.session_state.ai_suggestions = [m for m in matches if m[1] not in LOCAL_DICT]
    except:
        st.session_state.ai_suggestions = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)

# --- 3. UI 介面設計 ---
st.title("⚡ 語感實驗室：App 原型介面")
st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📝 原始文字輸入")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，有被驚訝到。", key="u_input")
    st.button("🚀 開始偵測並生成建議", on_click=run_detection, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.success("**處理後的最終文字：**")
        st.write(st.session_state.current_text)

with col_right:
    st.subheader("🤳 行動端修正面板")
    
    # 使用 st.container(border=True) 模擬手機螢幕感
    with st.container(border=True):
        if st.session_state.is_analyzed:
            st.markdown("### 📱 偵測到建議")
            
            # 詞庫建議 (藍色區塊感)
            if st.session_state.local_suggestions:
                st.caption("📘 本地詞庫精準比對")
                for i, (new, old) in enumerate(st.session_state.local_suggestions):
                    if old in st.session_state.current_text:
                        st.button(f"替換「{old}」→「{new}」", key=f"loc_{i}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
            
            # AI 建議 (紅色區塊感)
            if st.session_state.ai_suggestions:
                st.caption("🤖 AI 語意深度分析")
                for i, (new, old) in enumerate(st.session_state.ai_suggestions):
                    if old in st.session_state.current_text:
                        st.button(f"建議「{old}」改為「{new}」", key=f"ai_{i}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
            
            if not st.session_state.local_suggestions and not st.session_state.ai_suggestions:
                st.write("✨ 完美！目前文字非常符合台灣語感。")
        else:
            st.markdown("<br><br><h4 style='text-align: center; color: gray;'>等待輸入偵測內容...</h4><br><br>", unsafe_allow_html=True)

    if st.session_state.is_analyzed:
        if st.button("📋 一鍵複製修正結果", use_container_width=True):
            st.balloons()
            st.toast("已模擬複製到剪貼簿！")
