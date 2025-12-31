import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="語感專家：除錯寫入版", layout="wide")

if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)

def run_sync_analysis(text):
    if not text.strip(): return
    
    # 1. AI 辨識邏輯
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f'找出文字中的中國用語。文字："{text}"。格式：原詞|建議|解釋'
    
    try:
        response = model.generate_content(prompt)
        ai_res = []
        for line in response.text.strip().split('\n'):
            if "|" in line:
                p = line.split("|")
                if len(p) >= 3:
                    ai_res.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        st.session_state.res_list = ai_res
        
        # 2. 💥 強制同步區 💥
        if ai_res:
            st.info("🔄 偵測到新詞彙，正在嘗試連線 Google Sheets...")
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # 強制讀取名為 Sheet1 的工作表
                df = conn.read(worksheet="Sheet1", ttl=0)
                
                new_data = pd.DataFrame([
                    {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': 'AI學習', 'suggestion': i['r']} 
                    for i in ai_res
                ])
                
                # 合併與去重
                updated_df = pd.concat([df, new_data]).drop_duplicates(subset=['original'], keep='last')
                
                # 執行寫入
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("✅ 雲端同步成功！資料已寫入 Sheet1。")
                
            except Exception as e:
                # 這裡會噴出具體的報錯訊息
                st.error(f"❌ 雲端同步失敗！錯誤訊息如下：")
                st.code(str(e))
                st.warning("提示：如果是 'Authentication failed'，請檢查 Secrets 的 private_key 是否真的只有一整行且包含 \\n")

    except Exception as ai_e:
        st.error(f"AI 辨識失敗：{ai_e}")

# 介面排版
st.title("🧠 語感專家：終極除錯版")
u_in = st.text_area("📝 輸入文字：", height=150)
if st.button("🚀 分析並同步至雲端"):
    st.session_state.f_text = u_in
    run_sync_analysis(u_in)

# 顯示辨識卡片
for i, item in enumerate(st.session_state.res_list):
    with st.expander(f"📌 {item['w']}", expanded=True):
        st.write(item['e'])
        if st.button(f"修正為 {item['r']}", key=f"f_{i}"):
            do_fix(item['w'], item['r'])
            st.rerun()
