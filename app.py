import streamlit as st
import google.generativeai as genai

# 1. API 設定 (請確保你在 Streamlit Cloud 的 Secrets 有設定 GOOGLE_API_KEY)
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

# 3. 簡單網頁介面
st.title("🇹🇼 台灣用語轉換器")

user_input = st.text_area("在此輸入文字：", height=200)

if st.button("🚀 開始轉換"):
    if user_input:
        # 顯示詞庫結果
        st.subheader("📍 詞庫快速標註")
        st.markdown(get_conversion(user_input))
        
        # 顯示 AI 結果
        try:
            st.divider()
            st.subheader("🤖 AI 深度潤飾")
            model = genai.GenerativeModel('gemini-1.5-flash')
            ai_res = model.generate_content(f"將此大陸用語轉為道地台灣說法：{user_input}")
            st.success(ai_res.text)
        except Exception as e:
            st.error(f"AI 連線失敗: {e}")
    else:
        st.warning("請先輸入文字")
