import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import re

# --- 1. 頁面精進設定 ---
st.set_page_config(page_title="語感專家：安全模式版", page_icon="🧠", layout="wide")

# 初始化 AI
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'ai_results' not in st.session_state:
    st.session_state.ai_results = []

def apply_correction(old, new):
    st.session_state.user_text = st.session_state.user_text.replace(old, new)

# --- 3. 雲端資料庫 (加入嚴格超時保護) ---
def safe_get_db():
    try:
        # 使用 st.connection 的自定義參數，若連線失敗不報錯
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 設定極短的緩存，失敗則回傳空表
        return conn.read(ttl="1h") 
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'explanation'])

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：安全模式版")
st.info("若右側無回應，代表雲端資料庫連線逾時，系統已切換至 AI 即時辨識模式。")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 輸入文字：", height=200, key="user_text")
    
    if st.button("🚀 啟動辨識 (安全模式)", use_container_width=True):
        if u_input.strip():
            with st.spinner("AI 正在解析中..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""找出文字中的中國用語，以 JSON 回傳：
                    [{{"w": "原詞", "r": "台灣建議", "e": "解釋"}}]
                    解釋中請將『源自大陸』改為『源自中國』。文字：{u_input}"""
                    
                    response = model.generate_content(prompt)
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        st.session_state.ai_results = json.loads(match.group(0))
                except:
                    st.error("AI 暫時無法連線。")

    st.markdown("---")
    st.subheader("📋 修正後結果")
    st.code(st.session_state.user_text, language=None)

with col_res:
    st.subheader("🤳 辨識建議")
    
    # 建立顯示清單
    final_cards = []
    
    # 嘗試比對資料庫 (這部分現在被保護起來了)
    db_df = safe_get_db()
    if not db_df.empty:
        for _, row in db_df.iterrows():
            if str(row['original']) in st.session_state.user_text:
                final_cards.append({
                    "w": row['original'], 
                    "r": row['replacement'], 
                    "e": str(row['explanation']).replace("源自大陸", "源自中國")
                })

    # 合併 AI 的結果
    for item in st.session_state.ai_results:
        if item['w'] in st.session_state.user_text and item['w'] not in [c['w'] for c in final_cards]:
            final_cards.append(item)

    if final_cards:
        for i, card in enumerate(final_cards):
            with st.expander(f"📌 建議修正：{card['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {card['e']}")
                st.button(f"👉 修正為「{card['r']}」", key=f"btn_{i}", on_click=apply_correction, args=(card['w'], card['r']))
    else:
        st.write("目前查無建議。")
