import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 初始化與核心詞庫 ---
st.set_page_config(page_title="語感專家", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 那些需要「極度精準」解釋的詞，我們手動保留最高優先權
PREMIUM_WIKI = {
    "土豆": {
        "title": "🥔 土豆的語意陷阱",
        "explanation": "這是一個極易混淆的詞：\n- **中國**指「馬鈴薯」(Potato)\n- **台灣**指「花生」(Peanut)",
        "options": [
            {"to": "馬鈴薯", "label": "🍟 換成馬鈴薯 (指蔬菜)", "desc": "🇨🇳 中國語境"},
            {"to": "花生", "label": "🥜 換成花生 (指堅果)", "desc": "🇹🇼 台灣語境"}
        ]
    }
}

# --- 2. AI 核心功能 ---
def analyze_text_and_get_wiki(text):
    """叫 AI 先偵測詞彙，再針對每個詞寫百科"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prompt 強化：要求 AI 同時找出詞彙並生成百科內容
    prompt = f"""
    分析以下文字中的中國用語："{text}"
    請回傳一個 JSON 列表，每個物件包含：
    1. "word": 偵測到的原詞
    2. "title": 該詞的百科標題 (如: 視頻 vs 影片)
    3. "tw_term": 台灣慣用語
    4. "diff": 兩岸語境的詳細差異說明
    5. "suggestion": 給台灣使用者的建議
    
    僅回傳 JSON，格式範例：
    [{{"word":"視頻", "title":"📺 視頻 vs 影片", "tw_term":"影片", "diff":"台灣習慣稱影片...", "suggestion":"建議修正..."}}]
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0))
    except:
        return []

# --- 3. UI 邏輯 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'wiki_results' not in st.session_state: st.session_state.wiki_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. 畫面呈現 ---
st.title("📱 語感專家：AI 全自動百科")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入內容：", height=200, value="這視頻質量真好，我想吃土豆。")
    if st.button("🚀 執行深度語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        with st.spinner("AI 正在分析語境並編寫百科..."):
            st.session_state.wiki_results = analyze_text_and_get_wiki(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科建議")
    if st.session_state.is_analyzed:
        found_any = False
        
        # 遍歷 AI 偵測到的結果
        for item in st.session_state.wiki_results:
            word = item['word']
            if word in st.session_state.current_text:
                found_any = True
                
                # A. 如果是「土豆」等精選詞，顯示更直覺的二選一介面
                if word in PREMIUM_WIKI:
                    info = PREMIUM_WIKI[word]
                    with st.expander(f"📌 精選百科：{word}", expanded=True):
                        st.markdown(f"### {info['title']}")
                        st.write(info['explanation'])
                        for opt in info['options']:
                            st.caption(f"📍 {opt['desc']}")
                            if st.button(opt['label'], key=f"pre_{word}_{opt['to']}", use_container_width=True):
                                apply_change(word, opt['to']); st.rerun()
                
                # B. 一般 AI 自動生成的百科
                else:
                    with st.expander(f"🤖 AI 百科：{word}", expanded=True):
                        st.markdown(f"### {item['title']}")
                        st.write(f"🇹🇼 **台灣慣用：** {item['tw_term']}")
                        st.write(f"🔍 **語境差異：** {item['diff']}")
                        st.info(f"💡 **建議：** {item['suggestion']}")
                        if st.button(f"👉 將「{word}」修正為「{item['tw_term']}」", key=f"ai_{word}", use_container_width=True):
                            apply_change(word, item['tw_term']); st.rerun()

        if not found_any:
            st.success("🎉 目前文字看起來非常本土！")
