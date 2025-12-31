import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與本地核心詞庫 ---
st.set_page_config(page_title="語感百科專家", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 本地精選詞庫 (確保最核心的詞永遠最直覺)
LOCAL_WIKI = {
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "中國指「馬鈴薯」，台灣指「花生」。",
        "options": [{"to": "馬鈴薯", "label": "🍟 換成馬鈴薯"}, {"to": "花生", "label": "🥜 換成花生"}]
    }
}

# --- 2. AI 自動百科生成邏輯 ---
def get_ai_wiki(word):
    """當本地找不到詞時，請 AI 按照百科格式寫一份"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    你是兩岸語境專家。請針對詞彙「{word}」分析其在中國與台灣的語意差異，並只回傳 JSON。
    JSON 格式：
    {{
      "title": "標題",
      "explanation": "簡單的百科解釋(20字內)",
      "tw_term": "台灣對應的慣用語",
      "suggestion": "給使用者的建議"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # 清理並讀取 JSON
        clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group(0)
        return json.loads(clean_json)
    except:
        return None

# --- 3. 邏輯處理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_cache' not in st.session_state: st.session_state.ai_cache = {}

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. UI 介面 ---
st.title("📱 語感專家：AI 自動百科模式")

col1, col2 = st.columns([1, 1.2])

with col1:
    u_input = st.text_area("輸入文字：", height=200, value="這視頻質量真好，我想吃土豆。")
    if st.button("🚀 執行語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        st.session_state.is_analyzed = True
        
        # 模擬偵測到的中國用語清單 (這部分未來可由 AI 初步過濾)
        detected_words = ["視頻", "質量", "土豆"] 
        
        # 針對沒看過的詞，自動去問 AI
        for w in detected_words:
            if w not in LOCAL_WIKI and w not in st.session_state.ai_cache:
                with st.spinner(f"正在為「{w}」編寫百科..."):
                    wiki = get_ai_wiki(w)
                    if wiki: st.session_state.ai_cache[w] = wiki

with col2:
    if st.session_state.is_analyzed:
        text = st.session_state.current_text
        
        # 顯示本地精選卡片
        for word, info in LOCAL_WIKI.items():
            if word in text:
                with st.expander(f"📌 精選百科：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    cols = st.columns(len(info['options']))
                    for i, opt in enumerate(info['options']):
                        if cols[i].button(opt['label'], key=f"local_{word}_{i}"):
                            apply_change(word, opt['to']); st.rerun()

        # 顯示 AI 自動生成的卡片
        for word, info in st.session_state.ai_cache.items():
            if word in text:
                with st.expander(f"🤖 AI 自動百科：{word}", expanded=True):
                    st.markdown(f"### {info.get('title')}")
                    st.write(info.get('explanation'))
                    st.info(f"💡 建議：{info.get('suggestion')}")
                    if st.button(f"👉 換成「{info.get('tw_term')}」", key=f"ai_{word}"):
                        apply_change(word, info.get('tw_term')); st.rerun()
