import streamlit as st

# --- 1. 語感百科資料庫 (WORD_WIKI) ---
# 這裡整合了您要求的所有百科資訊與語境解釋
WORD_WIKI = {
    # 【歧義辨析類】需顯示解釋並提供二選一
    "土豆": {
        "type": "ambiguous",
        "title": "🥔 土豆 (Tǔ dòu) 的兩岸差異",
        "explanation": "兩岸指稱物完全不同：\n- **中國用法**：指「馬鈴薯」(Potato)\n- **台灣用法**：指「花生」(Peanut)",
        "options": [
            {"to": "馬鈴薯", "desc": "🇨🇳 中國語境 (如:洋芋片原料)", "icon": "🍟"},
            {"to": "花生", "desc": "🇹🇼 台灣語境 (如:土豆麵筋)", "icon": "🥜"}
        ]
    },
    "窩心": {
        "type": "ambiguous",
        "title": "❤️ 窩心 (Wō xīn) 的語意相反",
        "explanation": "這個詞在兩岸語意完全相反：\n- **中國用法**：指「憋屈、心裡難受」\n- **台灣用法**：指「貼心、感到溫暖」",
        "options": [
            {"to": "貼心", "desc": "🇹🇼 台灣語境 (感到溫暖)", "icon": "🥰"},
            {"to": "憋屈", "desc": "🇨🇳 中國語境 (心裡難受)", "icon": "😣"}
        ]
    },
    "感冒": {
        "type": "ambiguous",
        "title": "🤧 感冒 (Gǎnmào) 的程度差異",
        "explanation": "用法語氣不同：\n- **中國用法**：「不感冒」指不感興趣。\n- **台灣用法**：「很感冒」指非常反感、討厭。",
        "options": [
            {"to": "反感", "desc": "🇹🇼 台灣語境 (討厭/看不順眼)", "icon": "💢"},
            {"to": "不感興趣", "desc": "🇨🇳 中國語境 (沒興趣/無感)", "icon": "😶"}
        ]
    },
    # 【固定修正類】顯示百科解釋與單一建議
    "視頻": {
        "type": "fix",
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "台灣習慣稱「影片」；「視頻」在台灣多指物理上的「視訊訊號」。",
        "suggestion": "建議改用「影片」更符合台灣日常習慣。"
    },
    "質量": {
        "type": "fix",
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "台灣指好壞用「品質」；「質量」專指物理學重量 (Mass)。",
        "suggestion": "若是指產品好壞，請修正為「品質」。"
    },
    "信息": {
        "type": "fix",
        "title": "📩 信息 vs 訊息",
        "tw_term": "訊息",
        "explanation": "通訊軟體或資料內容，台灣統一稱為「訊息」。",
        "suggestion": "建議修正為「訊息」。"
    },
    "水平": {
        "type": "fix",
        "title": "📈 水平 vs 水準",
        "tw_term": "水準",
        "explanation": "形容人的素養、表現或技術高低，台灣必用「水準」。",
        "suggestion": "建議修正為「水準」。"
    },
    "優化": {
        "type": "fix",
        "title": "✨ 優化 vs 調整/改善",
        "tw_term": "改善",
        "explanation": "雖然優化也通用，但台灣傳統習慣用「改善、調整、提升」。",
        "suggestion": "可考慮修正為「改善」或「調整」。"
    }
}

# --- 2. 邏輯處理函數 ---
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state:
    st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 3. UI 介面設計 ---
st.set_page_config(page_title="語感百科專家", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 語感守護者：百科對照與直覺轉換")
st.write("輸入文字，我們會同步告知台灣語境的差異與建議。")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 文字輸入")
    default_text = "這視頻質量真好，我想吃土豆，但他對土豆不感冒。"
    u_input = st.text_area("請輸入內容：", height=250, value=default_text, key="u_input")
    
    if st.button("🚀 執行語感百科偵測", use_container_width=True):
        st.session_state.current_text = u_input
        st.session_state.is_analyzed = True
    
    if st.session_state.is_analyzed:
        st.markdown("---")
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.current_text, language=None)
        if st.button("清空重置"):
            st.session_state.is_analyzed = False
            st.rerun()

with col2:
    st.subheader("🤳 語感百科卡片")
    
    if st.session_state.is_analyzed:
        text = st.session_state.current_text
        found_any = False
        
        # 遍歷資料庫尋找匹配詞彙
        for word, info in WORD_WIKI.items():
            if word in text:
                found_any = True
                # 使用 Expander 呈現百科卡片視覺
                with st.expander(f"📌 發現詞彙：{word}", expanded=True):
                    st.markdown(f"### {info['title']}")
                    st.write(info['explanation'])
                    
                    if info['type'] == "ambiguous":
                        st.markdown("**💡 請依據您的語境點選正確修正：**")
                        # 並排顯示二選一按鈕
                        btn_cols = st.columns(len(info['options']))
                        for i, opt in enumerate(info['options']):
                            with btn_cols[i]:
                                btn_label = f"{opt['icon']} {opt['desc']}\n\n👉 換成「{opt['to']}」"
                                if st.button(btn_label, key=f"btn_{word}_{i}", use_container_width=True):
                                    apply_change(word, opt['to'])
                                    st.rerun()
                    else:
                        # 固定修正顯示單一按鈕
                        st.info(f"💡 {info['suggestion']}")
                        if st.button(f"👉 修正為台灣語境：{info['tw_term']}", key=f"fix_{word}", use_container_width=True):
                            apply_change(word, info['tw_term'])
                            st.rerun()
        
        if not found_any:
            st.success("🎉 檢查完畢！這段文字目前的用語非常符合台灣語境。")
    else:
        st.info("👋 請在左側輸入文字並點擊「執行偵測」。\n\n系統將自動分析「土豆、視頻、窩心、感冒」等易混淆詞彙並提供百科說明。")

# --- 4. 頁尾 ---
st.markdown("---")
st.caption("語感守護者 v2.0 - 您的兩岸用語導航員")
