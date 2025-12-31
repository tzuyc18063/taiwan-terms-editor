import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 頁面精進設定 ---
st.set_page_config(page_title="語感專家：AI 自動學習版", page_icon="🧠", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 雲端記憶核心 ---
def get_cloud_db():
    try:
        # 增加緩存時間至 10 秒，減少對 Google 的請求頻率，避免卡頓
        return conn.read(ttl="10s").dropna(subset=['original'])
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

def save_to_cloud(new_cards):
    if not new_cards: return
    try:
        existing_df = get_cloud_db()
        new_df = pd.DataFrame(new_cards)
        # 合併並去重 
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
        conn.update(data=updated_df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"雲端寫入失敗，請檢查 Google Sheet 權限：{e}")

# --- 3. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.session_state.final_result = st.session_state.user_text

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：AI 自動學習版")
st.caption("輸入新詞（如：質量、激活、軟件），AI 會自動辨識並永久存入您的雲端資料庫。")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 輸入文字：", height=200, key="user_text", placeholder="例如：我們要優化這個產品的質量。")
    
    if st.button("🚀 啟動 AI 智慧辨識", use_container_width=True):
        st.session_state.final_result = u_input
        
        # 建立 AI 模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 核心 Prompt
        prompt = f"""找出文字中不符合台灣習慣的中國用語（如：質量、優化、軟件）。
        文字："{u_input}"
        請回傳 JSON 列表：
        [ {{"original": "原詞", "replacement": "台灣建議", "title": "詞彙百科", "explanation": "解釋(請將『源自大陸』改為『源自中國』)", "suggestion": "建議說法"}} ]
        若無發現回傳 []。"""
        
        with st.spinner("AI 正在學習新詞並同步雲端..."):
            try:
                response = model.generate_content(prompt)
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    new_cards = json.loads(json_match.group(0))
                    if new_cards:
                        save_to_cloud(new_cards)
                st.session_state.is_analyzed = True
                st.rerun()
            except Exception as e:
                st.warning("AI 回應較慢，已優先載入雲端現有記憶。")

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.final_result, language=None)

with col_wiki:
    st.subheader("🤳 雲端智慧百科")
    db_df = get_cloud_db()
    current_text = st.session_state.user_text
    found_any = False
    
    # 只要雲端有紀錄的詞，即便 AI 這次沒抓到，也會強制顯示
    for i, row in db_df.iterrows():
        word = str(row['original'])
        if word and word in current_text:
            found_any = True
            with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                st.markdown(f"### {row['title']}")
                # 再次確保用語精進
                explanation = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {explanation}")
                st.button(f"👉 修正「{word}」", key=f"btn_{i}", on_click=apply_correction, args=(word, str(row['replacement'])), use_container_width=True)
    
    if not found_any and current_text:
        st.info("💡 目前雲端尚無此詞彙紀錄，請按左側按鈕讓 AI 學習。")
