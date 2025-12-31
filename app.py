import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：穩定修正版", page_icon="🧠", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 雲端資料庫讀取 ---
def get_cloud_db():
    try:
        df = conn.read(ttl="5s") # 縮短緩存時間讓更新更快
        return df.dropna(subset=['original'])
    except:
        return pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])

# --- 3. 狀態管理 (關鍵：解決按鈕沒反應) ---
# 使用 session_state 來確保文字輸入框的內容可以被程式修改
if 'user_text' not in st.session_state:
    st.session_state.user_text = "職場內卷太嚴重"

# 定義按鈕觸發的函數
def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.toast(f"✅ 已修正：{old_word} ➜ {new_word}")

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：穩定修正版")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 文字輸入")
    # 使用 key="user_text" 綁定狀態，這樣 apply_correction 才能生效
    u_input = st.text_area("請輸入內容：", height=200, key="user_text")
    
    if st.button("🚀 執行辨識", use_container_width=True):
        st.session_state.is_analyzed = True
        st.rerun() # 強制重新整理以載入最新雲端資料

with col_wiki:
    st.subheader("🤳 雲端智慧百科")
    db_df = get_cloud_db()
    
    # 只要文字框有內容就進行即時比對
    current_text = st.session_state.user_text
    found_any = False
    
    for i, row in db_df.iterrows():
        word = str(row['original'])
        if word and word in current_text:
            found_any = True
            with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                st.markdown(f"### {row['title']}")
                # 這裡修正您的要求：將「源自大陸」改為「源自中國」
                explanation = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {explanation}")
                
                # 修改後的按鈕回傳機制
                st.button(
                    f"👉 修正「{word}」為「{row['replacement']}」", 
                    key=f"btn_{i}",
                    on_click=apply_correction,
                    args=(word, str(row['replacement'])),
                    use_container_width=True
                )
    
    if not found_any and current_text:
        st.info("💡 雲端目前查無對應詞彙。")
