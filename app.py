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

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""
if 'temp_cards' not in st.session_state:
    st.session_state.temp_cards = []

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.session_state.final_result = st.session_state.user_text

# --- 3. 雲端記憶核心 ---
def get_cloud_db():
    try:
        # 增加緩存時間，大幅減少卡頓感 
        return conn.read(ttl="60s").dropna(subset=['original'])
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：AI 自動學習版")
st.caption("AI 會自動捕捉新詞並存入雲端，若轉圈圈請稍等，修正建議會優先跳出。")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 輸入文字：", height=200, key="user_text", placeholder="例如：我們要優化這個產品的質量。")
    
    if st.button("🚀 啟動 AI 智慧辨識", use_container_width=True):
        st.session_state.final_result = u_input
        
        # 建立 AI 模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""找出文字中不符合台灣習慣的中國用語（如：質量、優化、軟件）。
        文字："{u_input}"
        請嚴格回傳 JSON 列表格式（不要有其他文字）：
        [ {{"original": "原詞", "replacement": "台灣建議", "title": "詞彙百科", "explanation": "解釋(請將『源自大陸』改為『源自中國』)", "suggestion": "建議說法"}} ]"""
        
        with st.spinner("AI 正在解析語感..."):
            try:
                response = model.generate_content(prompt)
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    st.session_state.temp_cards = json.loads(json_match.group(0))
                    # 💡 這裡不直接寫入雲端，改在下方分次處理以防卡死
            except:
                st.warning("AI 學習暫時忙碌。")

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.final_result, language=None)

with col_wiki:
    st.subheader("🤳 智慧辨識結果")
    
    # A. 優先顯示這一次 AI 剛抓到的詞
    current_text = st.session_state.user_text
    found_any = False
    
    # 建立目前需要顯示的清單 (整合雲端 + 本次新增)
    db_df = get_cloud_db()
    combined_list = st.session_state.temp_cards + db_df.to_dict('records')
    
    # 用來防止重複顯示
    shown_words = set()

    for i, row in enumerate(combined_list):
        word = str(row['original'])
        if word and word in current_text and word not in shown_words:
            shown_words.add(word)
            found_any = True
            with st.expander(f"📌 辨識到：{word}", expanded=True):
                st.markdown(f"### {row['title']}")
                explanation = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {explanation}")
                st.button(f"👉 修正「{word}」", key=f"btn_{i}", on_click=apply_correction, args=(word, str(row['replacement'])), use_container_width=True)
    
    # B. 最後偷偷執行存檔，不讓使用者等
    if st.session_state.temp_cards:
        try:
            # 只有當真的有新詞時才觸發寫入 
            existing_df = db_df
            new_df = pd.DataFrame(st.session_state.temp_cards)
            updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
            conn.update(data=updated_df)
            st.session_state.temp_cards = [] # 寫完就清空
        except:
            pass

    if not found_any and current_text:
        st.info("💡 目前查無非在地詞彙。")
