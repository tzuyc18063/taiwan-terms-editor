import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心百科資料庫 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 核心詞庫：包含生活、職場、以及容易「習以為常」的大陸用語
WORD_WIKI = {
    "優化": {
        "title": "✨ 優化 vs 改善/提升",
        "tw_term": "改善",
        "explanation": "雖然「優化」在技術領域通用，但台灣傳統習慣用「改善」、「提升」或「調整」。",
        "suggestion": "建議在非技術文件夾中修正為「改善」或「提升」。"
    },
    "視頻": {"title": "📺 視頻 vs 影片", "tw_term": "影片", "explanation": "台灣習慣稱內容為「影片」。", "suggestion": "建議修正為「影片」。"},
    "服務員": {"title": "💁 服務員 vs 服務生", "tw_term": "服務生", "explanation": "台灣習慣稱「服務生」或「店員」。", "suggestion": "建議修正為「服務生」。"},
    "土豆": {
        "title": "🥔 土豆的兩岸差異",
        "explanation": "兩岸指代物完全不同：中國指「馬鈴薯」，台灣指「花生」。",
        "is_ambiguous": True,
        "options": [{"to": "馬鈴薯", "desc": "🍟 換成馬鈴薯"}, {"to": "花生", "desc": "🥜 換成花生"}]
    }
}

# --- 2. AI 深度偵測補位函數 ---
def get_ai_fallback_wiki(text, existing_found_words):
    if "GOOGLE_API_KEY" not in st.secrets: return []
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 強化 Prompt：要求 AI 識別那些「看似正常但非在地」的詞
    prompt = f"""
    任務：識別文字中「非台灣在地習慣」的用語。
    輸入文字："{text}"
    已跳過詞彙：{existing_found_words}
    
    請特別注意：
    - 網路熱詞：媽生(好皮)、氛圍感、種草、給力、YYDS。
    - 職場慣用但非台灣首選：優化(建議:改善)、項目(建議:專案)、水平(建議:水準)。
    - 生活用語：服務員、菜單(選單)、打印。

    請按照 JSON 格式回傳列表：
    [
      {{
        "word": "偵測到的原詞",
        "title": "標題",
        "tw_term": "台灣道地用語",
        "diff": "說明語境差異",
        "suggestion": "修正建議"
      }}
    ]
    若無則回傳 []。只需 JSON 內容。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: return []

# --- 3. 狀態與 UI 邏輯 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. 介面呈現 ---
st.title("📱 語感專家：全方位百科模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("試試：我們需要優化這款底妝，打造媽生好皮。", height=250)
    
    if st.button("🚀 執行深度偵測", use_container_width=True):
        st.session_state.current_text = u_input
        found_in_wiki = [w for w in WORD_WIKI if w in u_input]
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
        
        # 顯示核心百科（含優化）
        for word, info in WORD_WIKI.items():
            if word in curr_text:
                found_any = True
                with st.expander(f"📌 精選百科：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    if info.get('is_ambiguous'):
                        cols = st.columns(2)
                        for i, opt in enumerate(info['options']):
                            if cols[i].button(opt['desc'], key=f"opt_{word}_{i}"):
                                apply_change(word, opt['to']); st.rerun()
                    else:
                        if st.button(f"👉 修正為「{info['tw_term']}」", key=f"fix_{word}", use_container_width=True):
                            apply_change(word, info['tw_term']); st.rerun()

        # 顯示 AI 自動生成的網路熱詞與職場用語
        for item in st.session_state.ai_results:
            word = item['word']
            if word in curr_text:
                found_any = True
                with st.expander(f"✨ 流行語百科：{word}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🔍 **語境說明：** {item['diff']}")
                    st.write(f"🇹🇼 **台灣習慣：** {item['tw_term']}")
                    if st.button(f"👉 修正為「{item['tw_term']}」", key=f"ai_{word}", use_container_width=True):
                        apply_change(word, item['tw_term']); st.rerun()

        if not found_any:
            st.success("🎉 檢查完畢！文字目前的用語非常道地。")
