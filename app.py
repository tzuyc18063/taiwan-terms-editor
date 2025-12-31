import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 頁面設定 ---
st.set_page_config(page_title="語感專家：全自動同步版", page_icon="🧠", layout="wide")

if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)
    st.toast(f"✅ 已修正：{old_w}")

# --- 2. 核心邏輯：辨識 + 強制同步 ---
def power_analysis(text):
    if not text.strip(): return
    
    # 預設保險規則
    fallback_rules = [
        {"w": "視頻", "r": "影片", "e": "源自中國，台灣習慣稱為『影片』。"},
        {"w": "質量", "r": "品質", "e": "源自中國，台灣指物理量，品質才指好壞。"},
        {"w": "優化", "r": "改善", "e": "源自中國，台灣多用『改善』、『提升』或『最佳化』。"}
    ]
    manual_results = [r for r in fallback_rules if r['w'] in text]
    
    try:
        # AI 配置
        safe = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safe)
        prompt = f'找出文字中的中國用語（如：質量、視頻、優化）。文字："{text}"。格式：原詞|建議|解釋（解釋中「源自大陸」改為「源自中國」）'
        
        response = model.generate_content(prompt)
        ai_results = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    p = line.split("|")
                    if len(p) >= 3:
                        ai_results.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        
        # 合併結果
        st.session_state.res_list = list({item['w']: item for item in (manual_results + ai_results)}.values())
        
        # --- 💥 強制同步雲端 ---
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # 讀取現有資料
            existing_df = conn.read(ttl=0) # ttl=0 強制抓取最新資料
            
            # 準備新資料
            new_data = pd.DataFrame([
                {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': '語感建議', 'suggestion': i['r']} 
                for i in st.session_state.res_list
            ])
            
            # 合併並去重
            updated_df = pd.concat([existing_df, new_data]).drop_duplicates(subset=['original'], keep='last')
            
            # 執行更新
            conn.update(data=updated_df)
            st.success("✅ 雲端資料庫已同步更新！")
        except Exception as sheet_err:
            st.warning(f"⚠️ AI 辨識成功，但雲端寫入失敗。請檢查 Sheet 權限：{sheet_err}")

    except Exception as e:
        st.session_state.res_list = manual_results

# --- 3. 介面呈現 ---
st.title("🧠 語感專家：全自動同步版")

c1, c2 = st.columns([1, 1.2])

with c1:
    user_in = st.text_area("📝 輸入文字：", height=200, key="main_input_area")
    if st.button("🚀 啟動辨識與自動學習", use_container_width=True):
        st.session_state.f_text = user_in
        power_analysis(user_in)
        st.rerun()

    if st.session_state.f_text:
        st.markdown("---")
        st.subheader("📋 修正結果")
        st.code(st.session_state.f_text, language=None)

with c2:
    st.subheader("🤳 辨識卡片")
    found = False
    for i, item in enumerate(st.session_state.res_list):
        if item['w'] in st.session_state.f_text:
            found = True
            with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {item['e']}")
                st.button(f"👉 修正為「{item['r']}」", key=f"btn_{i}", on_click=do_fix, args=(item['w'], item['r']), use_container_width=True)
    
    if not found and st.session_state.f_text:
        st.success("🎉 暫無建議")
