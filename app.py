import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 核心配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 請在此處輸入你的 Gemini API Key
# 你可以從 https://aistudio.google.com/ 免費取得
API_KEY = "你的_GEMINI_API_KEY" 

if API_KEY != "你的_GEMINI_API_KEY":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("請先在代碼中填入 Gemini API Key 才能執行 AI 偵測")

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_results' not in st.session_state: st.session_state.ai_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 2. AI 背景運行邏輯 ---
def call_ai_expert(text):
    prompt = f"""
    你是一位台灣繁體中文語感專家。請分析以下這段文字中，哪些詞彙屬於中國大陸用語或不符合台灣在地語感（例如：視頻、很火、質量、軟件）。
    
    文字內容："{text}"
    
    請僅以 JSON 格式回傳分析結果，格式如下：
    [
      {{"original": "大陸詞彙", "taiwan": "台灣建議", "reason": "差異解釋", "example": "台灣用法例句"}}
    ]
    如果沒有發現任何需要修正的詞彙，請回傳空列表 []。
    """
    try:
        response = model.generate_content(prompt)
        # 提取 JSON 內容
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return []
    except Exception as e:
        st.error(f"AI 運行出錯: {e}")
        return []

# --- 3. UI 介面 ---
st.title("📱 語感守護者：AI 自動化模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請輸入內容：", height=150, value="這個視頻真的火。", key="u_input")
    
    if st.button("🚀 執行 AI 語感掃描", use_container_width=True):
        if API_KEY == "你的_GEMINI_API_KEY":
            st.warning("⚠️ 請先設定 API Key")
        else:
            with st.spinner("AI 專家正在分析中..."):
                st.session_state.current_text = u_input
                st.session_state.ai_results = call_ai_expert(u_input)
                st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**最終文字預覽：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 AI 語感專家分析")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            results = st.session_state.ai_results
            
            if not results:
                st.success("✨ AI 偵測完成：這段文字看起來很有台灣味！")
            else:
                st.write(f"🤖 **AI 偵測到 {len(results)} 處建議：**")
                
                for item in results:
                    # 只有當詞彙還存在於文字中時才顯示卡片
                    if item['original'] in st.session_state.current_text:
                        with st.expander(f"📌 建議修正：{item['original']} ➔ {item['taiwan']}", expanded=True):
                            st.write(f"🇹🇼 **台灣用法：** {item['taiwan']}")
                            st.write(f"💡 **差異解釋：** {item['reason']}")
                            st.caption(f"📖 {item['example']}")
                            
                            if st.button(f"直接修正「{item['original']}」", key=f"btn_{item['original']}"):
                                apply_change(item['original'], item['taiwan'])
                                st.rerun()
        else:
            st.write("等待掃描任務...")
