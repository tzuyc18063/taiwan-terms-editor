import streamlit as st
import google.generativeai as genai
import re
import time

st.set_page_config(page_title="台灣用語 AI 智慧標註", page_icon="🇹🇼")

# 設定 API
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 固定模型版本，提高穩定性
@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

def ai_tagging(text):
    p = f"你是一位台灣繁體中文編輯。找出大陸用語或支式文法（如：噁心我、有被驚訝到），將其轉為道地台灣說法。改動處必須使用 [台灣用語](原始語) 格式輸出。文字：{text}"
    try:
        resp = model.generate_content(p)
        return re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', resp.text)
    except Exception as e:
        # 針對 429 錯誤提供中文說明
        if "429" in str(e):
            return "⚠️ **系統提示**：請求太過頻繁，請等待約 30 秒後再試一次。"
        return f"錯誤: {e}"

st.title("🇹🇼 台灣用語 AI 智慧標註")
user_input = st.text_area("📝 輸入文字：", height=200)

if st.button("🚀 執行分析"):
    if user_input:
        with st.spinner('AI 分析中...'):
            res = ai_tagging(user_input)
            st.markdown(res)
    else:
        st.warning("請輸入內容")
