import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="語感專家：智慧同步版", page_icon="🧠", layout="wide")

# 初始化 Session 狀態，確保修正過程不閃退
if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

# 修正按鈕觸發的函式
def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)
    st.toast(f"✅ 已修正：{old_w} → {new_w}")

# --- 2. 核心 AI 辨識與雲端寫入邏輯 ---
def run_full_analysis(text):
    if not text.strip(): return
    
    # 手動保險規則：即便 AI 抽風，這三個詞也一定會偵測到
    fallback = [
        {"w": "視頻", "r": "影片", "e": "源自中國用語，台灣習慣稱為『影片』。"},
        {"w": "質量", "r": "品質", "e": "源自中國用語，台灣指物理量（如質量守恆），形容好壞時用『品質』。"},
        {"w": "優化", "r": "改善", "e": "源自中國用語，台灣多用『改善』、『提升』或『最佳化』。"}
    ]
    
    try:
        # AI 安全設定：關閉過濾器以確保穩定回傳
        safe_config = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safe_config)
        
        prompt = f"""你是一個台灣繁體中文語感專家。請找出文字中的中國大陸用語。
        文字內容："{text}"
        請嚴格按格式回傳：原詞|建議修正|解釋（解釋中『源自大陸』一律改為『源自中國』）"""
        
        response = model.generate_content(prompt)
        ai_results = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        ai_results.append({"w": parts[0].strip(), "r": parts[1].strip(), "e": parts[2].strip()})
        
        # 合併手動規則與 AI 結果，並移除重複項
        final_detected = list({item['w']: item for item in ([r for r in fallback if r['w'] in text] + ai_results)}.values())
        st.session_state.res_list = final_detected
        
        # --- 💥 雲端同步學習 (利用 Service Account) 💥 ---
        if final_detected:
            try:
                # 使用 secrets 中的 [connections.gsheets] 設定連線
                conn = st.connection("gsheets", type=GSheetsConnection)
                # ttl=0 確保讀取最新資料，不使用快取
                existing_df = conn.read(ttl=0).dropna(subset=['original'])
                
                # 準備要同步的新資料
                sync_df = pd.DataFrame([
                    {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': '智慧學習', 'suggestion': i['r']} 
                    for i in final_detected
                ])
                
                # 合併新舊資料，若原詞相同則以新的為主
                updated_df = pd.concat([existing_df, sync_df]).drop_duplicates(subset=['original'], keep='last')
                
                # 執行更新命令
                conn.update(data=updated_df)
                st.success(f"✅ AI 發現了 {len(final_detected)} 個詞彙，已自動同步至雲端百科！")
            except Exception as sheet_err:
                st.warning(f"⚠️ 辨識成功，但雲端同步失敗（請檢查 Secrets 或權限）：{sheet_err}")

    except Exception as e:
        st.error(f"AI 辨識服務暫時中斷：{e}")
        st.session_state.res_list = [r for r in fallback if r['w'] in text]

# --- 3. 介面排版 ---
st.title("🧠 語感專家：智慧同步學習版")
st.markdown("輸入文字後，AI 會自動辨識中國用語，並將新發現的詞彙**永久存入**雲端資料庫。")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📝 原始文字")
    # key="main_input" 確保輸入框獨立
    raw_input = st.text_area("請在此輸入欲檢查的段落：", height=250, key="main_input")
    
    if st.button("🚀 開始分析並同步", use_container_width=True):
        st.session_state.f_text = raw_input
        with st.spinner("AI 正在學習並同步雲端..."):
            run_full_analysis(raw_input)
            st.rerun()

    if st.session_state.f_text:
        st.markdown("---")
        st.subheader("📋 修正後結果")
        # 顯示修正後的文字內容
        st.code(st.session_state.f_text, language=None)

with col_right:
    st.subheader("🤳 智慧辨識建議")
    
    found_item = False
    for i, item in enumerate(st.session_state.res_list):
        # 只有當該詞還存在於修正後的文字中時才顯示卡片
        if item['w'] in st.session_state.f_text:
            found_item = True
            with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {item['e']}")
                st.button(
                    f"👉 修正為「{item['r']}」", 
                    key=f"fix_{i}", 
                    on_click=do_fix, 
                    args=(item['w'], item['r']), 
                    use_container_width=True
                )
    
    if not found_item and st.session_state.f_text:
        st.success("🎉 太棒了！文字中沒有發現需要修正的用語。")
