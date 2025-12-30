import streamlit as st
import google.generativeai as genai
import os

# --- 1. 配置與 AI 模型初始化 ---
# 優先讀取雲端 Secrets，若無則讀取本地字串
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰" # 僅供本地測試使用

genai.configure(api_key=API_KEY)

def init_gemini():
    try:
        # 自動偵測可用模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"AI 初始化失敗: {e}")
        return None

model = init_gemini()

# --- 2. 詞庫設定 (把你想轉換的詞都加在這裡) ---
def load_dictionary():
    return {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "計算機": "電腦",
        "優化": "最佳化", "支持": "支援", "屏幕": "螢幕", "公交": "公車",
        "水平": "水準", "立馬": "立刻", "特好": "很好", 
        "牛逼": "厲害", "牛逼的": "很強的", "很牛": "很強",
        "很火": "很紅", "火了": "紅了", "搞定": "處理好",
        "親們": "大家", "給力": "帶勁", "走起": "出發",
        "肯定": "一定", "估計": "大概", "合同": "合約",
        "驚訝到": "嚇一跳", "驚訝到了": "嚇了一跳", "有被": "被"
    }

# --- 3. 核心處理邏輯 ---

# 邏輯 A: 詞庫標註 (暴力替換版，保證成功)
def dictionary_process(text):
    current_dict = load_dictionary()
    result_text = text

    # 按詞彙長度排序（由長到短），避免「火」先被換掉導致「很火」失效
    sorted_keys = sorted(current_dict.keys(), key=len, reverse=True)

    for key in sorted_keys:
        if key in result_text:
            # 找到關鍵字，直接取代為紅底標籤
            replacement = f" :red-background[{current_dict[key]}({key})] "
            result_text = result_text.replace(key, replacement)
            
    return result_text

# 邏輯 B: AI 深度潤飾 (處理文法與語感)
def ai_process(text):
    prompt = f"""
    你是一位極度嚴謹的台灣繁體中文編輯。
    你的任務是將輸入文字中「所有的」中國大陸用語徹底轉換為台灣本土說法。
    
    特別要求：
    1. 「很火」轉換為「很紅」；「牛逼」轉換為「厲害」；「水平」轉換為「水準」。
    2. 修正支式文法（如：「有被...到」、「進行一個...的動作」）。
    3. 語氣要像道地的台灣人在 Dcard 或 PTT 上的發言，保持流暢自然。

    待處理文字：
    {text}
    """
    if model:
        response = model.generate_content(prompt)
        return response.text
    return "AI 模型尚未就緒"

# --- 4. 網頁介面設計 ---
st.set_page_config(page_title="台灣用語 AI 編輯器", page_icon="🇹🇼", layout="wide")

st.sidebar.title("⚙️ 功能設定")
if model:
    st.sidebar.success(f"✅ AI 狀態：已連接 ({model.model_name})")

mode = st.sidebar.selectbox("請選擇轉換深度", ["詞庫快速標註", "AI 深度潤飾 (含文法)"])
st.sidebar.divider()
st.sidebar.info("💡 **詞庫標註**：直接比對詞庫並以紅底標出。\n\n💡 **AI 潤飾**：處理長篇文章與語氣修正。")

st.title("🇹🇼 智慧型台灣用語編輯器")
st.markdown("---")

col1, col2 = st.columns(2)

with col1: