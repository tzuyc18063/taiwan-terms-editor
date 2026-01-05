import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 穩定初始化 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"系統初始化異常：{e}")
    st.stop()

# --- 3. 本地必殺清單 (絕對不會失效) ---
STATIC_CHECK = {
    "套路": "花招 / 手段",
    "視頻": "影片",
    "很火": "很紅 / 熱門",
    "牛逼": "厲害 / 強",
    "質量": "品質",
    "優化": "最佳化 / 改善",
    "走心": "用心 / 認真",
    "反饋": "回饋"
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_all():
    for item in st.session_state.final_results:
        old = item['original']
        new = item['taiwan'].split(' / ')[0]
        st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.session_state.final_results = []
    st.rerun()

# --- 4. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 穩定診斷模式：在地詞彙 + AI 流行語偵測")

c1, c2 = st.columns([1, 1.2])

with c1:
    u_input = st.text_area("請輸入文字：", height=250, value=st.session_state.current_text if st.session_state.current_text else "視頻質量很好，但他一直在背後蛐蛐我。", key="input_box")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 執行語感掃描", use_container_width=True):
            st.session_state.current_text = u_input
            all_res = []
            
            # 軌道一：本地比對 (秒出)
            for cn, tw in STATIC_CHECK.items():
                if cn in u_input:
                    all_res.append({"original": cn, "taiwan": tw, "reason": "台灣在地習慣用法。"})
            
            # 軌道二：AI 偵測 (針對蛐蛐等新詞)
            with st.spinner("AI 正在偵測流行語..."):
                try:
                    prompt = f"你是台灣語感專家。找出以下文字中不符合台灣習慣的流行語或大陸用語（如：蛐蛐）。文字：{u_input}。請僅回傳 JSON 陣列 [{{'original': '...', 'taiwan': '...', 'reason': '...'}}]"
                    response = model.generate_content(prompt)
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        ai_data = json.loads(match.group())
                        for a in ai_data:
                            if not any(r['original'] == a['original'] for r in all_res):
                                all_res.append(a)
                except:
                    pass
            
            st.session_state.final_results = all_res

    with col2:
        if st.button("🧹 重置編輯器", use_container_width=True):
            st.session_state.current_text = ""
            st.session_state.final_results = []
            st.rerun()

    if st.session_state.current_text:
        st.write("---")
        st.subheader("📋 修正後的文字預覽")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("💡 語感調整建議")
    # 只顯示還存在於文字中的建議
    active_res = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
    
    if active_res:
        if st.button("🪄 一鍵套用所有建議", use_container_width=True):
            apply_all()
            
        for item in active_res:
            with st.expander(f"📌 {item['original']} ➔ {item['taiwan']}", expanded=True):
                st.write(f"📘 **理由：** {item['reason']}")
                if st.button(f"套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                    st.session_state.current_text = st.session_state.current_text.replace(item['original'], item['taiwan'].split(' / ')[0])
                    st.rerun()
    else:
        st.write("目前沒有偵測到需要調整的詞彙。")
