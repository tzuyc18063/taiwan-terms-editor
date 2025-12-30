import streamlit as st
import google.generativeai as genai

# --- 1. 配置與 AI 模型初始化 ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的金鑰"

genai.configure(api_key=API_KEY)

def init_gemini():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"AI 初始化失敗: {e}")
        return None

model = init_gemini()

# --- 2. 詞庫設定 ---
def load_dictionary():
    return {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "計算機": "電腦",
        "優化": "最佳化", "支持": "支援", "屏幕": "螢幕", "公交": "公車",
        "水平": "水準", "立馬": "立刻", "特好": "很好", 
        "牛逼": "厲害", "很火": "很紅", "火了": "紅了",
        "搞定": "處理好", "親們": "大家", "給力": "帶勁",
        "肯定": "一定", "驚訝到了": "嚇了一跳", "有被": "被"
    }

# --- 3. 核心處理邏輯 ---
def dictionary_process(text):
    current_dict = load_dictionary()
    result_text = text
    sorted_keys = sorted(current_dict.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in result_text:
            replacement = f" :red-background[{current_dict[key]}({key})] "
            result_text = result_text.replace(key, replacement)
    return result_text

def ai_process(text):
    prompt = f"你是一位台灣繁體中文編輯。將以下文字的大陸用語轉換為台灣本土說法：\n\n{text}"
    if model:
        response = model.generate_content(prompt)
        return response.text
    return "AI 模型尚未就緒"

# --- 4. 網頁介面設計 ---
st.set_page_config(page_title="台灣用語 AI 編輯器", layout="wide")

st.title("🇹🇼 智慧型台灣用語編輯器")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 原始文字")
    user_input = st.text_area("內容：", height=300)
    process_btn = st.button("🚀 執行轉換")

with col2:
    st.subheader("✨ 轉換結果")
    if process_btn and user_input:
        mode = st.sidebar.selectbox("模式", ["詞庫快速標註", "AI 深度潤飾"])
        if mode == "詞庫快速標註":
            st.markdown(dictionary_process(user_input))
        else:
            st.success(ai_process(user_input))
