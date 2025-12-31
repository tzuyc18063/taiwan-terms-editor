import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# 1. 基本設定
st.set_page_config(page_title="語感專家：穩定版", layout="wide")

if 'res_list' not in st.session_state: st.session_state.res_list = []
if 'f_text' not in st.session_state: st.session_state.f_text = ""

def do_fix(old, new):
    st.session_state.f_text = st.session_state.f_text.replace(old, new)
    st.toast(f"✅ 已修正：{old}")

# 2. 核心邏輯
def run_sync_analysis(text):
    if not text.strip(): return
    
    # 嘗試多個可能的模型名稱以避開 404
    model_names = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    model = None
    
    for name in model_names:
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel(name)
            # 測試測試是否可用
            test_resp = model.generate_content("test", generation_config={"max_output_tokens": 1})
            break 
        except:
            continue

    if not model:
        st.error("❌ 無法連線至 Gemini AI 模型，請檢查 API Key 權限。")
        return

    try:
        prompt = f'找出文字中的中國用語。文字："{text}"。格式：原詞|建議|解釋'
        response = model.generate_content(prompt)
        
        ai_res = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    p = line.split("|")
                    if len(p) >= 3:
                        ai_res.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        
        st.session_state.res_list = ai_res
        
        # 3. 雲端同步
        if ai_res:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                # 讀取 Sheet1
                df = conn.read(worksheet="Sheet1", ttl=0)
                
                new_data = pd.DataFrame([
                    {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': 'AI學習', 'suggestion': i['r']} 
                    for i in ai_res
                ])
                
                updated_df = pd.concat([df, new_data]).drop_duplicates(subset=['original'], keep='last')
                # 寫入 Sheet1
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("✅ 雲端同步成功！")
            except Exception as e:
                st.warning(f"⚠️ 辨識完成，但雲端同步失敗：{e}")

    except Exception as e:
        st.error(f"分析失敗：{e}")

# 3. 介面
st.title("🧠 語感專家：穩定版")
u_in = st.text_area("📝 輸入文字：", height=150, value=st.session_state.f_text)

if st.button("🚀 開始分析"):
    st.session_state.f_text = u_in
    with st.spinner("AI 思考中..."):
        run_sync_analysis(u_in)
    st.rerun()

# 顯示結果
if st.session_state.f_text:
    st.subheader("📋 修正後結果")
    st.code(st.session_state.f_text)

for i, item in enumerate(st.session_state.res_list):
    if item['w'] in st.session_state.f_text:
        with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
            st.write(item['e'])
            if st.button(f"修正為 {item['r']}", key=f"btn_{i}"):
                do_fix(item['w'], item['r'])
                st.rerun()
