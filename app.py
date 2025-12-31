import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置 ---
st.set_page_config(page_title="語感專家：終極版", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 【核心保險名單】優先於 AI，只要出現就強制跳百科 ---
# 這樣可以解決截圖中 AI 漏抓的問題
MANDATORY_WIKI = {
    "媽生好皮": {
        "title": "✨ 媽生好皮 vs 天生好皮膚",
        "replacement": "天生好皮膚",
        "explanation": "這是大陸社群熱詞。台灣不說「好皮」，請完整修正為「好皮膚」或「好膚質」。",
        "suggestion": "建議修正為「天生好皮膚」。"
    },
    "特好": {
        "title": "👍 特好 vs 很好/非常棒",
        "replacement": "很好",
        "explanation": "「特」作為副詞在大陸極為常用（特美、特好），台灣更習慣說「很好」或「非常」。",
        "suggestion": "建議修正為「很好」或「非常棒」。"
    },
    "驚訝到": {
        "title": "😲 驚訝到 vs 感到驚訝",
        "replacement": "感到驚訝",
        "explanation": "「被...到」是大陸常用的語法結構。台灣更習慣直接描述情緒，如「感到驚訝」或「嚇了一跳」。",
        "suggestion": "建議修正為「感到驚訝」。"
    },
    "優化": {
        "title": "✨ 優化 vs 改善/提升",
        "replacement": "改善",
        "explanation": "台灣日常語境建議使用「改善」或「提升」。",
        "suggestion": "建議修正為「改善」。"
    }
}

# --- 3. 強化 AI 引擎 (修正 404 並設定最嚴格 Prompt) ---
def start_strict_analysis(text):
    if not text.strip(): return []
    # 使用穩定版模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    任務：你是台灣語境審核員，必須抓出文字中所有大陸用語，不可遺漏。
    目標文字："{text}"
    
    要求：
    1. 針對「特好」、「有被...到」、「媽生」、「視頻」、「很火」等詞必須報警。
    2. 只要台灣有更道地的說法，就請生成百科。
    3. 必須回傳 JSON 格式。
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except:
        return []

# --- 4. 介面邏輯 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def update_text(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast(f"✅ 已更新")

st.title("📱 語感專家：終極在地化辨識")
st.caption("結合「強制名單」與「智慧分析」，解決 AI 漏抓問題。")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    default_text = "這款粉底液特好，有被驚訝到，簡直是媽生好皮"
    u_input = st.text_area("請輸入內容：", height=200, value=default_text)
    
    if st.button("🚀 執行深度掃描", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("正在進行多重辨識..."):
            # A. AI 辨識
            ai_results = start_strict_analysis(u_input)
            
            # B. 強制名單比對 (保證 100% 抓到)
            final_cards = []
            seen_words = []
            
            # 優先處理強制名單
            for word, info in MANDATORY_WIKI.items():
                if word in u_input:
                    card = info.copy()
                    card['original'] = word
                    final_cards.append(card)
                    seen_words.append(word)
            
            # 補上 AI 發現的其他詞
            for r in ai_results:
                if r['original'] not in seen_words:
                    final_cards.append(r)
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        # 過濾目前文字中還存在的詞
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        
        if not active_cards:
            st.success("🎉 目前文字已完全符合台灣在地語感！")
        else:
            for item in active_cards:
                with st.expander(f"📌 百科辨識：{item['original']}", expanded=True):
                    st.markdown(f"### {item.get('title', '語法分析')}")
                    st.write(item.get('explanation', ''))
                    target = item.get('replacement', '')
                    if st.button(f"👉 修正為「{target}」", key=f"btn_{item['original']}", use_container_width=True):
                        update_text(item['original'], target)
                        st.rerun()
