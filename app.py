import streamlit as st
import google.generativeai as genai
import re

# --- 1. 配置 ---
st.set_page_config(page_title="語感實驗室", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# 本地詞庫
LOCAL_DICT = {"視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害", "立馬": "立刻", "特好": "很好"}

# --- 2. 核心邏輯 ---
def run_detection():
    text = st.session_state.u_input
    if not text: return
    st.session_state.current_text = text
    st.session_state.is_analyzed = True

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"已更新為台灣語感：{new}")

# --- 3. UI 介面 ---
st.title("📱 語感守護者：手機 App 原型")
st.markdown("---")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 模擬複製內容")
    st.text_area("在社群軟體複製的文字：", height=150, value="這視頻質量特好，有被驚訝到。", key="u_input")
    st.button("🚀 偵測並開啟懸浮窗", on_click=run_detection, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.success("**修正後的文字 (準備發佈)：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 懸浮窗模擬 (對話氣泡模式)")
    
    # 這裡模擬手機內部的 UI
    with st.container(border=True):
        if st.session_state.is_analyzed:
            # 模擬 App 傳送一條偵測訊息
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("偵測到大陸用語！建議調整如下：")
                
                # 自動搜尋關鍵字並生成對話式按鈕
                text = st.session_state.current_text
                found_any = False
                
                # 1. 詞庫建議
                for old, new in LOCAL_DICT.items():
                    if old in text:
                        found_any = True
                        st.button(f"修改「{old}」👉「{new}」", key=f"btn_{old}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
                
                # 2. 模擬 AI 語法建議
                if "有被" in text:
                    found_any = True
                    st.button("修改「有被驚訝到」👉「我很驚訝」", key="btn_ai_1",
                              on_click=apply_change, args=("有被驚訝到", "我很驚訝"), use_container_width=True)
                
                if not found_any:
                    st.write("🎉 檢查完畢，這段文字非常有台灣味！")
        else:
            st.info("請在左側輸入文字後按下偵測，模擬 App 懸浮氣泡跳出的效果。")

    if st.session_state.is_analyzed:
        st.button("📋 一鍵複製到剪貼簿", use_container_width=True)
