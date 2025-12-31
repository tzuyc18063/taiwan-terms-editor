import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：全自動智慧版", page_icon="🧠", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Secrets 中設定 GOOGLE_API_KEY")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""
if 'ai_detected' not in st.session_state:
    st.session_state.ai_detected = []

def apply_correction(old, new):
    st.session_state.final_result = st.session_state.final_result.replace(old, new)
    st.toast(f"✅ 已修正：{old} -> {new}")

# --- 3. 自動學習核心 (核心修改：強制寫入) ---
def run_auto_learning(text):
    if not text.strip(): return
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    任務：辨識文字中不符合台灣習慣的中國用語（如：質量、優化、軟件、內卷、視頻）。
    輸入文字："{text}"
    要求：
    1. 必須以 JSON 列表格式回傳。
    2. 解釋中將『源自大陸』改為『源自中國』。
    格式範例：[ {{"original": "原詞", "replacement": "台灣建議", "title": "百科標題", "explanation": "解釋內容", "suggestion": "建議說法"}} ]
    """
    
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            new_data_list = json.loads(match.group(0))
            st.session_state.ai_detected = new_data_list
            
            # --- 強制自動寫入 Google Sheets ---
            if new_data_list:
                # 1. 讀取現有雲端資料
                existing_df = conn.read(ttl="5s").dropna(subset=['original'])
                # 2. 轉換新資料為 DataFrame
                new_df = pd.DataFrame(new_data_list)
                # 3. 合併並去重 (以 original 欄位為準，保留最新的解釋)
                updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
                # 4. 寫回雲端 (實現自動學習)
                conn.update(data=updated_df)
                st.cache_data.clear() # 清除緩存確保下次讀到新的
    except Exception as e:
        st.error(f"自動學習同步失敗：{e}")

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：全自動智慧學習版")
st.caption("AI 發現新詞後會自動寫入雲端資料庫，實現永久智慧記憶。")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 文字輸入：", height=250, key="user_text", placeholder="在此輸入文字，AI 會自動學習新詞...")
    
    if st.button("🚀 啟動 AI 辨識並同步學習", use_container_width=True):
        st.session_state.final_result = u_input
        with st.spinner("AI 正在學習新詞並寫入雲端大腦..."):
            run_auto_learning(u_input)
            st.rerun()

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.final_result, language=None)

with col_res:
    st.subheader("🤳 智慧辨識與雲端百科")
    
    # 這裡顯示目前偵測到的卡片
    current_text = st.session_state.final_result
    display_list = []
    seen = set()

    # 優先從本次 AI 偵測的結果顯示
    for item in st.session_state.ai_detected:
        if item['original'] in current_text:
            display_list.append(item)
            seen.add(item['original'])

    if display_list:
        for i, card in enumerate(display_list):
            with st.expander(f"📌 智慧記憶：{card['original']}", expanded=True):
                st.markdown(f"### {card.get('title', '語感修正')}")
                # 確保解釋中的「源自中國」
                exp = str(card.get('explanation', '')).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {exp}")
                st.button(
                    f"👉 修正為「{card['replacement']}」", 
                    key=f"fix_{i}", 
                    on_click=apply_correction, 
                    args=(card['original'], card['replacement']),
                    use_container_width=True
                )
    else:
        if current_text:
            st.success("🎉 目前查無非在地用語，或 AI 已完成同步。")
