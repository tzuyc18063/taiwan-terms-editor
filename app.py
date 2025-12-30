import streamlit as st
import google.generativeai as genai

# 1. API 設定 (確保 Streamlit Secrets 已填入 GOOGLE_API_KEY)
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的金鑰"

genai.configure(api_key=API_KEY)

# 2. 轉換函數
def get_conversion(text):
    dct = {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害",
        "很火": "很紅", "水平": "水準", "估計": "大概", "立馬": "立刻",
        "有被": "被", "親們": "大家", "特好": "很好"
    }
    res = text
    for k in sorted(dct.keys(), key=len, reverse=True):
        if k in res:
            res = res.replace(k, f" :red-background[{dct[k]}({k})] ")
    return res

# 3. 網頁介面設計
st.set_page_config(page_title="台灣用語轉換器", layout="wide")
st.title("🇹🇼 智慧型台灣用語編輯器")

user_input = st.text_area("請輸入內容：", height=250, placeholder="例如：這視頻真的很火...")

if st.button("🚀 執行轉換"):
    if user_input:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 詞庫快速標註")
            st.markdown(get_conversion(user_input))
        
        with col2:
            st.subheader("🤖 AI 深度潤飾")
            try:
                # 修正模型名稱路徑
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                ai_res = model.generate_content(f"將此大陸用語轉為道地台灣說法：{user_input}")
                st.success(ai_res.text)
            except Exception as e:
                # 如果 flash 失敗，嘗試使用 pro 版本
                try:
                    model = genai.GenerativeModel('models/gemini-pro')
                    ai_res = model.generate_content(f"將此大陸用語轉為道地台灣說法：{user_input}")
                    st.success(ai_res.text)
                except:
                    st.error(f"AI 連線失敗。請確認 API Key 是否有效。錯誤訊息: {e}")
    else:
        st.warning("請先輸入文字")
