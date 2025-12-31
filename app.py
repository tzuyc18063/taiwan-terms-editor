import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 頁面與連線初始化 ---
st.set_page_config(page_title="語感專家：雲端終極版", page_icon="🧠", layout="wide")

# 連接您的 Google Sheet
# 請確保 Secrets 中 connections.gsheets.spreadsheet 網址正確
conn = st.connection("gsheets", type=GSheetsConnection)

# 初始化 Gemini AI
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 雲端資料庫核心功能 ---
def get_cloud_db():
    """讀取雲端表單內容"""
    try:
        # ttl=0 確保每次點擊按鈕都是讀取最新的 Google Sheet 資料
        df = conn.read(ttl="0")
        return df.dropna(subset=['original']) # 過濾掉空行
    except Exception as e:
        st.error(f"雲端資料庫讀取失敗：{e}")
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

def save_to_cloud(new_cards):
    """將 AI 抓到的新詞自動寫入 Google Sheet"""
    if not new_cards: return
    
    existing_df = get_cloud_db()
    new_df = pd.DataFrame(new_cards)
    
    # 整合新舊資料，若原詞相同則以新的為主
    updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
    
    # 強制寫回 Google Sheet
    conn.update(data=updated_df)
    st.cache_data.clear()

# --- 3. 智慧辨識與聯網搜尋 ---
def start_smart_analysis(text):
    if not text.strip(): return []
    
    # 使用 Gemini 1.5 Flash 並開啟 Google 搜尋工具
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search_retrieval": {}}]
    )
    
    # 強化 Prompt：針對您提到的詞彙下達絕對指令
    prompt = f"""
    任務：你是最嚴格的台灣語境校正專家。
    待處理文字："{text}"
    
    指令：
    1. 只要出現「內卷」、「視頻」、「很火」、「媽生」、「特好」、「驚訝到」等詞，必須視為大陸用語。
    2. 自動搜尋這些詞在台灣 PTT、Dcard 或新聞中的地道說法。
    3. 必須回傳以下 JSON 格式：
    [ {{"original": "原詞", "replacement": "台灣建議", "title": "百科標題", "explanation": "為什麼不道地？", "suggestion": "修正建議"}} ]
    """
    try:
        response = model.generate_content(prompt)
        # 提取 JSON 區塊
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            new_cards = json.loads(json_match.group(0))
            # 查完後自動「永久記住」到雲端表單
            save_to_cloud(new_cards)
            return new_cards
        return []
    except Exception as e:
        st.warning(f"AI 聯網辨識暫時忙碌，改由雲端資料庫直接比對。")
        return []

# --- 4. UI 介面設定 ---
st.title("🧠 語感專家：具備「永久記憶」的雲端 AI")
st.caption("AI 查完新詞會自動同步至您的 Google Sheet，實現集體智慧記憶。")

# 狀態管理
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入內容（例如：職場內卷太嚴重，簡直是媽生好皮）：", height=200)
    
    if st.button("🚀 啟動聯網智慧辨識", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("AI 正在搜尋並同步雲端大腦..."):
            # 執行分析並儲存新詞
            start_smart_analysis(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.processed_text, language=None)

with col_right:
    st.subheader("🤳 雲端智慧百科")
    if st.session_state.is_analyzed:
        # 強制從雲端讀取最新記憶
        db_df = get_cloud_db()
        current_text = st.session_state.processed_text
        found_any = False
        
        # 比對目前文字中是否包含資料庫裡的詞
        for index, row in db_df.iterrows():
            word = str(row['original'])
            if word and word in current_text:
                found_any = True
                with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                    st.markdown(f"### {row['title']}")
                    st.write(f"🔍 **語境百科：** {row['explanation']}")
                    st.info(f"💡 **修正建議：** {row['suggestion']}")
                    
                    if st.button(f"👉 修正為「{row['replacement']}」", key=f"btn_{word}_{index}"):
                        st.session_state.processed_text = current_text.replace(word, str(row['replacement']))
                        st.rerun()
        
        if not found_any:
            st.success("🎉 這段文字目前讀起來很在地！若有新詞，AI 辨識後會自動存入雲端。")
