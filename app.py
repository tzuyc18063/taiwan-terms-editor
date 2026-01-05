import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 核心初始化 ---
def initialize_model():
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"❌ 系統連結失敗：{str(e)}")
        return None

model = initialize_model()

# --- 3. 狀態管理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已更新：{old} ➔ {target_new}")

# --- 4. 強化分析邏輯：禁用「大陸」稱呼、強調詞彙並非獨有 ---
def ai_data_analyze(text):
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請深度分析以下文字中不符合台灣在地口語習慣的詞彙（包含中國用語、流行語、新興動詞等）。
    
    待分析文字："{text}"
    
    【重要指令】：
    1. 稱呼規範：在解釋理由時，一律嚴格使用「中國」一詞，禁止使用「大陸」。
    2. 語意精準度：若該詞彙並非中國獨有（台灣也有人使用），請在理由中明確說明「它並非中國獨有詞彙」，
       但要解釋為何在台灣語境下建議調整（例如：台灣有更道地的說法、語意在台灣容易產生誤解、或是使用頻率的差異）。
    3. 理由範例：「很火」在中國指受歡迎，但在台灣常指生氣；「噁心到我了」雖然在語法上可被理解，但台灣更常用「我覺得很噁心」。
    
    【回傳格式】：
    請嚴格以 JSON 陣列格式回傳：
    [
      {{
        "original": "原詞彙",
        "taiwan": "台灣建議",
        "reason": "深度語意對比說明 (須遵守上述指令)",
        "example": "台灣在地範例"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        st.error(f"⚠️ 分析異常：{str(e)}")
        return []

# --- 5. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 深度解析語意差異：精準辨析兩岸用法誤區")

c1, c2 = st.columns([1, 1.2])

with c1:
    u_input = st.text_area("請輸入文字：", height=250, 
                           value=st.session_state.current_text if st.session_state.current_text else "視頻質量很好，但他一直在背後蛐蛐我，這讓我很火。", 
                           key="u_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 執行深度分析", use_container_width=True):
            with st.spinner("語感顧問分析中..."):
                st.session_state.current_text = u_input
                st.session_state.final_results = ai_data_analyze(u_input)
                st.session_state.is_analyzed = True
                st.rerun()

    with col2:
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
            st.success("✨ 文字目前符合台灣在地語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                for item in active_results:
                    st.session_state.current_text = st.session_state.current_text.replace(item['original'], item['taiwan'].split(' / ')[0])
                st.rerun()
                
            for item in active_results:
                with st.expander(f"📌 {item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **理由：** {item['reason']}")
                    st.caption(f"📖 **範例：** {item['example']}")
                    if st.button(f"套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.write("等待掃描結果...")
