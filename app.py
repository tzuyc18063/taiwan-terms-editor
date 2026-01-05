import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # 使用具備強大推理能力的模型
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("❌ 系統提示：請確認 API 金鑰設定是否正確。")
    st.stop()

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已更新：{old} ➔ {target_new}")

def apply_all_changes():
    for item in st.session_state.final_results:
        old = item['original']
        new = item['taiwan'].split(' / ')[0]
        if old in st.session_state.current_text:
            st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast("✅ 已套用所有建議，文字已在地化")
    st.session_state.final_results = []

# --- 2. 大數據 AI 分析邏輯 ---
def ai_data_analyze(text):
    # 這裡不再使用手動清單，全權交由 AI 根據大數據判斷
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請運用你背後的大數據與語言模型知識，分析以下文字。
    
    【任務目標】：
    1. 找出文字中「不符合台灣道地用法」的詞彙（包括大陸用語、公文式用語、或非在地習慣的流行語）。
    2. 提供台灣最自然的替代詞。
    3. 說明為什麼這在台灣不自然（請用溫和、專業的口吻）。
    
    【待分析文字】："{text}"
    
    【回傳規範】：
    - 請嚴格以 JSON 陣列格式回傳。
    - 若文字已經非常符合台灣在地語感，請回傳 []。
    - 格式範例：
    [
      {{
        "original": "原詞彙",
        "taiwan": "台灣在地建議",
        "reason": "調整建議（請說明語感差異，禁用大陸術語）",
        "example": "台灣在地範例"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 清洗 JSON 資料
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        st.error(f"分析時發生錯誤：{e}")
        return []

# --- 3. 使用者介面 ---
st.title("📱 語感守護者：大數據自動偵測")
st.markdown("#### 運用 AI 技術，讓您的文字更貼近台灣在地的表達習慣")

c1, c2 = st.columns([1, 1.2])

with c1:
    with st.container():
        st.subheader("📝 輸入內容")
        u_input = st.text_area("請在此輸入文字（AI 會自動偵測）：", height=250, 
                               value="這個套路真的很火，視頻質量牛逼，需要優化一下。", key="u_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行大數據掃描", use_container_width=True):
                with st.spinner("語感顧問正在分析大數據..."):
                    st.session_state.current_text = u_input
                    st.session_state.final_results = ai_data_analyze(u_input)
                    st.session_state.is_analyzed = True
        
        with col_btn2:
            if st.button("🧹 重置編輯器", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.is_analyzed = False
                st.session_state.final_results = []
                st.rerun()

    if st.session_state.is_analyzed:
        st.write("---")
        st.subheader("📋 修正後的文字")
        st.code(st.session_state.current_text, language=None)
        st.caption("💡 提示：點擊右上角即可複製文字。")

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 經過 AI 大數據檢查，這段文字非常符合台灣在地語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                apply_all_changes()
                st.rerun()
                
            st.warning(f"🔔 發現 {len(active_results)} 處建議調整的詞彙：")
            for item in active_results:
                with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **調整建議：** {item['reason']}")
                    st.caption(f"📖 **在地範例：** {item['example']}")
                    if st.button(f"套用此項：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.write("掃描完成後，建議調整資訊會顯示於此。")
