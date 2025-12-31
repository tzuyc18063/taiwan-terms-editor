import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="語感專家：復活診斷版", layout="wide")

# 初始化
if 'res_list' not in st.session_state: st.session_state.res_list = []
if 'f_text' not in st.session_state: st.session_state.f_text = ""

# 核心分析函式
def run_analysis(text):
    if not text.strip(): return
    
    try:
        # 1. 配置 AI (直接使用 secrets 裡的 Key)
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # 使用最基礎的模型名稱以避開 404
        model = genai.GenerativeModel('gemini-pro') 
        
        st.info("📡 正在呼叫 AI 進行辨識...")
        prompt = f'找出文字中的中國大陸用語。文字："{text}"。格式：原詞|建議|解釋'
        response = model.generate_content(prompt)
        
        if not response.text:
            st.error("❌ AI 回傳內容為空，請檢查 API Key。")
            return

        results = []
        for line in response.text.strip().split('\n'):
            if "|" in line:
                p = line.split("|")
                if len(p) >= 3:
                    results.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        
        st.session_state.res_list = results
        
        # 2. 嘗試同步雲端
        if results:
            st.info("🔄 辨識成功，嘗試寫入 Google Sheets...")
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                # 強制讀取 Sheet1
                df = conn.read(worksheet="Sheet1", ttl=0)
                
                new_df = pd.DataFrame([
                    {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': 'AI學習', 'suggestion': i['r']} 
                    for i in results
                ])
                
                updated = pd.concat([df, new_df]).drop_duplicates(subset=['original'], keep='last')
                conn.update(worksheet="Sheet1", data=updated)
                st.success("✅ 雲端同步成功！")
            except Exception as e_sheet:
                st.warning(f"⚠️ 辨識完成但同步失敗：{e_sheet}")

    except Exception as e_all:
        st.error(f"❌ 發生錯誤：{e_all}")

# 介面排版
st.title("🧠 語感專家：復活診斷版")
u_in = st.text_area("📝 輸入文字（如：視頻、質量）：", height=150, value=st.session_state.f_text)

if st.button("🚀 開始分析", use_container_width=True):
    st.session_state.f_text = u_in
    run_analysis(u_in)
    # 移除 st.rerun() 避免訊息消失

# 顯示辨識卡片
if st.session_state.res_list:
    st.subheader("🤳 辨識建議")
    for i, item in enumerate(st.session_state.res_list):
        with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
            st.write(f"🔍 {item['e']}")
            if st.button(f"修正為 {item['r']}", key=f"b_{i}"):
                st.session_state.f_text = st.session_state.f_text.replace(item['w'], item['r'])
                st.rerun()
