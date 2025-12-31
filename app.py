import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：全自動同步版", page_icon="🧠", layout="wide")

if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)
    st.toast(f"✅ 已修正：{old_w}")

# --- 2. 核心邏輯：辨識 + 寫入 ---
def power_analysis(text):
    if not text.strip(): return
    
    # 手動保險規則 (確保一定有東西能寫入)
    fallback_rules = [
        {"w": "視頻", "r": "影片", "e": "源自中國，台灣習慣稱為『影片』。"},
        {"w": "質量", "r": "品質", "e": "源自中國，台灣多指物理量，品質才指好壞。"},
        {"w": "優化", "r": "改善", "e": "源自中國，台灣多用『改善』、『提升』或『最佳化』。"}
    ]
    
    try:
        # AI 辨識
        safe = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safe)
        prompt = f'你是一個語感專家。找出文字中的中國用語。文字："{text}"。格式：原詞|建議|解釋（解釋中「源自大陸」改為「源自中國」）'
        
        response = model.generate_content(prompt)
        ai_results = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    p = line.split("|")
                    if len(p) >= 3:
                        ai_results.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        
        # 合併結果
        final_list = list({item['w']: item for item in ([r for r in fallback_rules if r['w'] in text] + ai_results)}.values())
        st.session_state.res_list = final_list
        
        # --- 💥 強制同步雲端 💥 ---
        if final_list:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # 1. 讀取目前的資料 (ttl=0 強制刷新)
            df = conn.read(ttl=0).dropna(subset=['original'])
            
            # 2. 建立新資料列
            new_rows = pd.DataFrame([
                {'original': i['w'], 'replacement': i['r'], 'title': '語感建議', 'explanation': i['e'], 'suggestion': i['r']} 
                for i in final_list
            ])
            
            # 3. 合併並移除重複原詞
            updated_df = pd.concat([df, new_rows]).drop_duplicates(subset=['original'], keep='last')
            
            # 4. 寫回 Google Sheets
            conn.update(data=updated_df)
            st.success(f"✅ 成功將 {len(final_list)} 個詞彙同步至雲端資料庫！")

    except Exception as e:
        st.error(f"同步過程中發生錯誤：{e}")
        st.session_state.res_list = [r for r in fallback_rules if r['w'] in text]

# --- 3. 介面 ---
st.title("🧠 語感專家：全自動同步版")

c1, c2 = st.columns([1, 1.2])

with c1:
    user_in = st.text_area("📝 輸入文字：", height=200, key="txt_in")
    if st.button("🚀 啟動辨識並更新資料庫", use_container_width=True):
        st.session_state.f_text = user_in
        power_analysis(user_in)
        st.rerun()

    if st.session_state.f_text:
        st.markdown("---")
        st.subheader("📋 修正結果")
        st.code(st.session_state.f_text, language=None)

with c2:
    st.subheader("🤳 辨識卡片")
    for i, item in enumerate(st.session_state.res_list):
        if item['w'] in st.session_state.f_text:
            with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {item['e']}")
                st.button(f"👉 修正為「{item['r']}」", key=f"btn_{i}", on_click=do_fix, args=(item['w'], item['r']), use_container_width=True)
