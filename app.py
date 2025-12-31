import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 安全取得 API KEY
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化 Session State
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# 本地快速詞庫
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "在意", "內存": "記憶體", "優化": "調整"
}

# --- 2. 核心偵測邏輯 ---
def run_detection():
    text = st.session_state.u_input
    if not text: return
    st.session_state.current_text = text
    st.session_state.is_analyzed = True

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已更新：{new}")

# --- 3. UI 介面設計 ---
st.title("📱 語感守護者：中國用語轉台灣用語")
st.markdown("---")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 複製內容輸入")
    st.text_area("在此貼上你想要檢查的文字：", height=150, 
                 value="這視頻質量特好，有被驚訝到，希望大家能多優化內容。", 
                 key="u_input")
    st.button("🚀 開始偵測用語", on_click=run_detection, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.markdown("### 📝 修正後的最終文字")
        # 使用 code 區塊方便用戶一鍵複製，且視覺上更清晰
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 懸浮窗預覽")
    
    # 使用 Container 模擬手機螢幕邊框
    with st.container(border=True):
        if st.session_state.is_analyzed:
            # 模擬 App 內部的智慧助理氣泡
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.markdown("##### 🔍 偵測報告")
                st.write("我們發現了一些**中國用語**，建議調整如下：")
                st.divider()
                
                text = st.session_state.current_text
                found_any = False
                
                # A. 顯示詞庫建議
                for old, new in LOCAL_DICT.items():
                    if old in text:
                        found_any = True
                        st.button(f"📘 將「{old}」修正為「{new}」", key=f"btn_{old}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
                
                # B. 模擬 AI 文法建議 (例如：有被...)
                if "有被" in text:
                    found_any = True
                    st.button("🤖 將「有被驚訝到」修正為「我很驚訝」", key="btn_ai_gram",
                              on_click=apply_change, args=("有被驚訝到", "我很驚訝"), use_container_width=True)
                
                if not found_any:
                    st.success("🎉 太棒了！這段文字目前沒有偵測到明顯的中國用語。")
        else:
            st.info("👋 請在左側輸入內容並按下偵測，模擬 App 自動跳出的建議視窗。")

    if st.session_state.is_analyzed:
        st.button("📋 一鍵複製修正成果", use_container_width=True)
