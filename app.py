import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 初始化與模型選取邏輯 ---
def initialize_model():
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
        
        # 尋找目前 API KEY 支援的模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先選擇清單：按順序挑選最穩定的版本
        preferred_names = [
            'models/gemini-1.5-flash', 
            'models/gemini-pro',
            'models/gemini-1.0-pro'
        ]
        
        selected_model = None
        for name in preferred_names:
            if name in available_models:
                selected_model = name
                break
        
        if not selected_model:
            # 如果預設名單都沒對上，就選清單中的第一個
            selected_model = available_models[0]
            
        return genai.GenerativeModel(selected_model)
    except Exception as e:
        st.error(f"❌ 初始化失敗：{str(e)}")
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

# --- 4. 語感分析邏輯 ---
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
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        st.error(f"⚠️ 分析過程中發生異常，請確認 API 狀態。詳細訊息：{str(e)}")
        return []

# --- 5. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 運用 AI 技術，協助您的文字更貼近台灣在地的表達習慣")

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
            st.success("✨ 文字目前非常符合台灣在地的語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                for item in active_results:
                    apply_change(item['original'], item['taiwan'])
                st.rerun()
                
            st.warning(f"🔔 發現 {len(active_results)} 處建議調整的詞彙：")
            for item in active_results:
                with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **調整建議：** {item['reason']}")
                    st.caption(f"📖 **在地範例：** {item['example']}")
                    if st.button(f"套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.write("等待掃描結果...")
