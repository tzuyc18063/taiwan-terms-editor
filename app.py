import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心百科資料庫 (WORD_WIKI) ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 這裡塞入了最完整的「生活高頻詞」列表
WORD_WIKI = {
    # 【生活常用類】
    "服務員": {
        "title": "💁 服務員 vs 服務生",
        "tw_term": "服務生",
        "explanation": "台灣日常口語習慣稱呼為「服務生」或「店員」。",
        "suggestion": "建議修正為「服務生」或「店員」更顯親切。"
    },
    "打印": {
        "title": "🖨️ 打印 vs 列印",
        "tw_term": "列印",
        "explanation": "台灣習慣使用「列印」；「打印」多指物理性的蓋章或印製。",
        "suggestion": "建議修正為「列印」。"
    },
    "菜單": {
        "title": "📜 菜單的語意差異",
        "explanation": "兩岸皆用菜單，但在軟體介面(UI)中，台灣習慣稱之為「選單」。",
        "is_ambiguous": True,
        "options": [{"to": "選單", "desc": "💻 換成選單 (軟體介面)"}, {"to": "菜單", "desc": "🍴 維持菜單 (餐廳點菜)"}]
    },
    "合同": {
        "title": "📜 合同 vs 合約",
        "tw_term": "合約",
        "explanation": "台灣商業與法律場合習慣使用「合約」或「契約」。",
        "suggestion": "建議修正為「合約」。"
    },
    "立馬": {
        "title": "🐎 立馬 vs 立刻/馬上",
        "tw_term": "立刻",
        "explanation": "台灣較少使用「立馬」，習慣用「立刻、馬上」。",
        "suggestion": "建議修正為「立刻」或「馬上」。"
    },
    
    # 【科技與職場類】
    "視頻": {
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "台灣習慣稱內容為「影片」；「視頻」多指訊號或視訊。",
        "suggestion": "建議修正為「影片」。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "指產品優劣台灣用「品質」；「質量」專指物理重量(Mass)。",
        "suggestion": "若指產品好壞，請換成「品質」。"
    },
    "水平": {
        "title": "📈 水平 vs 水準",
        "tw_term": "水準",
        "explanation": "形容人的素養、表現或技術高低，台灣必用「水準」。",
        "suggestion": "建議修正為「水準」。"
    },
    "信息": {
        "title": "📩 信息 vs 訊息",
        "tw_term": "訊息",
        "explanation": "手機簡訊或通訊軟體內容，台灣統一稱為「訊息」。",
        "suggestion": "建議修正為「訊息」。"
    },
    "優化": {
        "title": "✨ 優化 vs 調整/改善",
        "tw_term": "改善",
        "explanation": "雖然優化通用，但台灣傳統習慣用「改善、調整、提升」。",
        "suggestion": "建議修正為「改善」或「提升」。"
    },

    # 【語意陷阱類 (最重要)】
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "兩岸指代物完全不同：中國指「馬鈴薯」，台灣指「花生」。",
        "is_ambiguous": True,
        "options": [{"to": "馬鈴薯", "desc": "🍟 換成馬鈴薯 (Potato)"}, {"to": "花生", "desc": "🥜 換成花生 (Peanut)"}]
    },
    "窩心": {
        "title": "❤️ 窩心的語意相反",
        "explanation": "中國指「難受/憋屈」，台灣指「貼心/溫暖」。",
        "is_ambiguous": True,
        "options": [{"to": "貼心", "desc": "🥰 台灣語境 (暖心)"}, {"to": "憋屈", "desc": "😣 中國語境 (難受)"}]
    },
    "感冒": {
        "title": "🤧 感冒的語氣差異",
        "explanation": "中國「不感冒」是指沒興趣；台灣「很感冒」是指反感、討厭。",
        "is_ambiguous": True,
        "options": [{"to": "反感", "desc": "💢 換成反感 (討厭)"}, {"to": "沒興趣", "desc": "😶 換成沒興趣 (無感)"}]
    }
}

# --- 2. AI 深度偵測補位函數 ---
def get_ai_fallback_wiki(text, existing_found_words):
    """強化版 AI：偵測本地詞庫沒寫到的詞，並確保語感敏銳"""
    if "GOOGLE_API_KEY" not in st.secrets: return []
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    任務：找出文字中「非台灣習慣」的中國大陸用語。
    輸入文字："{text}"
    已跳過詞彙(由本地處理)：{existing_found_words}
    
    規範：台灣口語更習慣「服務生、列印、選單、警察、計程車」。
    請找出其他潛在的大陸用語，並嚴格按照 JSON 格式回傳列表：
    [
      {{
        "word": "偵測到的原詞",
        "title": "標題 (例如: 項目 vs 專案)",
        "tw_term": "台灣道地用語",
        "diff": "兩岸語境差異說明",
        "suggestion": "修正建議"
      }}
    ]
    若無則回傳 []。不可回傳 Markdown 語法，只需 JSON。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: return []

# --- 3. 狀態管理與邏輯 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. UI 介面 ---
st.title("📱 語感專家：終極百科整合模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    default_val = "服務員，簽署合同前先讓我看視頻質量，不然我很感冒。"
    u_input = st.text_area("請輸入內容：", height=250, value=default_val, key="u_input_area")
    
    if st.button("🚀 啟動全方位語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        # 找出內建詞
        found_in_wiki = [w for w in WORD_WIKI if w in u_input]
        # 叫 AI 找剩下的
        with st.spinner("AI 百科編寫中..."):
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
        
        # A. 優先跑【核心詞庫】
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
                        if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}"):
                            apply_change(word, info['tw_term']); st.rerun()

        # B. 跑【AI 補位百科】
        for item in st.session_state.ai_results:
            word = item['word']
            if word in curr_text:
                found_any = True
                with st.expander(f"🤖 AI 百科：{word}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🇹🇼 **台灣慣用：** {item['tw_term']}")
                    st.write(f"🔍 **語境差異：** {item['diff']}")
                    if st.button(f"👉 修正為「{item['tw_term']}」", key=f"ai_{word}"):
                        apply_change(word, item['tw_term']); st.rerun()

        if not found_any:
            st.success("🎉 檢查完畢！目前文字非常符合台灣語境。")
