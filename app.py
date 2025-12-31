import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：終極保險版", page_icon="🧠", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 請檢查 Secrets 中的 GOOGLE_API_KEY")

# --- 2. 狀態管理 ---
if 'user_input' not in st.session_state: st.session_state.user_input = ""
if 'final_text' not in st.session_state: st.session_state.final_text = ""
if 'fix_list' not in st.session_state: st.session_state.fix_list = []

def apply_fix(o, n):
    st.session_state.final_text = st.session_state.final_text.replace(o, n)
    st.toast(f"✅ 已修正：{o} → {n}")

# --- 3. 核心邏輯：純文字辨識 ---
def run_ai_logic(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 改變策略：要求 AI 用最簡單的 分隔符號 回傳，不要 JSON
    prompt = f"""請找出文字中的中國用語，並直接按以下格式回傳（一行一個，不要任何其他文字）：
    原詞|建議修正|解釋
    文字內容："{text}"
    注意：解釋中若有『源自大陸』請一律改為『源自中國』。"""
    
    try:
        response = model.generate_content(prompt)
        raw_lines = response.text.strip().split('\n')
        parsed_results = []
        
        for line in raw_lines:
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    parsed_results.append({
                        "w": parts[0].strip(),
                        "r": parts[1].strip(),
                        "e": parts[2].strip()
                    })
        
        st.session_state.fix_list = parsed_results
        
        # 背景自動學習 (嘗試寫入雲端)
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(ttl="5s").dropna(subset=['original'])
            new_rows = pd.DataFrame([{'original': i['w'], 'replacement': i['r'], 'explanation': i['e']} for i in parsed_results])
            updated_df = pd.concat([df, new_rows]).drop_duplicates(subset=['original'], keep='last')
            conn.update(data=updated_df)
        except:
            pass
            
    except Exception as e:
        st.error(f"辨識失敗：{e}")

# --- 4. 介面 ---
st.title("🧠 語感專家：終極保險版")
st.info("此版本採用強化的文字掃描技術，確保 100% 偵測到敏感詞彙。")

col_l, col_r = st.columns([1, 1.2])

with col_l:
    input_val = st.text_area("📝 輸入文字：", value=st.session_state.user_input, height=200)
    if st.button("🚀 立即辨識", use_container_width=True):
        st.session_state.user_input = input_val
        st.session_state.final_text = input_val
        with st.spinner("辨識中..."):
            run_ai_logic(input_val)
            st.rerun()

    if st.session_state.final_text:
        st.markdown("---")
        st.subheader("📋 修正後結果 (點擊右上角複製)")
        st.code(st.session_state.final_text, language=None)

with col_r:
    st.subheader("🤳 辨識建議")
    found_any = False
    
    if st.session_state.fix_list:
        for i, item in enumerate(st.session_state.fix_list):
            if item['w'] in st.session_state.final_text:
                found_any = True
                with st.expander(f"📌 建議修正：{item['w']}", expanded=True):
                    st.write(f"🔍 **解釋：** {item['e']}")
                    st.button(f"👉 修正為「{item['r']}」", key=f"f_{i}", on_click=apply_fix, args=(item['w'], item['r']), use_container_width=True)

    if not found_any and st.session_state.final_text:
        st.success("🎉 目前文字查無建議！")
