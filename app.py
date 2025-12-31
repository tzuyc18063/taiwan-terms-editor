import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 初始化 ---
# 將頁面標題改為台灣常用的「精進版」
st.set_page_config(page_title="語感專家：結果精進版", page_icon="🧠", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = "我們要優化這個產品。"
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.session_state.final_result = st.session_state.user_text
    st.toast(f"✅ 已修正：{old_word} ➜ {new_word}")

# --- 3. 介面呈現 ---
# 標題也進行在地化修正
st.title("🧠 語感專家：穩定修正 + 結果精進版")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入內容：", height=200, key="user_text")
    
    if st.button("🚀 啟動智慧辨識", use_container_width=True):
        st.session_state.final_result = u_input
        st.rerun()

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        
        # 點擊右側小圖示即可複製
        st.code(st.session_state.final_result, language=None)
        
        if hasattr(st, "copy_to_clipboard"):
            if st.button("📋 點此複製全文"):
                st.copy_to_clipboard(st.session_state.final_result)
                st.success("已複製到剪貼簿！")
        
        if st.button("🧹 清空結果", type="primary"):
            st.session_state.final_result = ""
            st.rerun()

with col_wiki:
    st.subheader("🤳 雲端智慧百科")
    try:
        # 讀取 Google Sheet 資料 
        db_df = conn.read(ttl="5s").dropna(subset=['original'])
    except:
        db_df = pd.DataFrame(columns=['original', 'replacement', 'title', 'explanation', 'suggestion'])
    
    current_text = st.session_state.user_text
    found_any = False
    
    # 這裡加入對「優化」的即時偵測 (即便資料庫沒寫)
    temp_dict = [
        {"original": "優化", "replacement": "改善 / 提升", "title": "優化 vs 改善", "explanation": "「優化」為中國用語，台灣習慣說「改善」、「精進」或「提升品質」。"}
    ]
    
    # 轉換為 DataFrame 方便比對
    custom_df = pd.DataFrame(temp_dict)
    full_df = pd.concat([db_df, custom_df]).drop_duplicates(subset=['original'])

    for i, row in full_df.iterrows():
        word = str(row['original'])
        if word and word in current_text:
            found_any = True
            with st.expander(f"📌 雲端記憶：{word}", expanded=True):
                st.markdown(f"### {row['title']}")
                # 將「源自大陸」修正為「源自中國」
                explanation = str(row['explanation']).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {explanation}")
                
                st.button(
                    f"👉 一鍵修正「{word}」", 
                    key=f"btn_{i}_{word}",
                    on_click=apply_correction,
                    args=(word, str(row['replacement'])),
                    use_container_width=True
                )
    
    if not found_any and current_text:
        st.success("🎉 目前文字查無非在地用語！")
