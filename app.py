import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. 頁面配置與本地詞庫 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 建立本地備援詞庫 (即使 AI 掛掉也能運作)
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害",
    "立馬": "立刻", "特好": "很好", "優化": "調整"
}
# 本地歧義詞
LOCAL_AMBIGUOUS = {
    "土豆": {"choices": ["馬鈴薯", "花生"], "desc": "中國指馬鈴薯，台灣指花生"}
}

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# --- 2. 混合偵測邏輯 ---
def run_hybrid_analysis():
    text = st.session_state.u_input
    if not text: return
    
    st.session_state.current_text = text
    st.session_state.is_analyzed = True
    
    # 初始化 AI 結果
    st.session_state.ai_fix = []
    st.session_state.ai_options = []

    # 嘗試呼叫 AI
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"分析中國用語並回傳 JSON (fix: 直接換, options: 歧義)。文字：{text}"
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            st.session_state.ai_fix = data.get('fix', [])
            st.session_state.ai_options = data.get('options', [])
    except Exception as e:
        if "429" in str(e):
            st.warning("⚠️ AI 每日額度已滿，目前使用「本地詞庫」為您服務。")
        else:
            st.error("AI 暫時無法連線。")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已更新：{new}")

# --- 3. UI 介面 ---
st.title("📱 語感守護者：穩定版")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，我想吃點土豆。", key="u_input")
    st.button("🚀 執行偵測", on_click=run_hybrid_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 互動預覽")
    with st.container(border=True):
        if st.session_state.is_analyzed:
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("🔍 **建議修正：**")
                
                curr_text = st.session_state.current_text
                
                # A. 先跑本地歧義偵測 (例如：土豆)
                for old, info in LOCAL_AMBIGUOUS.items():
                    if old in curr_text:
                        st.warning(f"⚠️ 多義詞「{old}」")
                        cols = st.columns(len(info['choices']))
                        for i, choice in enumerate(info['choices']):
                            with cols[i]:
                                st.button(f"{choice}", key=f"loc_opt_{i}", on_click=apply_change, args=(old, choice), use_container_width=True)

                # B. 再跑本地固定詞庫 (例如：視頻)
                for old, new in LOCAL_DICT.items():
                    if old in curr_text:
                        st.button(f"📘 將「{old}」換成「{new}」", key=f"loc_fix_{old}", on_click=apply_change, args=(old, new), use_container_width=True)

        else:
            st.info("👋 請輸入文字後點擊偵測。")

if st.session_state.is_analyzed:
    st.button("📋 複製成果", use_container_width=True)
