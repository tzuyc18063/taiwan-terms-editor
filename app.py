import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：AI 自動學習版", page_icon="🧠", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 核心功能：雲端讀寫 ---
def get_cloud_db():
    try:
        return conn.read(ttl="5s").dropna(subset=['original'])
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

def save_to_cloud(new_cards):
    """將 AI 抓到的新詞自動追加到 Google Sheets"""
    if not new_cards: return
    existing_df = get_cloud_db()
    new_df = pd.DataFrame(new_cards)
    # 結合新舊資料並去重
    updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
    conn.update(data=updated_df)
    st.cache_data.clear()

# --- 3. 核心功能：AI 深度辨識與自動學習 ---
def start_deep_learning(text):
    if not text.strip(): return
    
    # 建立 AI 模型 (使用 Flash 以平衡速度與準確度)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 指令：找出非台灣在地用語
    prompt = f"""
    任務：你是台灣用語與中國用語對照專家。
    輸入文字："{text}"
    
    指令：
    1. 找出其中不符合台灣習慣的詞（如：優化、視頻、質量、合同、激活、軟件）。
    2. 必須以 JSON 列表格式回傳，格式如下：
    [ {{"original": "原詞", "replacement": "台灣建議", "title": "詞彙百科", "explanation": "解釋(請將『源自大陸』一律寫成『源自中國』)", "suggestion": "建議說法"}} ]
    3. 如果沒有發現，請回傳 []。
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            new_cards = json.loads(json_match.group(0))
            # 💡 關鍵：將 AI 的發現自動存入 Google Sheets 實現永久記憶
            save_to_cloud(new_cards)
    except Exception as e:
        st.error(f"AI 學習失敗：{e}")

# --- 4. 狀態管理與修正 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.session_state.final_result = st.session_state.user_text

# --- 5. 介面呈現 ---
st.title("🧠 語感專家：AI 自動學習版")
st.caption("AI 會自動將新發現的非在地詞彙寫入您的雲端資料庫。")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("請輸入任何文字：", height=200, key="user_text", placeholder="例如：我們要優化這個產品的質量。")
    
    if st.button("🚀 啟動 AI 學習辨識", use_container_width=True):
        st.session_state.final_result = u_input
        with st.spinner("AI 正在分析並同步雲端大腦..."):
            start_deep_learning(u_input)
            st.rerun()

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.final_result, language=None)

with col_wiki:
    st.subheader("🤳 雲端智慧百科 (含永久記憶)")
    db_df = get_cloud_db() # 讀取包含 AI 剛寫入的新資料 
    
    current_text = st.session_state.user_text
    found_any = False
    
    for i, row in db_df.iterrows():
        word = str(row['original'])
        if word and word in current_text:
            found_any = True
            with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                st.markdown(f"### {row['title']}")
                # 再次確保顯示為「源自中國」
                explanation = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {explanation}")
                st.button(f"👉 修正「{word}」", key=f"btn_{i}", on_click=apply_correction, args=(word, str(row['replacement'])), use_container_width=True)
    
    if not found_any and current_text:
        st.info("💡 目前資料庫與 AI 尚未發現非在地詞彙。")
