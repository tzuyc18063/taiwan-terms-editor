import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感實驗室", page_icon="⚡", layout="wide")

# 取得 API KEY
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化 Session State
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state:
    st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []
if 'is_analyzed' not in st.session_state:
    st.session_state.is_analyzed = False

# --- 2. 本地詞庫 ---
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "在意", "內存": "記憶體", "優化": "調整"
}

# --- 3. 模型獲取 ---
@st.cache_resource
def get_working_model():
    try:
        # 修正第 40 行可能的截斷問題
        priority = ['models/gemini-1.5-flash', 'models/gemini-2.0-flash-exp']
        return genai.GenerativeModel(priority[0])
    except:
        return None

# --- 4. 偵測函數 ---
def run_hybrid_detection():
    text = st.session_state.user_input_box
    if not text:
        return

    # A. 詞庫偵測
    st.session_state.local_suggestions = [(v, k) for k, v in LOCAL_DICT.items() if k in text]
    st.session_state.current_text = text
    st.session_state.is_analyzed = True

    # B. AI 偵測
    model = get_working_model()
    if model:
        try:
            prompt = f"你是台灣編輯，修正大陸用語或文法。改動處用 [台灣用語](原詞) 格式。不要解釋。文字：{text}"
            response = model.generate_content(prompt)
            matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
            st.session_state.ai_suggestions = [m for m in matches if m[1] not in LOCAL_DICT]
        except Exception as e:
            st.session_state.ai_suggestions = []
            if "429" in str(e):
                st.warning("⚠️ AI 額度滿了，目前僅顯示詞庫建議。")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已替換：{old} → {new}")

# --- 5. UI 佈局 ---
st.title("⚡ 語感實驗室 (App 實境模擬版)")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📝 輸入區")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，有被驚訝到。", key="user_input_box")
    st.button("🚀 執行偵測", on_click=run_hybrid_detection, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.divider()
        st.info("**即時預覽：**\n\n" + st.session_state.current_text)

with col_right:
    st.subheader("🤳 手機預覽")
    with st.container(border=True):
        st.markdown("<div style='text-align:center; color:#888;'>📱 語感氣泡建議</div>", unsafe_allow_html=True)
        
        if st.session_state.is_analyzed:
            if st.session_state.local_suggestions:
                st.caption("📘 詞庫建議")
                for i, (new, old) in enumerate(st.session_state.local_suggestions):
                    if old in st.session_state.current_text:
                        st.button(f"「{old}」→「{new}」", key=f"loc_{i}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
            
            if st.session_state.ai_suggestions:
                st.caption("🤖 AI 語意建議")
                for i, (new, old) in enumerate(st.session_state.ai_suggestions):
                    if old in st.session_state.current_text:
                        st.button(f"「{old}」建議改為「{new}」", key=f"ai_{i}", 
                                  on_click=apply_change, args=(old, new), use_container_width=True)
        else:
            st.write("等待偵測內容...")

    if st.session_state.is_analyzed:
        if st.button("📋 複製最終結果", use_container_width=True):
            st.success("已模擬複製！")
