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

# --- 2. 智慧模型偵測（解決 404） ---
@st.cache_resource
def get_safe_model():
    # 嘗試清單：有些版本需要 models/ 前綴，有些不需要
    model_names = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-pro',
        'models/gemini-pro'
    ]
    
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # 測試一下是否真的能跑
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except Exception:
            continue
    return None

model = get_safe_model()

# --- 3. 標註邏輯 (增加錯誤處理) ---
def ai_tagging(text):
    if not model:
        return "❌ 錯誤：找不到可用的 AI 模型，請檢查 API Key 是否有效。"
    
    p = f"你是一位台灣繁體中文編輯。找出大陸用語或支式文法（如：噁心我、有被驚訝到），將其轉為道地台灣說法。改動處必須使用 [台灣用語](原始語) 格式輸出。文字：{text}"
    
    try:
        resp = model.generate_content(p)
        # 正規表達式標註
        return re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', resp.text)
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            return "⚠️ **額度已滿**：請等待 30 秒後再點擊一次。"
        if "404" in err_msg:
            return "❌ **模型錯誤 (404)**：Google 暫時不支援此模型路徑，請嘗試重新整理網頁。"
        return f"發生未知錯誤: {e}"

# --- 4. 介面 ---
st.title("🇹🇼 台灣用語 AI 智慧標註")
st.caption(f"當前連線模型: {model.model_name if model else '未連線'}")

user_input = st.text_area("📝 輸入文字：", height=200, placeholder="例如：這視頻質量特好，你不要噁心我...")

if st.button("🚀 執行 AI 智慧分析", use_container_width=True):
    if user_input:
        with st.spinner('AI 正在嘗試多個通道連線中...'):
            res = ai_tagging(user_input)
            st.markdown(res)
            
            # 顯示純淨版方便複製
            if "red-background" in res:
                st.divider()
                clean = re.sub(r' :red-background\[(.*?)\((.*?)\)\] ', r'\1', res)
                st.subheader("📋 修正後全文字")
                st.code(clean, language=None)
    else:
        st.warning("請先輸入文字")
