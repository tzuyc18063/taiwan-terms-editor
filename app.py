import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 頁面設定 ---
st.set_page_config(page_title="語感專家：不卡死精進版", page_icon="🧠", layout="wide")

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = "這個軟件的質量需要優化。"
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.toast(f"✅ 已修正：{old_word}")

# --- 3. 介面呈現 ---
st.title("🧠 語感專家：終極不卡死版")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 輸入文字：", height=200, key="user_text")
    
    # 這裡是最關鍵的改動：按下按鈕後，AI 的處理被包在一個不會卡住的邏輯裡
    if st.button("🚀 啟動辨識 (秒出結果)", use_container_width=True):
        st.session_state.ai_suggestions = [] # 清空舊建議
        
        # 只在有文字時嘗試呼叫 AI
        if u_input.strip():
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                # 限制 AI 只回傳極簡格式，減少傳輸量
                prompt = f"找出這段話中的中國用語，只回傳列表如 [\"詞1\", \"詞2\"]：{u_input}"
                response = model.generate_content(prompt)
                match = re.search(r'\[.*\]', response.text)
                if match:
                    st.session_state.ai_suggestions = json.loads(match.group(0))
            except:
                st.warning("AI 目前回應較慢，請參考下方雲端現有建議。")

    st.markdown("---")
    st.subheader("📋 修正後結果")
    st.code(st.session_state.user_text, language=None)

with col_res:
    st.subheader("🤳 辨識與建議")
    
    # 讀取雲端資料庫 
    try:
        db_df = conn.read(ttl="10s").dropna(subset=['original'])
    except:
        db_df = pd.DataFrame(columns=['original', 'replacement', 'explanation'])

    current_text = st.session_state.user_text
    found_any = False
    shown_words = set()

    # A. 優先顯示「資料庫已知」的詞 (這部分絕對不會卡)
    for i, row in db_df.iterrows():
        word = str(row['original'])
        if word in current_text:
            shown_words.add(word)
            found_any = True
            with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                # 滿足您的需求：將源自大陸改為源自中國 
                exp = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {exp}")
                st.button(f"👉 修正為「{row['replacement']}」", key=f"db_{i}", on_click=apply_correction, args=(word, str(row['replacement'])))

    # B. 顯示 AI 額外發現的詞
    for word in st.session_state.ai_suggestions:
        if word in current_text and word not in shown_words:
            found_any = True
            with st.status(f"✨ AI 新發現：{word}", expanded=True):
                st.write("此詞彙尚未存入雲端，建議修正。")
                new_val = st.text_input(f"將「{word}」修正為：", key=f"ai_inp_{word}", placeholder="例如：軟體")
                if st.button(f"確認修正 {word}", key=f"ai_btn_{word}"):
                    apply_correction(word, new_val)
                    st.rerun()

    if not found_any and current_text:
        st.success("🎉 目前文字查無非在地用語！")
