import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心百科資料庫 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 建立具備「歧義處理」功能的基礎詞庫
BASE_WIKI = {
    "很火": {
        "title": "🔥 「火」的語意辨析",
        "explanation": "在台灣，「火」有兩種截然不同的意思：\n1. **很紅/熱門** (大陸常用)\n2. **很生氣/火大** (台灣在地口語)",
        "is_ambiguous": True,
        "options": [
            {"to": "很紅", "label": "📈 換成「很紅」(指熱門)"},
            {"to": "很火大", "label": "💢 換成「很火大」(指生氣)"},
            {"to": "很火", "label": "👌 維持原樣"}
        ]
    },
    "媽生好皮": {"to": "天生好皮膚", "title": "✨ 媽生好皮 vs 天生好皮膚", "explanation": "台灣不簡稱「好皮」，建議修正為「好皮膚」或「好膚質」。", "is_ambiguous": False},
    "視頻": {"to": "影片", "title": "📺 視頻 vs 影片", "explanation": "台灣日常習慣稱呼為「影片」。", "is_ambiguous": False}
}

# --- 2. AI 偵測引擎 ---
def auto_detect_and_wiki(text):
    if not text.strip(): return []
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    你現在是台灣語境專家。請分析以下文字中不符合「台灣道地口語」的大陸用語或熱詞。
    輸入文字："{text}"
    要求：
    1. 找出大陸用語（如：媽生好皮、很火、優化、視頻等）。
    2. 若遇到「很火」，請在說明中註明這可能有「生氣」或「熱門」兩種含意。
    請僅回傳 JSON 列表：
    [
      {{"original": "原詞", "replacement": "建議", "title": "標題", "explanation": "解釋", "is_ambiguous": false}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except:
        return []

# --- 3. 介面邏輯 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_correction(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast(f"✅ 已更新文字")

# --- 4. UI 呈現 ---
st.title("📱 語感專家：歧義辨識模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入文字（例如：這視頻很火 / 我真的很火）：", height=200)
    
    if st.button("🚀 執行智能偵測", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("分析中..."):
            ai_results = auto_detect_and_wiki(u_input)
            # 合併 AI 與本地詞庫 (本地歧義處理優先)
            final_cards = []
            detected_words = []
            
            # 先檢查本地詞庫的歧義詞
            for word, info in BASE_WIKI.items():
                if word in u_input:
                    card = info.copy()
                    card['original'] = word
                    final_cards.append(card)
                    detected_words.append(word)
            
            # 再補上 AI 偵測到且不重複的詞
            for r in ai_results:
                if r['original'] not in detected_words:
                    final_cards.append(r)
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        
        if not active_cards:
            st.success("🎉 文字讀起來非常本土！")
        else:
            for item in active_cards:
                with st.expander(f"📌 百科發現：{item['original']}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(item['explanation'])
                    
                    # 歧義處理：顯示多個按鈕讓使用者選擇
                    if item.get('is_ambiguous'):
                        st.warning("⚠️ 此詞在台灣有多重含意，請選擇您的真正意圖：")
                        cols = st.columns(len(item['options']))
                        for i, opt in enumerate(item['options']):
                            if cols[i].button(opt['label'], key=f"opt_{item['original']}_{i}"):
                                apply_correction(item['original'], opt['to'])
                                st.rerun()
                    else:
                        # 一般詞：單一修正按鈕
                        if st.button(f"👉 修正為「{item.get('replacement', item.get('tw_term'))}」", key=f"fix_{item['original']}", use_container_width=True):
                            apply_correction(item['original'], item['replacement'])
                            st.rerun()
