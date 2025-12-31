import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：終極穩定版", page_icon="🧠", layout="wide")

# 建立雲端連線
conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 雲端資料庫操作 (加入緩存與錯誤處理) ---
def get_cloud_db():
    try:
        # 使用 ttl=10 避免頻繁請求導致卡頓
        df = conn.read(ttl="10s")
        return df.dropna(subset=['original'])
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

def save_to_cloud(new_cards):
    if not new_cards: return
    try:
        existing_df = get_cloud_db()
        new_df = pd.DataFrame(new_cards)
        updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
        conn.update(data=updated_df)
        st.cache_data.clear()
    except:
        st.warning("暫時無法寫入雲端，但您可以繼續使用。")

# --- 3. 智慧辨識引擎 (增加超時保護) ---
def start_analysis(text):
    if not text.strip(): return []
    
    # 優先檢查：如果雲端已經有了，就不一定要等聯網 AI
    db_df = get_cloud_db()
    for word in db_df['original']:
        if word in text:
            # 如果文字中包含已知詞彙，直接回傳 True 觸發顯示
            return [] 

    # 若是新詞，才啟動 AI
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"請分析此段文字中的大陸用語並以 JSON 格式回傳：{text}"
    
    try:
        # 移除聯網搜尋工具以增加速度，避免卡死
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            new_cards = json.loads(json_match.group(0))
            save_to_cloud(new_cards)
            return new_cards
    except:
        return []
    return []

# --- 4. 介面 ---
st.title("🧠 語感專家：穩定加速版")

if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""

col1, col2 = st.columns([1, 1.2])

with col1:
    u_input = st.text_area("請輸入內容：", height=200, value="職場內卷太嚴重")
    if st.button("🚀 執行辨識", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("智慧比對中..."):
            start_analysis(u_input)
            st.session_state.is_analyzed = True

with col2:
    if st.session_state.is_analyzed:
        db_df = get_cloud_db()
        current_text = st.session_state.processed_text
        found = False
        
        for i, row in db_df.iterrows():
            word = str(row['original'])
            if word in current_text:
                found = True
                with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                    st.write(f"**建議：** {row['replacement']}")
                    st.caption(row['explanation'])
                    if st.button(f"修正「{word}」", key=f"f_{i}"):
                        st.session_state.processed_text = current_text.replace(word, str(row['replacement']))
                        st.rerun()
        if not found:
            st.info("查無紀錄，AI 正在學習中。")
