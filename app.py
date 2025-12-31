import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心百科資料庫 (WORD_WIKI) ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 這裡修正了偵測邏輯，將「媽生好皮」作為完整詞條處理
WORD_WIKI = {
    # 【流行語與美妝類 - 完整詞組偵測】
    "媽生好皮": {
        "title": "✨ 媽生好皮 vs 天生好皮膚",
        "tw_term": "天生好皮膚",
        "explanation": "大陸美妝熱詞，「媽生」意指天生，「好皮」在大陸簡稱膚況，但在台灣必須說「好皮膚」或「好膚質」。",
        "suggestion": "建議完整修正為「天生好皮膚」或「原生感好膚質」。"
    },
    "媽生": {
        "title": "✨ 媽生 vs 天生",
        "tw_term": "天生",
        "explanation": "形容極其自然，如同娘胎帶來。台灣習慣直接用「天生」或「原生」。",
        "suggestion": "建議修正為「天生」。"
    },
    "優化": {
        "title": "✨ 優化 vs 改善/提升",
        "tw_term": "改善",
        "explanation": "台灣日常更習慣說「改善」、「提升」或「調整」，較少在非技術場合使用「優化」。",
        "suggestion": "建議根據語境修正為「改善」、「提升」或「完善」。"
    },
    "服務員": {
        "title": "💁 服務員 vs 服務生",
        "tw_term": "服務生",
        "explanation": "台灣稱呼餐廳或服務場所人員為「服務生」或「店員」。",
        "suggestion": "建議修正為「服務生」。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "大陸慣用「質量」，台灣形容產品好壞一律使用「品質」。",
        "suggestion": "建議修正為「品質」。"
    }
}

# --- 2. AI 深度偵測補位函數 ---
def get_ai_fallback_wiki(text, existing_found_words):
    if "GOOGLE_API_KEY" not in st.secrets: return []
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    任務：找出文字中「非台灣在地習慣」的大陸用語或社群熱詞。
    輸入文字："{text}"
    已跳過詞彙：{existing_found_words}
    
    【偵測重點】：
    - 流行熱詞：媽生好皮(建議:天生好皮膚)、氛圍感、種草。
    - 台灣人不用「好皮」來形容皮膚，必須用「好皮膚」。
    - 職場：項目(專案)、信息(訊息)、水平(水準)。
    
    請回傳 JSON 格式列表：
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
    default_val = "我們要優化這款底妝，打造媽生好皮，這質量的效果服務員也說好。"
    u_input = st.text_area("請輸入內容：", height=250, value=default_val)
    
    if st.button("🚀 執行深度語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        # 排序詞庫，長詞優先（避免媽生好皮被媽生切斷）
        sorted_keys = sorted(WORD_WIKI.keys(), key=len, reverse=True)
        found_in_wiki = [w for w in sorted_keys if w in u_input]
        
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
        
        # A. 核心詞庫偵測 (優先處理長詞)
        sorted_keys = sorted(WORD_WIKI.keys(), key=len, reverse=True)
        for word in sorted_keys:
            if word in curr_text:
                info = WORD_WIKI[word]
                found_any = True
                with st.expander(f"📌 精選百科：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    st.info(f"💡 {info.get('suggestion', '')}")
                    if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}", use_container_width=True):
                        apply_change(word, info['tw_term']); st.rerun()

        # B. AI 補位偵測
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
