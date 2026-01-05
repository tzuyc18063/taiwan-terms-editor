import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 您最滿意的初始化邏輯 (確保 AI 權限完整) ---
def initialize_model():
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
        
        # 動態尋找最適合的模型名稱
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        preferred_names = [
            'models/gemini-1.5-flash', 
            'models/gemini-pro'
        ]
        
        selected_model = None
        for name in preferred_names:
            if name in available_models:
                selected_model = name
                break
        
        if not selected_model:
            selected_model = available_models[0]
            
        return genai.GenerativeModel(selected_model)
    except Exception as e:
        st.error(f"❌ 系統連結失敗：{str(e)}")
        return None

model = initialize_model()

if not model:
    st.stop()

# --- 3. 狀態管理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已更新：{old} ➔ {target_new}")

# --- 4. 您最滿意的深度 AI 分析 (強化對比指令) ---
def ai_data_analyze(text):
    # 此指令能觸發 AI 進行兩岸語意對比 (如：很火 vs 生氣)
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請深度分析以下文字，找出不符合台灣在地習慣的詞彙（如大陸用語、流行語、蛐蛐等）。
    
    待分析文字："{text}"
    
    【回傳規範】：
    - 請嚴格以 JSON 陣列格式回傳。
    - 理由 (reason) 必須包含「兩岸語意對比」，例如解釋某詞在台灣是否會造成誤解。
    - 格式：
    [
      {{
        "original": "原詞彙",
        "taiwan": "台灣建議",
        "reason": "深度語意對比說明",
        "example": "台灣在地範例"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 精準抓取 JSON 區塊，避免雜訊導致空白
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        st.error(f"⚠️ 分析過程中發生異常：{str(e)}")
        return []

# --- 5. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 回歸 AI 深度模式：解析語意誤區與在地用法")

c1, c2 = st.columns([1, 1.2])

with c1:
    u_input = st.text_area("請輸入文字：", height=250, 
                           value=st.session_state.current_text if st.session_state.current_text else "這個套路真的很火，但他一直在背後蛐蛐我。", 
                           key="u_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 執行語感掃描", use_container_width=True):
            with st.spinner("語感顧問正在深度分析中..."):
                st.session_state.current_text = u_input
                st.session_state.final_results = ai_data_analyze(u_input)
                st.session_state.is_analyzed = True
                st.rerun() # 確保畫面立即更新

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
