import streamlit as st
import google.generativeai as genai

# 1. API 設定
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的金鑰"

genai.configure(api_key=API_KEY)

# 2. 詞庫與邏輯
def translate_text(text):
    # 這就是你要的暴力替換詞庫
    dct = {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害",
        "很火": "很紅", "水平": "水準", "估計": "大概", "立馬": "立刻"
    }
    res = text
    # 按長度排序，避免短詞破壞長詞
    for k in sorted(dct.keys(), key=len, reverse=True):
        if k in res:
            res = res.replace(k, f" :red-background[{dct[k]}({k})] ")
    return res

# 3. 網頁介面
st.set_page_config(page_title="用語轉換器")
st.title("🇹🇼 台灣用語轉換器")

# 輸入區
user_input = st.text_area("請輸入文字：", height=200)
btn = st.button("🚀 開始轉換")

# 輸出區
if btn and user_input:
    st.subheader("轉換結果：")
    # 直接執行轉換並顯示
    result = translate_text(user_input)
    st.markdown(result)

    # 這裡順便跑一下 AI 潤飾作為對照
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_res = model.generate_content(f"將此大陸用語轉為台灣說法：{user_input}")
        st.divider()
        st.subheader("🤖 AI 深度潤飾：")
        st.write(ai_res.text)
    except:
        st.error("AI 暫時無法連線，僅顯示詞庫標註。")
