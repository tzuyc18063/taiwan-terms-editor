import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 穩定初始化 ---
def initialize_system():
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
            st.stop()
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash'
        if target not in available_models:
            target = available_models[0]
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"❌ 初始化失敗：{str(e)}")
        return None

model = initialize_system()

# --- 3. 狀態管理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已替換：{old} ➔ {target_new}")

# --- 4. 深度對比分析邏輯 ---
def ai_data_analyze(text):
    if not text.strip():
        return []
        
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請分析以下文字，找出不符合台灣在地習慣的詞彙（包含大陸用語、流行語、網路黑話如「蛐蛐」）。
    
    待分析文字："{text}"
    
    【回傳規範】：
    1. 請嚴格以 JSON 陣列格式回傳。
    2. 每個建議必須包含：
       - "original": 原詞彙
       - "taiwan": 台灣在地建議
       - "reason": 深度對比說明。請務必解釋該詞在兩岸語意上的差異或誤區。
         (例如：「很火」在大陸指受歡迎，但在台灣常指「很生氣」；「走心」在台灣有時指在意或鑽牛角尖。)
       - "example": 提供一個台灣道地的使用範例句。
    3. 若無建議則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[\s*{{.*}}\s*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception:
        return []

# --- 5. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 運用 AI 技術，深度解析兩岸語法差異與誤區")

c1, c2 = st.columns([1, 1.2])

with c1:
    with st.container():
        st.subheader("📝 輸入內容")
        u_input = st.text_area("請輸入文字：", height=250, 
                               value=st.session_state.current_text if st.session_state.current_text else "這個套路真的很火，但他一直在背後蛐蛐我。", 
                               key="text_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行深度掃描", use_container_width=True):
                if u_input:
                    with st.spinner("語感顧問正在分析語意誤區..."):
                        st.session_state.current_text = u_input
                        st.session_state.final_results = ai_data_analyze(u_input)
                        st.session_state.is_analyzed = True
                        st.rerun()
        
        with col_btn2:
            if st.button("🧹 重置編輯器", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.is_analyzed = False
                st.session_state.final_results = []
                st.rerun()

    if st.session_state.is_analyzed:
        st.write("---")
        st.subheader("📋 修正後的文字預覽")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("💡 語意對比建議")
    if st.session_state.is_analyzed:
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 文字目前非常符合台灣在地的語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                for item in active_results:
                    apply_change(item['original'], item['taiwan'])
                st.rerun()
                
            for item in active_results:
                with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **語意解析：** {item['reason']}")
                    st.caption(f"📖 **在地範例：** {item['example']}")
                    if st.button(f"套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.info("等待掃描結果，將為您解析語意差異。")
