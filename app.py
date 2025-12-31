import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 頁面設定 ---
st.set_page_config(page_title="語感專家：同步除錯版", page_icon="🧠", layout="wide")

if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)
    st.toast(f"✅ 已修正：{old_w}")

# --- 2. 核心邏輯 ---
def run_full_analysis(text):
    if not text.strip(): return
    
    # 手動保險
    fallback = [
        {"w": "視頻", "r": "影片", "e": "源自中國用語，台灣習慣稱為『影片』。"},
        {"w": "質量", "r": "品質", "e": "源自中國用語，台灣指物理量，形容好壞時用『品質』。"},
        {"w": "優化", "r": "改善", "e": "源自中國用語，台灣多用『改善』、『提升』或『最佳化』。"}
    ]
    
    try:
        # AI 辨識
        safe_config = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safe_config)
        prompt = f'你是一個台灣語感專家。找出文字中的中國用語。文字："{text}"。格式：原詞|建議修正|解釋（解釋中「源自大陸」改為「源自中國」）'
        
        response = model.generate_content(prompt)
        ai_results = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        ai_results.append({"w": parts[0].strip(), "r": parts[1].strip(), "e": parts[2].strip()})
        
        # 合併偵測結果
        final_detected = list({item['w']: item for item in ([r for r in fallback if r['w'] in text] + ai_results)}.values())
        st.session_state.res_list = final_detected
        
        # --- 💥 雲端同步偵錯區 💥 ---
        if final_detected:
            try:
                # 建立連線
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # 讀取現有資料 (ttl=0 強制不使用緩存)
                existing_df = conn.read(ttl=0)
                
                # 準備新資料（確保欄位名稱與您的 Sheet 第一列完全一致）
                new_entries = []
                for i in final_detected:
                    new_entries.append({
                        'original': i['w'],
                        'replacement': i['r'],
                        'explanation': i['e'],
                        'title': '智慧學習',
                        'suggestion': i['r']
                    })
                sync_df = pd.DataFrame(new_entries)
                
                # 合併並去重
                if not existing_df.empty:
                    updated_df = pd.concat([existing_df, sync_df]).drop_duplicates(subset=['original'], keep='last')
                else:
                    updated_df = sync_df
                
                # 執行更新
                conn.update(data=updated_df)
                st.success(f"✅ 成功同步 {len(final_detected)} 個詞彙到雲端表單！")
                
            except Exception as sheet_err:
                # 如果寫入失敗，直接把原因噴出來
                st.error(f"❌ 雲端同步失敗！原因：{sheet_err}")
                st.info("💡 提示：請檢查 Secrets 裡的 private_key 格式是否包含換行符號 \\n，以及試算表是否已授權編輯給 Service Account。")

    except Exception as e:
        st.error(f"AI 服務異常：{e}")
        st.session_state.res_list = [r for r in fallback if r['w'] in text]

# --- 3. 介面 ---
st.title("🧠 語感專家：智慧同步除錯版")

col_l, col_r = st.columns([1, 1.2])

with col_l:
    u_input = st.text_area("📝 原始文字：", height=200, key="input_area")
    if st.button("🚀 啟動分析並強制同步", use_container_width=True):
        st.session_state.f_text = u_input
        with st.spinner("正在嘗試同步雲端..."):
            run_full_analysis(u_input)
            st.rerun()

    if st.session_state.f_text:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        st.code(st.session_state.f_text, language=None)

with col_r:
    st.subheader("🤳 辨識建議")
    found = False
    for i, item in enumerate(st.session_state.res_list):
        if item['w'] in st.session_state.f_text:
            found = True
            with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {item['e']}")
                st.button(f"👉 修正為「{item['r']}」", key=f"fix_{i}", on_click=do_fix, args=(item['w'], item['r']), use_container_width=True)
    
    if not found and st.session_state.f_text:
        st.success("🎉 目前無建議或已完成同步。")
