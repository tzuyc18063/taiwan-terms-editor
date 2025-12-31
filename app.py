import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化所有狀態
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
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-2.0-flash-exp', 'models/gemini-1.5-flash', 'gemini-1.5-flash']
        for target in priority:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

# --- 4. 偵測函數 ---
def run_detection():
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
            if "429" in str(e): st.warning("AI 額度滿了，僅顯示詞庫建議。")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"已替換: {old} -> {new}")

# --- 5. UI ---
st.title("⚡ 語感實驗室 (穩定版)")

c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📝 輸入區")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，有被驚訝到。", key="user_input_box")
    st.button("🚀 執行偵測", on_click=run_detection, use_container_width=True)
    
    # 在輸入區下面也放一個預覽，確保數據有進去
    if st.session_state.is_analyzed:
        st.write("---")
        st.write("**當前處理文本：**")
        st.info(st.session_state.current_text)

with c2:
    st.subheader("🤳 手機預覽")
    # 手機殼容器
    st.markdown("""
    <style>
    .phone { border: 10px solid #333; border-radius: 25px; padding: 15px; height: 450px; background: white; overflow-y: auto; color: black; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="phone">', unsafe_allow_html=True)
    
    if st.session_state.is_analyzed:
        # 顯示詞庫建議
        for i, (new, old) in enumerate(st.session_state.local_suggestions):
            if old in st.session_state.current_text:
                st.button(f"📘 {old} -> {new}", key=f"l_{i}", on_click=apply_change, args=(old, new), use_container_width=True)
        
        # 顯示 AI 建議
        for i, (new, old) in enumerate(st.session_state.ai_suggestions):
            if old in st.session_state.current_text:
                st.button(f"🤖 {old} -> {new}", key=f"a_{i}", on_click=apply_change, args=(old, new), use_container_width=True)
        
        if not st.session_state.local_suggestions and not st.session_state.ai_suggestions:
            st.write("✅ 偵測完畢：文字看起來很道地！")
    else:
        st.write("👋 請在左側輸入文字後點擊偵測按鈕。")
    
    st.markdown('</div>', unsafe_allow_html=True)
