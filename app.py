import streamlit as st
import google.generativeai as genai
import re

# --- 1. 頁面配置 ---
st.set_page_config(
    page_title="台灣用語 AI 智慧標註編輯器",
    page_icon="🇹🇼",
    layout="wide"
)

# --- 2. AI 初始化與模型偵測 ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_ai_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available:
                return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

model = load_ai_model()

# --- 3. 核心標註邏輯 ---
def ai_smart_tagging(text):
    if not model:
        return "AI 連線失敗，請檢查 API Key。"
    
    prompt = f"""
    你是一位極度專業的台灣繁體中文編輯。
    請找出文字中的「中國大陸用語」或「不道地的支式文法」（例如：噁心我、有被驚訝到、進行一個動作）。
    
    任務要求：
    1. 將其轉換為道地的台灣本土說法。
    2. 輸出時，凡是有改動的地方，必須使用 [台灣用語](大陸原始用語) 的格式呈現。
    3. 沒改動的地方保持原樣。
    4. 修正文法使其符合台灣口語習慣（包含語氣助詞、動詞用法）。

    待處理文字：{text}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text
        # 正規表達式：將 [新詞](舊詞) 轉換為紅底標籤
        final_output = re.sub(r'\[(.*?)\]\((.*?)\)', r' :red-background[\1(\2)] ', res_text)
        return final_output
    except Exception as e:
        return f"處理出錯：{e}"

# --- 4. 介面設計 ---
st.sidebar.title("⚙️ 控制面板")
st.sidebar.info("本工具利用 AI 自動偵測並修正「大陸用語」與「支式文法」。")

if model:
    st.sidebar.success(f"✅ AI 模型已就緒\n({model.model_name})")
else:
    st.sidebar.error("❌ AI 未連線")

st.sidebar.divider()
st.sidebar.markdown("""
**測試範例：**
1. 這視頻質量特好。
2. 他這番話有被驚訝到。
3. 你不要噁心我。
""")

st.title("🇹🇼 台灣用語 AI 智慧標註編輯器")
st.markdown("---")

# 輸入區
user_input = st.text_area(
    "📝 請輸入要分析的內容：", 
    height=250, 
    placeholder="在此輸入文字，例如：這視頻真的很火，質量特好，有被驚訝到，你不要噁心我..."
)

if st.button("🚀 執行 AI 智慧掃描", use_container_width=True):
    if user_input:
        with st.spinner('AI 正在深度掃描語感與詞彙...'):
            result = ai_smart_tagging(user_input)
            
            # 結果顯示區
            st.subheader("✨ 智慧標註結果")
            st.markdown(f"> {result}")
            
            # 功能區
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 純淨台灣版")
                # 移除標註標籤，只保留新詞
                clean_text = re.sub(r' :red-background\[(.*?)\((.*?)\)\] ', r'\1', result)
                st.code(clean_
