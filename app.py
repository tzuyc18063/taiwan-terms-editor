import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化設定 ---
st.set_page_config(page_title="語感專家：終極版", page_icon="🧠", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 找不到 GOOGLE_API_KEY，請檢查 Secrets 設定。")

# --- 2. 狀態管理 (確保輸入與結果分離) ---
if 'user_input_content' not in st.session_state:
    st.session_state.user_input_content = ""
if 'final_output_result' not in st.session_state:
    st.session_state.final_output_result = ""
if 'ai_cards' not in st.session_state:
    st.session_state.ai_cards = []

# 修正函式：僅修改下方結果，不連動上方輸入框
def execute_fix(old, new):
    st.session_state.final_output_result = st.session_state.final_output_result.replace(old, new)
    st.toast(f"✅ 修正成功：{old} → {new}")

# --- 3. 核心邏輯：AI 優先與安全寫入 ---
def process_analysis(text):
    if not text.strip(): return
    
    # 步驟 A: AI 辨識 (最快跳出建議)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""請找出文字中的中國用語（如：質量、視頻、優化、軟件）。
    文字："{text}"
    要求：1. JSON 回傳 2. 將『源自大陸』改為『源自中國』。
    格式：[ {{"w": "原詞", "r": "建議", "t": "百科標題", "e": "解釋內容"}} ]"""
    
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            new_results = json.loads(match.group(0))
            st.session_state.ai_cards = new_results
            
            # 步驟 B: 安全寫入雲端 (若失敗不報錯、不卡住)
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                # 設定短時間 ttl 避免讀取卡死
                df = conn.read(ttl="5s")
                sync_data = pd.DataFrame([
                    {'original': r['w'], 'replacement': r['r'], 'title': r['t'], 'explanation': r['e']} 
                    for r in new_results
                ])
                updated_df = pd.concat([df, sync_data]).drop_duplicates(subset=['original'], keep='last')
                conn.update(data=updated_df)
            except:
                pass # 忽略雲端錯誤，確保 UI 流暢
    except Exception as e:
        st.error(f"AI 服務暫時忙碌中：{e}")

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：絕對不卡死版")
st.caption("AI 自動學習模式：新詞彙會自動同步至雲端百科。")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📝 文字輸入")
    # 上方輸入框：固定對應 user_input_content
    raw_text = st.text_area("在此輸入文字：", value=st.session_state.user_input_content, height=200, key="main_input")
    
    if st.button("🚀 啟動辨識 (AI 優先)", use_container_width=True):
        st.session_state.user_input_content = raw_text
        st.session_state.final_output_result = raw_text
        with st.spinner("AI 正在快速分析..."):
            process_analysis(raw_text)
            st.rerun()

    if st.session_state.final_output_result:
        st.markdown("---")
        st.subheader("📋 修正後結果 (點擊右上角複製)")
        # 下方結果區：顯示修正後的內容
        st.code(st.session_state.final_output_result, language=None)

with col_right:
    st.subheader("🤳 智慧辨識建議")
    
    current_text = st.session_state.final_output_result
    has_suggestion = False
    
    # 直接顯示 AI 剛剛抓到的結果
    if st.session_state.ai_cards:
        for i, card in enumerate(st.session_state.ai_cards):
            if card['w'] in current_text:
                has_suggestion = True
                with st.expander(f"📌 建議修正：{card['w']}", expanded=True):
                    # 再次確保解釋文字符合要求
                    clean_exp = str(card['e']).replace("源自大陸", "源自中國")
                    st.write(f"🔍 **解釋：** {clean_exp}")
                    st.button(
                        f"👉 修正為「{card['r']}」", 
                        key=f"fix_btn_{i}", 
                        on_click=execute_fix, 
                        args=(card['w'], card['r']), 
                        use_container_width=True
                    )
    
    if not has_suggestion and current_text:
        st.success("🎉 目前文字查無建議。")
