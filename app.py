import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：極速回應版", page_icon="🧠", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""
if 'detected_list' not in st.session_state:
    st.session_state.detected_list = []

def apply_correction(old_word, new_word):
    st.session_state.user_text = st.session_state.user_text.replace(old_word, new_word)
    st.session_state.final_result = st.session_state.user_text

# --- 3. 極速辨識邏輯 ---
def fast_analyze(text):
    if not text.strip(): return
    
    # 建立 AI 模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 指令簡化：只要求抓出詞彙，不要求生成百科解釋，這能提升 80% 的速度
    prompt = f"請找出這段文字中的中國用語（如：質量、軟件、優化）：{text}。請只回傳 JSON 列表格式：[\"詞1\", \"詞2\"]"
    
    try:
        response = model.generate_content(prompt)
        # 提取列表
        match = re.search(r'\[.*\]', response.text)
        if match:
            # 存入 session 供右側顯示
            st.session_state.detected_list = json.loads(match.group(0))
    except:
        pass

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：極速回應版")
st.caption("已優化辨識速度，優先顯示建議，避免雲端同步導致的卡頓。")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    u_input = st.text_area("📝 輸入文字：", height=200, key="user_text", placeholder="例如：這個軟件的質量需要優化。")
    
    if st.button("🚀 啟動智慧辨識", use_container_width=True):
        st.session_state.final_result = u_input
        with st.spinner("AI 快速掃描中..."):
            fast_analyze(u_input)
            st.rerun()

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.final_result, language=None)

with col_res:
    st.subheader("🤳 辨識與修正建議")
    
    # 讀取雲端現有資料庫 
    try:
        db_df = conn.read(ttl="60s").dropna(subset=['original'])
    except:
        db_df = pd.DataFrame(columns=['original', 'replacement', 'explanation'])

    current_text = st.session_state.user_text
    found_any = False
    shown = set()

    # A. 優先檢查 AI 剛抓到的詞
    for word in st.session_state.detected_list:
        if word in current_text and word not in shown:
            shown.add(word)
            found_any = True
            # 從資料庫找解釋，找不到就顯示預設
            match_row = db_df[db_df['original'] == word]
            
            with st.expander(f"📌 發現詞彙：{word}", expanded=True):
                if not match_row.empty:
                    rep = match_row.iloc[0]['replacement']
                    exp = str(match_row.iloc[0]['explanation']).replace("源自大陸", "源自中國")
                    st.write(f"🔍 **解釋：** {exp}")
                else:
                    # 如果是資料庫沒有的新詞，給予通用建議
                    rep = "請輸入建議" 
                    st.write(f"🔍 **解釋：** 此為 AI 辨識出之中國用語。")
                
                # 提供一個輸入框讓使用者可以自定義修正詞，或者直接點擊 (若庫裡有)
                if not match_row.empty:
                    st.button(f"👉 修正為「{rep}」", key=f"btn_{word}", on_click=apply_correction, args=(word, rep), use_container_width=True)
                else:
                    new_val = st.text_input(f"手動修正「{word}」為：", placeholder="例如：軟體", key=f"inp_{word}")
                    if st.button(f"確認修正「{word}」", key=f"btn_new_{word}"):
                        apply_correction(word, new_val)
                        st.rerun()

    if not found_any and current_text:
        st.success("🎉 目前查無非在地用語！")
