import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 核心保險詞庫 (僅放最容易誤判或最重要的詞) ---
BASE_WIKI = {
    "很火": {
        "title": "🔥 「火」的語意辨析",
        "explanation": "這個詞在台灣具備兩種截然不同的語境，請確認您的意思：",
        "is_ambiguous": True,
        "options": [
            {"to": "很紅", "label": "📈 換成「很紅」(指熱門)"},
            {"to": "很火大", "label": "💢 換成「很火大」(指生氣)"},
            {"to": "很火", "label": "👌 維持原樣"}
        ]
    }
}

# --- 3. 全自動 AI 辨識引擎 (這就是自動抓取的關鍵) ---
def start_ai_analysis(text):
    if not text.strip(): return []
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 這裡的指令強化了 AI 的自主搜尋能力
    prompt = f"""
    任務：你是台灣語言與社群文化專家。
    分析文字："{text}"
    
    指令：
    1. 【自動抓取】：找出所有大陸用語（包含新詞、美妝流行語、職場用語、口語慣用語）。
    2. 【即時百科】：即便該詞不在你的範例中，只要台灣不常用，就請根據你的知識自動編寫百科內容。
    3. 【修正建議】：台灣人形容膚況會說「皮膚」或「膚質」，不說「好皮」。
    
    回傳 JSON 格式：
    [
      {{
        "original": "原詞",
        "replacement": "台灣在地建議",
        "title": "百科標題",
        "explanation": "自動生成的語境解釋",
        "suggestion": "給使用者的修正建議"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except:
        return []

# --- 4. 介面與邏輯 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def update_text(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast("✅ 已完成語感修正")

st.title("📱 語感專家：AI 全自動辨識")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    user_input = st.text_area("您可以輸入任何文字，AI 會自動掃描所有用語：", height=250)
    
    if st.button("🚀 啟動全自動智慧辨識", use_container_width=True):
        st.session_state.processed_text = user_input
        with st.spinner("AI 正在自動分析並編寫百科中..."):
            # AI 會自動抓取所有詞，包含沒寫在程式裡的
            ai_results = start_ai_analysis(user_input)
            
            # 整合本地歧義保險
            final_cards = []
            seen_words = []
            for word, info in BASE_WIKI.items():
                if word in user_input:
                    card = info.copy(); card['original'] = word
                    final_cards.append(card); seen_words.append(word)
            
            for r in ai_results:
                if r['original'] not in seen_words:
                    final_cards.append(r)
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 自動生成的對照百科")
    if st.session_state.is_analyzed:
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        if not active_cards:
            st.success("🎉 AI 掃描完畢，目前文字看起來非常本土！")
        else:
            for item in active_cards:
                with st.expander(f"✨ 自動辨識：{item['original']}", expanded=True):
                    st.markdown(f"### {item.get('title', item['original'])}")
                    st.write(item.get('explanation', 'AI 自動辨識詞彙'))
                    if item.get('is_ambiguous'):
                        st.warning("⚠️ 此詞有歧義，請點擊正確選項：")
                        cols = st.columns(len(item['options']))
                        for i, opt in enumerate(item['options']):
                            if cols[i].button(opt['label'], key=f"opt_{item['original']}_{i}"):
                                update_text(item['original'], opt['to']); st.rerun()
                    else:
                        target = item.get('replacement', '')
                        if st.button(f"👉 修正為「{target}」", key=f"fix_{item['original']}", use_container_width=True):
                            update_text(item['original'], target); st.rerun()
