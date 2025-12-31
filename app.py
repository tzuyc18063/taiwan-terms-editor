import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd
import json
import re

# --- 1. 初始化與頁面設定 ---
st.set_page_config(page_title="語感專家：終極精進版", page_icon="🧠", layout="wide")

# 設置 Google AI
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Secrets 中設定 GOOGLE_API_KEY")

# 初始化連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 狀態管理 ---
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""
if 'ai_detected' not in st.session_state:
    st.session_state.ai_detected = []

# 💡 關鍵修正：修正動作只影響 final_result，不影響 user_text
def apply_correction(old, new):
    st.session_state.final_result = st.session_state.final_result.replace(old, new)
    st.toast(f"✅ 已將「{old}」修正為「{new}」")

# --- 3. 核心邏輯：AI 辨識與自動學習 ---
def run_analysis(text):
    if not text.strip(): return
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    任務：辨識文字中不符合台灣習慣的中國用語（如：質量、優化、軟件、視頻、內卷）。
    輸入："{text}"
    要求：
    1. 以 JSON 列表格式回傳。
    2. 解釋內容必須將『源自大陸』一律寫成『源自中國』。
    格式：[ {{"original": "原詞", "replacement": "台灣建議", "title": "百科標題", "explanation": "解釋", "suggestion": "建議"}} ]
    """
    
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            new_data = json.loads(match.group(0))
            st.session_state.ai_detected = new_data
            
            # 自動同步到雲端
            try:
                existing_df = conn.read(ttl="1h").dropna(subset=['original'])
                new_df = pd.DataFrame(new_data)
                updated_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['original'], keep='last')
                conn.update(data=updated_df)
            except:
                pass 
    except Exception as e:
        st.error(f"AI 辨識發生錯誤：{e}")

# --- 4. 介面呈現 ---
st.title("🧠 語感專家：終極精進版")
st.caption("AI 自動學習與雲端記憶。修正僅會影響下方結果，保留上方原始輸入供參考。")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 文字輸入")
    # 上方輸入框：固定對應 user_text
    u_input = st.text_area("請輸入內容：", height=250, key="user_text", placeholder="例如：這段視頻的質量需要優化。")
    
    if st.button("🚀 啟動 AI 智慧辨識", use_container_width=True):
        st.session_state.final_result = u_input # 初始化結果為原始文字
        with st.spinner("AI 正在分析語感..."):
            run_analysis(u_input)
            st.rerun()

    if st.session_state.final_result:
        st.markdown("---")
        st.subheader("📋 修正後結果 (點擊右上角複製)")
        # 下方結果區：顯示修正後的 final_result
        st.code(st.session_state.final_result, language=None)
        
        if st.button("🧹 清空所有內容", type="secondary"):
            st.session_state.user_text = ""
            st.session_state.final_result = ""
            st.session_state.ai_detected = []
            st.rerun()

with col_res:
    st.subheader("🤳 智慧辨識與修正建議")
    
    display_cards = []
    seen = set()
    
    # 使用 final_result 作為偵測基準，確保修正後卡片會消失
    current_check_text = st.session_state.final_result
    
    # 1. 本次 AI 抓到的
    for item in st.session_state.ai_detected:
        if item['original'] in current_check_text:
            display_cards.append(item)
            seen.add(item['original'])
    
    # 2. 雲端資料庫有的 
    try:
        db_df = conn.read(ttl="10s").dropna(subset=['original'])
        for _, row in db_df.iterrows():
            word = str(row['original'])
            if word in current_check_text and word not in seen:
                display_cards.append(row.to_dict())
                seen.add(word)
    except:
        pass

    if display_cards:
        for i, card in enumerate(display_cards):
            with st.expander(f"📌 發現詞彙：{card['original']}", expanded=True):
                st.markdown(f"### {card.get('title', '語感建議')}")
                # 強制替換「源自大陸」為「源自中國」 
                exp = str(card.get('explanation', '')).replace("源自大陸", "源自中國")
                st.write(f"🔍 **解釋：** {exp}")
                
                st.button(
                    f"👉 修正為「{card['replacement']}」", 
                    key=f"fix_{i}_{card['original']}",
                    on_click=apply_correction,
                    args=(card['original'], str(card['replacement'])),
                    use_container_width=True
                )
    else:
        if st.session_state.final_result:
            st.success("🎉 目前結果中查無非在地用語！")
