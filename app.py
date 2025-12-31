import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 核心百科資料庫 (WORD_WIKI) ---
# 這裡放入所有我們整理好的「標準答案」
WORD_WIKI = {
    "視頻": {
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "台灣習慣稱「影片」；「視頻」在台灣多指物理訊號。",
        "suggestion": "建議修正為「影片」。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "台灣指好壞用「品質」；「質量」專指物理重量 (Mass)。",
        "suggestion": "若指產品優劣，請換成「品質」。"
    },
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "兩岸指代物完全不同：中國指「馬鈴薯」，台灣指「花生」。",
        "is_ambiguous": True,
        "options": [{"to": "馬鈴薯", "desc": "🍟 換成馬鈴薯"}, {"to": "花生", "desc": "🥜 換成花生"}]
    },
    "合同": {
        "title": "📜 合同 vs 合約",
        "tw_term": "合約",
        "explanation": "台灣商業與法律場合習慣使用「合約」或「契約」。",
        "suggestion": "建議修正為「合約」。"
    },
    "窩心": {
        "title": "❤️ 窩心的語意相反",
        "explanation": "中國指「難受」，台灣指「貼心」。",
        "is_ambiguous": True,
        "options": [{"to": "貼心", "desc": "🥰 台灣語境 (暖心)"}, {"to": "憋屈", "desc": "😣 中國語境 (難受)"}]
    }
}

# --- 2. 配置與 AI 補位函數 ---
st.set_page_config(page_title="語感專家", layout="wide")
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def get_ai_fallback_wiki(text, existing_words):
    """叫 AI 找尋詞庫以外的中國用語並生成百科"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    分析："{text}"。請忽略這些已偵測詞：{existing_words}。
    找出其他中國大陸用語，並回傳 JSON 列表：
    [{{"word":"原詞", "title":"標題", "tw_term":"台灣慣用語", "diff":"語境差異", "suggestion":"建議"}}]
    若無則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: return []

# --- 3. 狀態管理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. UI 呈現 ---
st.title("📱 語感專家：全功能百科模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("試試：簽署合同前先看視頻。", height=200, key="u_input_area")
    
    if st.button("🚀 執行深度偵測", use_container_width=True):
        st.session_state.current_text = u_input
        # 找出哪些詞是內建的
        found_in_wiki = [w for w in WORD_WIKI if w in u_input]
        # 剩下的叫 AI 去找
        with st.spinner("AI 正在搜尋其他潛在用語..."):
            st.session_state.ai_results = get_ai_fallback_wiki(u_input, found_in_wiki)
        st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科建議")
    if st.session_state.is_analyzed:
        curr_text = st.session_state.current_text
        found_any = False
        
        # A. 先跑【內建百科】(100% 穩定)
        for word, info in WORD_WIKI.items():
            if word in curr_text:
                found_any = True
                with st.expander(f"📌 精選百科：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    if info.get('is_ambiguous'):
                        cols = st.columns(len(info['options']))
                        for i, opt in enumerate(info['options']):
                            if cols[i].button(opt['desc'], key=f"opt_{word}_{i}"):
                                apply_change(word, opt['to']); st.rerun()
                    else:
                        st.info(f"💡 {info['suggestion']}")
                        if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}"):
                            apply_change(word, info['tw_term']); st.rerun()

        # B. 再跑【AI 補位百科】(處理像 '合同' 這種新詞)
        for item in st.session_state.ai_results:
            word = item['word']
            if word in curr_text:
                found_any = True
                with st.expander(f"🤖 AI 百科：{word}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🇹🇼 **台灣慣用：** {item['tw_term']}")
                    st.write(f"🔍 **差異：** {item['diff']}")
                    if st.button(f"👉 修正為「{item['tw_term']}」", key=f"ai_{word}"):
                        apply_change(word, item['tw_term']); st.rerun()

        if not found_any:
            st.success("🎉 文字看起來非常本土！")
