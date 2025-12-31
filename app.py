import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 初始化與 API 設定 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

# 確保從 Streamlit Secrets 讀取金鑰
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Secrets 中設定您的 GOOGLE_API_KEY")

# --- 2. 核心百科資料庫 (包含歧義處理與完整詞組) ---
BASE_WIKI = {
    "媽生好皮": {
        "title": "✨ 媽生好皮 vs 天生好皮膚",
        "replacement": "天生好皮膚",
        "explanation": "這是大陸社群熱詞。在台灣，我們不說「好皮」，習慣稱呼為「好皮膚」或「好膚質」。",
        "is_ambiguous": False
    },
    "優化": {
        "title": "✨ 優化 vs 改善/提升",
        "replacement": "改善",
        "explanation": "「優化」在台灣多用於電腦技術，日常生活中建議使用「改善」、「提升」或「調整」。",
        "is_ambiguous": False
    },
    "很火": {
        "title": "🔥 「火」的語意辨析",
        "explanation": "這個詞在台灣具備兩種截然不同的語境，請確認您的意思：",
        "is_ambiguous": True,
        "options": [
            {"to": "很紅", "label": "📈 換成「很紅」(指熱門)"},
            {"to": "很火大", "label": "💢 換成「很火大」(指生氣)"},
            {"to": "很火", "label": "👌 維持原樣"}
        ]
    },
    "智能": {
        "title": "🧠 智能 vs 智慧",
        "replacement": "智慧",
        "explanation": "大陸習慣稱「智能」，台灣則普遍使用「智慧」，如智慧型手機、智慧家庭。",
        "is_ambiguous": False
    }
}

# --- 3. AI 自動辨識引擎 (修正 404 錯誤並強化語感) ---
def start_ai_analysis(text):
    if not text.strip(): return []
    
    # 呼叫最新的穩定模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    任務：你是台灣語言專家，請辨識以下文字中「非台灣習慣」的大陸用語或熱詞。
    輸入文字："{text}"
    
    規則：
    1. 找出大陸用語（如：視頻、質量、項目、打印、信息）。
    2. 特別偵測：媽生好皮（必須改為「天生好皮膚」）、很火（註明有熱門或生氣兩種可能）。
    3. 台灣不習慣將「智能」用於軟體功能，建議改為「智慧」或「自動」。
    
    請僅回傳 JSON 格式列表：
    [
      {{
        "original": "原詞",
        "replacement": "台灣建議",
        "title": "百科標題",
        "explanation": "語境差異解釋",
        "suggestion": "修正建議",
        "is_ambiguous": false
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except Exception as e:
        return []

# --- 4. 狀態管理與 UI ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def update_text(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast(f"✅ 文字已成功更新")

# --- UI 呈現 ---
st.title("📱 語感專家：在地化智慧辨識版")
st.caption("自動辨識大陸社群用語與網路熱詞，並提供即時百科對照。")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📝 文字輸入")
    user_input = st.text_area("請輸入您要辨識的文字：", height=250, value="這視頻的智能偵測功能很火，能幫你打造媽生好皮。")
    
    if st.button("🚀 啟動智慧辨識", use_container_width=True):
        st.session_state.processed_text = user_input
        with st.spinner("AI 專家分析中..."):
            # 1. 執行 AI 辨識
            ai_results = start_ai_analysis(user_input)
            
            # 2. 整合本地詞庫 (本地歧義處理優先)
            final_cards = []
            seen_words = []
            
            # 先檢查本地核心詞庫 (處理媽生好皮、火、智能等)
            # 長詞優先排列，避免誤判
            sorted_base = sorted(BASE_WIKI.items(), key=lambda x: len(x[0]), reverse=True)
            for word, info in sorted_base:
                if word in user_input:
                    card = info.copy()
                    card['original'] = word
                    final_cards.append(card)
                    seen_words.append(word)
            
            # 再補上 AI 偵測到的其他詞彙
            for r in ai_results:
                if r['original'] not in seen_words:
                    final_cards.append(r)
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.processed_text, language=None)

with col_right:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        # 只顯示目前文字中還存在的詞卡
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        
        if not active_cards:
            st.success("🎉 檢查完畢！目前的文字用語非常道地且本土。")
        else:
            for item in active_cards:
                with st.expander(f"📌 百科發現：{item['original']}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(item['explanation'])
                    
                    # 歧義處理按鈕
                    if item.get('is_ambiguous'):
                        st.warning("⚠️ 此詞有不同語境，請點擊正確的選項：")
                        btn_cols = st.columns(len(item['options']))
                        for i, opt in enumerate(item['options']):
                            if btn_cols[i].button(opt['label'], key=f"opt_{item['original']}_{i}"):
                                update_text(item['original'], opt['to'])
                                st.rerun()
                    # 一般修正按鈕
                    else:
                        suggestion = item.get('replacement', item.get('tw_term'))
                        if st.button(f"👉 修正為「{suggestion}」", key=f"fix_{item['original']}", use_container_width=True):
                            update_text(item['original'], suggestion)
                            st.rerun()
    else:
        st.info("請在左側輸入文字，點擊「啟動智慧辨識」來開始語感掃描。")
