import streamlit as st
import google.generativeai as genai
import re

# --- 1. 初始化設定 ---
st.set_page_config(page_title="台灣用語 AI 智慧標註", page_icon="🇹🇼", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

def get_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available:
                return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

# --- 2. 智慧標註核心邏輯 ---
def ai_smart_tagging(text):
    model = get_model()
    if not model:
        return "AI 連線失敗，請檢查 API Key。"
    
    prompt = f"""
    你是一位極度專業的台灣繁體中文編輯。
    請找出以下文字中的「中國大陸用語」或「不道地的支式文法」（例如：噁心我、有被驚訝到）。
    
    任務要求：
    1. 將其轉換為道地的台灣本土說法。
    2. 輸出時，凡是有改動的地方，必須使用 [台灣用語](大陸原始用語) 的格式呈現。
    3. 沒改動的地方保持原樣。
    4. 修正文法使其符合台灣口語習慣。

    待處理文字：{text}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text
        # 轉換為 Streamlit 紅底標籤
        final_output = re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', res_text)
        return final_output
    except Exception as e:
        return f"處理出錯：{e}"

# --- 3. 網頁介面 ---
st.title("🇹🇼 台灣用語 AI 智慧標註")
st.markdown("AI 自動偵測大陸用語與支式文法，並提供紅底標註建議。")
st.divider()

user_input = st.text_area("📝 請輸入文字：", height=200, placeholder="例如：這視頻質量特好，你不要噁心我。")

if st.button("🚀 開始 AI 智慧分析", use_container_width=True):
    if user_input:
        with st.spinner('AI 掃描語法中...'):
            result = ai_smart_tagging(user_input)
            st.subheader("✨ 分析結果")
            st.markdown(result)
            
            st.divider()
            with st.expander("查看純淨台灣版"):
                clean_text = re.sub(r' :red-background\[(.*?)\((.*?)\)\] ', r'\1', result)
                st.write(clean_text)
    else:
        st.warning("請先輸入文字")

st.divider()
st.caption("AI 驅動：支援文法與詞彙自動辨識")
