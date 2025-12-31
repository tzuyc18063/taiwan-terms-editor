import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="秒開版語感實驗室", page_icon="⚡", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 初始化所有狀態，防止網頁重整後變數消失
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'local_suggestions' not in st.session_state:
    st.session_state.local_suggestions = []
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []

# --- 2. 本地快速詞庫 ---
LOCAL_DICT = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好", "合同": "合約",
    "信息": "訊息", "走心": "在意", "內存": "記憶體", "優化": "調整"
}

# --- 3. 智慧模型獲取 ---
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

# --- 4. 核心偵測函數 ---
def run_hybrid_detection():
    # 確保輸入框有文字
    text = st.session_state.user_input_box
    if not text:
        return

    # A. 本地詞庫偵測 (0秒反應)
    local_found = []
    for old, new in LOCAL_DICT.items():
        if old in text:
            local_found.append((new, old))
    
    st.session_state.local_suggestions = local_found
    st.session_state.current_text = text

    # B. AI 偵測 (需等待 2-3 秒)
    model = get_working_model()
    if model:
        prompt = f"你是台灣編輯，修正大陸用語或文法。改動處用 [台灣用語](原詞) 格式。不要解釋。文字：{text}"
        try:
            response = model.generate_content(prompt)
            ai_matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
            # 過濾重複，若詞庫已處理則 AI 不重複顯示
            st.session_state.ai_suggestions = [m for m in ai_matches if m[1] not in LOCAL_DICT]
        except Exception as e:
            st.session_state.ai_suggestions = []
            if "429" in str(e):
                st.warning("⚠️ AI 額度目前已滿，您可以先處理藍色的詞庫建議。")
    else:
        st.session_state.ai_suggestions = []

def apply_replacement(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已替換：{old} → {new}")

# --- 5. UI 佈局 ---
st.title("⚡ 語感實驗室：秒開加速版")

col_input, col_mobile = st.columns([1, 1])

with col_input:
    st.subheader("📝 原始文字")
    st.text_area("在此輸入內容：", height=150, 
                 value="這視頻質量特好，有被驚訝到，你不要噁心我。", 
                 key="user_input_box")
    st.button("🚀 執行雙重偵測", on_click=run_hybrid_detection, use_container_width=True)

with col_mobile:
    st.subheader("🤳 互動預覽 (App 模擬)")
    
    # 注入手機模擬 CSS
    st.markdown("""
    <style>
    .mobile-screen { border: 12px solid #333; border-radius: 30px; width: 300px; height: 500px; margin: auto; padding: 20px; background: #fff; overflow-y: auto; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mobile-screen">', unsafe_allow_html=True)
    
    has_any = False
    
    # 顯示本地藍色按鈕
    for i, (new, old) in enumerate(st.session_state.local_suggestions):
        if old in st.session_state.current_text:
            has_any = True
            st.button(f"📘 詞庫：{old}→{new}", key=f"loc_{i}", 
                      on_click=apply_replacement, args=(old, new), use_container_width=True)

    # 顯示 AI 紅色按鈕
    for i, (new, old) in enumerate(st.session_state.ai_suggestions):
        if old in st.session_state.current_text:
            has_any = True
            st.button(f"🤖 AI：{old}→{new}", key=f"ai_{i}", 
                      on_click=apply_replacement, args=(old, new), use_container_width=True)
    
    if has_any:
        st.divider()
        st.write("**目前預覽：**")
        st.info(st.session_state.current_text)
        if st.button("📋 複製最終結果", key="copy_btn"):
            st.success("已複製！")
    else:
        st.markdown('<div style="text-align:center; margin-top:150px; color:#ccc;">等待偵測內容...</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
