import streamlit as st
import google.generativeai as genai
import re

# --- 1. 初始化設定 ---
st.set_page_config(page_title="台灣用語 AI 智慧標註", page_icon="🇹🇼")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# --- 2. 暴力掃描可用模型 (解決 404/找不到模型問題) ---
@st.cache_resource
def get_any_working_model():
    try:
        # 直接從系統抓取你這把 Key 權限內的所有模型
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：2.0 Flash -> 1.5 Flash -> 1.5 Pro -> 隨便一個能動的
        priority = ['models/gemini-2.0-flash-exp', 'models/gemini-1.5-flash', 'models/gemini-1.5-pro']
        
        for target in priority:
            if target in model_list:
                m = genai.GenerativeModel(target)
                m.generate_content("test", generation_config={"max_output_tokens": 1})
                return m
        
        # 如果優先名單都沒有，就抓第一個可用的
        if model_list:
            m = genai.GenerativeModel(model_list[0])
            return m
    except Exception as e:
        st.error(f"掃描模型時發生錯誤: {e}")
    return None

model = get_any_working_model()

# --- 3. 標註邏輯 ---
def ai_tagging(text):
    if not model:
        return "❌ 錯誤：無法從您的 API Key 找到任何可用模型。請確認 API Key 是否填寫正確，或到 Google AI Studio 檢查狀態。"
    
    p = f"你是一位台灣繁體中文編輯。找出大陸用語或支式文法（如：噁心我、有被驚訝到），將其轉為道地台灣說法。改動處必須使用 [台灣用語](原始語) 格式輸出。文字：{text}"
    
    try:
        resp = model.generate_content(p)
        return re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', resp.text)
    except Exception as e:
        if "429" in str(e): return "⚠️ 額度已滿，請等待 30 秒。"
        return f"發生未知錯誤: {e}"

# --- 4. 介面 ---
st.title("🇹🇼 台灣用語 AI 智慧標註")
if model:
    st.caption(f"✅ 已自動匹配可用模型: {model.model_name}")
else:
    st.error("❌ 無法偵測到模型")

user_input = st.text_area("📝 輸入文字：", height=200, placeholder="例如：這視頻質量特好，你不要噁心我...")

if st.button("🚀 執行 AI 智慧分析", use_container_width=True):
    if user_input:
        with st.spinner('AI 正在思考中...'):
            res = ai_tagging(user_input)
            st.markdown(res)
            
            if "red-background" in res:
                st.divider()
                clean = re.sub(r' :red-background\[(.*?)\((.*?)\)\] ', r'\1', res)
                st.subheader("📋 修正後全文字")
                st.code(clean, language=None)
    else:
        st.warning("請先輸入文字")
