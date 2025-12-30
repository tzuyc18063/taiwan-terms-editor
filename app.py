import streamlit as st
import google.generativeai as genai

# --- 1. 初始化與 API 設定 ---
st.set_page_config(page_title="台灣用語 AI 編輯器", page_icon="🇹🇼", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰" # 本地測試用

genai.configure(api_key=API_KEY)

# 核心：自動尋找可用模型的連線邏輯
def get_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available:
                return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

# --- 2. 詞庫轉換邏輯 ---
def get_conversion(text):
    dct = {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害",
        "很火": "很紅", "水平": "水準", "估計": "大概", "立馬": "立刻",
        "有被": "被", "親們": "大家", "特好": "很好", "搞定": "處理好",
        "合同": "合約", "肯定": "一定", "軟件": "軟體", "硬件": "硬體"
    }
    res = text
    for k in sorted(dct.keys(), key=len, reverse=True):
        if k in res:
            res = res.replace(k, f" :red-background[{dct[k]}({k})] ")
    return res

# --- 3. 介面佈局 ---
st.title("🇹🇼 智慧型台灣用語編輯器")
st.markdown("這是一款結合 **詞庫精準標註** 與 **AI 語意潤飾** 的專業轉換工具。")
st.divider()

# 側邊欄設定
st.sidebar.title("⚙️ 設定")
model = get_working_model()
if model:
    st.sidebar.success(f"✅ AI 狀態：已連線")
    st.sidebar.caption(f"使用模型：{model.model_name}")
else:
    st.sidebar.error("❌ AI 未連線")

mode = st.sidebar.radio("轉換模式", ["同時顯示 (推薦)", "僅詞庫標註", "僅 AI 潤飾"])

# 主輸入區
user_input = st.text_area("📝 請輸入要處理的文字：", height=250, placeholder="例如：這視頻的質量特好，我也立馬被驚訝到了...")

if st.button("🚀 執行轉換", use_container_width=True):
    if user_input:
        # 建立左右兩欄
        col1, col2 = st.columns(2)
        
        if mode in ["同時顯示 (推薦)", "僅詞庫標註"]:
            with col1:
                st.subheader("📍 詞庫標註 (快速)")
                st.info("根據台灣習慣用語詞庫進行標記。")
                st.markdown(get_conversion(user_input))
        
        if mode in ["同時顯示 (推薦)", "僅 AI 潤飾"]:
            with col2:
                st.subheader("🤖 AI 深度潤飾 (流暢)")
                st.info("修正支式文法，語氣轉換為道地台灣口語。")
                if model:
                    with st.spinner('AI 正在思考中...'):
                        try:
                            prompt = f"你是一位台灣繁體中文編輯。將以下文字的大陸用語徹底轉為台灣道地說法，修正文法並保持流暢：\n\n{user_input}"
                            ai_res = model.generate_content(prompt)
                            st.success(ai_res.text)
                        except Exception as e:
                            st.error(f"生成失敗：{e}")
                else:
                    st.warning("AI 模型不可用，請檢查 API Key。")
    else:
        st.warning("請輸入內容後再點擊轉換。")

st.divider()
st.caption("核心技術：Gemini AI + Python Streamlit | 您的專屬語言助手")
