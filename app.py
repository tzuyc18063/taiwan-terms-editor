import streamlit as st
import google.generativeai as genai
import jieba
import os

# --- 1. 配置與 AI 模型初始化 ---
# 雲端部署後，程式會自動去 Secrets 找這把鑰匙
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # 這是為了讓你本地端測試還能動
    API_KEY = "你的正確金鑰" 

genai.configure(api_key=API_KEY)

# 移除快取，確保模型偵測是最即時的
def init_gemini():
    try:
        # 自動抓取該 API Key 權限下所有可用的模型
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("此 API Key 下找不到可用的生成模型，請檢查 Google AI Studio 設定。")
            return None
        
        # 優先順序：1.5-flash > 1.0-pro > 其他第一個可用模型
        if 'models/gemini-1.5-flash' in available_models:
            target = 'models/gemini-1.5-flash'
        elif 'models/gemini-pro' in available_models:
            target = 'models/gemini-pro'
        else:
            target = available_models[0]
            
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

# 初始化模型
model = init_gemini()

# --- 2. 詞庫設定 (把漏掉的詞補進去) ---
def load_dictionary():
    return {
        "視頻": "影片", "質量": "品質", "軟件": "軟體", "計算機": "電腦",
        "優化": "最佳化", "支持": "支援", "屏幕": "螢幕", "公交": "公車",
        "水平": "水準", "立馬": "立刻", "特好": "很好", 
        "牛逼": "厲害", "牛逼的": "很強的", "很牛": "很強",
        "肯定": "一定", "估計": "大概", "合同": "合約",
        "驚訝到": "嚇一跳", "驚訝到了": "嚇了一跳", "有被": "被",
        "很火": "很紅", "火了": "紅了", "搞定": "處理好",
        "親們": "大家", "給力": "給力/帶勁", "走起": "出發/開始"
    }

# --- 3. 核心處理邏輯 (確保強制加入詞庫) ---
def dictionary_process(text):
    current_dict = load_dictionary()
    
    # 關鍵：強制讓 jieba 優先識別這些詞，避免「很火」被切成「很」和「火」
    for key in current_dict.keys():
        jieba.add_word(key)
        
    words = jieba.cut(text)
    res = []
    for w in words:
        if w in current_dict:
            # 找到對應詞，紅底標註
            res.append(f":red-background[{current_dict[w]}({w})]")
        else:
            res.append(w)
    return "".join(res)

# --- 3. 核心處理邏輯 ---

# 邏輯 A: 詞庫標註
def dictionary_process(text):
    current_dict = load_dictionary()
    for key in current_dict.keys():
        jieba.add_word(key)
        
    words = jieba.cut(text)
    res = []
    for w in words:
        if w in current_dict:
            res.append(f":red-background[{current_dict[w]}({w})]")
        else:
            res.append(w)
    return "".join(res)

# 邏輯 B: AI 深度潤飾
def ai_process(text):
    prompt = f"""
    你是一位極度嚴謹的台灣繁體中文編輯。
    你的任務是將輸入文字中「所有的」中國大陸用語徹底轉換為台灣本土說法。
    
    特別要求：
    1. 「牛逼」必須轉換為「厲害」、「強」或「神」。
    2. 「水平」必須轉換為「水準」。
    3. 修正支式文法（如：「有被...到」、「進行一個...的動作」）。
    4. 語氣要像道地的台灣人在 Dcard 或 PTT 上的發言，保持流暢自然。

    待處理文字：
    {text}
    """
    if model:
        response = model.generate_content(prompt)
        return response.text
    return "模型未就緒"

# --- 4. 網頁介面設計 ---
st.set_page_config(page_title="台灣用語 AI 編輯器", page_icon="🇹🇼", layout="wide")

st.sidebar.title("⚙️ 功能設定")
if model:
    st.sidebar.success(f"已連接: {model.model_name}")

mode = st.sidebar.selectbox("請選擇轉換深度", ["詞庫快速標註", "AI 深度潤飾 (含文法)"])

st.title("🇹🇼 智慧型台灣用語編輯器")
st.markdown("---")

col1, col2 = st.columns(2)

# --- 注意這裡開始的縮進 ---
with col1:
    st.subheader("📝 原始文字")
    user_input = st.text_area("請輸入內容：", placeholder="例如：這水平肯定牛逼...", height=350)
    process_btn = st.button("🚀 執行轉換", use_container_width=True)

with col2:
    st.subheader("✨ 轉換結果")
    if process_btn and user_input:
        with st.spinner('處理中...'):
            if mode == "詞庫快速標註":
                result = dictionary_process(user_input)
                st.markdown(result)
            else:
                try:
                    result = ai_process(user_input)
                    st.success(result)
                except Exception as e:
                    st.error(f"AI 處理錯誤: {e}")
    else:

        st.info("請在左側輸入文字後點擊轉換按鈕。")
