import streamlit as st
import google.generativeai as genai

# --- 1. 配置與本地資料 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 固定轉換
LOCAL_FIX = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "優化": "調整"
}

# 歧義辨析 (增加詳細說明)
LOCAL_OPTIONS = {
    "土豆": [
        {"to": "馬鈴薯", "label": "🥔 改為「馬鈴薯」", "desc": "中國用語 (Potato)"},
        {"to": "花生", "label": "🥜 改為「花生」", "desc": "台灣本土用法 (Peanut)"}
    ],
    "窩心": [
        {"to": "貼心", "label": "❤️ 改為「貼心」", "desc": "中國指暖心"},
        {"to": "憋屈", "label": "😣 改為「憋屈」", "desc": "台灣指心裡悶苦"}
    ]
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def run_analysis():
    st.session_state.current_text = st.session_state.u_input
    st.session_state.is_analyzed = True

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 2. UI 介面 ---
st.title("📱 語感守護者 (語境解析強化版)")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("請輸入包含「土豆」的句子：", height=150, 
                 value="我想吃土豆，順便看看視頻。", key="u_input")
    st.button("🚀 執行偵測", on_click=run_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.info("**修正後的結果：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 互動預覽")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("🔍 **偵測到易混淆詞彙：**")
                
                curr_text = st.session_state.current_text
                found = False
                
                # A. 顯示歧義詞按鈕 (帶有解釋)
                for old, options in LOCAL_OPTIONS.items():
                    if old in curr_text:
                        found = True
                        st.warning(f"⚠️ 偵測到「{old}」，請依語境選擇：")
                        
                        # 顯示選項
                        for opt in options:
                            # 顯示說明文字
                            st.caption(f"📍 {opt['desc']}")
                            # 顯示按鈕
                            st.button(opt['label'], key=f"opt_{old}_{opt['to']}", 
                                      on_click=apply_change, args=(old, opt['to']), 
                                      use_container_width=True)
                        st.divider()
                
                # B. 顯示固定詞庫
                for old, new in LOCAL_FIX.items():
                    if old in curr_text:
                        found = True
                        st.button(f"📘 將「{old}」換成「{new}」", key=f"fix_{old}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
                
                if not found:
                    st.success("🎉 目前文字沒偵測到明顯的中國用語。")
        else:
            st.info("👋 請輸入文字後點擊偵測。")
