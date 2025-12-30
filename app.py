import streamlit as st
import google.generativeai as genai
import re

# --- 1. 設定與 AI 初始化 ---
st.set_page_config(page_title="台灣用語 AI 智慧標註", page_icon="🇹🇼", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

@st.cache_resource
def get_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((t for t in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro'] if t in available), available[0])
        return genai.GenerativeModel(target)
    except: return None

model = get_model()

# --- 2. 標註邏輯 ---
def ai_tagging(text):
    if not model: return "AI 未連線"
    p = f"你是一位台灣繁體中文編輯。找出大陸用語或支式文法（如：噁心我、有被驚訝到），將其轉為道地台灣說法。改動處必須使用 [台灣用語](原始語) 格式輸出。文字：{text}"
    try:
        resp = model.generate_content(p)
        # 轉換標籤格式
        return re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', resp.text)
    except Exception as e: return f"錯誤: {e}"

# --- 3. 介面設計 ---
st.sidebar.title("⚙️ 設定面板")
if model: st.sidebar.success(f"✅ AI 已連線 ({model.model_name})")
else: st.sidebar.error("❌ AI 未連線")

st.title("🇹🇼 台灣用語 AI 智慧標註")
st.markdown("---")

user_input = st.text_area("📝 輸入文字：", height=200, placeholder="例如：這視頻質量特好，你不要噁心我...")

if st.button("🚀 執行 AI 智慧分析", use_container_width=True):
    if user_input:
        with st.spinner('AI 正在分析...'):
            res = ai_tagging(user_input)
            st.subheader("✨ 智慧標註結果")
            st.markdown(res)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📋 純淨版")
                # 移除所有標記格式，只保留轉換後文字
                clean = re.sub(r' :red-background\[(.*?)\((.*?)\)\] ', r'\1', res)
                st.code(clean, language=None)
            with c2:
                st.subheader("🔍 修正細節")
                matches = re.findall(r'\[(.*?)\]\((.*?)\)', res.replace(' :red-background', ''))
                for n, o in matches: st.write(f"❌ `{o}` → ✅ `{n}`")
    else: st.warning("請輸入內容")

st.divider()
st.caption("AI 技術支援：Gemini 智慧識別系統")
