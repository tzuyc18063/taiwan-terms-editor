import streamlit as st
import google.generativeai as genai
import re

# --- 1. 配置與 AI 初始化 ---
st.set_page_config(page_title="互動式標註實驗室", page_icon="🖱️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# --- 2. 核心邏輯：解析標籤為互動清單 ---
def get_ai_suggestions(text):
    prompt = f"你是台灣編輯，修正大陸用語或文法。改動處用 [台灣用語](原詞) 格式。不要解釋。文字：{text}"
    try:
        response = model.generate_content(prompt)
        # 找出所有 [新](舊) 的匹配
        matches = re.findall(r'\[(.*?)\]\((.*?)\)', response.text)
        return matches, response.text
    except:
        return [], "AI 暫時繁忙"

# --- 3. UI 佈局 ---
st.title("🖱️ 特定詞彙互動修改模擬")
st.markdown("模擬 App 的**「精準修正」**模式：不強迫全改，只改你點選的部分。")

col_input, col_mobile = st.columns([1, 1])

with col_input:
    st.subheader("📝 原始文字")
    u_input = st.text_area("輸入模擬剪貼簿文字：", height=150, value="這視頻質量特好，有被驚訝到，你不要噁心我。")
    if st.button("🚀 開始偵測", use_container_width=True):
        st.session_state.suggestions, st.session_state.raw_ai = get_ai_suggestions(u_input)
        st.session_state.current_text = u_input

with col_mobile:
    st.subheader("🤳 互動手機預覽")
    
    # 手機外殼 CSS
    st.markdown("""
    <style>
    .mobile-screen {
        border: 12px solid #333; border-radius: 30px; width: 300px; height: 500px;
        margin: auto; padding: 20px; background: #fff; overflow-y: auto;
    }
    .suggestion-box {
        background: #fdf2f2; border: 1px solid #ffcfcf;
        border-radius: 10px; padding: 10px; margin-bottom: 10px;
        cursor: pointer; transition: 0.3s;
    }
    .suggestion-box:hover { background: #ffebeb; }
    .tag-old { color: #888; text-decoration: line-through; font-size: 0.8em; }
    .tag-new { color: #ff4b4b; font-weight: bold; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mobile-screen">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.8em; color:#666; margin-bottom:15px;">點擊你想套用的修正建議：</div>', unsafe_allow_html=True)

    if 'suggestions' in st.session_state and st.session_state.suggestions:
        # 建立一個模擬的互動清單
        for i, (new, old) in enumerate(st.session_state.suggestions):
            if st.button(f"替換「{old}」→「{new}」", key=f"sug_{i}"):
                # 執行單個替換
                st.session_state.current_text = st.session_state.current_text.replace(old, new)
                st.toast(f"已更新：{new}")
        
        st.divider()
        st.markdown("**目前預覽：**")
        st.write(st.session_state.current_text)
        
        if st.button("📋 複製最終結果", use_container_width=True):
            st.success("已模擬複製到剪貼簿！")
    else:
        st.markdown('<div style="text-align:center; margin-top:100px; color:#ccc;">等待偵測...</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 開發者筆記 ---
st.divider()
with st.expander("💡 為什麼要這樣設計？"):
    st.write("""
    1. **避免誤殺**：有些詞在特定語境下不需要改（例如討論大陸劇時保留原詞），給用戶選擇權。
    2. **教育意義**：用戶點擊的過程，也是在學習「喔，原來這叫支式文法」。
    3. **App 實現**：在 Android 中，這可以做成一個底部彈出視窗 (Bottom Sheet)，讓用戶勾選。
    """)
