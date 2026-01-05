import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 安全讀取 API KEY ---
try:
    # 從 Streamlit Secrets 中讀取，避免金鑰外洩
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("❌ 找不到 API Key。請確保已在 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# --- 3. 狀態管理與邏輯 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_results' not in st.session_state: st.session_state.ai_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已為您修正為：{new}")

def call_ai_expert(text):
    """驅動背後的 AI 進行兩岸語感分析"""
    prompt = f"""
    你是一位台灣繁體中文語感專家。請分析以下文字中，哪些詞彙屬於中國大陸用語、不符合台灣在地語感、或兩岸定義不同的詞。
    特別注意口語詞，例如「很火」、「牛逼」、「接地氣」、「給力」。
    
    待分析文字："{text}"
    
    請僅以 JSON 陣列格式回傳結果，不要有額外描述：
    [
      {{
        "original": "偵測到的詞",
        "taiwan": "台灣建議替換詞",
        "reason": "差異解釋（例如：語源差異或文化背景）",
        "example": "台灣用法的例句"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 清洗 JSON 字串
        json_str = re.search(r'\[.*\]', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return []

# --- 4. UI 介面 ---
st.title("📱 語感守護者：AI 自動化模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請輸入內容：", height=200, 
                           value="這個視頻真的很火，質量非常牛逼。", key="u_input")
    
    if st.button("🚀 執行 AI 專家偵測", use_container_width=True):
        with st.spinner("AI 專家正在診斷語感..."):
            st.session_state.current_text = u_input
            st.session_state.ai_results = call_ai_expert(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**最終文字預覽：**")
        st.markdown(f"""
            <div style="background:#f0f2f6; padding:15px; border-radius:10px; border:1px solid #ddd; line-height:1.6;">
                {st.session_state.current_text}
            </div>
        """, unsafe_allow_html=True)

with c2:
    st.subheader("🤳 語感專家診斷卡片")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            results = st.session_state.ai_results
            
            if not results:
                st.success("✨ AI 偵測完成：這段文字語感非常道地！")
            else:
                st.write(f"🤖 **偵測到 {len(results)} 個建議：**")
                for item in results:
                    # 檢查該詞是否還存在（避免重複顯示已修正的詞）
                    if item['original'] in st.session_state.current_text:
                        with st.expander(f"📌 建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                            st.write(f"🇹🇼 **台灣用法：** {item['taiwan']}")
                            st.write(f"💡 **差異解析：** {item['reason']}")
                            st.caption(f"📖 **在地例句：** {item['example']}")
                            
                            if st.button(f"修正為「{item['taiwan']}」", key=f"btn_{item['original']}"):
                                apply_change(item['original'], item['taiwan'])
                                st.rerun()
        else:
            st.write("等待掃描任務中...")

# --- 5. 底部功能 ---
st.divider()
if st.button("🧹 清空重置"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.ai_results = []
    st.rerun()
