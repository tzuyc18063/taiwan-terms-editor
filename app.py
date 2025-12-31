import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心詞庫 ---
st.set_page_config(page_title="語感專家", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 那些需要「極度精準」解釋的詞，我們手動保留最高優先權
PREMIUM_WIKI = {
    "土豆": {
        "title": "🥔 土豆的語意陷阱",
        "explanation": "兩岸指稱物完全不同：\n- **中國**指「馬鈴薯」(Potato)\n- **台灣**指「花生」(Peanut)",
        "options": [
            {"to": "馬鈴薯", "label": "🍟 換成馬鈴薯 (指蔬菜)"},
            {"to": "花生", "label": "🥜 換成花生 (指堅果)"}
        ]
    }
}

# --- 2. 核心偵測與百科生成 ---
def get_analysis(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 強制 AI 回傳結構化的百科資料
    prompt = f"""
    分析以下文字內容："{text}"
    請找出其中所有的中國大陸用語，並為每個詞編寫百科對照。
    必須以 JSON 格式回傳一個列表 (List)，格式如下：
    [
      {{
        "word": "原詞",
        "title": "標題 (如: 視頻 vs 影片)",
        "tw_term": "台灣慣用語",
        "diff": "簡述語境差異",
        "suggestion": "給使用者的建議"
      }}
    ]
    若無偵測到則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        # 增加正則過濾，確保只抓取 JSON 部分
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return []
    except:
        return []

# --- 3. 狀態與 UI 邏輯 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'wiki_results' not in st.session_state: st.session_state.wiki_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 4. 畫面呈現 ---
st.title("📱 語感專家：AI 全自動百科")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入內容：", height=200, value="這視頻質量真好，我想吃土豆。", key="u_input_area")
    
    if st.button("🚀 執行深度語感偵測", use_container_width=True):
        with st.spinner("語感專家正在編寫百科內容..."):
            st.session_state.current_text = u_input
            st.session_state.wiki_results = get_analysis(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科建議")
    
    if st.session_state.is_analyzed:
        curr_text = st.session_state.current_text
        found_any = False
        
        # 1. 優先掃描 AI 偵測出的詞
        for item in st.session_state.wiki_results:
            word = item['word']
            # 確保該詞還存在於目前的文字中
            if word in curr_text:
                found_any = True
                
                # A. 特殊處理「土豆」等精選百科
                if word in PREMIUM_WIKI:
                    info = PREMIUM_WIKI[word]
                    with st.expander(f"📌 精選百科：{word}", expanded=True):
                        st.markdown(f"### {info['title']}")
                        st.write(info['explanation'])
                        btn_cols = st.columns(len(info['options']))
                        for i, opt in enumerate(info['options']):
                            if btn_cols[i].button(opt['label'], key=f"pre_{word}_{i}", use_container_width=True):
                                apply_change(word, opt['to'])
                                st.rerun()
                
                # B. 顯示 AI 自動生成的百科
                else:
                    with st.expander(f"🤖 AI 百科：{word}", expanded=True):
                        st.markdown(f"### {item['title']}")
                        st.write(f"🇹🇼 **台灣慣用：** {item['tw_term']}")
                        st.write(f"🔍 **語境差異：** {item['diff']}")
                        st.info(f"💡 **建議：** {item['suggestion']}")
                        if st.button(f"👉 修正為「{item['tw_term']}」", key=f"ai_{word}", use_container_width=True):
                            apply_change(word, item['tw_term'])
                            st.rerun()

        if not found_any:
            st.success("🎉 目前文字看起來非常本土！")
    else:
        st.info("👋 請點擊偵測，查看 AI 針對「視頻、質量、土豆」生成的語境百科。")
