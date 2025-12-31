import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 核心百科資料庫 (這是最強大的後盾) ---
# 將您整理的百科資訊直接內建，確保 100% 觸發
WORD_WIKI = {
    "視頻": {
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "台灣習慣稱「影片」；「視頻」在台灣多指物理訊號。",
        "suggestion": "建議修正為「影片」以符合台灣日常習慣。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "台灣指好壞用「品質」；「質量」專指物理重量 (Mass)。",
        "suggestion": "若指產品優劣，請換成「品質」。"
    },
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "兩岸指代物完全不同：中國指「馬鈴薯」，台灣指「花生」。",
        "is_ambiguous": True,
        "options": [
            {"to": "馬鈴薯", "desc": "🍟 換成馬鈴薯 (Potato)"},
            {"to": "花生", "desc": "🥜 換成花生 (Peanut)"}
        ]
    }
}

# --- 2. 配置 ---
st.set_page_config(page_title="語感專家", layout="wide")
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 3. UI 呈現 ---
st.title("📱 語感專家：主動百科模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    # 這裡的預設文字包含關鍵字
    u_input = st.text_area("請輸入內容：", height=200, value="這視頻質量真好，我想吃土豆。", key="u_input_area")
    
    if st.button("🚀 執行語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科建議")
    
    if st.session_state.is_analyzed:
        curr_text = st.session_state.current_text
        found_any = False
        
        # 直接掃描內建百科 (這步最穩，不靠 AI 也能跑)
        for word, info in WORD_WIKI.items():
            if word in curr_text:
                found_any = True
                with st.expander(f"📌 百科對照：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    
                    if info.get('is_ambiguous'):
                        # 歧義處理 (土豆)
                        cols = st.columns(len(info['options']))
                        for i, opt in enumerate(info['options']):
                            if cols[i].button(opt['desc'], key=f"opt_{word}_{i}", use_container_width=True):
                                apply_change(word, opt['to'])
                                st.rerun()
                    else:
                        # 一般處理 (視頻、質量)
                        st.info(f"💡 建議：{info['suggestion']}")
                        if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}", use_container_width=True):
                            apply_change(word, info['tw_term'])
                            st.rerun()

        # 如果內建詞庫沒掃到，可以加一個 AI 補位區 (可選)
        if not found_any:
            st.success("🎉 目前文字看起來非常本土！")
    else:
        st.info("👋 請輸入文字後點擊偵測。")
