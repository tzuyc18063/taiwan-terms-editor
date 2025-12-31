import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心百科資料庫 (WORD_WIKI) ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 這裡包含了所有高頻詞、流行語以及容易被忽略的職場用語
WORD_WIKI = {
    # 【流行語與美妝類】
    "媽生": {
        "title": "✨ 媽生 vs 天生/自然",
        "tw_term": "天生",
        "explanation": "大陸社群（小紅書）熱詞，形容極致自然，像從娘胎帶出來的一樣。",
        "suggestion": "在台灣建議使用「天生」、「自然」或「原生感」。"
    },
    "氛圍感": {
        "title": "🕯️ 氛圍感 vs 很有感覺",
        "tw_term": "有氣質",
        "explanation": "大陸流行語，形容一種整體的氣息或環境營造出的感覺。",
        "suggestion": "台灣慣用「很有氣質」、「很有感覺」或「有氣氛」。"
    },
    "種草": {
        "title": "🌱 種草 vs 推薦/推坑",
        "tw_term": "推坑",
        "explanation": "指對某事物產生購買慾望。對應的還有「拔草」(消除慾望)。",
        "suggestion": "台灣常用「推坑」、「被燒到」或「強烈推薦」。"
    },
    
    # 【職場與高頻修正類】
    "優化": {
        "title": "✨ 優化 vs 改善/提升",
        "tw_term": "改善",
        "explanation": "雖然技術領域常用，但台灣日常更習慣說「改善」、「提升」或「調整」。",
        "suggestion": "建議修正為「改善」、「提升」或「完善」。"
    },
    "服務員": {
        "title": "💁 服務員 vs 服務生",
        "tw_term": "服務生",
        "explanation": "台灣習慣稱呼餐廳工作人員為「服務生」或「店員」。",
        "suggestion": "建議修正為「服務生」。"
    },
    "視頻": {
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "台灣習慣稱內容為「影片」；「視頻」多指物理訊號。",
        "suggestion": "建議修正為「影片」。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "指產品優劣台灣用「品質」；「質量」專指物理重量(Mass)。",
        "suggestion": "若指產品好壞，請換成「品質」。"
    },
    "合同": {
        "title": "📜 合同 vs 合約",
        "tw_term": "合約",
        "explanation": "台灣商業與法律場合習慣使用「合約」或「契約」。",
        "suggestion": "建議修正為「合約」。"
    },

    # 【語意歧義類】
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "中國指「馬鈴薯」，台灣指「花生」。",
        "is_ambiguous": True,
        "options": [{"to": "馬鈴薯", "desc": "🍟 換成馬鈴薯"}, {"to": "花生", "desc": "🥜 換成花生"}]
    }
}

# --- 2. 強化版 AI 深度偵測補位函數 ---
def get_ai_fallback_wiki(text, existing_found_words):
    if "GOOGLE_API_KEY" not in st.secrets: return []
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 強化 Prompt：嚴格要求 AI 抓出所有大陸社群用語
    prompt = f"""
    任務：找出文字中「非台灣在地習慣」的大陸用語或社群熱詞。
    輸入文字："{text}"
    已跳過詞彙：{existing_found_words}
    
    【偵測重點】：
    - 流行熱詞：媽生、氛圍感、種草、給力、YYDS、絕絕子。
    - 生活/職場：立馬、打印、水平、項目、信息、菜單(選單)。
    
    請回傳 JSON 格式列表。如果看到「媽生好皮」，請拆解出「媽生」並提供百科。
    [
      {{"word":"原詞", "title":"標題", "tw_term":"台灣慣用語", "diff":"語境差異", "suggestion":"建議"}}
    ]
    若無則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: return []

# --- 3. 狀態與邏輯處理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. UI 介面呈現 ---
st.title("📱 語感專家：全方位百科模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    default_val = "我們要優化這款底妝，打造媽生好皮，讓服務員也種草。"
    u_input = st.text_area("請輸入內容：", height=250, value=default_val)
    
    if st.button("🚀 執行深度語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        # 找出內建詞
        found_in_wiki = [w for w in WORD_WIKI if w in u_input]
        # 剩下的交給 AI
        with st.spinner("AI 百科生成中..."):
            st.session_state.ai_results = get_ai_fallback_wiki(u_input, found_in_wiki)
        st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        curr_text = st.session_state.current_text
        found_any = False
        
        # A. 核心詞庫偵測 (確保 100% 命中「優化」與「媽生」)
        for word, info in WORD_WIKI.items():
            if word in curr_text:
                found_any = True
                with st.expander(f"📌 精選百科：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    if info.get('is_ambiguous'):
                        btn_cols = st.columns(len(info['options']))
                        for i, opt in enumerate(info['options']):
                            if btn_cols[i].button(opt['desc'], key=f"opt_{word}_{i}"):
                                apply_change(word, opt['to']); st.rerun()
                    else:
                        st.info(f"💡 {info.get('suggestion', '')}")
                        if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}", use_container_width=True):
                            apply_change(word, info['tw_term']); st.rerun()

        # B. AI 補位偵測 (處理其他沒想到的詞)
        for item in st.session_state.ai_results:
            word = item['word']
            if word in curr_text:
                found_any = True
                with st.expander(f"🤖 AI 百科：{word}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🇹🇼 **台灣慣用：** {item['tw_term']}")
                    st.write(f"🔍 **差異說明：** {item['diff']}")
                    if st.button(f"👉 修正為「{item['tw_term']}」", key=f"ai_{word}", use_container_width=True):
                        apply_change(word, item['tw_term']); st.rerun()

        if not found_any:
            st.success("🎉 目前文字讀起來非常有台灣在地感！")
