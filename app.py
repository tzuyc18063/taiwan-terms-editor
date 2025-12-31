import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 初始化 ---
st.set_page_config(page_title="語感專家：最高嚴格度", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 核心保險詞庫 (處理歧義詞) ---
BASE_WIKI = {
    "很火": {
        "title": "🔥 「火」的語意辨析",
        "explanation": "在台灣，「火」在不同語境有截然不同的意思，請確認：",
        "is_ambiguous": True,
        "options": [
            {"to": "很紅", "label": "📈 換成「很紅」(指熱門)"},
            {"to": "很火大", "label": "💢 換成「很火大」(指生氣)"},
            {"to": "很火", "label": "👌 維持原樣"}
        ]
    }
}

# --- 3. 強化型 AI 辨識引擎 (最高嚴格度設定) ---
def start_ai_analysis(text):
    if not text.strip(): return []
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 調高嚴格度的指令
    prompt = f"""
    任務：你是最嚴苛的台灣語境校正專家。
    目標文字："{text}"
    
    【嚴格辨識準則】：
    1. 只要該詞彙在台灣有「更道地」的對應詞，就必須抓出來，不可放過。
    2. 監控類別：
       - 美妝/生活：媽生(天生)、好皮(好皮膚/好膚質)、種草(推坑)、氛圍感(氣質/有感覺)。
       - 職場/科技：優化(改善)、項目(專案)、智能(智慧)、質量(品質)、水平(水準)、給到(提供)。
       - 副詞/形容詞：特好(很好)、立馬(立刻)、走心(用心)、給力(厲害/出色)。
       - 語法：不道地的被動語態(如：有被驚訝到 -> 覺得驚訝)。
    3. 台灣絕對不說「好皮」，必須修正為「好皮膚」或「膚質」。
    
    請僅回傳 JSON 格式列表：
    [
      {{
        "original": "原詞",
        "replacement": "台灣在地建議",
        "title": "百科標題",
        "explanation": "為什麼這在大陸流行？台灣更道地的說法是什麼？",
        "suggestion": "具體的修正建議"
      }}
    ]
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
    st.toast(f"✅ 已完成語感修正")

st.title("📱 語感專家：最高嚴格度辨識")
st.caption("目前已將 AI 靈敏度調至最高，將偵測包含語法、副詞在內的所有非在地用語。")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    user_input = st.text_area("輸入任何文字，測試 AI 的嚴格程度：", height=250)
    
    if st.button("🚀 啟動最高靈敏度掃描", use_container_width=True):
        st.session_state.processed_text = user_input
        with st.spinner("AI 專家正在進行深度掃描..."):
            ai_results = start_ai_analysis(user_input)
            
            # 整合本地與 AI 結果
            final_cards = []
            seen_words = []
            # 處理歧義詞
            for word, info in BASE_WIKI.items():
                if word in user_input:
                    card = info.copy(); card['original'] = word
                    final_cards.append(card); seen_words.append(word)
            # 補上 AI 結果
            for r in ai_results:
                if r['original'] not in seen_words:
                    final_cards.append(r)
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        if not active_cards:
            st.success("🎉 掃描完畢！這段文字非常在地。")
        else:
            for item in active_cards:
                with st.expander(f"✨ 嚴格偵測：{item['original']}", expanded=True):
                    st.markdown(f"### {item.get('title', '語境差異辨析')}")
                    st.write(item.get('explanation', ''))
                    
                    if item.get('is_ambiguous'):
                        st.warning("⚠️ 此詞在台灣有多重含意：")
                        cols = st.columns(len(item['options']))
                        for i, opt in enumerate(item['options']):
                            if cols[i].button(opt['label'], key=f"opt_{item['original']}_{i}"):
                                update_text(item['original'], opt['to']); st.rerun()
                    else:
                        target = item.get('replacement', '')
                        if st.button(f"👉 修正為「{target}」", key=f"fix_{item['original']}", use_container_width=True):
                            update_text(item['original'], target); st.rerun()
