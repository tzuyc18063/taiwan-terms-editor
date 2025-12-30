import streamlit as st
import google.generativeai as genai

# 1. API 設定
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 2. 自動偵測模型 (核心修正：解決 404)
def get_working_model():
    try:
        # 抓取目前帳號所有可用模型
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 優先找 flash，找不到就找 pro，再找不到就隨便選第一個
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available:
                return genai.GenerativeModel(target)
        if available:
            return genai.GenerativeModel(available[0])
    except:
        pass
    return None

# 3. 轉換函數
def get_conversion(text):
    dct = {"視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害", "很火": "很紅", "水平": "水準"}
    res = text
    for k in sorted(dct.keys(), key=len, reverse=True):
        if k in res:
            res = res.replace(k, f" :red-background[{dct[k]}({k})] ")
    return res

# 4. 介面
st.set_page_config(page_title="台灣用語轉換器")
st.title("🇹🇼 智慧型台灣用語編輯器")

user_input = st.text_area("請輸入內容：", height=200)

if st.button("🚀 執行轉換"):
    if user_input:
        # A. 詞庫標註
        st.subheader("📍 詞庫快速標註")
        st.markdown(get_conversion(user_input))
        
        # B. AI 深度潤飾
        st.divider()
        st.subheader("🤖 AI 深度潤飾")
        model = get_working_model()
        if model:
            try:
                ai_res = model.generate_content(f"將此大陸用語轉為道地台灣說法：{user_input}")
                st.success(ai_res.text)
                st.info(f"當前使用模型：{model.model_name}")
            except Exception as e:
                st.error(f"生成失敗：{e}")
        else:
            st.error("找不到可用的 Gemini 模型，請檢查 API Key 權限。")
