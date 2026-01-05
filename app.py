import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # 【修正點】改用最穩定的模型名稱格式，並增加容錯處理
    # 這裡直接指定 'gemini-1.5-flash' 
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ 系統提示：金鑰或模型初始化失敗。錯誤訊息：{e}")
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
    st.toast("✅ 已套用所有在地化建議")
    st.session_state.final_results = []

# --- 2. AI 分析邏輯 (強化指令) ---
def ai_data_analyze(text):
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請分析以下文字，找出不符合台灣在地習慣的詞彙（包含大陸用語、流行語等）。
    
    待分析文字："{text}"
    
    請務必嚴格以 JSON 陣列格式回傳，若無建議則回傳 []。
    格式：
    [
      {{
        "original": "原詞彙",
        "taiwan": "台灣在地建議",
        "reason": "調整建議說明",
        "example": "台灣道地範例"
      }}
    ]
    """
    try:
        # 增加安全調用機制
        response = model.generate_content(prompt)
        # 確保抓取到 JSON 內容
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        # 若模型調用失敗，顯示更詳細的提示
        st.error(f"分析時發生錯誤，請稍後再試。原因：{str(e)}")
        return []

# --- 3. 使用者介面 ---
st.title("📱 語感守護者")
st.markdown("#### 運用 AI 技術，讓您的文字更貼近台灣在地的表達習慣")

c1, c2 = st.columns([1, 1.2])

with c1:
    with st.container():
        st.subheader("📝 輸入內容")
        u_input = st.text_area("請輸入文字：", height=250, 
                               value="這個套路真的很火，視頻質量牛逼，需要優化一下。", key="u_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行語感掃描", use_container_width=True):
                with st.spinner("語感顧問正在分析中..."):
                    st.session_state.current_text = u_input
                    # 重新整理結果
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

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 經過檢查，文字語感非常符合台灣在地習慣。")
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
        st.write("等待掃描結果...")
