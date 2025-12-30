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

# --- 2. 智慧模型偵測（避開 2.0 實驗版以免 429） ---
@st.cache_resource
def get_stable_model():
    try:
        # 取得所有可用模型清單
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：1.5-flash (最穩定且額度高) -> 1.5-pro -> 其他
        # 故意不放 2.0-flash-exp 以免一直被鎖
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'gemini-1.5-flash']
        
        for target in priority:
            if target in model_list:
                return genai.GenerativeModel(target)
        
        if model_list:
            return genai.GenerativeModel(model_list[0])
    except Exception as e:
        st.error(f"連線失敗: {e}")
    return None

model = get_stable_model()

# --- 3. 標註邏輯 ---
def ai_tagging(text):
    if not model:
        return "❌ 找不到可用模型"
    
    p = f"你是一位台灣繁體中文編輯。找出大陸用語或支式文法（如：噁心我、有被驚訝到），將其轉為道地台灣說法。改動處必須使用 [台灣用語](原始語) 格式輸出。文字：{text}"
    
    try:
        resp = model.generate_content(p)
        return re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', resp.text)
    except Exception as e:
        if "429" in str(e):
            return "⚠️ **額度暫時用完**：請等待 1 分鐘後再試。這是因為 Google 免費版的頻率限制。"
        return f"發生錯誤: {e}"

# --- 4. 介面 ---
st.title("🇹🇼 台灣用語 AI 智慧標註")
if model:
    st.caption(f"✅ 當前使用穩定模型: {model.model_name}")

user_input = st.text_area("📝 輸入文字：", height=200, placeholder="例如：這視頻質量特好，你不要噁心我...")

if st.button("🚀 執行 AI 分析", use_container_width=True):
    if user_input:
        with st.spinner('AI 正在分析中...'):
            res = ai_tagging(user_input)
            st.markdown(res)
    else:
        st.warning("請先輸入文字")

st.divider()
st.info("💡 如果出現 429 錯誤，是正常現象。請稍等 60 秒讓 Google 的免費配額重置。")
